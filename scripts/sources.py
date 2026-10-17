"""Fetch and verify the pinned font sources and Unicode 18 data."""
import hashlib
import io
import json
from pathlib import Path
from urllib.request import urlopen
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]


def verify(fetch=False):
    manifest = json.loads((ROOT / "sources/manifest.json").read_text())
    archives = {}
    for item in manifest["files"]:
        path = ROOT / item["path"]
        if not path.exists():
            if not fetch:
                raise ValueError(f"Missing source: {item['path']}; run scripts/sources.py")
            if "archive_member" in item:
                url = item["url"]
                if url not in archives:
                    with urlopen(url, timeout=60) as response:
                        archives[url] = response.read()
                archive = archives[url]
                if hashlib.sha256(archive).hexdigest() != item["archive_sha256"]:
                    raise ValueError(f"Archive checksum mismatch: {item['path']}")
                with ZipFile(io.BytesIO(archive)) as package:
                    data = package.read(item["archive_member"])
            else:
                with urlopen(item["url"], timeout=60) as response:
                    data = response.read()
            if hashlib.sha256(data).hexdigest() != item["sha256"]:
                raise ValueError(f"Download checksum mismatch: {item['path']}")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        if hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError(f"Source checksum mismatch: {item['path']}")
    return manifest


if __name__ == "__main__":
    print(f"Verified {len(verify(fetch=True)['files'])} pinned source files.")
