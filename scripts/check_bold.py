"""Check GenZui Serif Bold against the Noto Serif Bold instances."""
import hashlib

import pathops
from fontTools.ttLib import TTFont

from serif import CJK_BOLD, FAMILY, FAMILY_JA, OUT, STEM, VERSION, instance

BOLD = OUT / 'GenZuiSerif-Bold.ttf'


def signature(font, codepoint):
    path = pathops.Path()
    font.getGlyphSet()[font.getBestCmap()[codepoint]].draw(path.getPen())
    points = []
    for verb, args in path.segments:
        points.append((verb, tuple((round(x), round(y)) for x, y in args)))
    return points


def stem(font, codepoint):
    path = pathops.Path()
    font.getGlyphSet()[font.getBestCmap()[codepoint]].draw(path.getPen())
    bounds = path.bounds
    samples = []
    for y in range(int(bounds[1]) + 40, int(bounds[3]) - 40, 12):
        spans, inside, start = [], False, None
        for x in range(int(bounds[0]) - 2, int(bounds[2]) + 3):
            hit = path.contains((x + 0.5, y))
            if hit and not inside:
                start, inside = x, True
            elif not hit and inside:
                spans.append(x - start)
                inside = False
        stems = [span for span in spans if 20 <= span <= 180]
        if stems:
            samples.append(min(stems))
    samples.sort()
    return samples[len(samples) // 2]


def main():
    font = TTFont(BOLD, recalcTimestamp=False)
    assert font['name'].getDebugName(1) == FAMILY
    assert font['name'].getDebugName(2) == 'Bold'
    assert font['name'].getDebugName(4) == FAMILY + ' Bold'
    assert font['name'].getDebugName(6) == 'GenZuiSerif-Bold'
    assert font['name'].getDebugName(5) == 'Version ' + VERSION
    assert font['name'].getName(1, 3, 1, 0x411).toUnicode() == FAMILY_JA
    assert font['name'].getName(2, 3, 1, 0x411).toUnicode() == 'Bold'
    assert font['name'].getName(16, 3, 1, 0x409).toUnicode() == FAMILY
    assert font['name'].getName(17, 3, 1, 0x409).toUnicode() == 'Bold'
    assert font['OS/2'].usWeightClass == 700
    assert font['head'].macStyle & 1
    assert font['OS/2'].fsSelection & 32
    assert not font['OS/2'].fsSelection & 64
    assert 'fvar' not in font
    web = TTFont(OUT / 'GenZuiSerif-Bold.woff2')
    web.flavor = None
    assert web.getBestCmap() == font.getBestCmap()

    jp = instance('NotoSerifJP', 700, {0x30C8, 0x3042, 0x4E00, 0x6B63})
    for codepoint in (0x30C8, 0x3042, 0x4E00, 0x6B63):
        assert signature(font, codepoint) == signature(jp, codepoint), hex(codepoint)
    henta = instance('NotoSerifHentaigana', 700, {0x1B002})
    assert signature(font, 0x1B002) == signature(henta, 0x1B002)

    # Drawn WU is dilated from Regular, so its stem sits with Bold ト (105).
    wu = stem(font, 0x1B11F)
    assert 90 <= wu <= 125, wu
    assert abs(stem(font, 0x30C8) - 105) <= 8

    def bounds(source, codepoint):
        path = pathops.Path()
        source.getGlyphSet()[source.getBestCmap()[codepoint]].draw(path.getPen())
        return tuple(round(value) for value in path.bounds)

    with TTFont(CJK_BOLD) as cjk:
        # Cubic-to-quadratic conversion can move a bound by a fraction of a unit.
        assert all(abs(a - b) <= 1 for a, b in zip(bounds(font, 0x5344), bounds(cjk, 0x5344)))

    regular = OUT / (STEM + '.ttf')
    if regular.exists():
        regular_font = TTFont(regular, recalcTimestamp=False)
        assert font.getBestCmap().keys() == regular_font.getBestCmap().keys()
        assert stem(regular_font, 0x1B11F) < wu

    digest = hashlib.sha256(BOLD.read_bytes()).hexdigest()
    print(f'GenZui Serif Bold {VERSION}: {len(font.getBestCmap()):,} characters, WU stem {wu}, sha256 {digest}')


if __name__ == '__main__':
    main()
