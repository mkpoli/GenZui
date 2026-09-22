"""Build the offline GenZui specimen site from the checked font and Unicode data."""
import base64
import hashlib
import html
import json
import shutil
from bisect import bisect_right
from collections import Counter
import unicodedata
from zipfile import ZIP_DEFLATED, ZipFile

from fontTools.ttLib import TTFont
from repertoire import properties
from honkoku import TALLIES
from okinawan import DATA as OKINAWAN_DATA, PUA as OKINAWAN_PUA
from serif import FAMILY, OUT as FONT_OUT, STEM, VERSION
from sources import ROOT, verify
from refinement_proof import build_comparison
from browser_setup import build as build_browser_setup
from minnan_proof import build_study
from design_gallery import build_gallery
from family_switch import css as switch_css, html as switch_html
from sans_site import DOWNLOADS as SANS_DOWNLOADS, OUT as SANS_OUT, build_offline as build_sans_page, checked as sans_checked

OUT = ROOT / 'build/site'

KANA_GROUPS = {'hentaigana', 'historic-kana', 'small-kana', 'bmp-digraph',
               'cjk-kana-ligature', 'minnan-tone', 'phonetic-mark', 'compatibility-kana'}


def character_data(font, audit, provenance):
    cmap = font.getBestCmap()
    historic = {ord(c['character']): c for c in audit['characters']}
    ages = properties('DerivedAge.txt')
    numeric = properties('DerivedNumericType.txt')
    scripts = properties('Scripts.txt')
    blocks, starts = [], []
    for line in (ROOT/'data/unicode/Blocks.txt').read_text().splitlines():
        line = line.split('#', 1)[0].strip()
        if line:
            extent, label = (s.strip() for s in line.split(';'))
            first, last = (int(s, 16) for s in extent.split('..'))
            blocks.append((first, last, label)); starts.append(first)
    names, ranges, first_range = {}, [], None
    for line in (ROOT/'data/unicode/UnicodeData.txt').read_text().splitlines():
        fields = line.split(';'); cp = int(fields[0], 16)
        if fields[1].endswith(', First>'):
            first_range = (cp, fields[2], fields[1])
        elif fields[1].endswith(', Last>'):
            ranges.append((first_range[0], cp, first_range[1], first_range[2]))
        elif cp in cmap:
            names[cp] = (fields[1], fields[2])
    for first, last, category, range_name in ranges:
        for cp in (c for c in cmap if first <= c <= last):
            if range_name.startswith('<CJK Ideograph'):
                name = f'CJK UNIFIED IDEOGRAPH-{cp:04X}'
            elif range_name.startswith('<Hangul Syllable'):
                name = unicodedata.name(chr(cp))  # Stable algorithmic names.
            else:
                assert category == 'Co', range_name
                name = f'PRIVATE USE-{cp:04X}'
            names[cp] = (name, category)
    entries = []
    for cp in sorted(cmap):
        assert cp in names, f'Missing Unicode name: U+{cp:04X}'
        name, category = names[cp]
        index = bisect_right(starts, cp)-1
        assert index >= 0 and cp <= blocks[index][1]
        h = historic.get(cp)
        key = f'U+{cp:04X}'
        source = provenance['source_kinds'][key] if h or cp in OKINAWAN_PUA else 'jp'
        if cp in OKINAWAN_PUA:
            name = 'OKINAWAN ' + OKINAWAN_PUA[cp]['label'].upper() + ' (PRIVATE USE)'
        group = ('okinawan' if cp in OKINAWAN_PUA else 'han-numeral' if cp in numeric and scripts.get(cp) == 'Han' else
                 'ideographic-description' if 0x2FF0 <= cp <= 0x2FFF or cp == 0x31EF else
                 'tally-mark' if cp in TALLIES else h['group'] if h else 'base')
        entries.append({'cp': cp, 'name': name, 'category': category,
                        'block': blocks[index][2], 'age': 'Private use' if cp in OKINAWAN_PUA else ages[cp],
                        'source': source, 'group': group,
                        'label': h.get('label', name) if h else name,
                        'provisional': source == 'genzui',
                        'description': provenance['added'].get(key, '')})
    return entries


