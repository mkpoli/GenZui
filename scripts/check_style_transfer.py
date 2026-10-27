"""Check the paired experiment's splits, artifacts and metric controls."""

import json
from pathlib import Path

import numpy as np
from style_common import OUT, dataset, digest, verify_binding, verify_predictions
from style_metrics import measure


def check():
    data = dataset()
    cps = [r["cp"] for r in data["cjk"]]
    assert len(cps) == len(set(cps)) == 2640
    assert data["counts"] == {
        "train": 2048,
        "validation": 256,
        "test": 256,
        "stress": 80,
    }
    assert len(data["tangut"]) == len(set(data["tangut"])) == 140
    assert not set(cps) & set(data["tangut"])
    images = np.load(OUT / "cjk.npy", mmap_mode="r")
    assert images.shape == (2640, 2, 256, 256)
    for name in ("cjk", "tangut"):
        ink = np.load(OUT / f"{name}.npy", mmap_mode="r")
        assert not np.any(ink[..., 0, :]) and not np.any(ink[..., -1, :])
        assert not np.any(ink[..., :, 0]) and not np.any(ink[..., :, -1])
        assert (ink.sum(axis=(-1, -2)) > 0).all()
    control = images[0, 1]
    exact = measure(control, control)
    assert exact["iou"] == 1 and exact["boundary_error_em1000"] == 0
    assert exact["topology_match"] and exact["ink_ratio"] == 1
    moved = measure(np.roll(control, 4, axis=1), control)
    assert moved["iou"] < 1 and moved["boundary_error_em1000"] > 0
    assert measure(np.zeros_like(control), control)["iou"] == 0
    baseline = json.loads((OUT / "baseline.json").read_text())
    verify_binding(baseline)
    assert not any(r["error"] for r in baseline["records"].values())
    assert digest(OUT / "baseline.npy") == baseline["output_sha256"]
    for name in ("dual-style", "no-latent"):
        record = verify_predictions(name)
        training = json.loads((OUT / name / "training.json").read_text())
        verify_binding(training)
        assert training["checkpoint_sha256"] == record["checkpoint_sha256"]
        best = max(training["history"], key=lambda r: r["validation_iou"])
        assert record["checkpoint_step"] == best["step"]
        for script in ("cjk", "tangut"):
            pred = np.load(OUT / name / f"{script}-pred.npy", mmap_mode="r")
            field = np.load(OUT / name / f"{script}-field.npy", mmap_mode="r")
            assert np.isfinite(field).all()
            assert np.array_equal(pred >= 128, field > 0), (
                "Validation/export threshold differs"
            )
            assert (pred.sum(axis=(-1, -2)) > 0).all()
            assert (
                not (pred[..., 0, :] >= 128).any()
                and not (pred[..., -1, :] >= 128).any()
            )
            assert (
                not (pred[..., :, 0] >= 128).any()
                and not (pred[..., :, -1] >= 128).any()
            )
    metrics = json.loads((OUT / "metrics.json").read_text())
    verify_binding(metrics)
    assert len(metrics["records"]) == 336
    assert metrics["summary"]["test"]["dual-style"]["n"] == 256
    assert metrics["summary"]["stress"]["dual-style"]["n"] == 78
    assert metrics["summary"]["donor-control"]["dual-style"]["n"] == 2
    report = {
        "dataset_sha256": digest(OUT / "dataset.json"),
        "metrics_sha256": digest(OUT / "metrics.json"),
        "script_sha256": digest(Path(__file__)),
        "split_disjointness": "pass",
        "source_bounds_and_coverage": "pass",
        "artifact_bindings": "pass",
        "validation_checkpoint_selection": "pass",
        "strict_zero_threshold": "pass",
        "metric_identity_translation_empty_controls": "pass",
        "donor_controls_excluded_from_stress_aggregate": "pass",
    }
    (OUT / "checks.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    check()
