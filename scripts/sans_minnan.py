"""Minnan tone letters and phonetic marks drawn from Noto Sans JP's strokes.

GenZui Sans draws the 13 tone letters of Kana Extended-B and the two combining
marks from the face's own strokes; GenZui Serif keeps FRB Taiwanese Kana. The
structure of each form follows the period samples reproduced in L2/20-209R
(SAMPLES):

- straight strokes are the stem of katakana TO (ト), shortened along its
  straight middle and turned to the sample's slant;
- tone 5 is hiragana KU (く) with its arms turned to the sample's angle;
- the nasalized tones add the ring of the handakuten (゜) where the sample
  draws its loop, widened to the sample's loop at the handakuten's own ring
  weight;
- the overline is the prolonged sound mark (ー) shortened to FRB's width and
  the dot below is the halfwidth katakana middle dot (･).

Contours overlap as Noto Sans JP's own kana do, so every contour is a moved
copy of a Noto contour. Each part comes from the Noto Sans JP instance being
built: Bold is drawn from Noto Sans JP Bold's strokes on the same construction
and has the Regular outline's commands and points.
"""
import math

import pathops
from fontTools.misc.roundTools import otRound
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.ttGlyphPen import TTGlyphPen

from serif import contours, transform
from serif_forms import reshape
from sans_forms import span

PROPOSAL = 'https://www.unicode.org/L2/L2020/20209r-taiwan-kana.pdf'
# Page numbers are the proposal's printed pages, which match the PDF's.
TABLE = (f'{PROPOSAL} p. 18: Âng and Ogawa (1992), Minnan Classic Dictionary '
         'Collection, vol. 1 p. 3, table of signs (符號)')
HIRASAWA = f'{PROPOSAL} p. 20: Hirasawa (1914), Taiwan Proverb Collection, p. 147'
OGAWA_1938 = (f'{PROPOSAL} p. 21: Ogawa (1938), New Japanese–Taiwanese Dictionary, '
              'page not identified, via Liong et al. (1999) p. 16')
OVERLINED = f'{PROPOSAL} p. 19: Âng and Ogawa (1992) vol. 1 p. 3, overlined kana'
ASPIRATED = f'{PROPOSAL} p. 18: Âng and Ogawa (1992) vol. 1 p. 5, aspirated kana'
SAMPLES = {
    0x1AFF0: (TABLE, HIRASAWA),
    0x1AFF1: (TABLE, HIRASAWA),
    0x1AFF2: (TABLE, OGAWA_1938),
    0x1AFF3: (TABLE, HIRASAWA),
    0x1AFF5: (TABLE, HIRASAWA),
    0x1AFF6: (TABLE, OGAWA_1938),
    0x1AFF7: (TABLE,),
    0x1AFF8: (TABLE, HIRASAWA),
    0x1AFF9: (TABLE, HIRASAWA),
    0x1AFFA: (TABLE,),
    0x1AFFB: (TABLE, HIRASAWA),
    0x1AFFD: (TABLE, HIRASAWA),
    0x1AFFE: (TABLE,),
    0x0305: (OVERLINED,),
    0x0323: (ASPIRATED,),
}

