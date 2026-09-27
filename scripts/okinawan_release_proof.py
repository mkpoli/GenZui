"""Build the native Noto Bold proof with native dakuten comparisons."""
import json
import pathops
from fontTools.pens.recordingPen import RecordingPen

from fontTools import subset
from fontTools.ttLib import TTFont

from okinawan_ligatures import source
from okinawan import DAKUTEN, ENTRIES, voiced_parts
from serif import OUT as FONT_OUT, VERSION, glyph, contours, transform
from sources import ROOT

OUT = ROOT / 'build/okinawan-release'
VARIANTS = {'A': 1.0, 'B': .95}
NEIGHBOURS = {'TU': 'とつ', 'TI': 'てい', 'KWA': 'くわ', 'KWI': 'くい',
              'KWE': 'くえ', 'HWA': 'ふわ', 'HWI': 'ふい', 'HWE': 'ふえ',
              'WU': 'をう', 'TSI': 'つい'}


def composed_name(font, cp):
    cmap = font.getBestCmap()
    names = {lig.LigGlyph
             for lookup in font['GSUB'].table.LookupList.Lookup if lookup.LookupType == 4
             for sub in lookup.SubTable
             for lig in sub.ligatures.get(cmap[cp], [])
             if lig.Component == [cmap[0x3099]]}
    assert len(names) == 1, hex(cp)
    return names.pop()


def webfont(style, variant, vowel_weight=None):
    font = TTFont(FONT_OUT / f'GenZuiSerif-{style}.ttf', recalcTimestamp=False)
    if vowel_weight is not None:
        from okinawan_bold import drawings
        cmap = font.getBestCmap()
        for cp, parts in drawings(font, contours, vowel_weight=vowel_weight).items():
            merged = pathops.Path()
            for part in parts:
                shape = pathops.Path()
                part.replay(shape.getPen())
                merged = pathops.op(merged, shape, pathops.PathOp.UNION)
            pen = RecordingPen()
            merged.draw(pen)
            g = glyph([pen])
            name = cmap[cp]
            font['glyf'][name] = g
            g.recalcBounds(font['glyf'])
            font['hmtx'][name] = (1000, g.xMin)
            font['vmtx'][name] = (1000, 880-g.yMax)
    if variant != 'A' or vowel_weight is not None:
        for cp in DAKUTEN:
            name = composed_name(font, cp)
            parts = voiced_parts(font, cp, [contours(font, cp)], contours, transform,
                                 mark_scale=VARIANTS[variant])
            g = glyph(parts)
            font['glyf'][name] = g
            g.recalcBounds(font['glyf'])
            font['hmtx'][name] = (1000, g.xMin)
            font['vmtx'][name] = (1000, 880 - g.yMax)
    points = {int(g['codepoint'], 16) for g in source()['glyphs']} | set(DAKUTEN)
    points.update(range(0x3041, 0x30A0))
    options = subset.Options()
    options.recalc_timestamp = False
    sub = subset.Subsetter(options=options)
    sub.populate(unicodes=points)
    sub.subset(font)
    font.flavor = 'woff2'
    suffix = '-700' if vowel_weight is not None else ''
    font.save(OUT / f'{style.lower()}-{variant}{suffix}.woff2')


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    for style in ('Regular', 'Bold'):
        for variant in VARIANTS:
            webfont(style, variant)
    for variant in VARIANTS:
        webfont('Bold', variant, vowel_weight=700)
    data = {'version': VERSION, 'glyphs': [
        {'label': g['label'], 'character': chr(int(g['codepoint'], 16)), 'hasOptions': g['label'] not in ('TU', 'WU'),
         'neighbours': NEIGHBOURS[g['label']]} for g in source()['glyphs']],
        'voiced': [{'id': e['id'], 'label': e['label'],
                    'character': ''.join(chr(int(c, 16)) for c in e['output']),
                    'reference': DAKUTEN[int(e['output'][0], 16)][0],
                    'baseLabel': next((g['label'] for g in source()['glyphs'] if g['codepoint'] == e['output'][0]), None)}
                   for e in ENTRIES if len(e['output']) == 2
                   and int(e['output'][0], 16) in DAKUTEN]}
    template = (ROOT / 'templates/okinawan-release/index.html').read_text()
    (OUT / 'index.html').write_text(template.replace('{{DATA}}', json.dumps(data, ensure_ascii=False)))
    # Remove superseded comparison fonts.
    for name in ('regular.woff2', 'bold-C.woff2'):
        (OUT / name).unlink(missing_ok=True)
    print(f'Okinawan {VERSION} proof: native Bold recomposed; seven dakuten pairs in both weights.')


if __name__ == '__main__':
    build()
