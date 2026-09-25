"""Build the GenZui Sans page from the checked Sans font and package."""
import base64
import hashlib
import html
import json
from collections import Counter
from zipfile import ZipFile

from fontTools.ttLib import TTFont

from family_switch import css as switch_css, html as switch_html
from inventory import KANA_GROUPS, character_data
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
               'Noto Sans CJK JP Regular': 'cjk'}
# Reader-facing notes for the characters GenZui reworked in this family.
DESCRIPTIONS = {
    0x1B123: 'GenSeki’s KOTO, enlarged to the body height of TOKI, TOTE and TOMO and thinned back to their stroke width.',
    0x1B127: 'GenSeki’s alternate NE, enlarged to the katakana cap height and thinned back to their stroke width.',
    0x1B168: 'GenSeki’s small archaic YE, lowered onto the small-kana baseline.',
}
ORIGINS = {'jp': 'Noto Sans JP', 'hentaigana': 'Noto Sans Hentaigana', 'genseki': 'GenSeki Hentaigana Gothic',
           'frb': 'FRB Taiwanese Kana', 'genzui': 'GenZui drawing', 'cjk': 'Noto Sans CJK JP'}
DOWNLOADS = {STEM+'.ttf': STEM+'.ttf', STEM+'.woff2': STEM+'.woff2',
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
    entries = character_data(font, audit, kinds,
                             {f'U+{cp:04X}': text for cp, text in DESCRIPTIONS.items()})
    for entry in entries:
        # Refitted GenSeki outlines are GenZui work; the inventory marks them provisional.
        entry['provisional'] = entry['source'] == 'genzui' or entry['cp'] in DESCRIPTIONS
    return entries


def build_page(sans_font, serif_font, webfont_usage=''):
    """Render the page; font arguments are the URLs the page loads."""
    version, checks, package = checked()
    provenance = json.loads((OUT/'sources.json').read_text())['source_kinds']
    kinds = Counter(value.split(';')[0] for value in provenance.values())
    genzui = sum(count for kind, count in kinds.items() if 'GenZui' in kind or 'squared-katakana' in kind)
    assert kinds['Noto Sans Hentaigana instance at weight axis 380'] == 286 and kinds['GenSeki Hentaigana Gothic 1.201 Regular'] == 21
    entries = inventory(TTFont(OUT/(STEM+'.ttf')), provenance)
    counts = dict(Counter(e['source'] for e in entries))
    assert counts == {'jp': 16732, 'hentaigana': 290, 'genseki': 21, 'frb': 15, 'cjk': 1, 'genzui': genzui}, counts
    assert len(entries) == checks['encoded_characters']
    data = {'version': version, 'family': 'GenZui Sans', 'origins': ORIGINS, 'characters': entries,
            'counts': counts, 'total': len(entries),
            'historical': sum(e['group'] in KANA_GROUPS for e in entries)}
    hentaigana = ''.join(chr(cp) for cp in range(0x1B001, 0x1B11F)) + ' 𛀀𛄠𛄡𛄢 𛄣𛄤𛄥𛄦𛄧𛄨𛅨'
    page = (ROOT/'templates/sans.html').read_text()
    replacement = {
        '{{SANS_FONT}}': sans_font, '{{SERIF_FONT}}': serif_font,
        '{{CSS}}': (ROOT/'site/style.css').read_text(),
        '{{FAMILY_SWITCH_CSS}}': switch_css(),
        '{{FAMILY_SWITCH}}': switch_html('sans'),
        '{{VERSION}}': html.escape(version), '{{SERIF_VERSION}}': html.escape(SERIF_VERSION),
        '{{CHARACTER_COUNT}}': f"{checks['encoded_characters']:,}",
        '{{JP_COUNT}}': f"{kinds['Noto Sans JP Regular']:,}", '{{GENZUI_COUNT}}': str(genzui),
        '{{HENTAIGANA}}': hentaigana, '{{PAIRING_TEXT}}': PAIRING_TEXT,
        '{{EXTENDED_KANA_COUNT}}': str(data['historical']),
        '{{NUMERAL_COUNT}}': str(sum(e['group'] == 'han-numeral' for e in entries)),
        '{{DATA}}': json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c'),
        '{{JS}}': (ROOT/'site/main.js').read_text(),
        '{{FONT_SIZE}}': f'{(OUT/(STEM+".ttf")).stat().st_size/1048576:.1f}',
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