# How each form is built, for the provenance record and the specimen.
CONSTRUCTION = {
    0x1AFF0: 'the stem of ト shortened 80 units and turned 21° clockwise',
    0x1AFF1: 'the stem of ト shortened 30 units and turned 15° anticlockwise',
    0x1AFF2: 'the stem of ト shortened to 334 units and turned 50° clockwise',
    0x1AFF3: 'く with its arms turned to 58° from the horizontal and shortened to 400 units',
    0x1AFF5: 'the stem of ト',
    0x1AFF6: 'the stem of ト shortened to 334 units and turned 45° anticlockwise',
    0x1AFF7: 'the stem of ト with the ring of ゜ at its foot on the right',
    0x1AFF8: 'the tone-2 stroke with the ring of ゜ at its foot on the right, reaching 60 units below it',
    0x1AFF9: 'the tone-3 stroke with the ring of ゜ at its head on the left, reaching 40 units above it',
    0x1AFFA: 'a short stem of ト at the tone-4 slant, ending in the ring of ゜',
    0x1AFFB: 'the tone-5 く with the ring of ゜ closing its bend on the left',
    0x1AFFD: 'the stem of ト with the ring of ゜ on its right, centred 42% up the stem',
    0x1AFFE: 'a short stem of ト at the tone-8 slant, ending in the ring of ゜',
    0x0305: 'ー shortened to 762 units',
    0x0323: 'the halfwidth middle dot ･',
}
# Reader-facing names of the samples.
SAMPLE_NAMES = {
    TABLE: 'the table of signs in Âng and Ogawa’s Minnan Classic Dictionary Collection (1992)',
    OVERLINED: 'the overlined kana in Âng and Ogawa’s Minnan Classic Dictionary Collection (1992)',
    ASPIRATED: 'the aspirated kana in Âng and Ogawa’s Minnan Classic Dictionary Collection (1992)',
    HIRASAWA: 'Hirasawa’s Taiwan Proverb Collection (1914)',
    OGAWA_1938: 'Ogawa’s New Japanese–Taiwanese Dictionary (1938)',
}


def description(cp):
    """A sentence for the specimen's character detail."""
    samples = [SAMPLE_NAMES[s] for s in SAMPLES[cp]]
    text = CONSTRUCTION[cp]
    return (f'{text[0].upper()}{text[1:]}, from Noto Sans JP’s own strokes, after {" and ".join(samples)}. '
            'Advances and mark positions follow FRB Taiwanese Kana.')


# Slants and lengths measured on the table of signs (TABLE): tone 7 is upright and the
# longest stroke, tone 3 leans 15° and is nearly as long, tone 2 leans 21° at
# nine tenths, tones 4 and 8 are short strokes at about 50° and 45°. Positive
# angles turn anticlockwise. Trims shorten TO's 804-unit stem (Regular).
STROKES = {
    0x1AFF0: (-21, 80),
    0x1AFF1: (15, 30),
    0x1AFF2: (-50, 470),
    0x1AFF5: (0, 0),
    0x1AFF6: (45, 470),
}
# Nasalized forms: the plain stroke, its own trim, where the ring sits and on
# which side of the upright stem before it turns. 'beside-foot' and
# 'beside-head' set the ring against the stem, as the samples' b, 6, 9 and þ
# shapes do; 'beside' takes a height along the stem. 'end-foot' and 'end-head'
# continue the stroke into the ring, as the hollow heads of tones 4 and 8 do;
# their tails are about half (tone 4) and a third (tone 8) of the loop.
NASAL = {
    0x1AFF7: (0x1AFF5, 0, 'beside-foot', 1),
    0x1AFF8: (0x1AFF0, 80, 'beside-foot', 1, None, 36, 60),
    0x1AFF9: (0x1AFF1, 30, 'beside-head', -1, None, 36, 40),
    0x1AFFA: (0x1AFF2, 644, 'end-head', 0),
    0x1AFFD: (0x1AFF5, 0, 'beside', 1, .42),
    0x1AFFE: (0x1AFF6, 674, 'end-foot', 0),
}
SHORT = {0x1AFF2, 0x1AFF6, 0x1AFFA, 0x1AFFE}
KU_ANGLE, KU_REACH = 58, 400
# The bend: the first 150 units of each arm keep their length.
KU_BEND = 150
# On the nasalized tone 5 the loop's wall lies across the bend.
KU_LOOP_SHIFT = 30
# The loops measure about a third of the tone-7 stroke on the table; the ring
# widens to that while keeping the handakuten's ring weight.
LOOP_DIAMETER = 260
# The ring's counter overlaps a stem it sits beside by this much.
OVERLAP = 12
CENTRE_X, CENTRE_Y, SHORT_Y = 250, 400, 380
OVERLINE = (124, 886, 721)
DOT = (500, 380)


def noto(font, cp, indices=None):
    """Contours of a Noto Sans JP glyph at the integer coordinates the font
    stores; a freshly instantiated face still holds unrounded deltas."""
    return reshape(contours(font, cp, indices), lambda x, y: (otRound(x), otRound(y)))


def bounds(outline):
    shape = pathops.Path()
    outline.replay(shape.getPen())
    return shape.bounds


