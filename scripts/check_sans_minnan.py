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


# The structure of each form as the samples draw it, written independently of
# the construction tables in sans_minnan. Source: L2/20-209R p. 18, Âng and
# Ogawa (1992) vol. 1 p. 3, table of signs: plain tones in the 常音 column,
# nasalized in the 鼻音 column, rows 上平 (1), 上聲 (2), 上去 (3), 上入 (4),
# 下平 (5), 下去 (7), 下入 (8); 6, 9 and the nasalized 5 and 7 also on p. 20
# (Hirasawa 1914 p. 147). `slant` is where the stroke's upper end lies against
# its lower end. `ring` is the ring's side of the stroke's line, seen from its
# lower end towards its upper end ('axis' when the loop continues the line),
# and where along the stroke it sits. `joins` is the terminal that runs into
# the loop.
SAMPLE_SHAPES = {
    0x1AFF0: {'slant': 'right'},                       # 上聲 常音: /
    0x1AFF1: {'slant': 'left'},                        # 上去 常音: \
    0x1AFF2: {'slant': 'right'},                       # 上入 常音: short, head upper right
    0x1AFF3: {'bend': 'left'},                         # 下平 常音: <
    0x1AFF5: {'slant': 'upright'},                     # 下去 常音: |
    0x1AFF6: {'slant': 'left'},                        # 下入 常音: short, head upper left
    0x1AFF7: {'slant': 'upright', 'ring': ('right', 'foot')},   # 上平 鼻音: b
    0x1AFF8: {'slant': 'right', 'ring': ('right', 'foot'), 'joins': 'foot'},  # 上聲 鼻音: 6
    0x1AFF9: {'slant': 'left', 'ring': ('left', 'head'), 'joins': 'head'},    # 上去 鼻音: 9
    0x1AFFA: {'slant': 'right', 'ring': ('axis', 'head'), 'joins': 'head'},   # 上入 鼻音: loop upper right
    0x1AFFB: {'bend': 'left', 'ring': ('left', 'bend')},        # 下平 鼻音: < with a loop at the bend
    0x1AFFD: {'slant': 'upright', 'ring': ('right', 'middle')},  # 下去 鼻音: þ
    0x1AFFE: {'slant': 'left', 'ring': ('axis', 'foot'), 'joins': 'foot'},    # 下入 鼻音: loop lower right
}


def path(outline):
    shape = pathops.Path()
    outline.replay(shape.getPen())
    return shape


def terminals(outline):
    """The flat cuts of a stroke contour: its straight segments' end points,
    as {'head': (a, b), 'foot': (a, b)} by height."""
    cuts, previous = [], None
    for op, args in outline.value:
        if op == 'lineTo':
            cuts.append((previous, args[0]))
        if args:
            previous = args[-1]
    cuts.sort(key=lambda c: (c[0][1] + c[1][1])/2)
    return {'foot': cuts[0], 'head': cuts[-1]}


def mid(cut):
    return ((cut[0][0] + cut[1][0])/2, (cut[0][1] + cut[1][1])/2)


