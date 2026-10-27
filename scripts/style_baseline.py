"""Apply Tangut reconstruction to CJK with a CFF winding adapter."""

import argparse
import json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import tangut_geometry as geometry
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.reverseContourPen import ReverseContourPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from style_common import ROOT, dataset, digest
from style_data import OUT, SANS, SERIF, render

from sources import verify


class ReversedGlyph:
    def __init__(self, glyph):
        self.glyph = glyph

    def draw(self, pen):
        self.glyph.draw(ReverseContourPen(pen))


def initialize():
    geometry.initialize(SERIF, SANS)
    # CFF uses the opposite outer-contour direction to the TTF Tangut source.
    geometry.source_glyphs = {
        name: ReversedGlyph(glyph) for name, glyph in geometry.source_glyphs.items()
    }


def convert(cp):
    try:
        _, glyph, record = geometry.draw_glyph(cp)
        return cp, glyph, record, None
    except Exception as error:  # noqa: BLE001 — report failed glyphs in benchmark
        return cp, None, None, f"{type(error).__name__}: {error}"


def run(workers=4):
    verify(fetch=True, manifest="style-manifest.json")
    manifest = dataset()
    cps = [r["cp"] for r in manifest["cjk"] if r["split"] in ("test", "stress")]
    glyphs = {".notdef": TTGlyphPen(None).glyph()}
    records = {}
    with ProcessPoolExecutor(max_workers=workers, initializer=initialize) as pool:
        for i, (cp, glyph, record, error) in enumerate(pool.map(convert, cps), 1):
            if glyph is not None:
                glyphs[f"u{cp:X}"] = glyph
            records[f"U+{cp:04X}"] = {"construction": record, "error": error}
            if i % 32 == 0 or error:
                print(
                    json.dumps(
                        {
                            "done": i,
                            "total": len(cps),
                            "cp": f"U+{cp:X}",
                            "error": error,
                        }
                    ),
                    flush=True,
                )
    fb = FontBuilder(1000, isTTF=True)
    fb.setupGlyphOrder(list(glyphs))
    fb.setupCharacterMap({cp: f"u{cp:X}" for cp in cps if f"u{cp:X}" in glyphs})
    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics(
        {name: (1000, getattr(glyph, "xMin", 0)) for name, glyph in glyphs.items()}
    )
    fb.setupHorizontalHeader(ascent=880, descent=-120)
    fb.setupNameTable(
        {"familyName": "CJK conversion benchmark", "styleName": "Regular"}
    )
    fb.setupOS2(
        sTypoAscender=880, sTypoDescender=-120, usWinAscent=1000, usWinDescent=200
    )
    fb.setupPost()
    path = OUT / "baseline.ttf"
    fb.save(path)
    images = render(path, cps)
    for i, cp in enumerate(cps):
        if records[f"U+{cp:04X}"]["error"]:
            images[i] = 0
    np.save(OUT / "baseline.npy", images)
    provenance = {
        "cps": cps,
        "records": records,
        "dataset_sha256": digest(OUT / "dataset.json"),
        "output_sha256": digest(OUT / "baseline.npy"),
        "font_sha256": digest(path),
        "source_archive_sha256": digest(
            ROOT / "sources/upstream/NotoSerifTangut/tangut-source.tar.gz"
        ),
        "renderer_sha256": digest(ROOT / "scripts/style_data.py"),
        "adaptation": "CFF winding reversed for the TTF-oriented contour grouper. Existing Tangut width rule and geometry code retained; no CJK stem-zone hints are available. Algorithm rasterizes at 640 pixels/em; scores use 224 pixels/em.",
        "script_sha256": {
            p.name: digest(p)
            for p in [Path(__file__)]
            + [
                ROOT / "scripts" / name
                for name in (
                    "tangut_geometry.py",
                    "tangut_stems.py",
                    "tangut_spacing.py",
                    "tangut_design.py",
                    "tangut_folds.py",
                )
            ]
        },
    }
    (OUT / "baseline.json").write_text(json.dumps(provenance, indent=2) + "\n")
    print(
        json.dumps(
            {
                "finished": len(cps),
                "failed": sum(bool(r["error"]) for r in records.values()),
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=4)
    run(parser.parse_args().workers)
