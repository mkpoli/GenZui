"""Check GenZui Serif Bold against the Noto Serif Bold instances."""
import hashlib
import re

import numpy as np
import pathops
from fontTools.ttLib import TTFont
from skimage.morphology import medial_axis

from draft_bold import glyph_path, mask, parse, shape
from minnan import BOLD as MINNAN_BOLD, source_font
from sources import ROOT
from okinawan import PUA as OKINAWAN_PUA
from repertoire import MINNAN_MARKS, MINNAN_TONES
from serif import CJK_BOLD, FAMILY, FAMILY_JA, OUT, STEM, VERSION, instance
from serif_forms import CURVED_WU_BRIDGE, DESCRIPTIONS, HOOKED_WU, NARI_WAVE, wu_alternate

BOLD = OUT / 'GenZuiSerif-Bold.ttf'


def signature(font, codepoint):
    path = pathops.Path()
    font.getGlyphSet()[font.getBestCmap()[codepoint]].draw(path.getPen())
    points = []
    for verb, args in path.segments:
        points.append((verb, tuple((round(x), round(y)) for x, y in args)))
    return points


def weight(font, name):
    """Median stroke width along the glyph's medial axis, in font units."""
    path = pathops.Path()
    font.getGlyphSet()[name].draw(path.getPen())
    skeleton, distance = medial_axis(mask(pathops.simplify(path)), return_distance=True)
    widths = 2 * distance[skeleton]
    return float(np.median(widths[widths > 6]))


def height(font, name):
    glyph = font['glyf'][name]
    return glyph.yMax - glyph.yMin


def masters():
    """Each drawn Regular and Bold master pair, as SVG path data."""
    for module in ('serif_forms', 'okinawan'):
        source = (ROOT/'scripts'/f'{module}.py').read_text()
        for match in re.finditer(r"drawn\(\s*((?:'[^']*'\s*)+),\s*((?:'[^']*'\s*)+)\)", source):
            yield tuple(''.join(re.findall(r"'([^']*)'", match.group(k))) for k in (1, 2))
    yield HOOKED_WU[False]['stem'], HOOKED_WU[True]['stem']
    yield from zip(HOOKED_WU[False]['bars'], HOOKED_WU[True]['bars'])
    yield NARI_WAVE[False][0], NARI_WAVE[True][0]
    frb = source_font()
    for cp in (*MINNAN_TONES, *MINNAN_MARKS):
        yield glyph_path(frb.getGlyphSet(), frb.getBestCmap()[cp]), MINNAN_BOLD[f'U+{cp:04X}']


def point_masters():
    """Masters written as point tuples rather than path data."""
    yield CURVED_WU_BRIDGE[False], CURVED_WU_BRIDGE[True]
    yield NARI_WAVE[False][1:], NARI_WAVE[True][1:]


def shape_of(points):
    return [shape_of(p) for p in points] if isinstance(points[0], tuple) else len(points)


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
    assert font['OS/2'].panose.bWeight == 8
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

    # Masters share their commands and points, so the pair stays interpolable.
    pairs = list(masters())
    shapes = [[[(c, len(v)) for c, v in parse(d)] for d in pair] for pair in pairs]
    assert len(pairs) >= 41 and all(r == b for r, b in shapes)
    assert all(shape_of(r) == shape_of(b) for r, b in point_masters())
    # A Bold master that crosses itself where Regular does not folds into a
    # twist or a speck. Open paths are completed by native strokes.
    twisted = [b[:24] for r, b in pairs if b.rstrip().endswith('Z')
               and len(list(shape(b).contours)) != len(list(shape(r).contours))]
    assert not twisted, twisted

    # Every GenZui drawing gains weight as Noto's own kana do, 400 to 700.
    regular_path = OUT / (STEM + '.ttf')
    assert regular_path.exists(), 'Build Regular first: python scripts/serif.py'
    regular = TTFont(regular_path, recalcTimestamp=False)
    assert font.getBestCmap().keys() == regular.getBestCmap().keys()
    native = [weight(font, font.getBestCmap()[cp]) / weight(regular, regular.getBestCmap()[cp])
              for cp in map(ord, 'トあけほんえヨリキテふゆゐゑすつ')]
    low, high = min(native) - .12, max(native) + .12
    drawn = {f'U+{cp:04X}': regular.getBestCmap()[cp]
             for cp in (*DESCRIPTIONS, *OKINAWAN_PUA, *MINNAN_TONES, *MINNAN_MARKS)}
    drawn['ss01'] = wu_alternate(regular)
    gains = {}
    for label, name in drawn.items():
        heavy = wu_alternate(font) if label == 'ss01' else font.getBestCmap()[int(label[2:], 16)]
        if label in ('U+0305', 'U+0323'):
            # A bar's thickness and a dot's diameter carry a mark's weight.
            gains[label] = round(height(font, heavy) / height(regular, name), 2)
        else:
            gains[label] = round(weight(font, heavy) / weight(regular, name), 2)
    # Filled teardrop tones gain as Noto's dots do.
    dots = [weight(font, font.getBestCmap()[cp]) / weight(regular, regular.getBestCmap()[cp])
            for cp in map(ord, '・、')]
    bands = {label: (min(dots) - .12, max(dots) + .12) if label in ('U+1AFF2', 'U+1AFF6', 'U+0323')
             else (low, high) for label in gains}
    off = {k: (v, tuple(round(b, 2) for b in bands[k]))
           for k, v in gains.items() if not bands[k][0] <= v <= bands[k][1]}
    assert not off, off

    # A twisted corner in a master leaves specks after overlap removal.
    specks = {}
    for label in drawn:
        name = wu_alternate(font) if label == 'ss01' else font.getBestCmap()[int(label[2:], 16)]
        path = pathops.Path()
        font.getGlyphSet()[name].draw(path.getPen())
        small = [round(abs(c.area), 1) for c in path.contours if abs(c.area) < 150]
        if small:
            specks[label] = small
    assert not specks, specks

    def bounds(source, codepoint):
        path = pathops.Path()
        source.getGlyphSet()[source.getBestCmap()[codepoint]].draw(path.getPen())
        return tuple(round(value) for value in path.bounds)

    with TTFont(CJK_BOLD) as cjk:
        # Cubic-to-quadratic conversion can move a bound by a fraction of a unit.
        assert all(abs(a - b) <= 1 for a, b in zip(bounds(font, 0x5344), bounds(cjk, 0x5344)))

    digest = hashlib.sha256(BOLD.read_bytes()).hexdigest()
    print(f'GenZui Serif Bold {VERSION}: {len(font.getBestCmap()):,} characters; '
          f'{len(pairs) + 2} compatible masters; {len(gains)} drawings gain {min(gains.values())}-{max(gains.values())}x '
          f'(Noto kana {min(native):.2f}-{max(native):.2f}x); sha256 {digest}')


if __name__ == '__main__':
    main()
