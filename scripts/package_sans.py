"""Package the validated Sans font and its offline specimens."""
import hashlib
import json
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

from sans import OUT, ROOT, STEM, VERSION


def package():
    checks = json.loads((OUT/'checks.json').read_text())
    browsers = json.loads((OUT/'browser-checks.json').read_text())
    assert checks['status'] == browsers['status'] == 'passed'
    assert checks['family'] == browsers['family'] == 'GenZui Sans'
    for ext in ('ttf', 'woff2'):
        digest = hashlib.sha256((OUT/(STEM+'.'+ext)).read_bytes()).hexdigest()
        assert digest == checks[ext+'_sha256'] == browsers[ext+'_sha256'], 'Stale font validation: '+ext
    readme = f'''GenZui Sans / 源萃ゴシック
Regular · Version {VERSION}

Install
-------
Open GenZuiSans-Regular.ttf and choose Install. Select GenZui Sans or
源萃ゴシック in your application. This family can coexist with GenZui Serif.

Web
---
Keep genzui-sans.css beside GenZuiSans-Regular.woff2, load the stylesheet,
then use font-family: "GenZui Sans", sans-serif.

Specimens
---------
Open index.html for editable horizontal and vertical text. The page embeds
the font and works offline. preview.png provides a static overview.

Coverage and features
---------------------
{checks['encoded_characters']:,} encoded characters, including all 286 hentaigana and all
763 characters in Unicode 18's Hiragana/Katakana scripts and script extensions.
Noto Sans JP Regular supplies the Japanese base. Noto Sans Hentaigana supplies
290 historical forms; GenSeki Hentaigana Gothic supplies 21 further forms.

ss01 selects Hooked WU.

Minnan tone placement supports one to four fullwidth kana in vertical text
at default spacing. Longer groups need application-level positioning.

Licensing
---------
Fonts and derived outlines: SIL Open Font License 1.1. See OFL.txt and the
individual source licences. NOTICE.txt credits the contributing projects.

checks.json records outline, coverage and HarfBuzz shaping validation.
browser-checks.json identifies the browser engines tested with these files.
'''
    (OUT/'README.txt').write_text(readme)
    files = [STEM+'.ttf', STEM+'.woff2', 'genzui-sans.css', 'README.txt', 'NOTICE.txt',
             'OFL.txt', 'NotoSansHentaigana-OFL.txt', 'GenSeki-OFL.txt', 'GenSeki-README.md',
             'NotoSansCJK-OFL.txt', 'FRB-OFL.txt', 'FRB-README.md', 'Unicode-LICENSE.txt',
             'source-manifest.json', 'sans-source-manifest.json', 'sources.json',
             'checks.json', 'kana-coverage.json', 'browser-checks.json', 'index.html',
             'preview.png', 'hentaigana-contact-sheet.png']
    destination = ROOT/'dist'/f'{STEM}-{VERSION}.zip'
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
