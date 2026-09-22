"""Outline refits for GenZui Sans."""
import pathops
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen


# Donor outlines whose body sits outside the range of their kana peers. Each
# entry scales about the glyph's centre, then erodes the enlarged strokes back
# to the donor's stem width so the letter grows without getting heavier.
REFITS = {
    0x1B123: {'scale': 1.13, 'erode': 7, 'shift': (0, 0),
              'reason': 'KOTO body raised from 723 to 802 units, the range of TOKI, TOTE and TOMO'},
    0x1B127: {'scale': 1.06, 'erode': 2, 'shift': (0, 0),
              'reason': 'Alternate NE raised from 728 to 768 units, matching the katakana cap height'},
    0x1B168: {'scale': 1.0, 'erode': 0, 'shift': (0, -30),
              'reason': 'Small archaic YE lowered 30 units onto the small-kana baseline'},
}


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
