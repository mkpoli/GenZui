"""Trace learned distance fields for inspection; no stroke fitting or hinting."""

from functools import lru_cache

import numpy as np
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from skimage.measure import find_contours
from style_data import BASE, EM, PAD, SIZE


def field_path(field):
    # Pad with exterior so contours touching the canvas edge still close.
    paths = []
    for contour in find_contours(
        np.pad(field, 1, constant_values=-1), 0, fully_connected="high"
    ):
        points = contour[:, ::-1] - 0.5
        paths.append("M" + "L".join(f"{x:.3f},{y:.3f}" for x, y in points) + "Z")
    return "".join(paths)


@lru_cache(maxsize=8)
def glyph_set(font):
    return font.getGlyphSet()


def font_path(font, cp):
    name = font.getBestCmap().get(cp)
    if name is None:
        return None
    glyphs = glyph_set(font)
    pen = SVGPathPen(glyphs)
    scale = EM / font["head"].unitsPerEm
    glyphs[name].draw(TransformPen(pen, (scale, 0, 0, -scale, PAD, BASE)))
    return pen.getCommands()


def svg(path, field=False):
    # Native font contours use winding, including overlaps between strokes.
    rule = "evenodd" if field else "nonzero"
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SIZE} {SIZE}" width="{SIZE}" height="{SIZE}"><path fill="#202727" fill-rule="{rule}" d="{path}"/></svg>\n'
