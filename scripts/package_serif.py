"""Package the checked GenZui build with its sources, licences and installer."""
import hashlib
import json
import shutil
from zipfile import ZIP_DEFLATED, ZipFile

from serif import BOLD_STEM, FAMILY, OUT, PACKAGE, STEM, VERSION
from sources import ROOT, verify


def package():
    verify()
    checks = json.loads((OUT/'checks.json').read_text())
    browsers = json.loads((OUT/'browser-checks.json').read_text())
    assert checks['status'] == 'passed' and checks['family'] == FAMILY
    bold = json.loads((OUT/'checks-bold.json').read_text())
    assert bold['status'] == 'passed' and bold['family'] == FAMILY and bold['font_version'] == 'Version ' + VERSION
    for ext in ('ttf', 'woff2'):
        digest = hashlib.sha256((OUT/(STEM+'.'+ext)).read_bytes()).hexdigest()
        assert digest == checks[ext+'_sha256'] == browsers[ext+'_sha256']
        digest = hashlib.sha256((OUT/(BOLD_STEM+'.'+ext)).read_bytes()).hexdigest()
        assert digest == bold[ext+'_sha256'] == browsers['bold_'+ext+'_sha256']
    assert {r['browser'] for r in browsers['results']} == {'chrome', 'vivaldi', 'firefox'}
    assert all(r['status'] == 'passed' for r in browsers['results'])
    readme = (ROOT/'templates/serif-README.txt').read_text().replace('{{VERSION}}', VERSION)
    (OUT/'README.txt').write_text(readme)
    # A BOM allows Windows PowerShell 5.1 to read Japanese text correctly.
    (OUT/'Install-GenZui.ps1').write_text((ROOT/'scripts/install_windows.ps1').read_text(), encoding='utf-8-sig')
    shutil.copyfile(ROOT/'LICENSE-scripts.txt', OUT/'LICENSE-scripts.txt')
    shutil.copyfile(ROOT/'research'/f'kana-coverage-{VERSION}.json', OUT/'kana-coverage.json')
    files = [STEM+'.ttf', STEM+'.woff2', BOLD_STEM+'.ttf', BOLD_STEM+'.woff2', 'README.txt', 'Install-GenZui.ps1',
             'serif-proof.html', 'serif-proof.png', 'OFL.txt', 'NOTICE.txt',
             'Jigmo-CC0.txt', 'Jigmo-README.txt', 'Jigmo-THANKS.txt',
             'FRB-OFL.txt', 'FRB-README.md', 'NotoSerifCJK-OFL.txt',
             'Unicode-LICENSE.txt', 'LICENSE-scripts.txt', 'source-manifest.json',
             'okinawan-mappings.json', 'gugyeol-forms.json', 'sources.json', 'sources-bold.json', 'checks.json', 'checks-bold.json',
             'browser-checks.json', 'kana-coverage.json']
    (ROOT/'dist').mkdir(exist_ok=True)
    archive = ROOT/'dist'/PACKAGE
    with ZipFile(archive, 'w', compression=ZIP_DEFLATED) as z:
        for name in files:
            z.write(OUT/name, name)
    with ZipFile(archive) as z:
        assert z.testzip() is None
        assert set(z.namelist()) == set(files)
    print(f'Packaged {archive.name}: {len(files)} files.')


if __name__ == '__main__':
    package()
