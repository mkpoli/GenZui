"""Square-terminal Tangut outlines from serif contours and Noto Sans CJK strokes.

Source files and licences are pinned in sources/tangut-manifest.json.
The geometry and the known limits are described in research/tangut-sans.md.
"""

from itertools import pairwise

import aggdraw
import numpy as np
import pathops
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.basePen import BasePen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.recordingPen import DecomposingRecordingPen, RecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import find_objects, gaussian_filter1d, grey_opening, label
from skimage.measure import approximate_polygon
from skimage.morphology import skeletonize
from tangut_design import redraw
from tangut_folds import sharpen
from tangut_spacing import preserve_white
from tangut_stems import load_hints, straighten

SCALE = 0.64
PAD = 40
BASE = PAD + 880 * SCALE
SIZE = 720


def initialize(serif_path, sans_path):
    global font, sans, face, source_glyphs, source_cmap, sans_glyphs, sans_cmap
    load_hints()
    font = TTFont(serif_path)
    sans = TTFont(sans_path)
    source_glyphs, source_cmap = font.getGlyphSet(), font.getBestCmap()
    sans_glyphs, sans_cmap = sans.getGlyphSet(), sans.getBestCmap()
    face = ImageFont.truetype(str(serif_path), round(1000 * SCALE))


class RasterPen(BasePen):
    def __init__(self, dx, dy):
        super().__init__(None)
        self.path = aggdraw.Path()
        self.dx = dx
        self.dy = dy

    def xy(self, p):
        return p[0] * SCALE + self.dx, self.dy - p[1] * SCALE

    def _moveTo(self, p):
        self.path.moveto(*self.xy(p))

    def _lineTo(self, p):
        self.path.lineto(*self.xy(p))

    def _curveToOne(self, a, b, c):
        self.path.curveto(*self.xy(a), *self.xy(b), *self.xy(c))

    def _qCurveToOne(self, a, b):
        start = self._getCurrentPoint()
        c1 = tuple(start[i] + 2 / 3 * (a[i] - start[i]) for i in (0, 1))
        c2 = tuple(b[i] + 2 / 3 * (a[i] - b[i]) for i in (0, 1))
        self._curveToOne(c1, c2, b)

    def _closePath(self):
        self.path.close()


def groups_for(cp):
    gs = source_glyphs
    pen = DecomposingRecordingPen(gs)
    gs[source_cmap[cp]].draw(pen)
    contours = []
    part = []
    for op, args in pen.value:
        part.append((op, args))
        if op in ("closePath", "endPath"):
            p = RecordingPen()
            p.value = part
            area = AreaPen(None)
            p.replay(area)
            bounds = BoundsPen(None)
            p.replay(bounds)
            contours.append((p, area.value, bounds.bounds))
            part = []
    groups = [([p], b) for p, a, b in contours if a < 0]
    boundaries = []
    for records, _ in groups:
        boundary = pathops.Path()
        records[0].replay(boundary.getPen())
        boundaries.append(boundary)
    for p, a, b in contours:
        if a <= 0:
            continue
        points = [args[-1] for op, args in p.value if args and args[-1] is not None]
        candidates = [
            (i, (q[2] - q[0]) * (q[3] - q[1]))
            for i, (_, q) in enumerate(groups)
            if q[0] <= b[0]
            and q[1] <= b[1]
            and q[2] >= b[2]
            and q[3] >= b[3]
            and all(boundaries[i].contains(point) for point in points)
        ]
        if candidates:
            groups[min(candidates, key=lambda it: it[1])[0]][0].append(p)
        else:
            raise ValueError(f"Unattached hole {cp:X}")
    return groups