def rotate(outline, degrees):
    a = math.radians(degrees)
    c, s = math.cos(a), math.sin(a)
    return transform(outline, (c, s, -s, c, 0, 0))


def move(outline, dx, dy):
    return transform(outline, (1, 0, 0, 1, dx, dy))


def joined(parts):
    out = RecordingPen()
    for part in parts:
        part.replay(out)
    return out


def stem(font, trim=0, hidden=None):
    """TO's stem, centred on x 0 with its foot on y 0, its width and length.

    Shortening compresses only the straight middle between the flared ends,
    so the stem keeps its width and both terminals. A terminal that ends
    inside a ring (`hidden` 'foot' or 'head') is compressed with the middle.
    """
    outline = noto(font, ord('ト'), [0])
    x0, x1 = span(outline, 400)
    _, bottom, _, top = bounds(outline)
    low = bottom if hidden == 'foot' else bottom + 120
    high = top if hidden == 'head' else top - 120
    assert trim < high - low, trim
    scale = (high - low - trim) / (high - low)

    def point(x, y):
        if y < low:
            return x, y
        if y > high:
            return x, y - trim
        return x, low + (y - low)*scale

    return move(reshape(outline, point), -(x0 + x1)/2, -bottom), x1 - x0, top - bottom - trim


def ring(font):
    """The handakuten ring centred on the origin and widened to the loop size.

    Both circles move outward by the same distance, so the ring keeps its
    weight and Noto's curve construction. Returns the ring and its radii.
    """
    outer, inner = noto(font, 0x309C, [0]), noto(font, 0x309C, [1])
    x0, y0, x1, y1 = bounds(outer)
    cx, cy = (x0 + x1)/2, (y0 + y1)/2
    r_out = (x1 - x0)/2
    r_in = (bounds(inner)[2] - bounds(inner)[0])/2
    grow = LOOP_DIAMETER/2 - r_out
    parts = [reshape(c, lambda x, y, r=r: (cx + (x - cx)*(r + grow)/r, cy + (y - cy)*(r + grow)/r))
             for c, r in ((outer, r_out), (inner, r_in))]
    return move(joined(parts), -cx, -cy), r_out + grow, r_in + grow


def ku_geometry(font):
    """Noto's KU, its bend and its arms: the outline, the outer corner of the
    bend, the bend's centre, and per arm (1 upper, -1 lower) the vector from
    the centre to the middle of the terminal."""
    outline = noto(font, ord('く'))
    points = [p for _, args in outline.value for p in args if p]
    outer = min(points, key=lambda p: p[0])
    inner = min((p for p in points if p[0] > outer[0] + 60 and abs(p[1] - outer[1]) < 60),
                key=lambda p: p[0])
    vx, vy = (outer[0] + inner[0])/2, (outer[1] + inner[1])/2
    # KU is one contour drawn from the upper terminal; its lineTo crosses the
    # lower terminal.
    ops = outline.value
    turn = next(i for i, (op, _) in enumerate(ops) if op == 'lineTo')
    ends = {1: (ops[0][1][0], ops[-2][1][-1]), -1: (ops[turn-1][1][-1], ops[turn][1][0])}
    tips = {arm: ((a[0] + b[0])/2 - vx, (a[1] + b[1])/2 - vy) for arm, (a, b) in ends.items()}
    return outline, outer, (vx, vy), tips


def ku(font):
    """KU with each arm turned about the bend to the sample's angle and
    shortened along its own direction; the turn fades out across the bend.
    Returns the outline and the outer corner of its bend."""
    outline, outer, (vx, vy), tips = ku_geometry(font)

    def smooth(t):
        t = max(0, min(1, t))
        return t*t*(3 - 2*t)

    def point(x, y):
        dx, dy = x - vx, y - vy
        arm = 1 if dy >= 0 else -1
        tx, ty = tips[arm]
        length = math.hypot(tx, ty)
        ux, uy = tx/length, ty/length
        along = dx*ux + dy*uy
        # Shorten the arm beyond the bend along its own direction, which keeps
        # its width across the stroke.
        if along > KU_BEND:
            cut = (along - KU_BEND)/(length - KU_BEND)*(length - KU_REACH)
            dx, dy = dx - ux*cut, dy - uy*cut
        a = (math.radians(arm*KU_ANGLE) - math.atan2(ty, tx))*smooth((math.hypot(dx, dy) - 40)/110)
        c, s = math.cos(a), math.sin(a)
        return vx + c*dx - s*dy, vy + s*dx + c*dy

    return reshape(outline, point), point(*outer)


