"""Final GenZui Funatsu ligatures in the font's 1000-unit coordinate system.

The source outlines retain the Noto Serif JP stroke components and GenZui
joins. Bold uses an anisotropic expansion to retain Mincho stroke contrast.
"""
import json
from functools import lru_cache

import pathops
from fontTools.pens.basePen import BasePen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.svgLib.path import parse_path

from sources import ROOT

SOURCE = ROOT / 'data/okinawan/ligatures.json'
POINTS = frozenset((0xF450, 0xF452, 0xF454, 0xF456, 0xF458,
                    0xF45A, 0xF45B, 0xF45C, 0xF465, 0xF469))
# Horizontal stems receive less expansion than vertical stems.
BOLD_RADII = {
    'TU': (22, 8), 'TI': (22, 7), 'KWA': (18, 5), 'KWI': (20, 5),
    'KWE': (22, 7), 'HWA': (20, 5), 'HWI': (16, 4.5),
    'HWE': (18, 5), 'WU': (22, 8), 'TSI': (20, 5),
}


@lru_cache(maxsize=1)
def source():
    data = json.loads(SOURCE.read_text())
    assert data['unitsPerEm'] == 1000
    assert len(data['glyphs']) == len(POINTS)
    assert {int(g['codepoint'], 16) for g in data['glyphs']} == POINTS
    return data


def _smooth(value, lo, hi):
    t = min(1.0, max(0.0, (value - lo) / (hi - lo)))
    return t * t * (3 - 2 * t), 6 * t * (1 - t) / (hi - lo)


class _OpenVowelPen(BasePen):
    """Keep the added vowel clear of fu as their Bold strokes expand."""
    def __init__(self, out, shift):
        super().__init__(None)
        self.out, self.shift = out, shift

    def point(self, p):
        f, _ = _smooth(p[0], 500, 580)
        return p[0] + self.shift * f, p[1]

    def control(self, p, c):
        _, fx = _smooth(p[0], 500, 580)
        dx, dy = c[0] - p[0], c[1] - p[1]
        x, y = self.point(p)
        return x + (1 + self.shift * fx) * dx, y + dy

    def _moveTo(self, p):
        self.out.moveTo(self.point(p))

    def _lineTo(self, p):
        self.out.lineTo(self.point(p))

    def _curveToOne(self, b, c, d):
        a = self._getCurrentPoint()
        self.out.curveTo(self.control(a, b), self.control(d, c), self.point(d))

    def _qCurveToOne(self, b, c):
        a = self._getCurrentPoint()
        h0 = tuple(a[i] + (b[i] - a[i]) * 2 / 3 for i in (0, 1))
        h1 = tuple(c[i] + (b[i] - c[i]) * 2 / 3 for i in (0, 1))
        self._curveToOne(h0, h1, c)

    def _closePath(self):
        self.out.closePath()

    def _endPath(self):
        self.out.endPath()


def source_shape(glyph, bold=False, strength=1.0):
    merged = pathops.Path()
    for index, component in enumerate(glyph['components']):
        shape = pathops.Path()
        parse_path(component['path'], TransformPen(shape.getPen(), component['transform']))
        if bold and glyph['label'] in ('HWA', 'HWE') and index == 1:
            opened = pathops.Path()
            shift = 24 if glyph['label'] == 'HWA' else 32
            shape.draw(_OpenVowelPen(opened.getPen(), shift * strength))
            shape = opened
        if bold:
            radii = BOLD_RADII[glyph['label']]
            if glyph['label'] == 'HWA' and index == 2:
                # The small wa counter needs less expansion than its stem;
                # move the loop with the stem and retain a right sidebearing.
                shape = shape.transform(.97, 0, 0, 1, 580 * .03 + 24 * strength, 0)
                radii = (8, 5)
            shape = bold_shape(shape, radii, strength)
        merged = pathops.op(merged, shape, pathops.PathOp.UNION)
    if bold:
        # Offset intersection arithmetic can leave sub-unit slivers. These
        # have less than 0.01 square font units of area and cannot print.
        cleaned = pathops.Path()
        for contour in merged.contours:
            if abs(contour.area) >= .01:
                contour.draw(cleaned.getPen())
        merged = cleaned
    return merged


def bold_shape(shape, radii, strength=1.0):
    rx, ry = (r * strength for r in radii)
    scaled = shape.transform(1 / rx, 0, 0, 1 / ry, 0, 0)
    border = pathops.Path(scaled)
    border.stroke(2, pathops.LineCap.ROUND_CAP, pathops.LineJoin.ROUND_JOIN, 4)
    border.convertConicsToQuads(.025)
    return pathops.op(scaled, border, pathops.PathOp.UNION).transform(rx, 0, 0, ry, 0, 0)


def drawings(bold=False, strength=1.0):
    result = {}
    for glyph in source()['glyphs']:
        shape = source_shape(glyph, bold=bold, strength=strength)
        pen = RecordingPen()
        shape.draw(pen)
        result[int(glyph['codepoint'], 16)] = [pen]
    return result
