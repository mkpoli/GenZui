"""Paired Noto CJK style benchmark with character-disjoint evaluation."""

import hashlib
import json
from importlib.metadata import version
from pathlib import Path

import numpy as np
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import distance_transform_edt
from style_common import digest

from sources import verify

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build/style-transfer"
SERIF = ROOT / "sources/upstream/NotoSerifCJKjp/NotoSerifCJKjp-Regular.otf"
SANS = ROOT / "sources/upstream/NotoSansCJKjp/NotoSansCJKjp-Regular.otf"
TANGUT = ROOT / "sources/upstream/NotoSerifTangut/NotoSerifTangut-Regular.ttf"
SIZE = 256
EM = 224
PAD = 16
BASE = PAD + EM * 0.88
STRESS = "一丨丿丶乙亅二三十土士王玉工干千于口日田目月用中申甲由永水火木本末未米文父又友反皮支女如好安心必思手才寸丁了子小少川州山出凹凸門間雨雲龍鬱齒龜纖森語藏國鬢戀變邊"


def render(path, cps):
    font = ImageFont.truetype(str(path), EM)
    rows = []
    for cp in cps:
        im = Image.new("L", (SIZE, SIZE))
        ImageDraw.Draw(im).text((PAD, BASE), chr(cp), font=font, fill=255, anchor="ls")
        rows.append(np.asarray(im))
    return np.stack(rows)


def sdf(images):
    result = np.empty(images.shape, np.float16)
    for i, im in enumerate(images):
        mask = im >= 128
        signed = distance_transform_edt(mask) - distance_transform_edt(~mask)
        result[i] = np.clip(signed / 8, -1, 1)
    return result


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    verify(fetch=True, manifest="style-manifest.json")
    plan = json.loads((ROOT / "research/style-transfer/split.json").read_text())
    cps = [r["cp"] for r in plan["cjk"]]
    splits = [r["split"] for r in plan["cjk"]]
    if len(set(cps)) != len(cps):
        raise ValueError("Duplicate code points across splits")
    for path in (SERIF, SANS):
        with TTFont(path) as font:
            if not set(cps) <= font.getBestCmap().keys():
                raise ValueError("CJK source lacks requested code points")
    paired = np.stack([render(p, cps) for p in (SERIF, SANS)], axis=1)
    signatures = [hashlib.sha256(im.tobytes()).hexdigest() for im in paired]
    if len(set(signatures)) != len(signatures):
        raise ValueError("Duplicate raster pairs in fixed split")
    np.save(OUT / "cjk.npy", paired)
    fields = np.stack([sdf(paired[:, s]) for s in range(2)], axis=1)
    np.save(OUT / "cjk-sdf.npy", fields)
    tangut_cps = plan["tangut"]
    tangut = render(TANGUT, tangut_cps)
    np.save(OUT / "tangut.npy", tangut)
    np.save(OUT / "tangut-sdf.npy", sdf(tangut))
    manifest = {
        "seed": 20261027,
        "size": SIZE,
        "pixels_per_em": EM,
        "origin": [PAD, BASE],
        "cjk": [{"cp": c, "split": s} for c, s in zip(cps, splits)],
        "tangut": tangut_cps,
        "fonts": {
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (SERIF, SANS, TANGUT)
        },
        "counts": {s: splits.count(s) for s in sorted(set(splits))},
        "duplicate_pairs_removed": 0,
        "arrays": {
            name: digest(OUT / name)
            for name in ("cjk.npy", "cjk-sdf.npy", "tangut.npy", "tangut-sdf.npy")
        },
        "libraries": {
            name: version(name) for name in ("numpy", "Pillow", "scipy", "fonttools")
        },
        "script_sha256": digest(Path(__file__)),
        "split_sha256": digest(ROOT / "research/style-transfer/split.json"),
        "split_policy": "Disjoint code points; byte-identical raster pairs deduplicated. Components may recur across splits. Tangut is evaluation-only.",
    }
    (OUT / "dataset.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest["counts"]), flush=True)


if __name__ == "__main__":
    build()
