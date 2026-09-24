"""Funatsu's Okinawan kana composed from GenZui's own hiragana strokes.

The letters that keep their hand-drawn form are in okinawan_drawings.py.

Each letter is assembled from whole strokes of the Noto Serif kana it
extends, so the brush entries, the thick-thin contrast and the terminals are
Noto's. A stroke is cut only where the cut end is buried in another stroke.
Topology and placement follow the letters embedded in Funatsu's 2016 chart.

Coordinates are font units on a 1000-unit em with the baseline at 0; the
kana body runs from about -60 to 800.
"""
import pathops
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.recordingPen import RecordingPen

DRAWINGS = {}


def drawing(cp):
    def register(fn):
        DRAWINGS[cp] = fn
        return fn
    return register


class Kit:
    def __init__(self, font, contours, transform):
        self.font, self.contours, self.transform = font, contours, transform

    def part(self, ch, *indices):
        return self.contours(self.font, ord(ch), list(indices) if indices else None)

    @staticmethod
    def bounds(pen):
        b = BoundsPen(None)
        pen.replay(b)
        return b.bounds

    def move(self, pen, sx=1, sy=None, dx=0, dy=0, origin=None):
        """Scale about origin (default: the pen's lower-left) and translate."""
        sy = sx if sy is None else sy
        x0, y0 = origin or self.bounds(pen)[:2]
        return self.transform(pen, (sx, 0, 0, sy, x0 - sx * x0 + dx, y0 - sy * y0 + dy))

    def box(self, pen, left, bottom, right=None, top=None):
        """Fit into a box; a missing side keeps the aspect ratio."""
        x0, y0, x1, y1 = self.bounds(pen)
        sx = (right - left) / (x1 - x0) if right is not None else None
        sy = (top - bottom) / (y1 - y0) if top is not None else None
        sx, sy = sx or sy, sy or sx
        return self.transform(pen, (sx, 0, 0, sy, left - sx * x0, bottom - sy * y0))

    @staticmethod
    def _op(pen, polygon, op):
        shape, window = pathops.Path(), pathops.Path()
        pen.replay(shape.getPen())
        wp = window.getPen()
        wp.moveTo(polygon[0])
        for point in polygon[1:]:
            wp.lineTo(point)
        wp.closePath()
        out = RecordingPen()
        pathops.op(shape, window, op).draw(out)
        return out

    def keep(self, pen, *polygon):
        """The part of a stroke inside a polygon."""
        return self._op(pen, polygon, pathops.PathOp.INTERSECTION)

    def drop(self, pen, *polygon):
        """The part of a stroke outside a polygon."""
        return self._op(pen, polygon, pathops.PathOp.DIFFERENCE)


def small_i(k, left, bottom, right):
    """The two strokes of ぃ, as the vowel a Funatsu letter carries."""
    return [k.box(k.part('ぃ'), left, bottom, right)]


def fu_left(k):
    """ふ's top and centre stroke with its left dot; the right dot gives way."""
    parts = [k.part('ふ', 0), k.keep(k.part('ふ', 1), (0, -100), (330, -100), (330, 400), (0, 400))]
    return [k.move(p, sx=.82, sy=1, origin=(0, 0), dx=40) for p in parts]


@drawing(0xF45B)  # HWI
def hwi(k):
    return fu_left(k) + small_i(k, 540, -20, 960)


def stretch(k, pen, top, bottom):
    """Stretch a stroke along its length only, so its weight is unchanged."""
    y0, y1 = k.bounds(pen)[1::2]
    return k.move(pen, sx=1, sy=(top - bottom) / (y1 - y0), dy=bottom - y0)


def stem(k, x, bottom, top):
    """は's left stroke as the glottal mark before ゆ and よ."""
    return k.box(k.part('は', 1), x, bottom, None, top)


@drawing(0xF45E)  # glottal YU
def glottal_yu(k):
    return [stem(k, 40, 250, 760), k.box(k.part('ゆ'), 200, -62, 950)]


@drawing(0xF45F)  # glottal YO
def glottal_yo(k):
    return [stem(k, 90, 60, 760), k.move(k.part('よ'), dx=80)]


def dot(k):
    """こ's upper stroke, the short mark set above the glottal W letters."""
    return k.box(k.part('こ', 1), 330, 720, 640)


def dotted(k, body):
    """A body set a little smaller under the dot, keeping its proportions."""
    return [dot(k)] + [k.move(p, sx=.88, origin=(470, -40)) for p in body]


