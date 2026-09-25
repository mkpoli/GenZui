"""Package the validated Sans faces and their offline specimens."""
import hashlib
import json
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

from sans import BOLD_STEM, OUT, PACKAGE, ROOT, STEM, VERSION


def package():
    checks = json.loads((OUT/'checks.json').read_text())
    bold = json.loads((OUT/'checks-bold.json').read_text())
    browsers = json.loads((OUT/'browser-checks.json').read_text())
    assert checks['status'] == bold['status'] == browsers['status'] == 'passed'
    assert checks['family'] == bold['family'] == browsers['family'] == 'GenZui Sans'
    assert checks['version'] == bold['version'] == VERSION
    for stem, record, prefix in ((STEM, checks, ''), (BOLD_STEM, bold, 'bold_')):
        for ext in ('ttf', 'woff2'):
            digest = hashlib.sha256((OUT/(stem+'.'+ext)).read_bytes()).hexdigest()
            assert digest == record[ext+'_sha256'] == browsers[prefix+ext+'_sha256'], 'Stale font validation: '+stem+'.'+ext
    readme = f'''GenZui Sans / 源萃ゴシック
Regular and Bold · Version {VERSION}

Install
-------
Open GenZuiSans-Regular.ttf and GenZuiSans-Bold.ttf and choose Install.
Select GenZui Sans or 源萃ゴシック in your application; Bold is the family's
bold style. This family can coexist with GenZui Serif.

Web
---
Keep genzui-sans.css beside the two WOFF2 files, load the stylesheet, then use
font-family: "GenZui Sans", sans-serif. font-weight: 700 selects Bold.

Specimens
---------
Open index.html for editable horizontal and vertical text. The page embeds
the Regular font and works offline. preview.png provides a static overview.

Coverage and features
---------------------
{checks['encoded_characters']:,} encoded characters, including all 286 hentaigana and all
763 characters in Unicode 18's Hiragana/Katakana scripts and script extensions.
Noto Sans JP Regular and Bold supply the Japanese base. Noto Sans Hentaigana
supplies 290 historical forms from instances matched to each weight; GenSeki
Hentaigana Gothic Regular and Bold supply 20 further forms, and GenZui draws
the alternate WI from Noto Sans JP's strokes.

Minnan tone placement supports one to four fullwidth kana in vertical text
at default spacing. Longer groups need application-level positioning.

Licensing
---------
Fonts and derived outlines: SIL Open Font License 1.1. See OFL.txt and the
individual source licences. NOTICE.txt credits the contributing projects.

checks.json and checks-bold.json record outline, coverage and HarfBuzz
shaping validation for each face.
browser-checks.json identifies the browser engines tested with these files.
'''
    (OUT/'README.txt').write_text(readme)
    files = [STEM+'.ttf', STEM+'.woff2', BOLD_STEM+'.ttf', BOLD_STEM+'.woff2', 'genzui-sans.css', 'README.txt', 'NOTICE.txt',
             'OFL.txt', 'NotoSansHentaigana-OFL.txt', 'GenSeki-OFL.txt', 'GenSeki-README.md',
             'NotoSansCJK-OFL.txt', 'FRB-OFL.txt', 'FRB-README.md', 'Unicode-LICENSE.txt',
             'source-manifest.json', 'sans-source-manifest.json', 'sources.json', 'sources-bold.json',
             'checks.json', 'checks-bold.json', 'kana-coverage.json', 'browser-checks.json', 'index.html',
             'preview.png', 'hentaigana-contact-sheet.png']
    destination = ROOT/'dist'/PACKAGE
    destination.parent.mkdir(exist_ok=True)
    with ZipFile(destination, 'w', ZIP_DEFLATED, compresslevel=9) as archive:
        for name in files:
            info = ZipInfo(name, (2025, 6, 5, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, (OUT/name).read_bytes())
    with ZipFile(destination) as archive:
        assert archive.testzip() is None
        for name in files:
            assert archive.read(name) == (OUT/name).read_bytes()
    print(f'Packaged dist/{destination.name}: {len(files)} files.')


if __name__ == '__main__':
    package()
