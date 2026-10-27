"""Measure shape deviation on fixed-coordinate, held-out Noto CJK pairs."""

import json
from pathlib import Path

import numpy as np
from scipy.ndimage import binary_erosion, distance_transform_edt, label
from style_common import dataset, digest, verify_binding, verify_predictions
from style_data import EM, OUT


def topology(mask):
    components, _ = label(mask, np.ones((3, 3)))
    ink_sizes = np.bincount(components.ravel())[1:]
    white, _ = label(~mask)
    exterior = set(np.unique(np.r_[white[0], white[-1], white[:, 0], white[:, -1]]))
    holes = [
        n
        for n, area in enumerate(np.bincount(white.ravel()))
        if n and n not in exterior and area >= 4
    ]
    return int(np.count_nonzero(ink_sizes >= 4)), len(holes)


def measure(image, target):
    pred, truth = image >= 128, target >= 128
    pe, te = pred ^ binary_erosion(pred), truth ^ binary_erosion(truth)
    iou = (pred & truth).sum() / max(1, (pred | truth).sum())
    if pe.any() and te.any():
        # Symmetric mean boundary distance, in a 1000-unit em.
        distance = (
            (
                distance_transform_edt(~te)[pe].mean()
                + distance_transform_edt(~pe)[te].mean()
            )
            / 2
            * 1000
            / EM
        )
    else:
        distance = None
    ptop, ttop = topology(pred), topology(truth)
    return {
        "iou": float(iou),
        "boundary_error_em1000": float(distance) if distance is not None else None,
        "empty_prediction": not bool(pred.any()),
        "empty_target": not bool(truth.any()),
        "ink_ratio": float(pred.sum() / max(1, truth.sum())),
        "components": ptop[0],
        "holes": ptop[1],
        "target_components": ttop[0],
        "target_holes": ttop[1],
        "topology_match": ptop == ttop,
    }


def summarize(rows):
    distances = [
        r["boundary_error_em1000"]
        for r in rows
        if r["boundary_error_em1000"] is not None
    ]
    return {
        "n": len(rows),
        "mean_iou": float(np.mean([r["iou"] for r in rows])),
        "median_iou": float(np.median([r["iou"] for r in rows])),
        "mean_boundary_error_em1000": float(np.mean(distances)) if distances else None,
        "median_boundary_error_em1000": float(np.median(distances))
        if distances
        else None,
        "p95_boundary_error_em1000": float(np.percentile(distances, 95))
        if distances
        else None,
        "empty_predictions": sum(r["empty_prediction"] for r in rows),
        "empty_targets": sum(r["empty_target"] for r in rows),
        "extra_components": sum(
            max(0, r["components"] - r["target_components"]) for r in rows
        ),
        "missing_components": sum(
            max(0, r["target_components"] - r["components"]) for r in rows
        ),
        "extra_holes": sum(max(0, r["holes"] - r["target_holes"]) for r in rows),
        "missing_holes": sum(max(0, r["target_holes"] - r["holes"]) for r in rows),
        "mean_ink_ratio": float(np.mean([r["ink_ratio"] for r in rows])),
        "topology_match_fraction": float(np.mean([r["topology_match"] for r in rows])),
    }


def run(model_names=()):
    metadata = dataset()
    images = np.load(OUT / "cjk.npy", mmap_mode="r")
    baseline = json.loads((OUT / "baseline.json").read_text())
    verify_binding(baseline)
    if digest(OUT / "baseline.npy") != baseline["output_sha256"]:
        raise ValueError("Baseline pixels changed")
    base_images = np.load(OUT / "baseline.npy", mmap_mode="r")
    base_by_cp = {cp: i for i, cp in enumerate(baseline["cps"])}
    sources = {"serif_unchanged": images[:, 0]}
    for name in model_names:
        verify_predictions(name)
        sources[name] = np.load(OUT / name / "cjk-pred.npy", mmap_mode="r")
        if sources[name].shape != images[:, 0].shape:
            raise ValueError(f"Prediction shape mismatch: {name}")
    records = []
    for i, row in enumerate(metadata["cjk"]):
        if row["split"] not in ("test", "stress"):
            continue
        results = {
            name: measure(values[i], images[i, 1]) for name, values in sources.items()
        }
        results["skeleton_0_002"] = measure(
            base_images[base_by_cp[row["cp"]]], images[i, 1]
        )
        # The heuristic explicitly copies these Sans donor strokes.
        split = "donor-control" if row["cp"] in (0x4E00, 0x4E28) else row["split"]
        records.append({**row, "split": split, "methods": results})
    summary = {
        split: {
            name: summarize(
                [r["methods"][name] for r in records if r["split"] == split]
            )
            for name in records[0]["methods"]
        }
        for split in ("test", "stress", "donor-control")
    }
    result = {
        "summary": summary,
        "records": records,
        "dataset_sha256": digest(OUT / "dataset.json"),
        "prediction_manifests": {
            name: digest(OUT / name / "inference.json") for name in model_names
        },
        "baseline_sha256": digest(OUT / "baseline.json"),
        "script_sha256": digest(Path(__file__)),
        "coordinates": "Identical em scale, baseline and origin; no additional metric-time alignment. The heuristic fits reconstructed regions to source bounds during construction.",
        "topology": "8-connected ink and 4-connected white; regions under 4 pixels ignored. This is a raster diagnostic, not a correctness judgment.",
    }
    (OUT / "metrics.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    import sys

    run(sys.argv[1:])
