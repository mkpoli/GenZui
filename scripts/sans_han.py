"""Build GenZui Sans Han: every CJK ideograph that GenZui Sans lacks, in two files.

Each code point takes the first source that maps it, in this order:
Noto Sans CJK JP (the design GenZui Sans is built on), Sukima Gothic Main and
Sub (Japanese forms on the same Source Han Sans base), then Plangothic P1 and
P2 (Source Han Sans CN forms, mostly for the remaining extension ideographs).
GenZui Sans Han holds the BMP and plane 3; GenZui Sans Han SIP holds plane 2,
so each file stays under the 65,535-glyph limit.
"""
import copy
import hashlib
import json
import re
import shutil
from zipfile import ZipFile

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.reverseContourPen import ReverseContourPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont

from sources import ROOT, verify
from sans_sources import CACHE as SANS_CACHE, CJK, digest

SANS = ROOT / 'build/sans'
SANS_STEM = 'GenZuiSans-Regular'  # The built face the supplement complements.
CACHE = SANS_CACHE / 'han'
OUT = ROOT / 'build/sans-han'
MANIFEST = ROOT / 'sources/han-manifest.json'
VERSION = '0.100'
SUKIMA_DIR = 'sukima-gothic ver11.41/'
SUKIMA_MEMBERS = {
    'SukimaGothic-Regular ver11.41.ttf': 'SukimaGothic-Regular.ttf',
    'SukimaGothicSub-Regular ver11.41.ttf': 'SukimaGothicSub-Regular.ttf',
    'readme.txt': 'Sukima-readme.txt',
    'ライセンス/SIL_Open_Font_License_1.1.txt': 'Sukima-OFL.txt',
    'ライセンス/mplus-TESTFLIGHT-059/LICENSE_E': 'MPLUS-LICENSE_E.txt',
    'ライセンス/mplus-TESTFLIGHT-059/LICENSE_J': 'MPLUS-LICENSE_J.txt',
}
# Source key, file, description; earlier sources win.
SOURCES = (
    ('noto', CJK, 'Noto Sans CJK JP Regular'),
    ('sukima', CACHE/'SukimaGothic-Regular.ttf', 'Sukima Gothic 11.41 Main'),
    ('sukimasub', CACHE/'SukimaGothicSub-Regular.ttf', 'Sukima Gothic 11.41 Sub'),
    ('plangothic1', CACHE/'PlangothicP1-Regular.ttf', 'Plangothic P1 2.9.5795'),
    ('plangothic2', CACHE/'PlangothicP2-Regular.ttf', 'Plangothic P2 2.9.5795'),
)
FACES = (
    {'stem': 'GenZuiSansHan-Regular', 'family': 'GenZui Sans Han', 'family_ja': '源萃ゴシック漢字',
     'planes': {0, 3}, 'description': 'CJK ideographs of the BMP and plane 3 missing from GenZui Sans.'},
    {'stem': 'GenZuiSansHanSIP-Regular', 'family': 'GenZui Sans Han SIP', 'family_ja': '源萃ゴシック漢字SIP',
     'planes': {2}, 'description': 'CJK ideographs of plane 2 (Extensions B to F, I and compatibility supplement) missing from GenZui Sans.'},
)
# Blocks whose assigned characters make up the target repertoire.
BLOCKS = re.compile(r'^(CJK Unified Ideographs.*|CJK Compatibility Ideographs.*|Kangxi Radicals|'
                    r'CJK Radicals Supplement|CJK Strokes|Ideographic Description Characters)$')
ORIGIN = 880  # Vertical origin of the Source Han Sans em box on a 1000-unit em.
EM = 1000  # Every target character is full width.


def prepare():
    """Verify the pinned sources and extract the Sukima Gothic files."""
    verify(fetch=True)
    CACHE.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(MANIFEST.read_text())
    for item in manifest['files']:
        path = CACHE / item['filename']
        if not path.exists():
            if 'manual' in item:
                raise SystemExit(item['manual'])
            from urllib.request import urlopen
            print('Fetching ' + item['filename'], flush=True)
            with urlopen(item['url'], timeout=300) as response:
                path.write_bytes(response.read())
        if digest(path) != item['sha256']:
            raise ValueError('Source checksum mismatch: ' + item['filename'])
    with ZipFile(CACHE/'sukima-gothic_ver11.41.zip') as archive:
        for member, name in SUKIMA_MEMBERS.items():
            (CACHE/name).write_bytes(archive.read(SUKIMA_DIR + member))
    if not (CJK.exists() and (SANS_CACHE/'NotoSansCJK-OFL.txt').exists()):
        raise SystemExit('Run scripts/sans.py first: it fetches Noto Sans CJK JP.')
    return manifest


