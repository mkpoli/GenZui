"""Integrity checks shared by the fixed paired-style experiment."""

import hashlib
import json
from pathlib import Path

from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build/style-transfer"


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def dataset():
    data = json.loads((OUT / "dataset.json").read_text())
    if digest(ROOT / "scripts/style_data.py") != data["script_sha256"]:
        raise ValueError("Dataset rendering implementation changed")
    if digest(ROOT / "research/style-transfer/split.json") != data["split_sha256"]:
        raise ValueError("Dataset split plan changed")
    for name, expected in data["fonts"].items():
        if digest(ROOT / name) != expected:
            raise ValueError(f"Dataset font changed: {name}")
        cps = data["tangut"] if "Tangut" in name else [r["cp"] for r in data["cjk"]]
        if len(set(cps)) != len(cps):
            raise ValueError("Duplicate code points")
        with TTFont(ROOT / name) as font:
            if not set(cps) <= font.getBestCmap().keys():
                raise ValueError(f"Missing source glyphs: {name}")
    for name, expected in data["arrays"].items():
        if digest(OUT / name) != expected:
            raise ValueError(f"Dataset array changed: {name}")
    return data


def verify_binding(record):
    if record["dataset_sha256"] != digest(OUT / "dataset.json"):
        raise ValueError("Artifact belongs to another dataset")


def verify_predictions(name):
    directory = OUT / name
    record = json.loads((directory / "inference.json").read_text())
    verify_binding(record)
    if digest(directory / "best.pt") != record["checkpoint_sha256"]:
        raise ValueError(f"Checkpoint changed: {name}")
    for filename, expected in record["output_sha256"].items():
        if digest(directory / filename) != expected:
            raise ValueError(f"Prediction changed: {name}/{filename}")
    return record
