"""Fetch and verify the pinned fonts used by the font comparison page."""
import argparse
import hashlib
import io
import json
import os
import tarfile
from pathlib import Path
from urllib.request import Request, urlopen
from zipfile import ZipFile

from sources import ROOT

MANIFEST = ROOT/'sources/compare-manifest.json'
CACHE = ROOT/'build/compare'
DOWNLOADS = CACHE/'dl'
FONTS = CACHE/'fonts'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_archive(entry, local=None):
    """The archive bytes, checked against the pinned digest."""
    path = DOWNLOADS/entry['filename']
    if not path.exists():
        if entry.get('local_only'):
            source = Path(local or os.environ.get('GENZUI_SUKIMA_ZIP', ''))
            if not source.is_file():
                raise ValueError(f"{entry['name']} needs a login ({entry['page']}). Pass --sukima PATH or set GENZUI_SUKIMA_ZIP.")
            data = source.read_bytes()
        else:
            request = Request(entry['url'], headers={'User-Agent': 'genzui-compare/1'})
            with urlopen(request, timeout=120) as response:
                data = response.read()
        if digest(data) != entry['sha256']:
            raise ValueError(f"Archive checksum mismatch: {entry['filename']}")
        DOWNLOADS.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    data = path.read_bytes()
    if digest(data) != entry['sha256']:
        raise ValueError(f"Cached archive checksum mismatch: {path}")
    return data


def extract(entry, data):
    """Write the pinned members under build/compare/fonts/<id>/ after checking each digest."""
    names = {m['path'] for m in entry['members']}
    found = {}
    if entry['kind'] == 'tar.xz':
        with tarfile.open(fileobj=io.BytesIO(data), mode='r:xz') as archive:
            prefix = 'GenSekiHentaiganaGothic/'
            for member in archive.getmembers():
                if member.isfile() and member.name.removeprefix(prefix) in names:
                    found[member.name.removeprefix(prefix)] = archive.extractfile(member).read()
    else:
        with ZipFile(io.BytesIO(data)) as archive:
            root = entry.get('archive_root', '')
            for member in archive.namelist():
                if member.removeprefix(root) in names:
                    found[member.removeprefix(root)] = archive.read(member)
    for member in entry['members']:
        content = found.get(member['path'])
        if content is None or digest(content) != member['sha256']:
            raise ValueError(f"Member checksum mismatch: {entry['id']}/{member['path']}")
        target = font_dir(entry)/member['path']
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)


def font_dir(entry):
    return ROOT/entry['dir'] if entry['kind'] == 'repo' else FONTS/entry['id']


def verify(local=None):
    """Return the manifest after every pinned font and licence file is present and matches."""
    manifest = json.loads(MANIFEST.read_text())
    for entry in manifest['files']:
        if entry['kind'] == 'repo':
            for member in entry['members']:
                if digest((font_dir(entry)/member['path']).read_bytes()) != member['sha256']:
                    raise ValueError(f"Release checksum mismatch: {entry['id']}/{member['path']}")
            continue
        if all((font_dir(entry)/m['path']).is_file() and digest((font_dir(entry)/m['path']).read_bytes()) == m['sha256']
               for m in entry['members']):
            continue
        extract(entry, read_archive(entry, local))
    return manifest


def member(manifest, font_id, role=None, name=None):
    """Paths of one entry's members, filtered by role or file name."""
    entry = next(e for e in manifest['files'] if e['id'] == font_id)
    return [font_dir(entry)/m['path'] for m in entry['members']
            if (role is None or m['role'] == role) and (name is None or m['path'].endswith(name))]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sukima', help='local copy of sukima-gothic_ver11.41.zip')
    args = parser.parse_args()
    print(f"Verified {len(verify(args.sukima)['files'])} pinned font sources.")
