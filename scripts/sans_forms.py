"""Outline refits and drawings for GenZui Sans."""
import pathops
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen


# Donor outlines whose body sits outside the range of their kana peers. Each
# entry scales about the glyph's centre, then erodes the enlarged strokes back
# to the donor's stem width so the letter grows without getting heavier.
# GenSeki's Bold drawings have the same proportions and get the same fits.
REFITS = {
    400: {
        0x1B123: {'scale': 1.13, 'erode': 7, 'shift': (0, 0),
                  'reason': 'KOTO body raised from 723 to 802 units, the range of TOKI, TOTE and TOMO'},
        0x1B127: {'scale': 1.06, 'erode': 2, 'shift': (0, 0),
                  'reason': 'Alternate NE raised from 728 to 768 units, matching the katakana cap height'},
        0x1B168: {'scale': 1.0, 'erode': 0, 'shift': (0, -30),
                  'reason': 'Small archaic YE lowered 30 units onto the small-kana baseline'},
    },
    700: {
        0x1B123: {'scale': 1.12, 'erode': 7, 'shift': (0, 0),
                  'reason': 'KOTO body raised from 733 to 806 units, the range of TOKI, TOTE and TOMO'},
        0x1B127: {'scale': 1.125, 'erode': 7, 'shift': (0, 0),
                  'reason': 'Alternate NE raised from 735 to 813 units, matching the Bold katakana cap height'},
        0x1B168: {'scale': 1.0, 'erode': 0, 'shift': (0, -30),
                  'reason': 'Small archaic YE lowered 30 units onto the small-kana baseline'},
    },
}

# The drawn transcription symbols share one stroke per face: the half-turn
# arrow's ring weight, 36 units in Regular and 43 in Bold (Noto Sans JP's dashed
# frame has 31 and 37). The minus and the double arrow are drawn at that stroke;
# a scaled Noto arrow would keep Noto's much heavier stroke. The Bold half-turn
# arrow keeps the Regular drawing's outer edge and commands, its ring and barbs
# gaining 6-7 units inward.
SYMBOL_STROKE = {400: 36, 700: 43}


def double_arrow(stroke):
    """A double-headed arrow inside the IDC frame, every stroke `stroke` wide.

    Size and head angle follow Noto's arrow at the 0.72 scale the Serif uses:
    tips at x 165 and 835 on y 377, arms reaching 200 along and 150 across.
    """
    from fontTools.pens.svgPathPen import SVGPathPen
    reach = stroke/2 / 0.6  # a mitred tip extends half the stroke over sin(arm angle)
    left, right, y = 165 + reach, 835 - reach, 377
    shape = pathops.Path()
    pen = shape.getPen()
    pen.moveTo((left, y)); pen.lineTo((right, y)); pen.endPath()
    for x, direction in ((left, 1), (right, -1)):
        pen.moveTo((x + direction*200, y + 150)); pen.lineTo((x, y)); pen.lineTo((x + direction*200, y - 150))
        pen.endPath()
    shape.stroke(stroke, pathops.LineCap.BUTT_CAP, pathops.LineJoin.MITER_JOIN, 4)
    shape.simplify()
    svg = SVGPathPen(None, lambda v: f'{v:.1f}'.rstrip('0').rstrip('.'))
    shape.draw(svg)
    return svg.getCommands()


SANS_SYMBOLS = {
    400: {0x2FFE: double_arrow(SYMBOL_STROKE[400]),
          0x31EF: 'M230 362 H770 V398 H230 Z'},
    700: {0x2FFE: double_arrow(SYMBOL_STROKE[700]),
          0x2FFF: ('M470 710 C642 710 770 589 770 430 '
                   'C770 268 620 126 372 126 '
                   'L470 39 L441 8 L279 146 L441 284 L470 253 L370 164 '
                   'C585 164 727 283 727 430 C727 566 621 667 470 667 Z'),
          0x31EF: 'M230 359 H770 V402 H230 Z'},
}


# Minnan tone letters in Bold: a blend between the FRB outlines and the GenZui
# Bold masters drawn for Noto Serif JP Bold (data/minnan/bold.json). At 0.76
# their median weight gain over Regular is 1.53, the median gain of Noto Sans
# JP's kana; the full Serif masters gain 1.66.
BOLD_TONE_BLEND = 0.76


# Alternate WI, built like GenZui Serif's from the base font's own strokes:
# WI's bars and right stem, with NA's falling stroke as the left descent.
# NA's stroke is heavier than WI's stems, so it is thinned about its own
# centreline to the right stem's width. The descent then moves left and its
# foot comes back inward; the right stem keeps WI's position and the bars move
# closer, as in Serif. Both weights measure and move their own strokes.
WI_DESCENT_SHIFT, WI_FOOT_RETURN, WI_STEM_SHIFT = -160, 67, 0
WI_UPPER_DROP, WI_LOWER_RISE = 22, 30


def span(outline, y):
    """The horizontal extent of an outline at height y."""
    shape, band = pathops.Path(), pathops.Path()
    outline.replay(shape.getPen())
    pen = band.getPen()
    pen.moveTo((-200, y-.5)); pen.lineTo((1200, y-.5)); pen.lineTo((1200, y+.5)); pen.lineTo((-200, y+.5)); pen.closePath()
    x0, _, x1, _ = pathops.op(shape, band, pathops.PathOp.INTERSECTION).bounds
    return x0, x1


def alternate_wi(font):
    from serif import contours, glyph, transform
    from serif_forms import reshape

    stroke, stem = contours(font, ord('ナ'), [0]), contours(font, ord('ヰ'), [0])
    ratio = (lambda a, b: (b[1]-b[0])/(a[1]-a[0]))(span(stroke, 450), span(stem, 400))
    shape = pathops.Path()
    stroke.replay(shape.getPen())
    bottom, top = shape.bounds[1] + 12, shape.bounds[3] - 30
    centres = {}

    def centre(y):
        y = round(max(bottom, min(top, y)))
        if y not in centres:
            x0, x1 = span(stroke, y)
            centres[y] = (x0+x1)/2
        return centres[y]

    def descent(x, y):
        x = centre(y) + (x-centre(y))*ratio
        t = max(0, min(1, (350-y)/380))
        return x + WI_DESCENT_SHIFT + WI_FOOT_RETURN*t*t, y

    return glyph([reshape(stroke, descent),
                  transform(stem, (1, 0, 0, 1, WI_STEM_SHIFT, 0)),
                  transform(contours(font, ord('ヰ'), [3]), (1, 0, 0, 1, 0, -WI_UPPER_DROP)),
                  transform(contours(font, ord('ヰ'), [2]), (1, 0, 0, 1, 0, WI_LOWER_RISE))])


def refit(glyph_set, name, bounds, spec):
    scale, erode = spec['scale'], spec['erode']
    dx, dy = spec['shift']
    cx, cy = (bounds[0]+bounds[2])/2, (bounds[1]+bounds[3])/2
    shape = pathops.Path()
    glyph_set[name].draw(TransformPen(shape.getPen(),
                                      (scale, 0, 0, scale, cx-scale*cx+dx, cy-scale*cy+dy)))
    if erode:
        edge = pathops.Path(shape)
        edge.stroke(2*erode, pathops.LineCap.BUTT_CAP, pathops.LineJoin.ROUND_JOIN, 4)
        edge.convertConicsToQuads(.1)
        shape = pathops.op(shape, edge, pathops.PathOp.DIFFERENCE)
    shape.simplify()
    shape.convertConicsToQuads(.1)
    outline = RecordingPen()
    shape.draw(outline)
    return outline