def centred(parts, cy):
    x0, y0, x1, y1 = bounds(joined(parts))
    return [move(p, CENTRE_X - (x0 + x1)/2, cy - (y0 + y1)/2) for p in parts]


def nasal(font, plain, trim, where, side, height=None, overlap=OVERLAP, reach=0):
    end = where.split('-')[-1] if where.startswith(('end', 'tangent')) else None
    outline, width, length = stem(font, trim, end)
    loop, outer, inner = ring(font)
    if where.startswith('beside'):
        x = side*(width/2 + inner - overlap)
        y = outer if where == 'beside-foot' else length - outer if where == 'beside-head' else height*length
    elif where.startswith('tangent'):
        # The stroke runs along the ring and ends at its equator, its axis on
        # the middle of the ring's wall, as the 6 and 9 of the samples.
        x, y = side*(outer + inner)/2, 0 if where == 'tangent-foot' else length
    else:
        # The terminal ends in the middle of the ring's wall.
        x, middle = 0, (outer + inner)/2
        y = -middle if where == 'end-foot' else length + middle
    angle = STROKES[plain][0]
    outline, loop = rotate(outline, angle), rotate(move(loop, x, y), angle)
    if where in ('beside-foot', 'beside-head'):
        # On a slanted stroke, slide the ring along the stroke until it reaches
        # as far as the stroke's own end, as the loop of the samples' 6 and 9.
        index = 1 if where == 'beside-foot' else 3
        gap = bounds(outline)[index] - bounds(loop)[index] + (-reach if index == 1 else reach)
        a = math.radians(angle)
        t = gap/math.cos(a)
        loop = move(loop, -math.sin(a)*t, math.cos(a)*t)
    return [outline, loop]


def parts(font):
    """The contours of every form, as Noto contours moved into place."""
    forms = {}
    for cp, (angle, trim) in STROKES.items():
        forms[cp] = centred([rotate(stem(font, trim)[0], angle)], SHORT_Y if cp in SHORT else CENTRE_Y)
    shape, (vx, vy) = ku(font)
    forms[0x1AFF3] = centred([shape], CENTRE_Y)
    for cp, spec in NASAL.items():
        forms[cp] = centred(nasal(font, *spec), SHORT_Y if cp in SHORT else CENTRE_Y)
    # Tone 5's loop closes the vertex on the left.
    loop, outer, inner = ring(font)
    forms[0x1AFFB] = centred([shape, move(loop, vx + OVERLAP + KU_LOOP_SHIFT - inner, vy)], CENTRE_Y)

    bar = noto(font, 0x30FC)
    bx0, by0, bx1, _ = bounds(bar)
    left, right, base = OVERLINE
    bar = reshape(bar, lambda x, y: (x + (left - bx0 if x < 500 else right - bx1), y))
    forms[0x0305] = [move(bar, 0, base - by0)]
    dot = noto(font, 0xFF65)
    x0, y0, x1, y1 = bounds(dot)
    forms[0x0323] = [move(dot, DOT[0] - (x0 + x1)/2, DOT[1] - (y0 + y1)/2)]
    return forms


def ttglyph(contours_):
    pen = TTGlyphPen(None)
    joined(contours_).replay(pen)
    g = pen.glyph()
    if len(contours_) > 1:
        g.flags[0] |= 0x40  # OVERLAP_SIMPLE, as on Noto Sans JP's kana.
    return g


def build(font):
    """TrueType glyphs for every form; overlapping contours keep Noto's flag."""
    return {cp: ttglyph(contours_) for cp, contours_ in parts(font).items()}


def short_overline(font):
    """The overline narrowed for small kana, as minnan.layout narrows FRB's."""
    from minnan import SHORT_OVERLINE
    return ttglyph([transform(c, SHORT_OVERLINE) for c in parts(font)[0x0305]])
