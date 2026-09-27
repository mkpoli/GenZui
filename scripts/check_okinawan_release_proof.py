"""Verify proof choices against the actual fonts and native kana context."""
from functools import lru_cache

import pathops
from fontTools.pens.recordingPen import RecordingPen
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_l_y_f import Glyph

from check_serif import serialized, shape, shaper
from okinawan import DAKUTEN, ENTRIES, voiced_parts
from okinawan_ligatures import POINTS, drawings as approved_drawings
from okinawan_release_proof import OUT
from serif import OUT as FONT_OUT, contours, glyph, transform


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


def united(parts):
    merged = pathops.Path()
    for part in parts:
        path = pathops.Path()
        part.replay(path.getPen())
        merged = pathops.op(merged, path, pathops.PathOp.UNION)
    pen = RecordingPen()
    merged.draw(pen)
    return pen


def topology(pen):
    p = pathops.Path()
    pen.replay(p.getPen())
    p = pathops.simplify(p)
    return (sum(not c.clockwise for c in p.contours),
            sum(c.clockwise for c in p.contours))


def same_compiled(font, cp, parts, geometric=False):
    expected = glyph([united(parts)])
    expected = Glyph(expected.compile(font['glyf']))
    expected.expand(font['glyf'])
    actual = font['glyf'][font.getBestCmap()[cp]]
    if geometric:
        a, b = pathops.Path(), pathops.Path()
        expected.draw(a.getPen(), font['glyf'])
        actual.draw(b.getPen(), font['glyf'])
        assert pathops.op(a, b, pathops.PathOp.XOR).area < .01, (hex(cp), 'approved shape changed')
    else:
        assert actual.getCoordinates(font['glyf']) == expected.getCoordinates(font['glyf']), (hex(cp), 'stale composition')


def check():
    samples = [chr(cp) for cp in sorted(POINTS | {0xF467})]
    voiced = [''.join(chr(int(c, 16)) for c in e['output']) for e in ENTRIES
              if len(e['output']) == 2 and int(e['output'][0], 16) in DAKUTEN]
    assert len(voiced) == 7
    retained = {0xF452, 0xF45B, 0xF45C}
    approved = approved_drawings()
    from okinawan_bold import drawings
    for style in ('Regular', 'Bold'):
        full = TTFont(FONT_OUT / f'GenZuiSerif-{style}.ttf')
        selected = opened(f'{style.lower()}-B.woff2')
        alternative = opened(f'{style.lower()}-A.woff2')
        for text in samples + voiced:
            assert outline(selected, text) == outline(full, text), (style, repr(text), 'full font differs')
        # SI and ZI are confirmed and identical in both options.
        for text in (chr(0xF467), chr(0xF467)+'\u3099'):
            assert outline(selected, text) == outline(alternative, text), (style, 'SI changed')
        for cp in POINTS:
            differs = outline(selected, chr(cp)) != outline(alternative, chr(cp))
            assert differs == (style == 'Bold' or cp not in retained), (style, hex(cp), 'wrong option coverage')
        for cp, parts in drawings(full, contours, style=style).items():
            same_compiled(full, cp, parts)
            assert topology(contours(full, cp)) == topology(united(approved[cp])), (style, hex(cp), 'changed counters')
        if style == 'Regular':
            for cp in retained:
                same_compiled(full, cp, approved[cp], geometric=True)
        for face in (selected, alternative):
            for cp, donor in ((0xF454,'く'), (0xF456,'く'), (0xF458,'く'),
                              (0xF450,'と'), (0xF465,'を'), (0xF469,'つ')):
                cm = face.getBestCmap()
                assert abs(face['glyf'][cm[cp]].yMax-face['glyf'][cm[ord(donor)]].yMax) <= 1, (style, hex(cp), 'source top')
            for cp in DAKUTEN:
                original = contours(face, cp)
                parts = voiced_parts(face, cp, [original], contours, transform)
                assert parts[0].value == original.value, (style, hex(cp), 'voiced body shrank')
                body, mark = pathops.Path(), pathops.Path()
                parts[0].replay(body.getPen())
                parts[-1].replay(mark.getPen())
                assert pathops.op(body, mark, pathops.PathOp.INTERSECTION).area < .01, (style, hex(cp), 'dakuten collision')
                assert topology(parts[-1]) == (2,0), (style, hex(cp), 'dakuten pair')
                if face is alternative:
                    # A rebuilds voiced glyphs; B was compared with the full font above.
                    expected = glyph(parts)
                    expected = Glyph(expected.compile(face['glyf']))
                    expected.expand(face['glyf'])
                    ep = RecordingPen()
                    expected.draw(ep, face['glyf'])
                    actual = RecordingPen()
                    actual.value = outline(face, chr(cp)+'\u3099')
                    a, b = pathops.Path(), pathops.Path()
                    ep.replay(a.getPen())
                    actual.replay(b.getPen())
                    assert pathops.op(a, b, pathops.PathOp.XOR).area < .01, (style, hex(cp), 'voiced option does not follow base')

    print('Context proof passed: exact compiled choices, approved counters, retained forms, native top heights, unchanged voiced bodies, SI/ZI and clear dakuten in both options.')


if __name__ == '__main__':
    check()
