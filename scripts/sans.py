"""Build GenZui Sans Regular and Bold from pinned, drawn sans sources."""
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
from sans_forms import BOLD_TONE_BLEND, REFITS, SANS_BOLD_SYMBOLS, refit
from sans_sources import (BOLD_ARCHAIC, BOLD_ARCHAIC_AXIS, BOLD_TEXT, BOLD_TEXT_AXIS, CACHE, CJK, CJK_BOLD,
                          DONOR, GENSEKI, NOTO, TEXT, TEXT_AXIS, prepare)

OUT = ROOT / 'build/sans'
FAMILY = 'GenZui Sans'
FAMILY_JA = '源萃ゴシック'
STEM = 'GenZuiSans-Regular'
BOLD_STEM = 'GenZuiSans-Bold'
VERSION = '0.102'
PACKAGE = f'GenZuiSans-{VERSION}.zip'
# Simple archaic kana keep the Regular master beside ordinary katakana; the
# cursive hentaigana use the stem-matched axis-380 instance (see sans_sources).
# Bold takes both sets from instances matched to Noto Sans JP Bold.
REGULAR_WEIGHT = {0x1B000, 0x1B120, 0x1B121, 0x1B122}


def sources(weight):
    """The donor fonts and their descriptions for one face."""
    if weight == 400:
        return {'style': 'Regular', 'stem': STEM, 'archaic': DONOR, 'text': TEXT, 'cjk': CJK,
                'genseki': GENSEKI/'GenSekiHentaiganaGothic.ttf',
                'archaic_description': 'Noto Sans Hentaigana Regular instance',
                'text_description': f'Noto Sans Hentaigana instance at weight axis {TEXT_AXIS}',
                'genseki_description': 'GenSeki Hentaigana Gothic 1.201 Regular'}
    return {'style': 'Bold', 'stem': BOLD_STEM, 'archaic': BOLD_ARCHAIC, 'text': BOLD_TEXT, 'cjk': CJK_BOLD,
            'genseki': GENSEKI/'GenSekiHentaiganaGothic-Bold.ttf',
            'archaic_description': f'Noto Sans Hentaigana instance at weight axis {BOLD_ARCHAIC_AXIS}',
            'text_description': f'Noto Sans Hentaigana instance at weight axis {BOLD_TEXT_AXIS}',
            'genseki_description': 'GenSeki Hentaigana Gothic 1.201 Bold'}


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


