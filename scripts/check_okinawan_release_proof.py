"""Check that the Bold proof shows the compiled base and voiced choices."""
from functools import lru_cache

from fontTools.pens.recordingPen import RecordingPen
from fontTools.ttLib import TTFont

from check_serif import serialized, shape, shaper
from okinawan import ENTRIES
from okinawan_ligatures import POINTS
from okinawan_release_proof import OUT, VARIANTS
from serif import OUT as FONT_OUT


@lru_cache(maxsize=None)
def engine_for(font):
    return shaper(serialized(font))


def outline(font, text):
    shaped = shape(engine_for(font), text, 'ltr')
    assert len(shaped) == 1 and shaped[0][0], repr(text)
    name = font.getGlyphName(shaped[0][0])
    pen = RecordingPen()
    font.getGlyphSet()[name].draw(pen)
    return pen.value


def check():
    fonts = {}
    for variant in VARIANTS:
        font = TTFont(OUT / f'bold-{variant}.woff2')
        font.flavor = None
        fonts[variant] = font
    full = TTFont(FONT_OUT / 'GenZuiSerif-Bold.ttf')
    samples = [chr(cp) for cp in sorted(POINTS)]
    voiced = [''.join(chr(int(c, 16)) for c in e['output']) for e in ENTRIES
              if len(e['output']) == 2 and int(e['output'][0], 16) in POINTS]
    assert len(voiced) == 6
    for text in samples + voiced:
        a, b, c = [outline(fonts[v], text) for v in VARIANTS]
        assert a != b and b != c and a != c, (repr(text), 'variants repeat an outline')
        assert b == outline(full, text), (repr(text), 'standard proof differs from full Bold')
    regular = TTFont(OUT / 'regular.woff2')
    regular.flavor = None
    full_regular = TTFont(FONT_OUT / 'GenZuiSerif-Regular.ttf')
    for text in samples + voiced:
        assert outline(regular, text) == outline(full_regular, text)
    print('Proof: ten bases and six voiced forms vary in A/B/C; Regular and Bold B match the full fonts exactly.')


if __name__ == '__main__':
    check()