def target():
    """Assigned characters of the CJK ideograph, radical, stroke and IDC blocks."""
    data = ROOT/'data/unicode'
    blocks = [(int(a, 16), int(b, 16)) for a, b, name in
              re.findall(r'^([0-9A-F]+)\.\.([0-9A-F]+); (.+)$', (data/'Blocks.txt').read_text(), re.M)
              if BLOCKS.match(name)]
    assigned, first = set(), None
    for line in (data/'UnicodeData.txt').read_text().splitlines():
        cp, name = line.split(';')[:2]
        cp = int(cp, 16)
        if name.endswith(', First>'):
            first = cp
        elif name.endswith(', Last>'):
            assigned.update(range(first, cp+1))
        else:
            assigned.add(cp)
    return {cp for cp in assigned if any(a <= cp <= b for a, b in blocks)}


def assign(base):
    """Map each missing target code point to the first source that has it."""
    missing = target() - base
    fonts, choice = {}, {}
    for key, path, _ in SOURCES:
        font = TTFont(path, lazy=True)
        fonts[key] = font
        cmap = font.getBestCmap()
        for cp in sorted(missing & set(cmap)):
            choice[cp] = (key, cmap[cp])
        missing -= set(cmap)
    if missing:
        raise ValueError(f'{len(missing)} target characters have no source, e.g. U+{min(missing):04X}')
    return fonts, choice


def outline(font, name):
    """A TrueType outline on a 1000-unit em; CFF curves are converted, hints dropped."""
    scale = 1000 / font['head'].unitsPerEm
    pen = TTGlyphPen(None)
    target_pen = Cu2QuPen(pen, max_err=0.3) if 'CFF ' in font else pen
    if scale != 1:
        target_pen = TransformPen(target_pen, (scale, 0, 0, scale, 0, 0))
    advance = round(font['hmtx'][name][0] * scale)
    if advance != EM:
        # A few Sukima Gothic ideographs carry stray widths (984-1010); set them
        # on the full-width grid with the ink kept centred.
        target_pen = TransformPen(target_pen, (1, 0, 0, 1, (EM - advance) / 2 / scale, 0))
    # TrueType contours run clockwise. CFF sources run counter-clockwise, and so
    # do Sukima Gothic's TrueType outlines; reverse any glyph drawn that way.
    area = AreaPen(font.getGlyphSet())
    font.getGlyphSet()[name].draw(area)
    if area.value > 0:
        target_pen = ReverseContourPen(target_pen)
    font.getGlyphSet()[name].draw(target_pen)
    return pen.glyph(), advance


def panose(base):
    """GenZui Sans's PANOSE with the monospaced proportion."""
    value = copy.copy(base)
    value.bProportion = 9
    return value


def runs(cps, labels):
    """Contiguous code point runs sharing one label."""
    out = []
    for cp in sorted(cps):
        if out and out[-1][1] == cp-1 and out[-1][2] == labels[cp]:
            out[-1][1] = cp
        else:
            out.append([cp, cp, labels[cp]])
    return [{'first': f'U+{a:04X}', 'last': f'U+{b:04X}', 'source': s} for a, b, s in out]


def unicode_range(cps):
    parts = []
    for item in runs(cps, {cp: '' for cp in cps}):
        a, b = item['first'], item['last']
        parts.append(a if a == b else f'{a}-{b[2:]}')
    return ', '.join(parts)


def notices(fonts):
    lines = []
    for key in ('noto', 'sukima', 'plangothic1'):
        lines.extend(r.toUnicode() for r in fonts[key]['name'].names if r.nameID == 0)
    lines.append('Sukima Gothic kanji drawn by きなさ: https://booth.pm/ja/items/2117070')
    lines.append('Plangothic Project, Reserved Font Names "Plangothic" and "遍黑": '
                 'https://github.com/Fitzgerald-Porthmouth-Koenigsegg/Plangothic_Project')
    return '\n'.join(dict.fromkeys(line.strip() for line in lines if line.strip()))


