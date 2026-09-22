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
# The Regular instance sits on the Regular master; upstream gives it weight
# class 500. DemiLight (axis 300) is the instance upstream pairs with weight
# class 400, so it supplies the hentaigana beside Noto Sans JP Regular.
INSTANCES = CACHE / 'instances'
DONOR = INSTANCES / 'NotoSansHentaigana-Regular.ttf'
LIGHT = INSTANCES / 'NotoSansHentaigana-DemiLight.ttf'
CJK = CACHE / 'NotoSansCJKjp-Regular.otf'
EPOCH = '1749081600'


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
        for name in ('GenSekiHentaiganaGothic.ttf', 'OFL.txt', 'README.md'):
            target = GENSEKI / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.extractfile('GenSekiHentaiganaGothic/' + name).read())

    # Keep compiler versions in the cache key as well as the source archive hash.
    import importlib.metadata
    versions = {name: importlib.metadata.version(name)
                for name in ('fontmake', 'fonttools', 'glyphsLib', 'ufo2ft')}
    key = {'sources': manifest, 'compiler': versions, 'epoch': EPOCH,
           'instances': [DONOR.name, LIGHT.name]}
    stamp = CACHE / 'instance-build.json'
    previous = json.loads(stamp.read_text()) if stamp.exists() else {}
    hashes = {p.name: digest(p) for p in (DONOR, LIGHT) if p.exists()}
    if previous.get('inputs') != key or previous.get('sha256') != hashes or len(hashes) < 2:
        from fontmake.font_project import FontProject
        os.environ['SOURCE_DATE_EPOCH'] = EPOCH
        print('Compiling Noto Sans Hentaigana Regular and DemiLight', flush=True)
        FontProject().run_from_glyphs(
            str(NOTO / 'NotoSansHentaigana.glyphspackage'), output=['ttf'],
            interpolate='.* (Regular|DemiLight)$', master_dir='{tmp}',
            instance_dir='{tmp}', output_dir=str(INSTANCES))
        for path in (DONOR, LIGHT):
            font = TTFont(path, recalcTimestamp=False)
            # Both drawings exist upstream but lack Unicode assignments.
            for cp, name in ((0x1B000, 'archaicEkatakana'), (0x1B001, 'archaicYehiragana')):
                assert name in font.getGlyphOrder()
                assert font['glyf'][name].numberOfContours != 0
                for table in font['cmap'].tables:
                    if table.isUnicode() and table.format == 12:
                        table.cmap[cp] = name
            font.save(path)
        hashes = {p.name: digest(p) for p in (DONOR, LIGHT)}
        stamp.write_text(json.dumps({'inputs': key, 'sha256': hashes}, indent=2) + '\n')
    return manifest


if __name__ == '__main__':
    prepare()
    print('Verified Sans sources and compiled the Noto Sans Hentaigana instances.')
