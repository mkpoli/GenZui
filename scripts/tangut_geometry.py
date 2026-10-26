"""Square-terminal Tangut outlines from serif contours and Noto Sans CJK strokes.

Source files and licences are pinned in sources/tangut-manifest.json.
The geometry and the known limits are described in research/tangut-sans.md.
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from skimage.morphology import skeletonize
from skimage.measure import approximate_polygon
from scipy.ndimage import gaussian_filter1d, grey_opening, label, find_objects
import pathops
import aggdraw
from fontTools.pens.basePen import BasePen
from fontTools.pens.recordingPen import RecordingPen, DecomposingRecordingPen
from fontTools.pens.areaPen import AreaPen
from fontTools.ttLib import TTFont
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.transformPen import TransformPen

SCALE = 0.64
PAD = 40
BASE = PAD + 880 * SCALE
SIZE = 720


def initialize(serif_path, sans_path):
    global font, sans, face, source_glyphs, source_cmap, sans_glyphs, sans_cmap
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
                                    and np.dot(direction / max(norm, 1), inward) > 0.88
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
    width = 64 * min(1, (3600 / max(length, 1)) ** 0.5)
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


def draw_glyph(cp):
    results = [paths_for_group(group) for group in groups_for(cp)]
    paths = [p for result in results for p in result[0]]
    tips = set().union(*(result[2] for result in results))
    length = sum(np.linalg.norm(np.diff(p, axis=0), axis=1).sum() for p in paths)
    width = 64 * min(1, (3600 / max(length, 1)) ** 0.5)
    shape = pathops.Path()
    donors = []
    recovered = 0
    for points in paths:
        if len(points) < 2:
            continue
        length = np.linalg.norm(np.diff(points, axis=0), axis=1).sum()
        if length < 4:
            continue
        for reverse in (False, True):
            if reverse:
                points = points[::-1].copy()
            if tuple(points[0]) in tips and length > 150:
                distances = np.r_[
                    0, np.cumsum(np.linalg.norm(np.diff(points, axis=0), axis=1))
                ]
                trim = min(65, length * 0.15)
                at = min(len(points) - 3, int(np.searchsorted(distances, trim)))
                direction = points[min(len(points) - 1, at + 10)] - points[at]
                direction /= max(np.linalg.norm(direction), 1)
                points = points[at:].copy()
                points[0] -= direction * min(35, trim * 0.6)
            if reverse:
                points = points[::-1].copy()
        if len(points) > 6:
            p = gaussian_filter1d(points, 1.5, axis=0, mode="nearest")
            p[0] = points[0]
            p[-1] = points[-1]
            points = approximate_polygon(p, 2)
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
            c1, c2 = a + (b - prev) / 6, b - (after - a) / 6
            shape.cubicTo(*c1, *c2, *b)
        if np.linalg.norm(points[0] - points[-1]) < 2:
            shape.close()
    shape.stroke(width, pathops.LineCap.BUTT_CAP, pathops.LineJoin.MITER_JOIN, 3)
    shape.convertConicsToQuads(0.2)
    for d in donors:
        shape = pathops.op(shape, d, pathops.PathOp.UNION)
    shape.simplify()
    # Recover straight structural stems from the source ink, independently of branch pruning.
    original = Image.new("L", (SIZE, SIZE))
    ImageDraw.Draw(original).text(
        (PAD, BASE), chr(cp), font=face, fill=255, anchor="ls"
    )
    original_mask = np.asarray(original) > 127
    vertical = grey_opening(original_mask, size=(round(110 * SCALE), round(14 * SCALE)))
    labels, count = label(vertical)
    for i, box in enumerate(find_objects(labels), 1):
        if box is None:
            continue
        ys, xs = np.where(labels[box] == i)
        xs = xs + box[1].start
        ys = ys + box[0].start
        # Measure the original ink around the candidate, not the artificial vertical
        # strip produced by opening: diagonal terminals can contain a vertical strip.
        centre_x = int(round(np.median(xs)))
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
            "donor_strokes": len(donors),
            "recovered_stems": recovered,
            "source_groups": len(groups_for(cp)),
        },
    )
