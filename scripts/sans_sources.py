"""Verify the additional Sans sources and compile Noto's Sans Hentaigana instances."""
import hashlib
import json
import os
import tarfile
from pathlib import Path
from urllib.request import urlopen
from zipfile import ZipFile

from fontTools.ttLib import TTFont

from sources import ROOT, verify

CACHE = ROOT / 'build/sans-work'
SOURCE = CACHE / 'sources'
NOTO = SOURCE / 'NotoSansHentaigana'
GENSEKI = SOURCE / 'GenSekiHentaiganaGothic'
# The Regular instance sits on the Regular master (upstream weight class 500).
# GenZui adds an instance at axis 380, where the hentaigana's median stem
# (69.5 units) matches Noto Sans JP Regular's hiragana (69.3), for the
# hentaigana beside ordinary kana.
# Bold follows the same rule against Noto Sans JP Bold: at axis 720 the
# hentaigana's median stem is 108.3 units against 108.5 for the hiragana, and at
# axis 780 the four archaic kana sit with the Bold katakana (114.3).
INSTANCES = CACHE / 'instances'
STUDY = CACHE / 'NotoSansHentaigana-GenZui.glyphs'
TEXT_AXIS = 380
BOLD_TEXT_AXIS = 720
BOLD_ARCHAIC_AXIS = 780
DONOR = INSTANCES / 'NotoSansHentaigana-Regular.ttf'
TEXT = INSTANCES / 'NotoSansHentaigana-GenZui.ttf'
BOLD_TEXT = INSTANCES / 'NotoSansHentaigana-GenZuiBold.ttf'
BOLD_ARCHAIC = INSTANCES / 'NotoSansHentaigana-GenZuiBoldArchaic.ttf'
CJK = CACHE / 'NotoSansCJKjp-Regular.otf'
CJK_BOLD = CACHE / 'NotoSansCJKjp-Bold.otf'
EPOCH = '1749081600'
COMPILED = (DONOR, TEXT, BOLD_TEXT, BOLD_ARCHAIC)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare():
    verify(fetch=True)
    CACHE.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((ROOT / 'sources/sans-manifest.json').read_text())
    for item in manifest['files']:
        path = CACHE / item['filename']
        if not path.exists():
            print('Fetching ' + item['filename'], flush=True)
            with urlopen(item['url'], timeout=120) as response:
                data = response.read()
            if hashlib.sha256(data).hexdigest() != item['sha256']:
                raise ValueError('Download checksum mismatch: ' + item['filename'])
            path.write_bytes(data)
        if digest(path) != item['sha256']:
            raise ValueError('Source checksum mismatch: ' + item['filename'])

    # Extract only font sources and notices; archive paths never become output paths.
    with ZipFile(CACHE / 'hentaigana.zip') as archive:
        prefix = 'hentaigana-3aa4d30ee04254d3d0a69c500de7fda494e3b302/'
        for member in archive.namelist():
            relative = member.removeprefix(prefix)
            if not member.startswith(prefix) or member.endswith('/'):
                continue
            if relative == 'OFL.txt':
                target = NOTO / 'OFL.txt'
            elif relative.startswith('sources/NotoSansHentaigana.glyphspackage/'):
                relative = relative.removeprefix('sources/')
                if '..' in Path(relative).parts:
                    raise ValueError('Unsafe source archive member')
                target = NOTO / relative
            else:
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(member))
    with tarfile.open(CACHE / 'genseki.tar.xz') as archive:
        for name in ('GenSekiHentaiganaGothic.ttf', 'GenSekiHentaiganaGothic-Bold.ttf', 'OFL.txt', 'README.md'):
            target = GENSEKI / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.extractfile('GenSekiHentaiganaGothic/' + name).read())

    # Keep compiler versions in the cache key as well as the source archive hash.
    import importlib.metadata
    versions = {name: importlib.metadata.version(name)
                for name in ('fontmake', 'fonttools', 'glyphsLib', 'ufo2ft')}
    key = {'sources': manifest, 'compiler': versions, 'epoch': EPOCH,
           'instances': [p.name for p in COMPILED], 'text_axis': TEXT_AXIS,
           'bold_axes': [BOLD_TEXT_AXIS, BOLD_ARCHAIC_AXIS]}
    stamp = CACHE / 'instance-build.json'
    previous = json.loads(stamp.read_text()) if stamp.exists() else {}
    hashes = {p.name: digest(p) for p in COMPILED if p.exists()}
    if previous.get('inputs') != key or previous.get('sha256') != hashes or len(hashes) < len(COMPILED):
        from fontmake.font_project import FontProject
        from glyphsLib import GSFont, GSInstance
        os.environ['SOURCE_DATE_EPOCH'] = EPOCH
        print('Compiling the Noto Sans Hentaigana instances', flush=True)
        source = GSFont(str(NOTO / 'NotoSansHentaigana.glyphspackage'))
        for name, axis, weight in (('GenZui', TEXT_AXIS, 400), ('GenZuiBold', BOLD_TEXT_AXIS, 700),
                                   ('GenZuiBoldArchaic', BOLD_ARCHAIC_AXIS, 700)):
            instance = GSInstance()
            instance.name, instance.axes, instance.weight = name, [axis], weight
            source.instances.append(instance)
        source.save(str(STUDY))
        FontProject().run_from_glyphs(
            str(STUDY), output=['ttf'], interpolate='.* (Regular|GenZui|GenZuiBold|GenZuiBoldArchaic)$',
            master_dir='{tmp}', instance_dir='{tmp}', output_dir=str(INSTANCES))
        for path in COMPILED:
            font = TTFont(path, recalcTimestamp=False)
            # Both drawings exist upstream but lack Unicode assignments.
            for cp, name in ((0x1B000, 'archaicEkatakana'), (0x1B001, 'archaicYehiragana')):
                assert name in font.getGlyphOrder()
                assert font['glyf'][name].numberOfContours != 0
                for table in font['cmap'].tables:
                    if table.isUnicode() and table.format == 12:
                        table.cmap[cp] = name
            font.save(path)
        hashes = {p.name: digest(p) for p in COMPILED}
        stamp.write_text(json.dumps({'inputs': key, 'sha256': hashes}, indent=2) + '\n')
    return manifest


if __name__ == '__main__':
    prepare()
    print('Verified Sans sources and compiled the Noto Sans Hentaigana instances.')
