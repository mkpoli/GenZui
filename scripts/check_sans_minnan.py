"""Check GenZui Sans's drawn Minnan forms against Noto Sans JP's kana.

Each form must be the drawing sans_minnan builds from the base instance, have
no sliver contours, and keep the stroke widths of the Noto kana strokes it is
built from within two units. Bold must share Regular's commands and points
and gain weight within the range of Noto Sans JP's own kana.
"""
import math
import statistics

import pathops
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.perimeterPen import PerimeterPen
from fontTools.pens.recordingPen import RecordingPen

import sans_minnan
from repertoire import MINNAN_MARKS, MINNAN_TONES
from serif import contours, instance

FORMS = (*MINNAN_TONES, *MINNAN_MARKS)
KU = {0x1AFF3, 0x1AFFB}
# A contour thinner than this (twice its area over its perimeter) or smaller
# than this area is a sliver.
SLIVER_WIDTH, SLIVER_AREA = 15, 400
# Katakana vertical stems for the median reported beside the measurements.
STEM_SAMPLE = 'アイウエコサセチトナヒホモヨリルレロワヰヱ'


def contour(font, name, index):
    pen = RecordingPen()
    font.getGlyphSet()[name].draw(pen)
    found, current = [], []
    for op, args in pen.value:
        current.append((op, args))
        if op in ('closePath', 'endPath'):
            found.append(current)
            current = []
    out = RecordingPen()
    out.value = found[index]
    return out


def span(outline, y):
    """The horizontal extent of an outline at height y, at any x."""
    shape, band = pathops.Path(), pathops.Path()
    outline.replay(shape.getPen())
    pen = band.getPen()
    pen.moveTo((-5000, y-.5)); pen.lineTo((5000, y-.5)); pen.lineTo((5000, y+.5)); pen.lineTo((-5000, y+.5)); pen.closePath()
    x0, _, x1, _ = pathops.op(shape, band, pathops.PathOp.INTERSECTION).bounds
    return x0, x1


def across(outline, angle, where='middle'):
    """Width of a stroke at `angle` degrees from the horizontal, turned so the
    stroke points up: at its middle, or 100 units in from its 'foot' or
    'head' terminal."""
    upright = sans_minnan.rotate(outline, 90 - angle)
    _, y0, _, y1 = sans_minnan.bounds(upright)
    x0, x1 = span(upright, {'middle': (y0 + y1)/2, 'foot': y0 + 100, 'head': y1 - 100}[where])
    return x1 - x0


def arm(outline, angle, centre, length):
    """Median width of an arm of KU at `angle`, from 30% to 80% of the way
    between the end of the bend and the terminal at `length` from `centre`."""
    upright = sans_minnan.rotate(outline, 90 - angle)
    a = math.radians(90 - angle)
    y = math.sin(a)*centre[0] + math.cos(a)*centre[1]
    widths = []
    for f in (.3, .4, .5, .6, .7, .8):
        x0, x1 = span(upright, y + sans_minnan.KU_BEND + f*(length - sans_minnan.KU_BEND))
        widths.append(x1 - x0)
    return statistics.median(widths)


def ring_weight(outer, inner):
    """Ring weight from the radii of circles with the contours' areas, which
    a turn of the ring leaves unchanged."""
    radii = []
    for c in (outer, inner):
        area = AreaPen()
        c.replay(area)
        radii.append(math.sqrt(abs(area.value)/math.pi))
    return radii[0] - radii[1]


def slivers(font, name):
    """The thinnest and smallest contour of the filled outline and of each
    drawn contour."""
    shape = pathops.Path()
    font.getGlyphSet()[name].draw(shape.getPen())
    pieces = list(pathops.simplify(shape).contours)
    original = pathops.Path()
    font.getGlyphSet()[name].draw(original.getPen())
    pieces += list(original.contours)
    widths, areas = [], []
    for piece in pieces:
        area, perimeter = AreaPen(), PerimeterPen()
        piece.draw(area)
        piece.draw(perimeter)
        widths.append(2*abs(area.value)/perimeter.value)
        areas.append(abs(area.value))
    return min(widths), min(areas)


def weight(draw):
    area, perimeter = AreaPen(), PerimeterPen()
    draw(area)
    draw(perimeter)
    return 2*abs(area.value)/perimeter.value


def katakana_stem(base):
    """Median width of the straight vertical stems in STEM_SAMPLE."""
    widths = []
    for ch in STEM_SAMPLE:
        found = []
        outline = contours(base, ord(ch))
        for y in (250, 350, 450, 550):
            band = pathops.Path()
            pen = band.getPen()
            pen.moveTo((-200, y-.5)); pen.lineTo((1200, y-.5)); pen.lineTo((1200, y+.5)); pen.lineTo((-200, y+.5)); pen.closePath()
            shape = pathops.Path()
            outline.replay(shape.getPen())
            for piece in pathops.op(shape, band, pathops.PathOp.INTERSECTION).contours:
                x0, _, x1, _ = piece.bounds
                if 50 < x1 - x0 < 160:
                    found.append(x1 - x0)
        if found:
            widths.append(min(found))
    return statistics.median(widths)


