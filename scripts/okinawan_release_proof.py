"""Build a local Regular/Bold proof for the ten Okinawan ligatures."""
import json
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont

from okinawan_ligatures import drawings, source
from okinawan import ENTRIES
from serif import OUT as FONT_OUT, VERSION, glyph, contours, transform
from sources import ROOT

OUT = ROOT / 'build/okinawan-release'
VARIANTS = {'A': .85, 'B': 1.0, 'C': 1.15}
NEIGHBOURS = {'TU': 'とつ', 'TI': 'てい', 'KWA': 'くわ', 'KWI': 'くい',
              'KWE': 'くえ', 'HWA': 'ふわ', 'HWI': 'ふい', 'HWE': 'ふえ',
              'WU': 'をう', 'TSI': 'つい'}


def webfont(style, variant=None):
    font = TTFont(FONT_OUT / f'GenZuiSerif-{style}.ttf', recalcTimestamp=False)
    if variant and variant != 'B':
        cmap = font.getBestCmap()
        recipes = drawings(bold=True, strength=VARIANTS[variant])
        for cp, parts in recipes.items():
            name = cmap[cp]
            g = glyph(parts)
            font['glyf'][name] = g
            g.recalcBounds(font['glyf'])
            font['hmtx'][name] = (1000, g.xMin)
            font['vmtx'][name] = (1000, 880 - g.yMax)
        mark_glyph = font['glyf'][cmap[0x309B]]
        mark = transform(contours(font, 0x309B), (.72, 0, 0, .72,
                         810 - .72 * mark_glyph.xMin, 825 - .72 * mark_glyph.yMax))
        for entry in ENTRIES:
            if len(entry['output']) != 2:
                continue
            cp = int(entry['output'][0], 16)
            if cp not in recipes:
                continue
            names = {lig.LigGlyph
                     for lookup in font['GSUB'].table.LookupList.Lookup if lookup.LookupType == 4
                     for sub in lookup.SubTable
                     for lig in sub.ligatures.get(cmap[cp], [])
                     if lig.Component == [cmap[0x3099]]}
            assert len(names) == 1, entry['id']
            name = names.pop()
            g = glyph([transform(p, (.9, 0, 0, .9, 0, 0)) for p in recipes[cp]] + [mark])
            font['glyf'][name] = g
            g.recalcBounds(font['glyf'])
            font['hmtx'][name] = (1000, g.xMin)
            font['vmtx'][name] = (1000, 880 - g.yMax)
    points = {int(g['codepoint'], 16) for g in source()['glyphs']}
    points.update(range(0x3041, 0x30A0))
    options = subset.Options()
    options.recalc_timestamp = False
    sub = subset.Subsetter(options=options)
    sub.populate(unicodes=points)
    sub.subset(font)
    font.flavor = 'woff2'
    font.save(OUT / (f'bold-{variant}.woff2' if variant else 'regular.woff2'))


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    webfont('Regular')
    for variant in VARIANTS:
        webfont('Bold', variant)
    data = {'version': VERSION, 'glyphs': [
        {'label': g['label'], 'character': chr(int(g['codepoint'], 16)),
         'neighbours': NEIGHBOURS[g['label']],
         'voiced': next((''.join(chr(int(c, 16)) for c in e['output']) for e in ENTRIES
                         if len(e['output']) == 2 and e['output'][0] == g['codepoint']), None)} for g in source()['glyphs']]}
    template = (ROOT / 'templates/okinawan-release/index.html').read_text()
    (OUT / 'index.html').write_text(template.replace('{{DATA}}', json.dumps(data, ensure_ascii=False)))
    print(f'Okinawan {VERSION} proof: Regular and three Bold weights.')


if __name__ == '__main__':
    build()
