"""Package the validated GenZui Sans Han files as a separate download."""
import hashlib
import json
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

from sans_han import FACES, OUT, ROOT, VERSION

PACKAGE = f'GenZuiSansHan-{VERSION}.zip'


def package():
    checks = json.loads((OUT/'checks.json').read_text())
    assert checks['status'] == 'passed' and checks['version'] == VERSION
    for face in FACES:
        for ext in ('ttf', 'woff2'):
            data = (OUT/(face['stem']+'.'+ext)).read_bytes()
            assert hashlib.sha256(data).hexdigest() == checks['faces'][face['stem']][ext+'_sha256'], \
                'Stale validation: ' + face['stem'] + '.' + ext
    faces = checks['faces']
    lines = '\n'.join(f"{face['stem']}.ttf  {face['family']}: {faces[face['stem']]['encoded_characters']:,} characters"
                      for face in FACES)
    readme = f'''GenZui Sans Han / 源萃ゴシック漢字
Regular · Version {VERSION}

A companion to GenZui Sans. Together they cover all {checks['target_characters']:,} CJK
ideographs, radicals, strokes and ideographic description characters in
Unicode 18. These files hold only the {checks['covered_by_han']:,} that GenZui Sans lacks,
so install GenZui Sans as well and list it first.

{lines}

A font holds at most 65,535 glyphs, so the set is split by Unicode plane:
the first file covers the BMP and plane 3 (Extensions G, H and J), the
second covers plane 2 (Extensions B to F, I and the compatibility supplement).

Install
-------
Open both TTF files and choose Install. In applications, set the font list
or fallback to GenZui Sans first, then GenZui Sans Han and GenZui Sans Han SIP.

Web
---
Keep genzui-sans-han.css beside the WOFF2 files and load it after the
GenZui Sans stylesheet, then use
  font-family: "GenZui Sans", "GenZui Sans Han", sans-serif;
The stylesheet declares each file's unicode-range, so browsers download a
file only when a page uses one of its characters.

Sources
-------
Each character takes the first source that has it:
Noto Sans CJK JP, Sukima Gothic 11.41 Main and Sub, then Plangothic P1 and P2.
Noto Sans CJK and Sukima Gothic use Japanese forms. Plangothic, used for
{sum(f['by_source'].get('Plangothic P1 2.9.5795', 0) + f['by_source'].get('Plangothic P2 2.9.5795', 0) for f in faces.values()):,} rare extension ideographs, follows Chinese Mainland forms.
sources.json lists the source of every character; NOTICE.txt credits each
project. There is no Bold: Sukima Gothic and Plangothic have one weight.

Licensing
---------
SIL Open Font License 1.1. See OFL.txt and the individual source licences.
checks.json records coverage, outline and shaping validation.
'''
    (OUT/'README.txt').write_text(readme)
    files = [name for face in FACES for name in (face['stem']+'.ttf', face['stem']+'.woff2')] + [
        'genzui-sans-han.css', 'README.txt', 'NOTICE.txt', 'OFL.txt', 'NotoSansCJK-OFL.txt',
        'Sukima-OFL.txt', 'Sukima-readme.txt', 'MPLUS-LICENSE_E.txt', 'MPLUS-LICENSE_J.txt',
        'Plangothic-OFL.txt', 'han-source-manifest.json', 'sources.json', 'checks.json']
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
    print(f'Packaged dist/{PACKAGE}: {len(files)} files, {destination.stat().st_size/1e6:.1f} MB.')


if __name__ == '__main__':
    package()
