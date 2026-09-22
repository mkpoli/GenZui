"""Build GenZui Sans Regular from pinned, drawn sans sources."""
import copy
import json
import shutil

from fontTools.ttLib import TTFont

from sources import ROOT
from serif import add, add_feature, contours, glyph, instance, layout, transform
from repertoire import MINNAN_MARKS, MINNAN_TONES, repertoire
from compatibility import PAATU, add_paatu
from honkoku import HONKOKU, add_honkoku
from minnan import import_forms, layout as minnan_layout
from sans_forms import REFITS, refit
from sans_sources import CACHE, CJK, DONOR, GENSEKI, LIGHT, NOTO, prepare

OUT = ROOT / 'build/sans'
FAMILY = 'GenZui Sans'
FAMILY_JA = '源萃ゴシック'
STEM = 'GenZuiSans-Regular'
VERSION = '0.100'
# Simple archaic kana keep the Regular master beside ordinary katakana; the
# cursive hentaigana use the lighter DemiLight instance (see sans_sources).
REGULAR_WEIGHT = {0x1B000, 0x1B120, 0x1B121, 0x1B122}


def import_glyph(font, source, name, prefix):
    target = prefix + '.' + name
    if target in font['glyf']:
        return target
    outline = copy.deepcopy(source['glyf'][name])
    if outline.isComposite():
        for component in outline.components:
            component.glyphName = import_glyph(font, source, component.glyphName, prefix)
    add(font, target, outline)
    font['hmtx'][target] = source['hmtx'][name]
    # All donor outlines use the same 1000-unit em as Noto Sans JP.
    font['vmtx'][target] = (1000, 880 - outline.yMax)
    return target


def update_cmap(font, additions):
    for table in font['cmap'].tables:
        if table.isUnicode() and table.format in (4, 12):
            table.cmap.update({cp: name for cp, name in additions.items()
                               if cp <= (0xFFFF if table.format == 4 else 0x10FFFF)})


def source_notices(fonts):
    notices = []
    for font in fonts:
        notices.extend(r.toUnicode() for r in font['name'].names if r.nameID == 0)
    for path in (ROOT/'sources/upstream/NotoSansJP/OFL.txt', NOTO/'OFL.txt',
                 GENSEKI/'OFL.txt', ROOT/'sources/upstream/FRBTaiwaneseKana/LICENSE.txt'):
        notices.append(path.read_text().split('\n\n')[0])
    return '\n'.join(dict.fromkeys(notices))


