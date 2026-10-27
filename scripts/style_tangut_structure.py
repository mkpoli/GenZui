"""Screen Tangut transfer for lost source regions without a Sans target."""

import json
from pathlib import Path

import numpy as np
from scipy.ndimage import label
from style_common import OUT, ROOT, dataset, digest, verify_predictions
from style_data import EM, render
from style_metrics import topology


def retained_regions(source, prediction):
    ink, _ = label(source, np.ones((3, 3)))
    white, _ = label(~source)
    exterior = set(np.unique(np.r_[white[0], white[-1], white[:, 0], white[:, -1]]))
    fractions = []
    counters = []
    # Same substantial-region areas as the 0.002 geometric screen, in em units.
    for region, area in enumerate(np.bincount(ink.ravel())):
        if region and area >= 1000 * (EM / 1000) ** 2:
            fractions.append(float(prediction[ink == region].mean()))
    for region, area in enumerate(np.bincount(white.ravel())):
        if region and region not in exterior and area >= 2000 * (EM / 1000) ** 2:
            counters.append(float((~prediction)[white == region].mean()))
    ptop, stop = topology(prediction), topology(source)
    return {
        "source_ink_region_overlap": fractions,
        "source_counter_white_retention": counters,
        "ink_regions_below_10_percent": sum(v < 0.1 for v in fractions),
        "counters_below_10_percent": sum(v < 0.1 for v in counters),
        "component_delta_from_serif": ptop[0] - stop[0],
        "hole_delta_from_serif": ptop[1] - stop[1],
    }


def run():
    data = dataset()
    source = np.load(OUT / "tangut.npy", mmap_mode="r") >= 128
    font = ROOT / "build/tangut-sans/GenZuiSansTangut-Regular.ttf"
    methods = {"skeleton_0_002": render(font, data["tangut"]) >= 128}
    for name in ("dual-style", "no-latent"):
        verify_predictions(name)
        methods[name] = np.load(OUT / name / "tangut-pred.npy", mmap_mode="r") >= 128
    records = [
        {
            "cp": cp,
            "methods": {
                name: retained_regions(source[i], values[i])
                for name, values in methods.items()
            },
        }
        for i, cp in enumerate(data["tangut"])
    ]
    summary = {
        name: {
            "glyphs": len(records),
            "glyphs_with_lost_substantial_ink_region": sum(
                r["methods"][name]["ink_regions_below_10_percent"] > 0 for r in records
            ),
            "glyphs_with_closed_substantial_counter": sum(
                r["methods"][name]["counters_below_10_percent"] > 0 for r in records
            ),
            "glyphs_with_changed_component_count": sum(
                r["methods"][name]["component_delta_from_serif"] != 0 for r in records
            ),
            "glyphs_with_changed_hole_count": sum(
                r["methods"][name]["hole_delta_from_serif"] != 0 for r in records
            ),
        }
        for name in methods
    }
    result = {
        "summary": summary,
        "records": records,
        "dataset_sha256": digest(OUT / "dataset.json"),
        "script_sha256": digest(Path(__file__)),
        "heuristic_font_sha256": digest(font),
        "prediction_manifests": {
            name: digest(OUT / name / "inference.json")
            for name in ("dual-style", "no-latent")
        },
        "interpretation": "Conservative source-relative screen. Less than 10% retained area flags a nearly lost part/counter. Changes in small gaps, endpoints, connections and intended Sans optical design need visual review. Serif is not a Sans ground truth.",
    }
    (OUT / "tangut-structure.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    run()
