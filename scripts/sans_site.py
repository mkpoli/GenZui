"""Build the GenZui Sans page from the checked Sans font and package."""
import base64
import hashlib
import html
import json
from collections import Counter
from zipfile import ZipFile

from family_switch import css as switch_css, html as switch_html
from serif import OUT as SERIF_OUT, STEM as SERIF_STEM, VERSION as SERIF_VERSION
from sources import ROOT

OUT = ROOT/'build/sans'
STEM = 'GenZuiSans-Regular'
PAIRING_TEXT = '春はあけぼの。𛀂𛀆𛀋 𛄣𛄤𛄥 かなのかたちを読む。'
# Files published beside the Serif downloads. Licence and credit files carry the
# family name because the Serif set already occupies the plain names.
DOWNLOADS = {STEM+'.ttf': STEM+'.ttf', STEM+'.woff2': STEM+'.woff2',
             'OFL.txt': 'GenZuiSans-OFL.txt', 'NOTICE.txt': 'GenZuiSans-NOTICE.txt',
             'checks.json': 'GenZuiSans-checks.json', 'kana-coverage.json': 'GenZuiSans-kana-coverage.json'}


def checked():
    """Return the Sans version, checks and package after verifying they agree."""
    checks = json.loads((OUT/'checks.json').read_text())
    browsers = json.loads((OUT/'browser-checks.json').read_text())
    assert checks['status'] == browsers['status'] == 'passed'
    assert checks['family'] == browsers['family'] == 'GenZui Sans'
    version = checks['version']
    package = ROOT/'dist'/f'{STEM}-{version}.zip'
    assert package.is_file(), 'Package the checked Sans font first: scripts/package_sans.py'
    with ZipFile(package) as archive:
        for ext in ('ttf', 'woff2'):
            digest = hashlib.sha256((OUT/f'{STEM}.{ext}').read_bytes()).hexdigest()
            assert digest == checks[ext+'_sha256'] == browsers[ext+'_sha256'], 'Stale Sans validation: '+ext
            assert hashlib.sha256(archive.read(f'{STEM}.{ext}')).hexdigest() == digest, 'Rebuild the Sans package: its font bytes are stale.'
    return version, checks, package


def build_page(sans_font, serif_font, webfont_usage=''):
    """Render the page; font arguments are the URLs the page loads."""
    version, checks, package = checked()
    provenance = json.loads((OUT/'sources.json').read_text())['source_kinds']
    kinds = Counter(value.split(';')[0] for value in provenance.values())
    genzui = sum(count for kind, count in kinds.items() if 'GenZui' in kind or 'squared-katakana' in kind)
    assert kinds['Noto Sans Hentaigana DemiLight instance'] == 286 and kinds['GenSeki Hentaigana Gothic 1.201 Regular'] == 21
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