def paths_for_group(group):
    records, bounds = group
    x0, y0, x1, y1 = bounds
    dx = PAD - x0 * SCALE
    dy = PAD + y1 * SCALE
    image = Image.new(
        "L",
        (int((x1 - x0) * SCALE + 2 * PAD + 1), int((y1 - y0) * SCALE + 2 * PAD + 1)),
    )
    pen = RasterPen(dx, dy)
    for rec in records:
        rec.replay(pen)
    context = aggdraw.Draw(image)
    context.path(pen.path, aggdraw.Brush(255))
    context.flush()
    mask = np.asarray(image) > 127
    pixels = set(map(tuple, np.argwhere(skeletonize(mask))))

    def neighbors(p):
        y, x = p
        return [
            (y + dy, x + dx)
            for dy, dx in (
                (-1, 0),
                (1, 0),
                (0, -1),
                (0, 1),
                (-1, -1),
                (-1, 1),
                (1, -1),
                (1, 1),
            )
            if (y + dy, x + dx) in pixels
            and not (dy and dx and ((y, x + dx) in pixels or (y + dy, x) in pixels))
        ]

    for _ in range(3):
        adj = {p: neighbors(p) for p in pixels}
        remove = set()
        for start in sorted(pixels):
            if len(adj[start]) != 1:
                continue
            chain = [start]
            prev = None
            cur = start
            arc_length = 0.0
            while arc_length <= 96 * SCALE:
                following = [p for p in adj[cur] if p != prev]
                if len(following) != 1:
                    if len(following) > 1:
                        # A real crossing continues through its junction; a serif spur ends beside the stem.
                        ref = np.array(chain[max(0, len(chain) - 14)], float)
                        inward = np.array(cur, float) - ref
                        inward /= max(np.linalg.norm(inward), 1)
                        continuation = False
                        long_rays = []
                        for nxt in following:
                            queue = [
                                (
                                    cur,
                                    nxt,
                                    float(np.linalg.norm(np.array(cur) - nxt)),
                                    {cur},
                                    None,
                                )
                            ]
                            rays = []
                            while queue:
                                before, at, distance, visited, initial = queue.pop()
                                if at in visited:
                                    continue
                                if initial is None and distance >= 25 * SCALE:
                                    initial = np.array(at, float) - np.array(cur, float)
                                if distance >= round(140 * SCALE) or len(adj[at]) == 1:
                                    rays.append((at, distance, initial))
                                    continue
                                for after in adj[at]:
                                    if after != before and after not in visited:
                                        queue.append(
                                            (
                                                at,
                                                after,
                                                distance
                                                + np.linalg.norm(np.array(at) - after),
                                                visited | {at},
                                                initial,
                                            )
                                        )
                            for end, distance, initial in rays:
                                direction = (
                                    initial
                                    if initial is not None
                                    else np.array(end, float) - np.array(cur, float)
                                )
                                norm = np.linalg.norm(direction)
                                if (
                                    norm > 10 * SCALE
                                    and distance + arc_length > 200 * SCALE
                                    and np.dot(direction / max(norm, 1), inward) > 0.98
                                ):
                                    continuation = True
                                if distance >= round(140 * SCALE):
                                    long_rays.append(direction / max(norm, 1))
                        crossbar = any(
                            np.dot(a, b) < -0.88 for a in long_rays for b in long_rays
                        )
                        if not continuation and not crossbar:
                            remove.update(chain[:-1])
                    break
                previous = cur
                prev, cur = cur, following[0]
                arc_length += float(np.linalg.norm(np.array(previous) - cur))
                chain.append(cur)
        if not remove:
            break
        pixels -= remove
    adj = {p: neighbors(p) for p in pixels}
    seen = set()
    paths = []

    def trace(start, nxt):
        chain = [start]
        prev, cur = start, nxt
        seen.add(frozenset((start, nxt)))
        while True:
            chain.append(cur)
            if len(adj[cur]) != 2:
                break
            after = next(p for p in adj[cur] if p != prev)
            edge = frozenset((cur, after))
            if edge in seen:
                break
            seen.add(edge)
            prev, cur = cur, after
        paths.append(np.array([((x - dx) / SCALE, (dy - y) / SCALE) for y, x in chain]))

    for start in sorted(adj):
        if len(adj[start]) == 2:
            continue
        for nxt in adj[start]:
            if frozenset((start, nxt)) not in seen:
                trace(start, nxt)
    for start in sorted(adj):
        for nxt in adj[start]:
            if frozenset((start, nxt)) not in seen:
                trace(start, nxt)
    length = sum(np.linalg.norm(np.diff(p, axis=0), axis=1).sum() for p in paths)
    width = 68 * min(1, (4200 / max(length, 1)) ** 0.4)
    return (
        paths,
        float(width),
        {
            ((x - dx) / SCALE, (dy - y) / SCALE)
            for (y, x), ns in adj.items()
            if len(ns) == 1
        },
    )


def donor(char, box):
    gs = sans_glyphs
    name = sans_cmap[ord(char)]
    b = BoundsPen(gs)
    gs[name].draw(b)
    x0, y0, x1, y1 = b.bounds
    a, b, c, d = box
    sx = (c - a) / (x1 - x0)
    sy = (d - b) / (y1 - y0)
    shape = pathops.Path()
    gs[name].draw(
        TransformPen(shape.getPen(), (sx, 0, 0, sy, a - x0 * sx, b - y0 * sy))
    )
    return shape


