"""Funatsu's Okinawan kana composed from GenZui's own hiragana strokes.

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


def tu_body(k):
    """と's diagonal running into ち's turn and bulge.

    と and ち turn at nearly the same point. ち loses its descending stroke
    just inside と's diagonal (whose outer edge runs along y = x); と loses
    its bottom sweep on a slanted cut through ち's thick turn.
    """
    diagonal = k.keep(k.part('と', 0), (320, 130), (1000, 130), (1000, 1000), (0, 1000), (0, 450))
    bulge = k.drop(k.part('ち', 0), (0, 5), (480, 485), (480, 1000), (0, 1000))
    return [diagonal, bulge]


@drawing(0xF450)  # TU: と's tick over the diagonal and bulge
def tu(k):
    return [k.part('と', 1)] + tu_body(k)


@drawing(0xF452)  # TI: て with ぃ under its bar
def ti(k):
    # て is one contour. It is cut along the underside of the bar, measured
    # from the outline, across the span where the curve hangs from it. The
    # curve moves left to make room for ぃ; since the bar rises to the right,
    # its cut top then lands inside the bar.
    window = ((395, -100), (640, -100), (640, 617), (560, 620), (520, 612), (460, 594), (395, 576))
    bar = k.drop(k.part('て'), *window)
    curve = k.keep(k.part('て'), *window)
    return [bar, k.move(curve, dx=-140)] + small_i(k, 510, 10, 920)


@drawing(0xF456)  # KWI: く with ぃ
def kwi(k):
    return [k.move(k.part('く'), sx=1.2, sy=1, dx=-190)] + small_i(k, 470, -30, 960)


def ku_halves(k, lower_sy=1):
    """く split on the horizontal through its turn at y = 360.

    The lower arm may be flattened by scaling about that line, which keeps
    the two cut edges on top of each other.
    """
    upper = k.keep(k.part('く'), (0, 360), (1000, 360), (1000, 1000), (0, 1000))
    lower = k.keep(k.part('く'), (0, -100), (1000, -100), (1000, 360), (0, 360))
    return upper, k.move(lower, sx=1, sy=lower_sy, origin=(0, 360))


@drawing(0xF458)  # KWE: く's long arm, a flat connector and え's zigzag
def kwe(k):
    upper, lower = ku_halves(k, .3)
    # The chart draws く's arm long and shallow, and its lower arm as a near
    # level connector into え. え loses the left part of its top stroke; the
    # cut sits inside the connector's end.
    upper = k.move(upper, sx=1.45, sy=1, origin=(272, 360))
    lower = k.move(lower, sx=1.25, sy=1, origin=(272, 360))
    zigzag = k.drop(k.part('え', 0), (0, 390), (400, 390), (520, 470), (520, 700), (0, 700))
    zigzag = k.move(zigzag, sx=.8, sy=.5, origin=(600, 520), dx=110, dy=-280)
    return [k.move(p, dx=-170) for p in (upper, lower, zigzag)]


@drawing(0xF454)  # KWA: く with its lower arm flattened into わ's stem
def kwa(k):
    upper, lower = ku_halves(k, .3)
    # The flattened arm ends near (500, 235); わ's stem hangs from it with its
    # cut top inside the arm.
    loop = k.move(k.part('わ', 0), sx=.7, origin=(0, 0))
    stem = k.keep(k.move(k.part('わ', 2), sx=.7, origin=(0, 0)), (0, -100), (1000, -100), (1000, 250), (0, 250))
    return [k.move(upper, dx=-150), k.move(lower, dx=-150)] + [k.move(p, dx=254, dy=-10) for p in (loop, stem)]


def fu_left(k):
    """ふ's top and centre stroke with its left dot; the right dot gives way."""
    parts = [k.part('ふ', 0), k.keep(k.part('ふ', 1), (0, -100), (330, -100), (330, 400), (0, 400))]
    return [k.move(p, sx=.82, sy=1, origin=(0, 0), dx=40) for p in parts]


@drawing(0xF45A)  # HWA
def hwa(k):
    return fu_left(k) + [k.box(k.part('ゎ'), 520, -40, 960)]


@drawing(0xF45B)  # HWI
def hwi(k):
    return fu_left(k) + small_i(k, 540, -20, 960)


@drawing(0xF45C)  # HWE
def hwe(k):
    return fu_left(k) + [k.box(k.part('ぇ', 0), 500, -40, 960)]


def stretch(k, pen, top, bottom):
    """Stretch a stroke along its length only, so its weight is unchanged."""
    y0, y1 = k.bounds(pen)[1::2]
    return k.move(pen, sx=1, sy=(top - bottom) / (y1 - y0), dy=bottom - y0)


@drawing(0xF45D)  # glottal YA: は's left stroke before や, its flick aimed at the arm
def glottal_ya(k):
    mark = stretch(k, k.part('は', 1), 780, 170)
    return [k.move(mark, dx=-70), k.move(k.part('や'), sx=.84, sy=1, origin=(929, 0), dx=40)]


@drawing(0xF45E)  # glottal YU: い's first stroke beside ゆ's own left stroke
def glottal_yu(k):
    # ゆ's left stroke descends and hooks up into the loop; い's first stroke
    # makes the same movement, so the two run parallel and the mark's hook
    # points at the start of ゆ.
    mark = stretch(k, k.part('い', 0), 720, 90)
    return [k.move(mark, dx=-85), k.move(k.part('ゆ'), sx=.82, sy=1, origin=(910, 0), dx=60)]


@drawing(0xF45F)  # glottal YO: は's left stroke with よ in place of は's right half
def glottal_yo(k):
    # は's flick is drawn toward the next stroke; よ takes the room of は's
    # right half, so the spacing is は's own.
    right = k.box(k.part('よ'), 330, -37, 900)
    return [k.part('は', 1), right]


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
    mark = stretch(k, k.part('ぃ', 1), 590, 400)
    return [k.move(k.part('ん'), dx=-40), k.move(mark, dx=70)]


@drawing(0xF465)  # WU: を's bar, a ノ, a short tick and the body of TU
def wu(k):
    # The chart draws を's cross stroke as a plain ノ that ends in a free tip,
    # then a short tick below the bar whose foot rests on the third stroke,
    # which runs from the upper right into TU's turn and bulge.
    slash = stretch(k, k.part('な', 1), 800, 390)
    body = [k.move(p, sx=1, sy=.8, origin=(0, -40)) for p in tu_body(k)]
    tick = k.keep(k.part('い', 0), (0, 470), (1000, 470), (1000, 900), (0, 900))
    tick = k.move(tick, dx=330, dy=-110)
    return [k.part('を', 2), k.move(slash, dx=-40), tick] + body


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
    # begins, so the two read as one turning stroke, as in the chart.
    top = k.move(k.part('つ'), sx=1, sy=.77, origin=(0, 617), dy=233)
    first = k.move(stretch(k, k.part('い', 0), 450, 20), dx=225)
    second = k.move(stretch(k, k.part('い', 1), 330, 40), dx=60)
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
