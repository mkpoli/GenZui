"""Verify native Bold proof fonts, mark isolation, shaping and donor clearance."""
from functools import lru_cache

import pathops
from fontTools.pens.recordingPen import RecordingPen
from fontTools.ttLib import TTFont

from check_serif import serialized, shape, shaper
from okinawan import DAKUTEN, ENTRIES, voiced_parts
from okinawan_ligatures import POINTS
from okinawan_release_proof import OUT
from serif import OUT as FONT_OUT, contours, transform


@lru_cache(maxsize=None)
def engine_for(font):
    return shaper(serialized(font))


def outline(font, text):
    shaped = shape(engine_for(font), text, 'ltr')
    assert len(shaped) == 1 and shaped[0][0], repr(text)
    assert shaped[0][1] == 1000, (repr(text), 'advance')
    name = font.getGlyphName(shaped[0][0])
    pen = RecordingPen()
    font.getGlyphSet()[name].draw(pen)
    return pen.value


def opened(name):
    font = TTFont(OUT / name)
    font.flavor = None
    return font


def check():
    samples = [chr(cp) for cp in sorted(POINTS)]
    voiced = [''.join(chr(int(c, 16)) for c in e['output']) for e in ENTRIES
              if len(e['output']) == 2 and int(e['output'][0], 16) in DAKUTEN]
    assert len(voiced) == 7
    for style in ('Regular', 'Bold'):
        full = TTFont(FONT_OUT / f'GenZuiSerif-{style}.ttf')
        native = opened(f'{style.lower()}-A.woff2')
        compact = opened(f'{style.lower()}-B.woff2')
        for text in samples + voiced:
            assert outline(native, text) == outline(full, text), (style, repr(text), 'full font differs')
        for text in samples:
            assert outline(native, text) == outline(compact, text), 'mark option changes the base'
        for text in voiced:
            assert outline(native, text) != outline(compact, text), 'marks did not change'
        for cp in DAKUTEN:
            parts = voiced_parts(full, cp, [contours(full, cp)], contours, transform)
            body, mark = pathops.Path(), pathops.Path()
            for part in parts[:-1]:
                part.replay(body.getPen())
            parts[-1].replay(mark.getPen())
            assert pathops.op(body, mark, pathops.PathOp.INTERSECTION).area < .01, (style, hex(cp), 'dakuten collision')
    alternative = opened('bold-A-700.woff2')
    selected = opened('bold-A.woff2')
    for cp in POINTS:
        a, b = outline(alternative, chr(cp)), outline(selected, chr(cp))
        assert (a == b) == (cp in (0xF450, 0xF465)), (hex(cp), 'native donor choice')
    for text in voiced:
        # SI is native in both; TU keeps the same full-size body.
        if ord(text[0]) not in (0xF450, 0xF467):
            assert outline(alternative, text) != outline(selected, text), repr(text)
    print('Native proof passed: exact full-font outlines, eight donor alternatives, seven dakuten pairs, fixed advances and no mark collisions.')


if __name__ == '__main__':
    check()
