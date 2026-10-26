"""Fit straight stems using pinned Noto Tangut Glyphs stem zones and contour edges."""

import re
import tarfile
from itertools import pairwise
from pathlib import Path

import numpy as np

HINTS = {}


def load_hints():
    if HINTS:
        return
    with tarfile.open(
        Path(__file__).resolve().parents[1]
        / "sources/upstream/NotoSerifTangut/tangut-source.tar.gz"
    ) as archive:
        for member in archive:
            if not member.name.endswith(".glyph"):
                continue
            text = archive.extractfile(member).read().decode()
            encoded = re.search(r"\nunicode = (\d+);", text)
            block = re.search(r"hints = \((.*?)\n\);\nlayerId", text, re.DOTALL)
            if not encoded or not block:
                continue
            hints = []
            for record in re.findall(r"\{(.*?)\}", block[1], re.DOTALL):
                place = re.search(r"place = \((-?[\d.]+),([\d.]+)\);", record)
                if place and "type = Stem;" in record:
                    start, width = map(float, place.groups())
                    hints.append(
                        (
                            1 if "horizontal = 1;" in record else 0,
                            start + width / 2,
                            width,
                        )
                    )
            HINTS[int(encoded[1])] = hints


def straighten(paths, tips, cp, mask, scale, pad, base, edges=()):
    hints = HINTS.get(cp, [])

    def at(x, y):
        xx = np.rint(x * scale + pad).astype(int)
        yy = np.rint(base - y * scale).astype(int)
        return mask[np.clip(yy, 0, len(mask) - 1), np.clip(xx, 0, len(mask[0]) - 1)]

    new = []
    for points in paths:
        points = points.copy()
        # Choose the closest supported hint from the unmodified path. Hints for
        # another component can overlap in x/y; applying them in order moves stems.
        labels = []
        arc = np.r_[0, np.cumsum(np.linalg.norm(np.diff(points, axis=0), axis=1))]
        for axis in (0, 1):
            chosen = np.full(len(points), -1, dtype=int)
            best = np.full(len(points), np.inf)
            for index, (hint_axis, centre, width) in enumerate(hints):
                if hint_axis != axis:
                    continue
                delta = np.abs(points[:, axis] - centre)
                take = np.flatnonzero(
                    (delta < min(44, width * 0.6 + 12)) & (delta < best)
                )
                if not len(take):
                    continue
                coords = points[take, 1 - axis, None] + np.linspace(-48, 48, 13)
                support = at(coords, centre) if axis == 1 else at(centre, coords)
                accepted = take[np.mean(support, axis=1) > 0.91]
                chosen[accepted] = index
                best[accepted] = delta[accepted]
            start = 0
            while start < len(points):
                stop = start + 1
                while stop < len(points) and chosen[stop] == chosen[start]:
                    stop += 1
                if chosen[start] >= 0 and arc[stop - 1] - arc[start] >= 90:
                    centre = hints[chosen[start]][1]
                    trim = min(45, (arc[stop - 1] - arc[start]) * 0.15)
                    inner_start = max(
                        start, int(np.searchsorted(arc, arc[start] + trim))
                    )
                    inner_stop = min(
                        stop, int(np.searchsorted(arc, arc[stop - 1] - trim)) + 1
                    )
                    run = points[inner_start:inner_stop, axis]
                    variation = np.percentile(run, 95) - np.percentile(run, 5)
                    along = points[inner_start:inner_stop, 1 - axis]
                    slope = np.polyfit(along, run, 1)[0] if np.ptp(along) > 1 else 1
                    source_width = hints[chosen[start]][2]
                    low, high = np.percentile(along, [5, 95])
                    support = []
                    for side in (-1, 1):
                        coordinate = centre + side * source_width / 2
                        support.append(
                            sum(
                                max(0, min(high, end) - max(low, begin))
                                for fixed, value, begin, end in edges
                                if fixed == axis and abs(value - coordinate) < 2
                            )
                        )
                    straight_edges = min(support) > min(40, (high - low) * 0.35)
                    if (
                        variation <= 5
                        and abs(slope) < 0.01
                        or straight_edges
                        and abs(slope) < 0.06
                    ):
                        labels.append((inner_start, inner_stop, axis, centre))
                start = stop
        for start, stop, axis, centre in labels:
            points[start:stop, axis] = centre
        # Join nearby orthogonal runs at their common corner, keeping gradual curves.
        labels.sort()
        for left, right in pairwise(labels):
            _a, b, axis, centre = left
            c, _d, other, other_centre = right
            if axis == other or c < b or arc[c] - arc[b - 1] > 100:
                continue
            corner = np.empty(2)
            corner[axis] = centre
            corner[other] = other_centre
            if (
                np.linalg.norm(corner - points[b - 1])
                + np.linalg.norm(corner - points[c])
                < 150
            ):
                points[b:c] = corner
        # Fit the body direction beyond the serif, then extend a clean terminal
        # back to the source ink boundary. Remove the old tip instead of dragging it.
        flags = [tuple(paths[len(new)][0]) in tips, tuple(paths[len(new)][-1]) in tips]
        for reverse, free in zip((False, True), flags):
            if reverse:
                points = points[::-1].copy()
            if free and len(points) > 4:
                lengths = np.r_[
                    0, np.cumsum(np.linalg.norm(np.diff(points, axis=0), axis=1))
                ]
                trim = min(65, lengths[-1] * 0.16)
                index = min(len(points) - 3, int(np.searchsorted(lengths, trim)))
                farther = min(
                    len(points) - 1, int(np.searchsorted(lengths, lengths[index] + 35))
                )
                anchor = points[index].copy()
                direction = anchor - points[farther]
                norm = np.linalg.norm(direction)
                if norm > 1:
                    direction /= norm
                    axis = None
                    candidates = []
                    for start, stop, fixed, centre in labels:
                        distance = arc[-1] - arc[stop - 1] if reverse else arc[start]
                        if distance < 100 and abs(direction[1 - fixed]) > 0.8:
                            candidates.append((distance, fixed, centre))
                    if candidates:
                        _, fixed, centre = min(candidates)
                        for at_index in range(index, min(len(points) - 2, index + 80)):
                            if (
                                abs(points[at_index, fixed] - centre) < 0.2
                                and abs(
                                    points[min(len(points) - 1, at_index + 8), fixed]
                                    - centre
                                )
                                < 0.2
                            ):
                                index = at_index
                                anchor = points[index].copy()
                                break
                        axis = 1 - fixed
                        direction = (
                            np.array([np.sign(direction[0]), 0.0])
                            if axis == 0
                            else np.array([0.0, np.sign(direction[1])])
                        )
                    last = anchor.copy()
                    if axis is None:
                        # Curved tips taper in the serif face; keep a short square cut instead
                        # of extrapolating through the terminal swelling.
                        index = min(
                            len(points) - 3,
                            int(np.searchsorted(lengths, min(25, lengths[-1] * 0.08))),
                        )
                        points = points[index:]
                    else:
                        if at(*anchor):
                            for step in range(1, 151):
                                probe = anchor + direction * step
                                if not at(*probe):
                                    break
                                last = probe
                        points = np.vstack([last, points[index:]])
            if reverse:
                points = points[::-1].copy()
        keep = np.r_[True, np.linalg.norm(np.diff(points, axis=0), axis=1) > 0.1]
        if keep.sum() > 1:
            new.append(points[keep])
        else:
            new.append(points[:2])
    return new
