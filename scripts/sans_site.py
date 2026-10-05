"""Build the GenZui Sans page from the checked Sans font and package."""
import base64
import hashlib
import html
import json
from collections import Counter
from zipfile import ZipFile

from fontTools.ttLib import TTFont

from family_switch import css as switch_css, html as switch_html
from weight_switch import css as weight_css
from inventory import KANA_GROUPS, character_data
from gugyeol import FORMS as GUGYEOL_FORMS, PUA as GUGYEOL_PUA
from serif import OUT as SERIF_OUT, STEM as SERIF_STEM, VERSION as SERIF_VERSION
from sources import ROOT

OUT = ROOT/'build/sans'
STEM = 'GenZuiSans-Regular'
BOLD_STEM = 'GenZuiSans-Bold'
PAIRING_TEXT = '春はあけぼの。𛀂𛀆𛀋 𛄣𛄤𛄥 かなのかたちを読む。'
# Files published beside the Serif downloads. Licence and credit files carry the
# family name because the Serif set already occupies the plain names.
# Short source keys for the inventory, from the build's provenance strings.
SOURCE_KEYS = {'Noto Sans JP Regular': 'jp', 'Noto Sans Hentaigana': 'hentaigana',
               'GenSeki Hentaigana Gothic': 'genseki', 'FRB Taiwanese Kana': 'frb',
               'Noto Sans CJK JP Regular': 'cjk', '구결자': 'gugyeol'}
# Reader-facing notes for the characters GenZui reworked in this family.
DESCRIPTIONS = {
    0x1B123: 'GenSeki’s KOTO, enlarged to the body height of TOKI, TOTE and TOMO and thinned back to their stroke width.',
    0x1B127: 'GenSeki’s alternate NE, enlarged to the katakana cap height and thinned back to their stroke width.',
    0x1B168: 'GenSeki’s small archaic YE, lowered onto the small-kana baseline.',
    0x1B128: 'Noto Sans JP’s WI bars and right stem with NA’s falling stroke as the left descent, built like GenZui Serif’s alternate WI.',
}
# Upstream of each GenSeki outline, from the table and notes in GenSeki Hentaigana
# Gothic 1.201's README (A Shokaki, B Sukima, C its own additions).
SUKIMA_CHAIN = 'Sukima Gothic (きなさ), from Genshin Gothic, from Source Han Sans 1.002 and M+ OUTLINE FONTS'
GENSEKI_OWN = 'GenSeki Hentaigana Gothic’s own addition, made from GenSeki Gothic, from Source Han Sans'
GENSEKI_UNSTATED = 'GenSeki Hentaigana Gothic 1.201; its README does not state an origin'
GENSEKI_ORIGINS = {
    **{cp: SUKIMA_CHAIN for cp in (0x1B123, 0x1B124, 0x1B125, 0x1B126, 0x2A708, 0x2CEFF, 0x2CF00, 0x2CF02)},
    **{cp: GENSEKI_OWN for cp in (0x1B11F, 0x1B127)},
    **{cp: GENSEKI_UNSTATED for cp in (0x1B132, 0x1B150, 0x1B151, 0x1B152, 0x1B155,
                                       0x1B164, 0x1B165, 0x1B166, 0x1B167, 0x1B168)},
}
assert len(GENSEKI_ORIGINS) == 20
ORIGINS = {'jp': 'Noto Sans JP', 'hentaigana': 'Noto Sans Hentaigana', 'genseki': 'GenSeki Hentaigana Gothic',
           'frb': 'FRB Taiwanese Kana', 'genzui': 'GenZui drawing', 'cjk': 'Noto Sans CJK JP',
           'gugyeol': 'Twin ideograph (구결자)'}
DOWNLOADS = {STEM+'.ttf': STEM+'.ttf', STEM+'.woff2': STEM+'.woff2',
             BOLD_STEM+'.ttf': BOLD_STEM+'.ttf', BOLD_STEM+'.woff2': BOLD_STEM+'.woff2',
             'OFL.txt': 'GenZuiSans-OFL.txt', 'NOTICE.txt': 'GenZuiSans-NOTICE.txt',
             'checks.json': 'GenZuiSans-checks.json', 'kana-coverage.json': 'GenZuiSans-kana-coverage.json'}