def build_face(face, choice, fonts, base_font, notice):
    cps = sorted(cp for cp in choice if cp >> 16 in face['planes'])
    pen = TTGlyphPen(None)
    base_font.getGlyphSet()['.notdef'].draw(pen)
    glyphs, metrics, vmetrics = {'.notdef': pen.glyph()}, {'.notdef': base_font['hmtx']['.notdef']}, {}
    cmap, names = {}, {}
    for cp in cps:
        key, source_name = choice[cp]
        if (key, source_name) not in names:
            name = f'uni{cp:04X}' if cp <= 0xFFFF else f'u{cp:05X}'
            glyph, advance = outline(fonts[key], source_name)
            glyph.recalcBounds(None)
            glyphs[name] = glyph
            metrics[name] = (EM, getattr(glyph, 'xMin', 0))
            if advance != EM:
                face.setdefault('recentred', {})[f'U+{cp:04X}'] = advance
            names[(key, source_name)] = name
        cmap[cp] = names[(key, source_name)]
    for name, glyph in glyphs.items():
        if glyph.numberOfContours:
            glyph.recalcBounds(None)
        vmetrics[name] = (1000, ORIGIN - glyph.yMax if glyph.numberOfContours else 0)

    fb = FontBuilder(1000, isTTF=True)
    fb.setupGlyphOrder(list(glyphs))
    fb.setupCharacterMap(cmap)
    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=base_font['hhea'].ascent, descent=base_font['hhea'].descent)
    fb.setupVerticalMetrics(vmetrics)
    fb.setupVerticalHeader(ascent=500, descent=-500)
    style = 'Regular'
    fb.setupNameTable({
        'copyright': notice, 'familyName': face['family'], 'styleName': style,
        'uniqueFontIdentifier': VERSION + ';' + face['stem'], 'fullName': face['family'] + ' ' + style,
        'version': 'Version ' + VERSION, 'psName': face['stem'],
        'description': face['description'] + ' Use after GenZui Sans in a font list.',
        'licenseDescription': 'Licensed under the SIL Open Font License, Version 1.1. See OFL.txt.',
        'licenseInfoURL': 'https://openfontlicense.org',
        'typographicFamily': face['family'], 'typographicSubfamily': style,
    }, windows=True, mac=False)
    for nid, value in {1: face['family_ja'], 2: style, 4: face['family_ja'] + ' ' + style,
                       16: face['family_ja'], 17: style}.items():
        fb.font['name'].setName(value, nid, 3, 1, 0x411)
    os2 = base_font['OS/2']
    fb.setupOS2(version=4, usWeightClass=400, achVendID='NONE', fsType=0, fsSelection=64,
                sTypoAscender=os2.sTypoAscender, sTypoDescender=os2.sTypoDescender,
                sTypoLineGap=os2.sTypoLineGap, usWinAscent=os2.usWinAscent, usWinDescent=os2.usWinDescent,
                sxHeight=os2.sxHeight, sCapHeight=os2.sCapHeight, panose=panose(os2.panose),
                # The JIS code page, as in GenZui Sans; the SIP file's plane-2
                # characters belong to no legacy code page.
                ulCodePageRange1=(1 << 17) if 0 in face['planes'] else 0, ulCodePageRange2=0)
    # Every glyph has the 1000-unit full width.
    fb.setupPost(keepGlyphNames=False, isFixedPitch=1)
    font = fb.font
    font['gasp'] = TTFont(SANS/(SANS_STEM+'.ttf'), lazy=True)['gasp']
    font['head'].fontRevision = float(VERSION)
    font['OS/2'].recalcUnicodeRanges(font)
    font['OS/2'].recalcAvgCharWidth(font)
    print(f"Writing {face['stem']}: {len(cmap):,} characters, {len(glyphs):,} glyphs", flush=True)
    font.save(OUT/(face['stem']+'.ttf'))
    font = TTFont(OUT/(face['stem']+'.ttf'))
    font.flavor = 'woff2'
    font.save(OUT/(face['stem']+'.woff2'))
    return cmap


