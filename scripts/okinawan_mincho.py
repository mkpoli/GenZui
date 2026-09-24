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


def stem(k, x, bottom, top):
    """は's left stroke as the glottal mark before や, ゆ and よ."""
    return k.box(k.part('は', 1), x, bottom, None, top)


@drawing(0xF45D)  # glottal YA
def glottal_ya(k):
    return [stem(k, 60, 250, 760), k.box(k.part('や'), 230, -54, 940)]


@drawing(0xF45E)  # glottal YU
def glottal_yu(k):
    return [stem(k, 40, 250, 760), k.box(k.part('ゆ'), 200, -62, 950)]


@drawing(0xF45F)  # glottal YO
def glottal_yo(k):
    return [stem(k, 90, 60, 760), k.move(k.part('よ'), dx=80)]


def bar_over(k, ch):
    """こ's upper stroke set over a kana squeezed down to make room."""
    body = k.box(k.part(ch), 140, -50, 860, 640)
    return [k.box(k.part('こ', 1), 260, 690, 660), body]


@drawing(0xF460)  # glottal WA
def glottal_wa(k):
    return bar_over(k, 'ろ')


@drawing(0xF461)  # glottal WI
def glottal_wi(k):
    return bar_over(k, 'る')


@drawing(0xF462)  # glottal WE
def glottal_we(k):
    return bar_over(k, 'ゑ')


@drawing(0xF463)  # glottal N: ん with い's falling stroke at the upper right
def glottal_n(k):
    return [k.part('ん'), k.box(k.part('い', 1), 640, 440, None, 740)]


@drawing(0xF465)  # WU: を's bar and cross stroke over the body of TU
def wu(k):
    # The chart's third stroke runs from the upper right down to the left,
    # turns and swells into a bulge: the body of TU, set lower. Its diagonal
    # crosses を's tail, which is cut there so its end lies inside it.
    body = [k.move(p, sx=.95, sy=.9, origin=(500, -40), dy=-10) for p in tu_body(k)]
    cross = k.drop(k.part('を', 1), (440, -100), (1000, -100), (1000, 390), (440, 390))
    return [k.part('を', 2), cross] + body


@drawing(0xF467)  # SI: す with い's second stroke
def si(k):
    return [k.move(k.part('す'), dx=-130), k.box(k.part('い', 1), 660, -20, 860, 520)]


@drawing(0xF469)  # TSI: つ's top over ぃ
def tsi(k):
    top = k.box(k.part('つ'), 60, 420, 910, 790)
    return [top] + small_i(k, 180, -20, 700)


def dakuten(k):
    """ど's dakuten, raised to clear the wider Okinawan letters."""
    return k.move(k.part('ど', 0, 3), dx=-15, dy=70)


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
