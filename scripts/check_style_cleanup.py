"""Check outline-cleanup geometry, provenance, and empty-field handling."""

import json
from pathlib import Path

import numpy as np
from style_common import OUT, ROOT, digest, verify_binding, verify_predictions
from style_outline_fit import clean, raster, same_regions


def check():
    for value in (-1, 0):
        path, pixels, record = clean(np.full((256, 256), value, dtype=float))
        assert path == "" and not pixels.any() and record["fallback"]
    for invalid in (np.zeros((128, 128)), np.full((256, 256), np.nan)):
        try:
            clean(invalid)
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid field accepted")
    box = [
        [
            ("M", np.array([10.0, 10.0])),
            ("L", np.array([30.0, 10.0])),
            ("L", np.array([30.0, 30.0])),
            ("L", np.array([10.0, 30.0])),
            ("Z", None),
        ]
    ]
    assert raster(box, 1).sum() / 255 == 400  # No implicit contour expansion.
    a = np.zeros((24, 24), dtype=bool)
    a[4:12, 4:12] = True
    a[15:18, 15:18] = True
    missing = a.copy()
    missing[15:18, 15:18] = False
    hole = a.copy()
    hole[7:9, 7:9] = False
    assert same_regions(a, a)
    assert not same_regions(a, missing) and not same_regions(a, hole)
    report = json.loads((OUT / "cleanup/report.json").read_text())
    verify_binding(report)
    for model, expected in report["prediction_manifests"].items():
        verify_predictions(model)
        assert digest(OUT / model / "inference.json") == expected
    for name, expected in report["scripts"].items():
        assert digest(ROOT / "scripts" / name) == expected
    seen = set()
    for row in report["records"]:
        key = row["cp"], row["model"]
        assert key not in seen
        seen.add(key)
        assert row["source_iou"] >= 0.94
        assert row["max_sampled_boundary_shift_px"] <= 1.1
        assert row["segments"] <= row["raw_segments"]
        assert digest(OUT / "cleanup" / row["svg"]) == row["sha256"]
        assert (
            digest(OUT / "cleanup" / row["svg"].replace(".svg", ".png"))
            == row["raster_sha256"]
        )
    assert len(seen) == 952
    result = {
        "cases": len(seen),
        "empty_and_invalid_fields": "pass",
        "region_loss": "pass",
        "raster_area": "400px for a 20 by 20 rectangle",
        "report_sha256": digest(OUT / "cleanup/report.json"),
        "script_sha256": digest(Path(__file__)),
    }
    (OUT / "cleanup/checks.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    check()
