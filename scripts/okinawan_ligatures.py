"""Final GenZui Funatsu ligatures in the font's 1000-unit coordinate system.

The source outlines retain the Noto Serif JP stroke components and GenZui
joins. Bold is composed separately from Noto’s native Bold components.
"""
import json
from functools import lru_cache

import pathops
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.svgLib.path import parse_path

from sources import ROOT

SOURCE = ROOT / 'data/okinawan/ligatures.json'
POINTS = frozenset((0xF450, 0xF452, 0xF454, 0xF456, 0xF458,
                    0xF45A, 0xF45B, 0xF45C, 0xF465, 0xF469))


@lru_cache(maxsize=1)
def source():
    data = json.loads(SOURCE.read_text())
    assert data['unitsPerEm'] == 1000
    assert len(data['glyphs']) == len(POINTS)
    assert {int(g['codepoint'], 16) for g in data['glyphs']} == POINTS
    return data


def drawings():
    result = {}
    for glyph in source()['glyphs']:
        merged = pathops.Path()
        for component in glyph['components']:
            shape = pathops.Path()
            parse_path(component['path'], TransformPen(shape.getPen(), component['transform']))
            merged = pathops.op(merged, shape, pathops.PathOp.UNION)
        pen = RecordingPen()
        merged.draw(pen)
        result[int(glyph['codepoint'], 16)] = [pen]
    return result