def build():
    prepare()
    OUT.mkdir(parents=True, exist_ok=True)
    print('Instantiating Noto Sans JP Regular', flush=True)
    font = instance('NotoSansJP', 400)
    donor = TTFont(DONOR, recalcTimestamp=False)
    light = TTFont(LIGHT, recalcTimestamp=False)
    genseki = TTFont(GENSEKI/'GenSekiHentaiganaGothic.ttf', recalcTimestamp=False)
    assert font['head'].unitsPerEm == donor['head'].unitsPerEm == 1000
    assert light['head'].unitsPerEm == genseki['head'].unitsPerEm == 1000
    original = set(font.getBestCmap())
    targets = {ord(item['character']) for item in repertoire()}
    historical = targets - original - {PAATU} - set(HONKOKU) - set(MINNAN_TONES) - set(MINNAN_MARKS)
    provenance = {f'U+{cp:04X}': 'Noto Sans JP Regular' for cp in sorted(original)}
    additions, vertical = {}, {}
    donor_cmap, genseki_cmap = donor.getBestCmap(), genseki.getBestCmap()
    genseki_vertical = {}
    for feature in genseki['GSUB'].table.FeatureList.FeatureRecord:
        if feature.FeatureTag == 'vert':
            for index in feature.Feature.LookupListIndex:
                for sub in genseki['GSUB'].table.LookupList.Lookup[index].SubTable:
                    genseki_vertical.update(getattr(sub, 'mapping', {}))
    for cp in sorted(historical):
        if cp in donor_cmap:
            name = donor_cmap[cp]
            if cp in REGULAR_WEIGHT:
                source, prefix, description = donor, 'notoSansHist', 'Noto Sans Hentaigana Regular instance'
            else:
                source, prefix, description = light, 'notoSansHistLight', 'Noto Sans Hentaigana DemiLight instance'
            if cp in (0x1B000, 0x1B001):
                description += '; Unicode mapping restored for the upstream unencoded drawing'
        else:
            source, name, prefix = genseki, genseki_cmap[cp], 'genseki'
            description = 'GenSeki Hentaigana Gothic 1.201 Regular'
        target = import_glyph(font, source, name, prefix)
        if cp in REFITS:
            spec = REFITS[cp]
            g = source['glyf'][name]
            outline = glyph([refit(source.getGlyphSet(), name, (g.xMin, g.yMin, g.xMax, g.yMax), spec)])
            outline.recalcBounds(font['glyf'])
            font['glyf'][target] = outline
            font['hmtx'][target] = (1000, outline.xMin)
            font['vmtx'][target] = (1000, 880 - outline.yMax)
            description += '; GenZui refit: ' + spec['reason']
        additions[cp] = target
        provenance[f'U+{cp:04X}'] = description
        if source is genseki and name in genseki_vertical:
            vertical[target] = import_glyph(font, source, genseki_vertical[name], prefix)
    additions.update(import_forms(font, add))
    provenance.update({f'U+{cp:04X}': 'FRB Taiwanese Kana; GenZui mark and tone positioning'
                       for cp in (*MINNAN_TONES, *MINNAN_MARKS)})
    update_cmap(font, additions)

    layout(font, donor, vertical, historical, mark_anchor_x=815)
    minnan_layout(font, add, add_feature)
    add_paatu(font, add, glyph, add_feature)
    provenance[f'U+{PAATU:04X}'] = 'Noto Sans JP squared-katakana components'
    add_honkoku(font, add, glyph, contours, transform, source=CJK,
                tally_order=(0, 3, 1, 4, 2))
    provenance.update({f'U+{cp:04X}': ('Noto Sans CJK JP Regular' if cp == 0x5344 else
                       'Noto Sans JP components and GenZui transcription-symbol drawing')
                       for cp in HONKOKU})

    with TTFont(CJK) as cjk:
        notices = source_notices((font, donor, genseki, cjk))
    for nid in (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 18, 21, 22, 25):
        font['name'].removeNames(nameID=nid)
    for nid, value in {
        0: notices, 1: FAMILY, 2: 'Regular', 3: VERSION+';'+STEM,
        4: FAMILY+' Regular', 5: 'Version '+VERSION, 6: STEM, 16: FAMILY, 17: 'Regular',
        10: 'Japanese sans-serif with hentaigana, historical kana and Minnan tone letters.',
        13: 'Licensed under the SIL Open Font License, Version 1.1. See OFL.txt.',
        14: 'https://openfontlicense.org',
    }.items():
        font['name'].setName(value, nid, 3, 1, 0x409)
    for nid, value in {1: FAMILY_JA, 2: 'Regular', 4: FAMILY_JA+' Regular',
                       16: FAMILY_JA, 17: 'Regular'}.items():
        font['name'].setName(value, nid, 3, 1, 0x411)
    font['head'].fontRevision = float(VERSION)
    font['head'].macStyle = 0
    font['OS/2'].achVendID = 'NONE'
    font['OS/2'].usWeightClass = 400
    font['OS/2'].fsSelection = (font['OS/2'].fsSelection & ~33) | 64
    font['OS/2'].recalcUnicodeRanges(font)
    for tag in ('STAT', 'DSIG'):
        if tag in font:
            del font[tag]
    print('Writing TTF and WOFF2', flush=True)
    font.save(OUT/(STEM+'.ttf'))
    font.flavor = 'woff2'
    font.save(OUT/(STEM+'.woff2'))

    licence = (ROOT/'sources/upstream/NotoSansJP/OFL.txt').read_text().split('\n\n', 1)[1]
    (OUT/'OFL.txt').write_text(notices+'\n\n'+licence)
    for source, name in ((NOTO/'OFL.txt', 'NotoSansHentaigana-OFL.txt'),
                         (GENSEKI/'OFL.txt', 'GenSeki-OFL.txt'),
                         (GENSEKI/'README.md', 'GenSeki-README.md'),
                         (CACHE/'NotoSansCJK-OFL.txt', 'NotoSansCJK-OFL.txt'),
                         (ROOT/'sources/upstream/FRBTaiwaneseKana/LICENSE.txt', 'FRB-OFL.txt'),
                         (ROOT/'sources/upstream/FRBTaiwaneseKana/README.md', 'FRB-README.md'),
                         (ROOT/'sources/Unicode-LICENSE.txt', 'Unicode-LICENSE.txt'),
                         (ROOT/'sources/manifest.json', 'source-manifest.json'),
                         (ROOT/'sources/sans-manifest.json', 'sans-source-manifest.json')):
        shutil.copyfile(source, OUT/name)
    (OUT/'sources.json').write_text(json.dumps({
        'family': FAMILY, 'version': VERSION, 'encoded_characters': len(font.getBestCmap()),
        'refits': {f'U+{cp:04X}': spec for cp, spec in REFITS.items()},
        'source_kinds': provenance,
    }, ensure_ascii=False, indent=2)+'\n')
    (OUT/'NOTICE.txt').write_text(
        'GenZui Sans / 源萃ゴシック\n\n'
        'Noto Sans JP Regular: Japanese base, kana components and transcription symbols.\n'
        'https://github.com/google/fonts/tree/main/ofl/notosansjp\n'
        'Noto Sans Hentaigana: 286 hentaigana from the DemiLight instance, the weight\n'
        'upstream pairs with weight class 400; four archaic kana from the Regular instance.\n'
        'The upstream unencoded E and YE drawings receive U+1B000 and U+1B001.\n'
        'https://github.com/notofonts/hentaigana\n'
        'GenSeki Hentaigana Gothic 1.201: 21 historical kana, small kana and ligatures.\n'
        'GenZui refits KOTO, alternate NE and small archaic YE to their kana peers.\n'
        'Its source projects include GenSeki Gothic, Sukima Gothic and Shokaki Hentaigana Gothic.\n'
        'https://github.com/MihailJP/GenSekiHentaiganaGothic\n'
        'Noto Sans CJK JP Regular: U+5344 (卄), converted to TrueType curves.\n'
        'https://github.com/notofonts/noto-cjk\n'
        'FRB Taiwanese Kana by Fredrick R. Brennan: Minnan tone letters and combining marks.\n'
        'https://github.com/ctrlcctrlv/FRBTaiwaneseKana\n'
        'GenZui: transcription symbols, SQUARE PAATU and layout.\n\n'
        'Fonts and derived outlines are licensed under SIL OFL 1.1.\n'
        'Original copyright notices are retained in OFL.txt and the font metadata.\n')
    print(f'Built {FAMILY} {VERSION}: {len(font.getBestCmap()):,} encoded characters.', flush=True)
    from sans_specimen import build_specimen
    build_specimen()


if __name__ == '__main__':
    build()