def structure(font, name, cp):
    """Assert the sample's slant, ring side and position, the join of a
    terminal inside the ring's band, and a clear counter, on the outlines."""
    shape = SAMPLE_SHAPES.get(cp)
    if not shape:
        return {}
    stroke = contour(font, name, 0)
    found = {}
    if 'slant' in shape:
        cuts = terminals(stroke)
        head, foot = mid(cuts['head']), mid(cuts['foot'])
        lean = head[0] - foot[0]
        found['slant'] = 'upright' if abs(lean) < 20 else 'right' if lean > 0 else 'left'
    if 'bend' in shape:
        points = [p for _, args in stroke.value for p in args if p]
        bend = min(points, key=lambda p: p[0])
        tips = sorted(points, key=lambda p: p[1])
        found['bend'] = 'left' if bend[0] < tips[0][0] and bend[0] < tips[-1][0] else 'right'
    if 'ring' in shape:
        outer, inner = contour(font, name, 1), contour(font, name, 2)
        x0, y0, x1, y1 = sans_minnan.bounds(outer)
        centre = ((x0 + x1)/2, (y0 + y1)/2)
        side, where = shape['ring']
        if where == 'bend':
            assert path(outer).contains(bend), (hex(cp), 'bend outside the ring')
            position = 'bend'
        else:
            cuts = terminals(stroke)
            head, foot = mid(cuts['head']), mid(cuts['foot'])
            length = math.dist(head, foot)
            along = ((centre[0] - foot[0])*(head[0] - foot[0]) + (centre[1] - foot[1])*(head[1] - foot[1]))/length**2
            position = 'foot' if along < .3 else 'head' if along > .7 else 'middle'
            offset = ((centre[0] - foot[0])*(head[1] - foot[1]) - (centre[1] - foot[1])*(head[0] - foot[0]))/length
        if where == 'bend':
            found['ring'] = ('left' if centre[0] < bend[0] else 'right', position)
        else:
            found['ring'] = ('axis' if abs(offset) < 10 else 'right' if offset > 0 else 'left', position)
        # The counter holds no ink from the stroke.
        ink = pathops.op(path(stroke), path(inner), pathops.PathOp.INTERSECTION)
        assert ink.area < .5, (hex(cp), 'ink in the counter', ink.area)
        if 'joins' in shape:
            cut = terminals(stroke)[shape['joins']]
            ring_outer, ring_inner = path(outer), path(inner)
            for i in range(21):
                t = i/20
                point = (cut[0][0] + t*(cut[1][0] - cut[0][0]), cut[0][1] + t*(cut[1][1] - cut[0][1]))
                assert ring_outer.contains(point) and not ring_inner.contains(point), (hex(cp), 'terminal outside the band', point)
            found['joins'] = shape['joins']
    assert found == shape, (hex(cp), found, shape)
    return found


