"""Source-derived centrelines for tightly folded Tangut components.

Coordinates follow Noto Tangut's pinned Glyphs sources. Stroke weight and
square terminals are editorial sans adjustments.
"""

import pathops


def redraw(cp, width, donor):
    if cp == 0x16FE0:
        shape = pathops.Path()
        shape.moveTo(321, 746)
        shape.lineTo(620, 746)
        shape.cubicTo(568, 640, 470, 536, 350, 435)
        shape.lineTo(655, 450)
        shape.cubicTo(608, 299, 473, 115, 308, 15)
        shape.stroke(width, pathops.LineCap.BUTT_CAP, pathops.LineJoin.MITER_JOIN, 4)
        shape.convertConicsToQuads(0.2)
        shape.simplify()
        return shape
    bars = {
        0x188BB: (
            [(132, 655, 800), (140, 453, 925)],
            [(366.5, 453, 810), (596.5, 453, 810)],
            ((125, 463), (804, 646)),
        ),
        0x18943: (
            [(131, 768, 792), (135, 592, 924), (86, 471, 899)],
            [(312.5, 471, 710), (624.5, 471, 723)],
            ((124, 600), (806, 740)),
        ),
    }
    if cp not in bars:
        return None
    horizontal, vertical, diagonal = bars[cp]
    thin = width * 0.78
    shape = pathops.Path()
    shape.moveTo(*diagonal[0])
    shape.lineTo(*diagonal[1])
    shape.stroke(thin, pathops.LineCap.BUTT_CAP, pathops.LineJoin.MITER_JOIN, 2)
    for x, y, end in horizontal:
        shape = pathops.op(
            shape,
            donor("一", (x, y - thin / 2, end, y + thin / 2)),
            pathops.PathOp.UNION,
        )
    for x, y, end in vertical:
        shape = pathops.op(
            shape,
            donor("丨", (x - width / 2, y, x + width / 2, end)),
            pathops.PathOp.UNION,
        )
    return shape