def build():
    manifest = prepare()
    OUT.mkdir(parents=True, exist_ok=True)
    base_path = SANS/(SANS_STEM+'.ttf')
    if not base_path.exists():
        raise SystemExit('Build GenZui Sans Regular first: scripts/sans.py')
    base_font = TTFont(base_path, lazy=True)
    fonts, choice = assign(set(base_font.getBestCmap()))
    notice = notices(fonts)
    described = {key: text for key, _, text in SOURCES}
    record = {'family': 'GenZui Sans Han', 'version': VERSION,
              'base': {'file': base_path.name, 'sha256': digest(base_path)},
              'priority': [text for _, _, text in SOURCES], 'faces': {}}
    css = []
    for face in FACES:
        cmap = build_face(face, choice, fonts, base_font, notice)
        labels = {cp: described[choice[cp][0]] for cp in cmap}
        counts = {}
        for value in labels.values():
            counts[value] = counts.get(value, 0) + 1
        record['faces'][face['stem']] = {'family': face['family'], 'encoded_characters': len(cmap),
                                         'by_source': counts, 'recentred_source_widths': face.get('recentred', {}),
                                         'runs': runs(cmap, labels)}
        css.append('@font-face {\n'
                   '  font-family: "GenZui Sans Han";\n'
                   f"  src: url(\"{face['stem']}.woff2\") format(\"woff2\");\n"
                   '  font-display: swap;\n'
                   f'  unicode-range: {unicode_range(cmap)};\n'
                   '}\n')
    (OUT/'genzui-sans-han.css').write_text('\n'.join(css))
    (OUT/'sources.json').write_text(json.dumps(record, ensure_ascii=False, indent=1) + '\n')
    licence = (ROOT/'sources/upstream/NotoSansJP/OFL.txt').read_text().split('\n\n', 1)[1]
    (OUT/'OFL.txt').write_text(notice + '\n\n' + licence)
    for name in ('Sukima-readme.txt', 'Sukima-OFL.txt', 'MPLUS-LICENSE_E.txt', 'MPLUS-LICENSE_J.txt',
                 'Plangothic-OFL.txt'):
        shutil.copyfile(CACHE/name, OUT/name)
    shutil.copyfile(SANS_CACHE/'NotoSansCJK-OFL.txt', OUT/'NotoSansCJK-OFL.txt')
    shutil.copyfile(MANIFEST, OUT/'han-source-manifest.json')
    (OUT/'NOTICE.txt').write_text(
        'GenZui Sans Han / 源萃ゴシック漢字\n\n'
        'Every CJK ideograph, radical, stroke and ideographic description character\n'
        'in Unicode 18 that GenZui Sans lacks. Each character takes the first source\n'
        'below that has it; sources.json lists the source of every character.\n\n'
        'Noto Sans CJK JP Regular (Adobe and Google, Source Han Sans design).\n'
        'https://github.com/notofonts/noto-cjk\n'
        'Sukima Gothic 11.41 Main and Sub by きなさ, built on Genshin Gothic by\n'
        '自家製フォント工房, which joins Source Han Sans 1.002 and M+ OUTLINE FONTS;\n'
        'Sukima\'s readme gives Genshin-derived glyphs to 自家製フォント工房. Outlines scaled from a\n'
        '1024-unit to a 1000-unit em.\n'
        'https://booth.pm/ja/items/2117070\n'
        'Plangothic P1 and P2 2.9.5795 by the Plangothic Project, built on Source Han\n'
        'Sans CN with Chinese Mainland forms. Its README lists fonts it borrows from or\n'
        'refers to: Source Han Sans, other Noto fonts, Sukima Gothic, Chiron Hei HK,\n'
        'Zhudou Sans, Gothic Nguyen, Shokaki Hentaigana Gothic, Shanggu Sans and\n'
        'Chill Duan Sans.\n'
        'https://github.com/Fitzgerald-Porthmouth-Koenigsegg/Plangothic_Project\n\n'
        'Fonts and derived outlines are licensed under SIL OFL 1.1. Plangothic\n'
        'reserves the names "Plangothic" and "遍黑". M+ OUTLINE FONTS glyphs within\n'
        'Sukima Gothic follow the M+ FONTS LICENSE (MPLUS-LICENSE_E.txt).\n')
    total = sum(face['encoded_characters'] for face in record['faces'].values())
    print(f'Built GenZui Sans Han {VERSION}: {total:,} characters in {len(FACES)} files.', flush=True)
    return manifest


if __name__ == '__main__':
    build()