def check_minnan_forms(font, base, weight_class, regular=None):
    """Validate the drawn forms; `regular` is the built Regular face for Bold."""
    cmap = font.getBestCmap()
    drawn = sans_minnan.build(base)
    report = {'forms': {}, 'sliver_limits': {'width': SLIVER_WIDTH, 'area': SLIVER_AREA}}
    # Noto's own strokes, measured the way the forms are.
    to = sans_minnan.noto(base, ord('ト'), [0])
    ku, outer, centre, tips = sans_minnan.ku_geometry(base)
    angles = {k: math.degrees(math.atan2(ty, tx)) for k, (tx, ty) in tips.items()}
    source = {'TO stem': across(to, 90), 'TO foot': across(to, 90, 'foot'), 'TO head': across(to, 90, 'head'),
              'KU upper arm': arm(ku, angles[1], centre, math.hypot(*tips[1])),
              'KU lower arm': arm(ku, angles[-1], centre, math.hypot(*tips[-1])),
              'handakuten ring': ring_weight(sans_minnan.noto(base, 0x309C, [0]), sans_minnan.noto(base, 0x309C, [1])),
              'prolonged sound mark': across(sans_minnan.noto(base, 0x30FC), 0),
              'halfwidth middle dot': (lambda b: b[2] - b[0])(sans_minnan.bounds(sans_minnan.noto(base, 0xFF65)))}
    report['noto_strokes'] = {k: round(v, 1) for k, v in source.items()}
    report['katakana_stem_median'] = round(katakana_stem(base), 1)
    for cp in FORMS:
        name = cmap[cp]
        g, expected = font['glyf'][name], drawn[cp]
        assert list(g.coordinates) == list(expected.coordinates), hex(cp)
        assert list(g.flags) == list(expected.flags) and list(g.endPtsOfContours) == list(expected.endPtsOfContours), hex(cp)
        thin, small = slivers(font, name)
        assert thin >= SLIVER_WIDTH and small >= SLIVER_AREA, (hex(cp), thin, small)
        shape = structure(font, name, cp)
        widths = {}
        if cp in KU:
            # The bend's outer corner is the drawing's leftmost point; the
            # bend keeps its shape, so its centre keeps the same offset.
            first = contour(font, name, 0)
            corner = min((p for _, args in first.value for p in args if p), key=lambda p: p[0])
            moved = (centre[0] - outer[0] + corner[0], centre[1] - outer[1] + corner[1])
            for k, label in ((1, 'KU upper arm'), (-1, 'KU lower arm')):
                angle = sans_minnan.KU_NASAL_ANGLE if cp == 0x1AFFB else sans_minnan.KU_ANGLE
                widths[label] = arm(first, k*angle, moved, sans_minnan.KU_REACH)
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
            'min_contour_width': round(thin, 1), 'min_contour_area': round(small), 'structure': shape,
            'stroke_widths': {k: round(v, 1) for k, v in widths.items()}}
    if regular is not None:
        # Bold: the same commands and points as Regular, and a weight gain
        # within Noto Sans JP's own kana.
        # Noto's kana letters and its spacing voicing marks, whose handakuten
        # ring the nasalized forms carry.
        letters = [cp for cp in (*range(0x3041, 0x3097), *range(0x30A1, 0x30FB)) if cp in base.getBestCmap()]
        marks = [0x309B, 0x309C]
        light = instance('NotoSansJP', 400, letters + marks + [0xFF65, 0x30FB])

        def gain(cp):
            return (weight(lambda pen: base.getGlyphSet()[base.getBestCmap()[cp]].draw(pen)) /
                    weight(lambda pen: light.getGlyphSet()[light.getBestCmap()[cp]].draw(pen)))

        letter_gains = [gain(cp) for cp in letters]
        mark_gains = {f'U+{cp:04X}': round(gain(cp), 3) for cp in marks}
        low, high = min(letter_gains + [gain(cp) for cp in marks]), max(letter_gains)
        # Noto's two middle dots, the marks nearest the dot below.
        dot_gains = [gain(0xFF65), gain(0x30FB)]
        report['kana_letter_gain_range'] = [round(min(letter_gains), 3), round(high, 3)]
        report['kana_mark_gains'] = mark_gains
        report['kana_gain_range'] = [round(low, 3), round(high, 3)]
        report['middle_dot_gains'] = [round(g, 3) for g in dot_gains]
        rcmap = regular.getBestCmap()
        for cp in FORMS:
            g, r = font['glyf'][cmap[cp]], regular['glyf'][rcmap[cp]]
            assert list(g.flags) == list(r.flags) and list(g.endPtsOfContours) == list(r.endPtsOfContours), hex(cp)
            ratio = (weight(lambda pen: font.getGlyphSet()[cmap[cp]].draw(pen)) /
                     weight(lambda pen: regular.getGlyphSet()[rcmap[cp]].draw(pen)))
            # Noto's dots gain less than any kana; the dot below must gain
            # within the range of its two middle dots.
            if cp == 0x0323:
                assert min(dot_gains) - .01 <= ratio <= max(dot_gains) + .01, (ratio, dot_gains)
            else:
                assert low <= ratio <= high, (hex(cp), ratio, low, high)
            report['forms'][f'U+{cp:04X}']['bold_gain'] = round(ratio, 3)
    return report


if __name__ == '__main__':
    import json

    from fontTools.ttLib import TTFont

    from sans import OUT, STEM, BOLD_STEM
    regular = TTFont(OUT/(STEM+'.ttf'))
    results = {'Regular': check_minnan_forms(regular, instance('NotoSansJP', 400), 400),
               'Bold': check_minnan_forms(TTFont(OUT/(BOLD_STEM+'.ttf')), instance('NotoSansJP', 700), 700, regular)}
    print(json.dumps({style: {key: value for key, value in report.items() if key != 'forms'} | {
        'forms_checked': len(report['forms'])} for style, report in results.items()}, ensure_ascii=False, indent=2))
