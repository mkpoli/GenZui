"""Fetch and verify the pinned font sources and Unicode 18 data."""
import hashlib
import json
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]


def verify(fetch=False):
    manifest = json.loads((ROOT / "sources/manifest.json").read_text())
    for item in manifest["files"]:
        path = ROOT / item["path"]
        if not path.exists():
            if not fetch:
                raise ValueError(f"Missing source: {item['path']}; run scripts/sources.py")
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