def build(weight=400):
    """Build one static face. 400 is Regular. 700 is Bold, the named Noto instance."""
    prepare()
    OUT.mkdir(parents=True, exist_ok=True)
    face = sources(weight)
    style, stem, bold = face['style'], face['stem'], weight == 700
    tones = BOLD_TONE_BLEND if bold else False
    print(f'Instantiating Noto Sans JP {style}', flush=True)
    font = instance('NotoSansJP', weight)
    donor = TTFont(face['archaic'], recalcTimestamp=False)
    text_instance = TTFont(face['text'], recalcTimestamp=False)
    genseki = TTFont(face['genseki'], recalcTimestamp=False)
    assert font['head'].unitsPerEm == donor['head'].unitsPerEm == 1000
    assert text_instance['head'].unitsPerEm == genseki['head'].unitsPerEm == 1000
    original = set(font.getBestCmap())
    targets = {ord(item['character']) for item in repertoire()}
    historical = targets - original - {PAATU} - set(HONKOKU) - set(MINNAN_TONES) - set(MINNAN_MARKS)
    provenance = {f'U+{cp:04X}': f'Noto Sans JP {style}' for cp in sorted(original)}
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
                source, prefix, description = donor, 'notoSansHist', face['archaic_description']
            else:
                source, prefix, description = text_instance, 'notoSansHistText', face['text_description']
            if cp in (0x1B000, 0x1B001):
                description += '; Unicode mapping restored for the upstream unencoded drawing'
        else:
            source, name, prefix = genseki, genseki_cmap[cp], 'genseki'
            description = face['genseki_description']
        target = import_glyph(font, source, name, prefix)
        if cp in REFITS[weight]:
            spec = REFITS[weight][cp]
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
    additions.update(import_forms(font, add, tones))
    provenance.update({f'U+{cp:04X}': (f'FRB Taiwanese Kana outline blended {BOLD_TONE_BLEND} toward its GenZui Bold master' if bold else
                                       'FRB Taiwanese Kana') + '; GenZui mark and tone positioning'
                       for cp in (*MINNAN_TONES, *MINNAN_MARKS)})
    update_cmap(font, additions)

    # Bold's handakuten is 31 units wider and reaches 16 units lower; its marks
    # keep Regular's right edge and clearance above the base.
    layout(font, donor, vertical, historical, **({'mark_anchor_x': 784, 'mark_drop': 610} if bold else
                                                 {'mark_anchor_x': 815}))
    minnan_layout(font, add, add_feature, tones, edge_anchors=True)
    add_paatu(font, add, glyph, add_feature)
    provenance[f'U+{PAATU:04X}'] = 'Noto Sans JP squared-katakana components'
    add_honkoku(font, add, glyph, contours, transform, source=face['cjk'],
                tally_order=(0, 3, 1, 4, 2), symbols=SANS_BOLD_SYMBOLS if bold else None)
    provenance.update({f'U+{cp:04X}': (f'Noto Sans CJK JP {style}' if cp == 0x5344 else
                       'Noto Sans JP components and GenZui transcription-symbol drawing')
                       for cp in HONKOKU})

    # Both faces carry the notices of every source of the family.
    notices = source_notices([font] + [TTFont(sources(w)[key], recalcTimestamp=False)
                                       for w in (400, 700) for key in ('archaic', 'genseki', 'cjk')])
    for nid in (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 18, 21, 22, 25):
        font['name'].removeNames(nameID=nid)
    for nid, value in {
        0: notices, 1: FAMILY, 2: style, 3: VERSION+';'+stem,
        4: FAMILY+' '+style, 5: 'Version '+VERSION, 6: stem, 16: FAMILY, 17: style,
        10: 'Japanese sans-serif with hentaigana, historical kana and Minnan tone letters.',
        13: 'Licensed under the SIL Open Font License, Version 1.1. See OFL.txt.',
        14: 'https://openfontlicense.org',
    }.items():
        font['name'].setName(value, nid, 3, 1, 0x409)
    for nid, value in {1: FAMILY_JA, 2: style, 4: FAMILY_JA+' '+style,
                       16: FAMILY_JA, 17: style}.items():
        font['name'].setName(value, nid, 3, 1, 0x411)
    font['head'].fontRevision = float(VERSION)
    font['OS/2'].achVendID = 'NONE'
    font['OS/2'].usWeightClass = weight
    if bold:
        font['OS/2'].fsSelection = (font['OS/2'].fsSelection & ~65) | 32
        font['head'].macStyle = 1
        font['OS/2'].panose.bWeight = 8  # PANOSE Bold.
    else:
        font['OS/2'].fsSelection = (font['OS/2'].fsSelection & ~33) | 64
        font['head'].macStyle = 0
    font['OS/2'].recalcUnicodeRanges(font)
    for tag in ('STAT', 'DSIG'):
        if tag in font:
            del font[tag]
    print('Writing TTF and WOFF2', flush=True)
    font.save(OUT/(stem+'.ttf'))
    font.flavor = 'woff2'
    font.save(OUT/(stem+'.woff2'))

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
    (OUT/('sources-bold.json' if bold else 'sources.json')).write_text(json.dumps({
        'family': FAMILY, 'style': style, 'version': VERSION, 'encoded_characters': len(font.getBestCmap()),
        'refits': {f'U+{cp:04X}': spec for cp, spec in REFITS[weight].items()},
        'source_kinds': provenance,
    }, ensure_ascii=False, indent=2)+'\n')
    (OUT/'NOTICE.txt').write_text(
        'GenZui Sans / 源萃ゴシック\n\n'
        'Noto Sans JP Regular and Bold: Japanese base, kana components and transcription symbols.\n'
        'https://github.com/google/fonts/tree/main/ofl/notosansjp\n'
        'Noto Sans Hentaigana: 286 hentaigana from instances at weight axis 380 (Regular)\n'
        'and 720 (Bold), whose stems match Noto Sans JP; four archaic kana from the\n'
        'Regular instance and an instance at axis 780 (Bold).\n'
        'The upstream unencoded E and YE drawings receive U+1B000 and U+1B001.\n'
        'https://github.com/notofonts/hentaigana\n'
        'GenSeki Hentaigana Gothic 1.201 Regular and Bold: 21 historical kana, small kana and ligatures.\n'
        'GenZui refits KOTO, alternate NE and small archaic YE to their kana peers.\n'
        'Its source projects include GenSeki Gothic, Sukima Gothic and Shokaki Hentaigana Gothic.\n'
        'https://github.com/MihailJP/GenSekiHentaiganaGothic\n'
        'Noto Sans CJK JP Regular and Bold: U+5344 (卄), converted to TrueType curves.\n'
        'https://github.com/notofonts/noto-cjk\n'
        'FRB Taiwanese Kana by Fredrick R. Brennan: Minnan tone letters and combining marks.\n'
        'Bold blends them toward GenZui Bold masters drawn on the same points.\n'
        'https://github.com/ctrlcctrlv/FRBTaiwaneseKana\n'
        'GenZui: transcription symbols, SQUARE PAATU and layout.\n\n'
        'Fonts and derived outlines are licensed under SIL OFL 1.1.\n'
        'Original copyright notices are retained in OFL.txt and the font metadata.\n')
    print(f'Built {FAMILY} {style} {VERSION}: {len(font.getBestCmap()):,} encoded characters.', flush=True)
    if not bold:
        from sans_specimen import build_specimen
        build_specimen()


if __name__ == '__main__':
    build()