def checked():
    """Return the Sans version, checks and package after verifying they agree."""
    checks = json.loads((OUT/'checks.json').read_text())
    bold = json.loads((OUT/'checks-bold.json').read_text())
    browsers = json.loads((OUT/'browser-checks.json').read_text())
    assert checks['status'] == bold['status'] == browsers['status'] == 'passed'
    assert checks['family'] == bold['family'] == browsers['family'] == 'GenZui Sans'
    assert checks['version'] == bold['version']
    version = checks['version']
    package = ROOT/'dist'/f'GenZuiSans-{version}.zip'
    assert package.is_file(), 'Package the checked Sans font first: scripts/package_sans.py'
    with ZipFile(package) as archive:
        for stem, record, prefix in ((STEM, checks, ''), (BOLD_STEM, bold, 'bold_')):
            for ext in ('ttf', 'woff2'):
                digest = hashlib.sha256((OUT/f'{stem}.{ext}').read_bytes()).hexdigest()
                assert digest == record[ext+'_sha256'] == browsers[prefix+ext+'_sha256'], f'Stale Sans validation: {stem}.{ext}'
                assert hashlib.sha256(archive.read(f'{stem}.{ext}')).hexdigest() == digest, 'Rebuild the Sans package: its font bytes are stale.'
    return version, checks, package


def source_key(description):
    for prefix, key in SOURCE_KEYS.items():
        if description.startswith(prefix):
            return key
    return 'genzui'


def inventory(font, provenance):
    """Every encoded character with its Unicode name, block, source and group."""
    audit = json.loads((ROOT/'research/repertoire.json').read_text())
    kinds = {key: source_key(value) for key, value in provenance.items()}
    # A 구결자 carries the build's own note on which glyph it was drawn from.
    notes = {key: value for key, value in provenance.items() if kinds[key] == 'gugyeol'}
    upstream = {cp: f'Upstream: {text}.' for cp, text in GENSEKI_ORIGINS.items()}
    described = {cp: ' '.join(filter(None, (DESCRIPTIONS.get(cp), upstream.get(cp)))) for cp in {*DESCRIPTIONS, *upstream}}
    entries = character_data(font, audit, kinds, {**notes, **{f'U+{cp:04X}': text for cp, text in described.items()}})
    for entry in entries:
        # Refitted GenSeki outlines are GenZui work; the inventory marks them provisional.
        entry['provisional'] = entry['source'] == 'genzui' or entry['cp'] in DESCRIPTIONS
    return entries


def gugyeol_coverage(font, provenance):
    """Coverage of the checked parent, agreeing with its source record."""
    cmap=set(font.getBestCmap())
    assert {int(k.removeprefix('U+'),16) for k in provenance}==cmap
    registered={int(f['codepoint'],16) for f in GUGYEOL_FORMS}
    actual=cmap & registered
    tagged={int(k.removeprefix('U+'),16) for k,v in provenance.items() if source_key(v)=='gugyeol'}
    assert actual==tagged and actual<=set(GUGYEOL_PUA)
    return actual


