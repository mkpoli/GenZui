"""Package the validated GenZui Sans P faces as a separate download."""
import hashlib
import json
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

from sans import OUT, ROOT, VERSION
from sans_p import BOLD_STEM_P, FAMILY_P, PACKAGE_P, STEM_P


def package():
    checks = json.loads((OUT/'checks-p.json').read_text())
    assert checks['status'] == 'passed' and checks['family'] == FAMILY_P and checks['version'] == VERSION
    for stem, record in ((STEM_P, checks['regular']), (BOLD_STEM_P, checks['bold'])):
        for ext in ('ttf', 'woff2'):
            digest = hashlib.sha256((OUT/(stem+'.'+ext)).read_bytes()).hexdigest()
            assert digest == record[ext+'_sha256'], 'Stale font validation: '+stem+'.'+ext
    palt = json.loads((OUT/'sources-p.json').read_text())['baked_palt']
    readme = f'''GenZui Sans P / 源萃ゴシックP
Regular and Bold · Version {VERSION}

GenZui Sans with the widths of its OpenType palt feature applied by default.
Applications that ignore palt, such as Word and PowerPoint, set kana and
punctuation proportionally. The outlines, coverage and vertical layout are
those of GenZui Sans; use GenZui Sans where fixed-width kana are wanted.

Install
-------
Open GenZuiSansP-Regular.ttf and GenZuiSansP-Bold.ttf and choose Install.
Select GenZui Sans P or 源萃ゴシックP in your application. The family can
coexist with GenZui Sans.

Web
---
Keep genzui-sans-p.css beside the two WOFF2 files, load the stylesheet, then
use font-family: "GenZui Sans P", sans-serif.

What changed
------------
{palt['glyphs']} glyphs of Regular take the palt placement and advance of
GenZui Sans, shifted into their outlines and advances. The palt and halt
features are removed so that the widths are not applied twice. Vertical text
keeps the ink positions of GenZui Sans through a vert positioning lookup.
Kerning, mark positioning and every other glyph are unchanged.

Licensing
---------
Fonts and derived outlines: SIL Open Font License 1.1. See OFL.txt.
NOTICE.txt credits the contributing projects.

checks-p.json records the comparison with GenZui Sans. sources-p.json
lists the baked palt lookups.
'''
    (OUT/'README-P.txt').write_text(readme)
    files = [(STEM_P+'.ttf',)*2, (STEM_P+'.woff2',)*2, (BOLD_STEM_P+'.ttf',)*2, (BOLD_STEM_P+'.woff2',)*2,
             ('genzui-sans-p.css',)*2, ('README.txt', 'README-P.txt'), ('NOTICE.txt', 'NOTICE-P.txt'),
             ('OFL.txt',)*2, ('checks-p.json',)*2, ('sources-p.json',)*2, ('sources-p-bold.json',)*2]
    destination = ROOT/'dist'/PACKAGE_P
    destination.parent.mkdir(exist_ok=True)
    with ZipFile(destination, 'w', ZIP_DEFLATED, compresslevel=9) as archive:
        for name, source in files:
            info = ZipInfo(name, (2025, 6, 5, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, (OUT/source).read_bytes())
    with ZipFile(destination) as archive:
        assert archive.testzip() is None
        for name, source in files:
            assert archive.read(name) == (OUT/source).read_bytes()
    print(f'Packaged dist/{destination.name}: {len(files)} files.')


if __name__ == '__main__':
    package()