def stroke_paths(paths, width):
    shape = pathops.Path()
    donors = []
    for points in paths:
        if len(points) < 2:
            continue
        length = np.linalg.norm(np.diff(points, axis=0), axis=1).sum()
        if length < 4:
            continue
        if len(points) > 6:
            simplified = approximate_polygon(points, 3)
            corners = [0]
            for a, b, c in zip(simplified, simplified[1:], simplified[2:]):
                incoming, outgoing = b - a, c - b
                ni, no = np.linalg.norm(incoming), np.linalg.norm(outgoing)
                if ni < 3 or no < 3:
                    continue
                vi, vo = incoming / ni, outgoing / no
                axis_turn = (
                    min(abs(vi)) < 0.04 and min(abs(vo)) < 0.04 and np.dot(vi, vo) < 0.2
                )
                if axis_turn or np.dot(vi, vo) < -0.2:
                    matches = np.flatnonzero(np.all(points == b, axis=1))
                    if len(matches):
                        corners.append(int(matches[0]))
            corners.append(len(points) - 1)
            pieces = []
            for start, stop in pairwise(corners):
                segment = points[start : stop + 1]
                p = gaussian_filter1d(segment, 1.5, axis=0, mode="nearest")
                p[0], p[-1] = segment[0], segment[-1]
                simplified = approximate_polygon(p, 2)
                pieces.extend(simplified if not pieces else simplified[1:])
            points = np.asarray(pieces)
        x0, y0 = points.min(axis=0)
        x1, y1 = points.max(axis=0)
        if y1 - y0 < width * 0.7 and x1 - x0 > max(width * 1.5, (y1 - y0) * 10):
            y = (y1 + y0) / 2
            donors.append(donor("一", (x0, y - width / 2, x1, y + width / 2)))
            continue
        if x1 - x0 < width * 0.7 and y1 - y0 > max(width * 1.5, (x1 - x0) * 10):
            x = (x1 + x0) / 2
            donors.append(donor("丨", (x - width / 2, y0, x + width / 2, y1)))
            continue
        shape.moveTo(*points[0])
        for i in range(len(points) - 1):
            a, b = points[i], points[i + 1]
            prev, after = points[max(0, i - 1)], points[min(len(points) - 1, i + 2)]
            segment = b - a
            span = np.linalg.norm(segment)
            if span > width and min(abs(segment[0]), abs(segment[1])) < width * 0.1:
                shape.lineTo(*b)
                continue

            def handle(incoming, outgoing, fallback):
                ni, no = np.linalg.norm(incoming), np.linalg.norm(outgoing)
                if ni < 1 or no < 1:
                    return fallback / max(np.linalg.norm(fallback), 1)
                vi, vo = incoming / ni, outgoing / no
                # Preserve structural corners; smooth only gradual turns.
                axis_corner = min(abs(vi)) < 0.08 and min(abs(vo)) < 0.08
                if axis_corner and np.dot(vi, vo) < 0.8 or np.dot(vi, vo) < -0.2:
                    return fallback / max(np.linalg.norm(fallback), 1)
                tangent = vi + vo
                return tangent / max(np.linalg.norm(tangent), 1)

            c1 = a + handle(a - prev, segment, segment) * span / 3
            c2 = b - handle(segment, after - b, segment) * span / 3
            shape.cubicTo(*c1, *c2, *b)
        if np.linalg.norm(points[0] - points[-1]) < 2:
            shape.close()
    shape.stroke(width, pathops.LineCap.BUTT_CAP, pathops.LineJoin.MITER_JOIN, 1.8)
    shape.convertConicsToQuads(0.2)
    for d in donors:
        shape = pathops.op(shape, d, pathops.PathOp.UNION)
    shape = pathops.op(shape, pathops.Path(), pathops.PathOp.UNION)
    return shape, len(donors)