def build_page(sans_font, serif_font, webfont_usage='', sans_bold_font=None):
    """Render the page; font arguments are the URLs the page loads."""
    version, checks, package = checked()
    provenance = json.loads((OUT/'sources.json').read_text())['source_kinds']
    kinds = Counter(value.split(';')[0] for value in provenance.values())
    genzui = sum(count for kind, count in kinds.items() if 'GenZui' in kind or 'squared-katakana' in kind)
    assert kinds['Noto Sans Hentaigana instance at weight axis 380'] == 286 and kinds['GenSeki Hentaigana Gothic 1.201 Regular'] == 20
    parent=TTFont(OUT/(STEM+'.ttf'))
    available=gugyeol_coverage(parent,provenance)
    bold_provenance=json.loads((OUT/'sources-bold.json').read_text())['source_kinds']
    assert available==gugyeol_coverage(TTFont(OUT/(BOLD_STEM+'.ttf')),bold_provenance)
    entries = inventory(parent, provenance)
    assert available=={e['cp'] for e in entries if e['source']=='gugyeol'}
    counts = dict(Counter(e['source'] for e in entries))
    expected={'jp':16732,'hentaigana':290,'genseki':20,'frb':15,'cjk':1,'genzui':genzui}
    if available:expected['gugyeol']=len(available)
    assert counts==expected,counts
    assert len(entries) == checks['encoded_characters']
    data = {'version': version, 'family': 'GenZui Sans', 'origins': ORIGINS, 'characters': entries,
            'counts': counts, 'total': len(entries),
            'historical': sum(e['group'] in KANA_GROUPS for e in entries)}
    hentaigana = ''.join(chr(cp) for cp in range(0x1B001, 0x1B11F)) + ' 𛀀𛄠𛄡𛄢 𛄣𛄤𛄥𛄦𛄧𛄨𛅨'
    page = (ROOT/'templates/sans.html').read_text()
    replacement = {
        '{{GUGYEOL_FILTER}}': '<option value="gugyeol">구결자 twin ideographs</option>' if available else '',
        '{{SANS_FONT}}': sans_font, '{{SERIF_FONT}}': serif_font,
        '{{SANS_BOLD_FONT}}': sans_bold_font or data_uri(OUT/(BOLD_STEM+'.woff2')),
        '{{WEIGHT_SWITCH_CSS}}': weight_css(OUT/(STEM+'.woff2'), OUT/(BOLD_STEM+'.woff2')),
        '{{CSS}}': (ROOT/'site/style.css').read_text(),
        '{{FAMILY_SWITCH_CSS}}': switch_css(),
        '{{FAMILY_SWITCH}}': switch_html('sans'),
        '{{VERSION}}': html.escape(version), '{{SERIF_VERSION}}': html.escape(SERIF_VERSION),
        '{{CHARACTER_COUNT}}': f"{checks['encoded_characters']:,}",
        '{{JP_COUNT}}': f"{kinds['Noto Sans JP Regular']:,}", '{{GENZUI_COUNT}}': str(genzui),
        '{{GENSEKI_COUNT}}': str(kinds['GenSeki Hentaigana Gothic 1.201 Regular']),
        '{{HENTAIGANA}}': hentaigana, '{{PAIRING_TEXT}}': PAIRING_TEXT,
        '{{EXTENDED_KANA_COUNT}}': str(data['historical']),
        '{{NUMERAL_COUNT}}': str(sum(e['group'] == 'han-numeral' for e in entries)),
        '{{DATA}}': json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c'),
        '{{JS}}': (ROOT/'site/main.js').read_text(),
        '{{FONT_SIZE}}': f'{(OUT/(STEM+".ttf")).stat().st_size/1048576:.1f}',
        '{{BOLD_FONT_SIZE}}': f'{(OUT/(BOLD_STEM+".ttf")).stat().st_size/1048576:.1f}',
        '{{ZIP_SIZE}}': f'{package.stat().st_size/1048576:.1f}',
        '{{WEBFONT_SIZE}}': f'{(OUT/(STEM+".woff2")).stat().st_size/1048576:.1f}',
        '{{WEBFONT_USAGE}}': webfont_usage,
    }
    for token, value in replacement.items():
        page = page.replace(token, value)
    assert all(token not in page for token in replacement)
    assert '/home/' not in page
    return page


def data_uri(path):
    return 'data:font/woff2;base64,' + base64.b64encode(path.read_bytes()).decode()


def build_offline():
    """The development specimen embeds both families."""
    return build_page(data_uri(OUT/(STEM+'.woff2')), data_uri(SERIF_OUT/(SERIF_STEM+'.woff2')))


if __name__ == '__main__':
    version, checks, package = checked()
    print(f'GenZui Sans {version}: {checks["encoded_characters"]:,} characters; package {package.name}.')