def build():
    verify()
    checks = json.loads((FONT_OUT/'checks.json').read_text())
    assert checks['status'] == 'passed' and checks['family'] == FAMILY
    package = ROOT/'dist'/f'{STEM}-{VERSION}.zip'
    assert package.is_file(), 'Build the checked font package before the site.'
    for ext in ('ttf', 'woff2'):
        assert hashlib.sha256((FONT_OUT/(STEM+'.'+ext)).read_bytes()).hexdigest() == checks[ext+'_sha256']
    with ZipFile(package) as z:
        assert z.testzip() is None
        for ext in ('ttf', 'woff2'):
            assert hashlib.sha256(z.read(STEM+'.'+ext)).hexdigest() == checks[ext+'_sha256'], 'Rebuild the font package: its font bytes are stale.'
    font = TTFont(FONT_OUT/(STEM+'.ttf'))
    # Use the audited source assignments in addition to the Unicode inventory.
    audit = json.loads((ROOT/'research/repertoire.json').read_text())
    provenance = json.loads((FONT_OUT/'sources.json').read_text())
    entries = character_data(font, audit, provenance)
    source_counts = dict(Counter(e['source'] for e in entries))
    assert source_counts == {'jp': 16726, 'hentaigana': 290, 'genzui': 32 + len(OKINAWAN_PUA), 'frb': 15, 'cjk': 1}
    assert len(entries) == checks['encoded_characters']
    data = {'version': VERSION, 'family': FAMILY, 'characters': entries,
            'counts': source_counts, 'total': len(entries),
            'historical': sum(e['group'] in KANA_GROUPS for e in entries)}
    OUT.mkdir(parents=True, exist_ok=True)
    font_data = base64.b64encode((FONT_OUT/(STEM+'.woff2')).read_bytes()).decode()
    page = (ROOT/'site/serif.html').read_text()
    replacement = {
        '{{FONT}}': font_data,
        '{{CHARACTER_COUNT}}': f'{len(entries):,}',
        '{{CONSTRUCTION_COUNT}}': str(source_counts['genzui']),
        '{{OKINAWAN_DATA}}': json.dumps(OKINAWAN_DATA, ensure_ascii=False).replace('<', '\\u003c'),
        '{{OKINAWAN_JS}}': (ROOT/'site/okinawan.js').read_text() + '\n' + (ROOT/'site/okinawan-ui.js').read_text(),
        '{{NUMERAL_COUNT}}': str(sum(e['group'] == 'han-numeral' for e in entries)),
        '{{CSS}}': (ROOT/'site/style.css').read_text(),
        '{{FAMILY_SWITCH_CSS}}': switch_css(),
        '{{FAMILY_SWITCH}}': switch_html('serif'),
        '{{JS}}': (ROOT/'site/main.js').read_text(),
        '{{DATA}}': json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c'),
        '{{VERSION}}': html.escape(VERSION),
        '{{SANS_VERSION}}': html.escape(sans_checked()[0]),
        '{{FONT_SIZE}}': f'{(FONT_OUT/(STEM+".ttf")).stat().st_size/1048576:.1f}',
        '{{ZIP_SIZE}}': f'{package.stat().st_size/1048576:.1f}',
        '{{WEBFONT_SIZE}}': f'{(FONT_OUT/(STEM+".woff2")).stat().st_size/1048576:.1f}',
        '{{WEBFONT_USAGE}}': '<!-- webfont-usage -->',
    }
    for token, value in replacement.items():
        page = page.replace(token, value)
    assert all(token not in page for token in replacement)
    assert '/home/' not in page
    (OUT/'serif.html').write_text(page)
    sans_checks = json.loads((SANS_OUT/'checks.json').read_text())
    sans_provenance = json.loads((SANS_OUT/'sources.json').read_text())['source_kinds']
    landing = (ROOT/'site/landing.html').read_text()
    for token, value in {
        '{{SERIF_FONT}}': 'data:font/woff2;base64,'+font_data,
        '{{SANS_FONT}}': 'data:font/woff2;base64,'+base64.b64encode((SANS_OUT/'GenZuiSans-Regular.woff2').read_bytes()).decode(),
        '{{CSS}}': replacement['{{CSS}}'], '{{FAMILY_SWITCH_CSS}}': switch_css(), '{{FAMILY_SWITCH}}': switch_html(None),
        '{{VERSION}}': html.escape(VERSION), '{{SANS_VERSION}}': html.escape(sans_checks['version']),
        '{{CHARACTER_COUNT}}': replacement['{{CHARACTER_COUNT}}'], '{{CONSTRUCTION_COUNT}}': replacement['{{CONSTRUCTION_COUNT}}'],
        '{{SANS_CHARACTER_COUNT}}': f"{sans_checks['encoded_characters']:,}",
        '{{SANS_CONSTRUCTION_COUNT}}': str(sum('GenZui' in v.split(';')[0] or 'squared-katakana' in v for v in sans_provenance.values())),
        '{{FONT_SIZE}}': replacement['{{FONT_SIZE}}'],
        '{{SANS_FONT_SIZE}}': f"{(SANS_OUT/'GenZuiSans-Regular.ttf').stat().st_size/1048576:.1f}",
    }.items():
        landing = landing.replace(token, value)
    assert '{{' not in landing and '/home/' not in landing
    (OUT/'index.html').write_text(landing)
    (OUT/'refinements.html').write_text(build_comparison())
    (OUT/'minnan.html').write_text(build_study())
    (OUT/'gallery.html').write_text(build_gallery())
    (OUT/'sans.html').write_text(build_sans_page())
    shutil.copytree(build_browser_setup(), OUT/'browser', dirs_exist_ok=True)
    downloads = OUT/'downloads'; downloads.mkdir(exist_ok=True)
    for old in downloads.glob(STEM+'-*.zip'):
        if old.name != package.name:
            old.unlink()
    shutil.copyfile(package, downloads/package.name)
    sans_version, _, sans_package = sans_checked()
    for old in downloads.glob('GenZuiSans-Regular-*.zip'):
        if old.name != sans_package.name:
            old.unlink()
    shutil.copyfile(sans_package, downloads/sans_package.name)
    for source, name in SANS_DOWNLOADS.items():
        shutil.copyfile(SANS_OUT/source, downloads/name)
    for name in (STEM+'.ttf', STEM+'.woff2', 'OFL.txt', 'NOTICE.txt',
                 'Jigmo-CC0.txt', 'Jigmo-README.txt', 'Jigmo-THANKS.txt',
                 'FRB-OFL.txt', 'FRB-README.md',
                 'Unicode-LICENSE.txt', 'LICENSE-scripts.txt', 'kana-coverage.json', 'NotoSerifCJK-OFL.txt', 'okinawan-mappings.json'):
        shutil.copyfile(FONT_OUT/name, downloads/name)
    (OUT/'README.txt').write_text(
        'GenZui specimen site\n\nOpen index.html in a current browser.\n'
        'serif.html and sans.html are the family specimens; each embeds its font and full character inventory and works offline.\n'
        'Keep the downloads folder beside index.html for the download links.\n'
        'Only deliberate source links navigate to external websites.\n'
        'Font, Unicode data and script licences are included in downloads.\n'
    )
    archive = ROOT/'dist'/f'GenZui-Specimen-{VERSION}.zip'
    with ZipFile(archive, 'w', ZIP_DEFLATED) as z:
        for file in sorted(OUT.rglob('*')):
            if file.is_file(): z.write(file, file.relative_to(OUT))
    with ZipFile(archive) as z:
        assert z.testzip() is None
    print(f'Built offline specimen: {len(entries):,} searchable characters; {data["historical"]} historical targets.')


if __name__ == '__main__':
    build()