def fit_region(paths, width, bounds, transform=None):
    part, donors = stroke_paths(paths, width)
    if transform is not None:
        return part.transform(*transform), donors, transform
    x0, y0, x1, y1 = part.bounds
    a, b, c, d = bounds
    tx, ty, sx, sy = 0.0, 0.0, 1.0, 1.0
    if c - a > width * 1.5 and x1 - x0 > c - a:
        sx = (c - a) / (x1 - x0)
        tx = a - x0 * sx
    elif c - a > width * 1.5:
        tx = max(a - x0, min(0, c - x1))
    if d - b > width * 1.5 and y1 - y0 > d - b:
        sy = (d - b) / (y1 - y0)
        ty = b - y0 * sy
    elif d - b > width * 1.5:
        ty = max(b - y0, min(0, d - y1))
    transform = (sx, 0, 0, sy, tx, ty)
    return part.transform(*transform), donors, transform


def draw_glyph(cp):
    results = [paths_for_group(group) for group in groups_for(cp)]
    paths = [p for result in results for p in result[0]]
    tips = set().union(*(result[2] for result in results))
    original = Image.new("L", (SIZE, SIZE))
    ImageDraw.Draw(original).text(
        (PAD, BASE), chr(cp), font=face, fill=255, anchor="ls"
    )
    original_mask = np.asarray(original) > 127
    source_records = DecomposingRecordingPen(source_glyphs)
    source_glyphs[source_cmap[cp]].draw(source_records)
    edges = []
    current = None
    for op, args in source_records.value:
        if op == "lineTo" and current is not None:
            end = args[0]
            for axis in (0, 1):
                if abs(end[axis] - current[axis]) < 1:
                    low, high = sorted((end[1 - axis], current[1 - axis]))
                    if high - low > 25:
                        edges.append((axis, end[axis], low, high))
        if args and args[-1] is not None:
            current = args[-1]
        if op in ("closePath", "endPath"):
            current = None
    end_flags = [(tuple(p[0]) in tips, tuple(p[-1]) in tips) for p in paths]
    paths = straighten(paths, tips, cp, original_mask, SCALE, PAD, BASE, edges)
    paths = sharpen(paths, original_mask, SCALE, PAD, BASE)
    length = sum(np.linalg.norm(np.diff(p, axis=0), axis=1).sum() for p in paths)
    width = 68 * min(1, (4200 / max(length, 1)) ** 0.4)
    shapes = []
    original_shapes = []
    grouped = []
    grouped_flags = []
    boxes = []
    transforms = []
    donor_count = 0
    offset = 0
    for result, (records, bounds) in zip(results, groups_for(cp)):
        group_paths = paths[offset : offset + len(result[0])]
        grouped.append(group_paths)
        grouped_flags.append(end_flags[offset : offset + len(result[0])])
        boxes.append(bounds)
        offset += len(result[0])
        part, donors, transform = fit_region(group_paths, width, bounds)
        transforms.append(transform)
        donor_count += donors
        shapes.append(part)
        original_shape = pathops.Path()
        for record in records:
            record.replay(original_shape.getPen())
        original_shapes.append(original_shape)
    contractions = [0] * len(shapes)
    trims = {}
    # Each free end can move at most 64 units in eight bounded steps.
    for _ in range(8 * sum(sum(flags) for group in grouped_flags for flags in group)):
        choices = []
        for i in range(len(shapes)):
            for j in range(i):
                if (
                    pathops.op(
                        original_shapes[i],
                        original_shapes[j],
                        pathops.PathOp.INTERSECTION,
                    ).area
                    > 1
                ):
                    continue
                halo = pathops.Path(shapes[i])
                halo.stroke(
                    12, pathops.LineCap.BUTT_CAP, pathops.LineJoin.MITER_JOIN, 2
                )
                halo = pathops.op(halo, shapes[i], pathops.PathOp.UNION)
                collision = pathops.op(halo, shapes[j], pathops.PathOp.INTERSECTION)
                if collision.area <= 1:
                    continue
                centres = [
                    np.array(
                        [
                            (c.bounds[0] + c.bounds[2]) / 2,
                            (c.bounds[1] + c.bounds[3]) / 2,
                        ]
                    )
                    for c in collision.contours
                    if c.area > 1
                ]
                for region in (i, j):
                    for index, (points, flags) in enumerate(
                        zip(grouped[region], grouped_flags[region])
                    ):
                        if (
                            np.linalg.norm(np.diff(points, axis=0), axis=1).sum()
                            < width
                        ):
                            continue
                        for side, free in enumerate(flags):
                            if not free or trims.get((region, index, side), 0) >= 64:
                                continue
                            endpoint = points[0 if side == 0 else -1]
                            sx, _, _, sy, tx, ty = transforms[region]
                            endpoint = endpoint * [sx, sy] + [tx, ty]
                            distance = min(
                                (
                                    np.linalg.norm(endpoint - centre)
                                    for centre in centres
                                ),
                                default=np.inf,
                            )
                            if distance < width * 1.3:
                                choices.append((distance, region, index, side))
        if not choices:
            break
        _, region, index, side = min(choices)
        points = grouped[region][index]
        if side:
            points = points[::-1]
        lengths = np.r_[0, np.cumsum(np.linalg.norm(np.diff(points, axis=0), axis=1))]
        if lengths[-1] < width:
            break
        cut = 8
        at = int(np.searchsorted(lengths, cut))
        start = points[at - 1] + (points[at] - points[at - 1]) * (
            cut - lengths[at - 1]
        ) / (lengths[at] - lengths[at - 1])
        points = np.vstack([start, points[at:]])
        grouped[region][index] = points[::-1] if side else points
        shapes[region], _, _ = fit_region(
            grouped[region], width, boxes[region], transforms[region]
        )
        trims[(region, index, side)] = trims.get((region, index, side), 0) + cut
        contractions[region] += 1
    shape = pathops.Path()
    for part in shapes:
        shape = pathops.op(shape, part, pathops.PathOp.UNION)
    recovered = 0
    # Recover straight structural stems from the source ink, independently of branch pruning.
    original = Image.new("L", (SIZE, SIZE))
    ImageDraw.Draw(original).text(
        (PAD, BASE), chr(cp), font=face, fill=255, anchor="ls"
    )
    original_mask = np.asarray(original) > 127
    vertical = grey_opening(original_mask, size=(round(110 * SCALE), round(14 * SCALE)))
    labels, _count = label(vertical)
    for i, box in enumerate(find_objects(labels), 1):
        if box is None:
            continue
        ys, xs = np.where(labels[box] == i)
        xs = xs + box[1].start
        ys = ys + box[0].start
        # Measure the original ink around the candidate, not the artificial vertical
        # strip produced by opening: diagonal terminals can contain a vertical strip.
        centre_x = round(np.median(xs))
        rows = np.unique(ys)
        # Joined uprights can share a component without sharing a centreline.
        # Reject a donor that would bridge blank rows through a real counter.
        if np.count_nonzero(original_mask[rows, centre_x]) < len(rows) * 0.95:
            continue
        original_runs = []
        for row in rows:
            left = right = centre_x
            while left > 0 and original_mask[row, left - 1]:
                left -= 1
            while right + 1 < SIZE and original_mask[row, right + 1]:
                right += 1
            original_runs.append(((left + right) / 2, right - left + 1))
        typical = np.median([run[1] for run in original_runs])
        centres = [
            centre
            for centre, span in original_runs
            if typical * 0.5 <= span < typical * 1.5
        ]
        if (
            len(centres) < 10
            or np.percentile(centres, 90) - np.percentile(centres, 10) > 12 * SCALE
        ):
            continue
        if ys.max() - ys.min() < 120 * SCALE:
            continue
        xx = (np.median(xs) - PAD) / SCALE
        top = (BASE - ys.min()) / SCALE
        bottom = (BASE - ys.max()) / SCALE
        probes = np.linspace(bottom + width * 0.2, top - width * 0.2, 9)
        coverage = sum(shape.contains((float(xx), float(y))) for y in probes) / len(
            probes
        )
        if coverage < 0.8:
            shape = pathops.op(
                shape,
                donor(
                    "丨",
                    (
                        xx - width / 2,
                        bottom + width * 0.15,
                        xx + width / 2,
                        top - width * 0.15,
                    ),
                ),
                pathops.PathOp.UNION,
            )
            recovered += 1
    designed = redraw(cp, width, donor)
    if designed is not None:
        shape = designed
        recovered = 0
    shape = preserve_white(shape, original_mask, SCALE, PAD, BASE, width, RasterPen)
    pen = TTGlyphPen(None)
    shape.draw(Cu2QuPen(pen, max_err=0.4, reverse_direction=True))
    glyph = pen.glyph()
    glyph.recalcBounds(None)
    if glyph.numberOfContours <= 0:
        raise ValueError(f"Empty reconstructed glyph U+{cp:X}")
    return (
        cp,
        glyph,
        {
            "stroke_width": round(width, 3),
            "donor_strokes": donor_count,
            "recovered_stems": recovered,
            "source_groups": len(groups_for(cp)),
            "terminal_spacing_corrections": sum(contractions),
            "source_derived_redraw": designed is not None,
        },
    )