def check_minnan_forms(font, base, weight_class, regular=None):
    """Validate the drawn forms; `regular` is the built Regular face for Bold."""
    cmap = font.getBestCmap()
    drawn = sans_minnan.build(base)
    report = {'forms': {}, 'sliver_limits': {'width': SLIVER_WIDTH, 'area': SLIVER_AREA}}
    # Noto's own strokes, measured the way the forms are.
    to = contours(base, ord('ト'), [0])
    ku, outer, centre, tips = sans_minnan.ku_geometry(base)
    angles = {k: math.degrees(math.atan2(ty, tx)) for k, (tx, ty) in tips.items()}
    source = {'TO stem': across(to, 90), 'TO foot': across(to, 90, 'foot'), 'TO head': across(to, 90, 'head'),
              'KU upper arm': arm(ku, angles[1], centre, math.hypot(*tips[1])),
              'KU lower arm': arm(ku, angles[-1], centre, math.hypot(*tips[-1])),
              'handakuten ring': ring_weight(contours(base, 0x309C, [0]), contours(base, 0x309C, [1])),
              'prolonged sound mark': across(contours(base, 0x30FC), 0),
              'halfwidth middle dot': (lambda b: b[2] - b[0])(sans_minnan.bounds(contours(base, 0xFF65)))}
    report['noto_strokes'] = {k: round(v, 1) for k, v in source.items()}
    report['katakana_stem_median'] = round(katakana_stem(base), 1)
    for cp in FORMS:
        name = cmap[cp]
        g, expected = font['glyf'][name], drawn[cp]
        assert list(g.coordinates) == list(expected.coordinates), hex(cp)
        assert list(g.flags) == list(expected.flags) and list(g.endPtsOfContours) == list(expected.endPtsOfContours), hex(cp)
        thin, small = slivers(font, name)
        assert thin >= SLIVER_WIDTH and small >= SLIVER_AREA, (hex(cp), thin, small)
        widths = {}
        if cp in KU:
            # The bend's outer corner is the drawing's leftmost point; the
            # bend keeps its shape, so its centre keeps the same offset.
            first = contour(font, name, 0)
            corner = min((p for _, args in first.value for p in args if p), key=lambda p: p[0])
            moved = (centre[0] - outer[0] + corner[0], centre[1] - outer[1] + corner[1])
            for k, label in ((1, 'KU upper arm'), (-1, 'KU lower arm')):
                widths[label] = arm(first, k*sans_minnan.KU_ANGLE, moved, sans_minnan.KU_REACH)
        elif cp == 0x0305:
            widths['prolonged sound mark'] = across(contour(font, name, 0), 0)
        elif cp == 0x0323:
            b = sans_minnan.bounds(contour(font, name, 0))
            widths['halfwidth middle dot'] = b[2] - b[0]
        else:
            nasal = sans_minnan.NASAL.get(cp)
            angle = 90 + sans_minnan.STROKES[nasal[0] if nasal else cp][0]
            if nasal and nasal[2].startswith('end'):
                # A short tail ending in the ring: measure near its free
                # terminal against the same end of TO's stem.
                free = 'foot' if nasal[2] == 'end-head' else 'head'
                widths['TO ' + free] = across(contour(font, name, 0), angle, free)
            else:
                widths['TO stem'] = across(contour(font, name, 0), angle)
        if g.numberOfContours == 3:
            widths['handakuten ring'] = ring_weight(contour(font, name, 1), contour(font, name, 2))
        for label, value in widths.items():
            assert abs(value - source[label]) <= 2, (hex(cp), label, value, source[label])
        report['forms'][f'U+{cp:04X}'] = {
            'contours': g.numberOfContours, 'points': len(g.coordinates),
            'min_contour_width': round(thin, 1), 'min_contour_area': round(small),
            'stroke_widths': {k: round(v, 1) for k, v in widths.items()}}
    if regular is not None:
        # Bold: the same commands and points as Regular, and a weight gain
        # within Noto Sans JP's own kana.
        # Noto's kana letters and its spacing voicing marks, whose handakuten
        # ring the nasalized forms carry.
        letters = [cp for cp in (*range(0x3041, 0x3097), *range(0x30A1, 0x30FB)) if cp in base.getBestCmap()]
        marks = [0x309B, 0x309C]
        light = instance('NotoSansJP', 400, letters + marks + [0xFF65])

        def gain(cp):
            return (weight(lambda pen: base.getGlyphSet()[base.getBestCmap()[cp]].draw(pen)) /
                    weight(lambda pen: light.getGlyphSet()[light.getBestCmap()[cp]].draw(pen)))

        letter_gains = [gain(cp) for cp in letters]
        mark_gains = {f'U+{cp:04X}': round(gain(cp), 3) for cp in marks}
        low, high = min(letter_gains + [gain(cp) for cp in marks]), max(letter_gains)
        dot_gain = gain(0xFF65)
        report['kana_letter_gain_range'] = [round(min(letter_gains), 3), round(high, 3)]
        report['kana_mark_gains'] = mark_gains
        report['kana_gain_range'] = [round(low, 3), round(high, 3)]
        report['halfwidth_middle_dot_gain'] = round(dot_gain, 3)
        rcmap = regular.getBestCmap()
        for cp in FORMS:
            g, r = font['glyf'][cmap[cp]], regular['glyf'][rcmap[cp]]
            assert list(g.flags) == list(r.flags) and list(g.endPtsOfContours) == list(r.endPtsOfContours), hex(cp)
            gain = (weight(lambda pen: font.getGlyphSet()[cmap[cp]].draw(pen)) /
                    weight(lambda pen: regular.getGlyphSet()[rcmap[cp]].draw(pen)))
            # The dot below is Noto's halfwidth middle dot, whose own Bold
            # gains less than any kana; it must keep that mark's gain.
            if cp == 0x0323:
                assert abs(gain - dot_gain) <= .01, gain
            else:
                assert low <= gain <= high, (hex(cp), gain, low, high)
            report['forms'][f'U+{cp:04X}']['bold_gain'] = round(gain, 3)
    return report