@drawing(0xF460)  # glottal WA: ゐ's zig and rising loop, closing with わ's loop
def glottal_wa(k):
    # The chart's WA is WI without the small inner loop. Lowered by 42, わ's
    # loop runs on top of ゐ's along the bottom arc from x = 720 to 800 with
    # the same width, so they are joined at x = 740: ゐ loses its small loop
    # and the rest of its bottom, and わ supplies the end of the loop.
    top = k.drop(k.part('ゐ'), (410, -100), (740, -100), (740, 245), (410, 245))
    bottom = k.keep(k.move(k.part('わ', 0), dy=-42), (410, -100), (740, -100), (740, 245), (410, 245))
    return dotted(k, [top, bottom])


@drawing(0xF461)  # glottal WI
def glottal_wi(k):
    return dotted(k, [k.part('ゐ')])


@drawing(0xF462)  # glottal WE
def glottal_we(k):
    return dotted(k, [k.part('ゑ')])


@drawing(0xF463)  # glottal N: ん with い's falling stroke at the upper right
def glottal_n(k):
    mark = k.box(k.part('い', 1), 650, 420, None, 670)
    return [k.move(k.part('ん'), dx=-20), mark]


@drawing(0xF467)  # SI: す with a long falling stroke on the right
def si(k):
    # す moves left; its bar is shortened along its length only. The right
    # stroke is ぃ's lighter second stroke, lengthened the same way.
    bar = k.move(k.part('す', 2), sx=.84, sy=1, origin=(540, 0), dx=-140)
    # The loop and its counter stay one outline so the counter keeps its winding.
    rest = k.move(k.part('す', 0, 1, 3), dx=-140)
    right = stretch(k, k.part('ぃ', 1), 500, 20)
    return [bar, rest, k.move(right, dx=60)]


@drawing(0xF469)  # TSI: つ whose tail runs into い's first stroke
def tsi(k):
    # つ is raised and shortened; its tail ends where い's first stroke
    # begins, so the two read as one turning stroke, as in the chart. い's
    # second stroke sits under つ's curve, which keeps the letter compact.
    top = k.move(k.part('つ'), sx=1, sy=.77, origin=(0, 617), dy=233)
    first = k.move(stretch(k, k.part('い', 0), 450, 20), dx=225)
    second = k.move(stretch(k, k.part('い', 1), 350, 40), dx=-60)
    return [top, first, second]


CLEARANCE = 35


def _clear(parts, mark, margin):
    """Whether no part comes within margin units of the mark."""
    mark_path = pathops.Path()
    mark.replay(mark_path.getPen())
    grown = pathops.Path()
    for dx in (-margin, 0, margin):
        for dy in (-margin, 0, margin):
            moved = pathops.Path()
            mark_path.draw(TransformPen(moved.getPen(), (1, 0, 0, 1, dx, dy)))
            grown = pathops.op(grown, moved, pathops.PathOp.UNION)
    for part in parts:
        shape = pathops.Path()
        part.replay(shape.getPen())
        if list(pathops.op(shape, grown, pathops.PathOp.INTERSECTION).segments):
            return False
    return True


def voiced(k, parts):
    """A letter with ど's dakuten, fitted the way Noto's voiced kana are.

    The dakuten starts from Noto's position. The letter may be narrowed from
    its left edge or lowered toward the baseline (as Noto sets つ lower in
    づ), and the mark raised by at most 90 units to stay inside the line,
    until CLEARANCE units separate them. The least change wins, with changes
    to the letter weighed a little heavier than raising the mark.
    """
    left = min(k.bounds(p)[0] for p in parts)
    options = sorted(((2 - sx - sy) * 1000 + dy * .8, sx, sy, dy)
                     for sx in (1, .96, .92, .88, .84, .8, .76)
                     for sy in (1, .95, .9, .85) for dy in (0, 30, 60, 90))
    for _, sx, sy, dy in options:
        mark = k.move(k.part('ど', 0, 3), dy=dy)
        narrowed = [k.move(p, sx=sx, sy=sy, origin=(left, -40)) for p in parts]
        if _clear(narrowed, mark, CLEARANCE):
            return narrowed + [mark]
    raise ValueError('no dakuten fit')


# The ordinary kana each letter is read against, shown beside it on the
# study page. A glottal letter is built on a different kana (WA on ろ).
BASES = {
    0xF450: 'と', 0xF452: 'て', 0xF454: 'く', 0xF456: 'く', 0xF458: 'く',
    0xF45A: 'ふ', 0xF45B: 'ふ', 0xF45C: 'ふ', 0xF45D: 'や', 0xF45E: 'ゆ',
    0xF45F: 'よ', 0xF460: 'わ', 0xF461: 'ゐ', 0xF462: 'ゑ', 0xF463: 'ん',
    0xF465: 'を', 0xF467: 'す', 0xF469: 'つい',
}


def outlines(kit):
    return {cp: fn(kit) for cp, fn in DRAWINGS.items()}
