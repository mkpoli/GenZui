"""Measure bounded curve fitting on the held-out learned CJK/Tangut outlines."""

import json
from pathlib import Path

import numpy as np
from PIL import Image
from style_common import OUT, ROOT, dataset, digest, verify_predictions
from style_metrics import measure, summarize
from style_outline_fit import clean
from style_vectors import svg


def run():
    data = dataset()
    directory = OUT / "cleanup"
    directory.mkdir(exist_ok=True)
    records = []
    targets = np.load(OUT / "cjk.npy", mmap_mode="r")
    for model in ("dual-style", "no-latent"):
        verify_predictions(model)
        for script in ("cjk", "tangut"):
            fields = np.load(OUT / model / f"{script}-field.npy", mmap_mode="r")
            rows = (
                data["cjk"]
                if script == "cjk"
                else [{"cp": cp, "split": "tangut"} for cp in data["tangut"]]
            )
            for i, row in enumerate(rows):
                if row["split"] in ("train", "validation"):
                    continue
                if row["cp"] in (0x4E00, 0x4E28) and row["split"] == "stress":
                    row = {**row, "split": "donor-control"}
                path, pixels, fit = clean(fields[i])
                name = f"{row['cp']:X}-{model}-fitted"
                (directory / f"{name}.svg").write_text(svg(path, field=True))
                Image.fromarray(pixels).save(directory / f"{name}.png")
                record = {
                    **row,
                    "model": model,
                    **fit,
                    "svg": f"{name}.svg",
                    "sha256": digest(directory / f"{name}.svg"),
                    "raster_sha256": digest(directory / f"{name}.png"),
                }
                if script == "cjk":
                    record["target"] = measure(pixels, targets[i, 1])
                    record["raw_target"] = measure(
                        (fields[i] > 0).astype(np.uint8) * 255, targets[i, 1]
                    )
                records.append(record)
                (directory / f"{name}.json").write_text(json.dumps(record) + "\n")
            print(f"{model} {script}: {len(records)} glyphs total", flush=True)
    summary = {}
    for model in ("dual-style", "no-latent"):
        for split in ("test", "stress", "donor-control", "tangut"):
            rows = [r for r in records if r["model"] == model and r["split"] == split]
            summary[f"{model}/{split}"] = {
                "n": len(rows),
                "fallbacks": sum(r["fallback"] for r in rows),
                "min_source_iou": min(r["source_iou"] for r in rows),
                "max_sampled_boundary_shift_px": max(
                    r["max_sampled_boundary_shift_px"] for r in rows
                ),
                "raw_segments": sum(r["raw_segments"] for r in rows),
                "fitted_segments": sum(r["segments"] for r in rows),
                **(
                    {
                        "raw_target": summarize([r["raw_target"] for r in rows]),
                        "target": summarize([r["target"] for r in rows]),
                    }
                    if split != "tangut"
                    else {}
                ),
            }
    result = {
        "dataset_sha256": digest(OUT / "dataset.json"),
        "prediction_manifests": {
            m: digest(OUT / m / "inference.json") for m in ("dual-style", "no-latent")
        },
        "scripts": {
            p.name: digest(p)
            for p in (
                Path(__file__),
                ROOT / "scripts/style_outline_fit.py",
                ROOT / "scripts/style_metrics.py",
                ROOT / "scripts/style_vectors.py",
            )
        },
        "limits": "Sampled boundary displacement <= 1.1 pixels; IoU >= 0.94 at 512px; one-to-one ink/counter correspondence checked at 256px and 512px. These raster checks are not continuous-topology guarantees. Terminals and joins are inherited from the prediction.",
        "summary": summary,
        "records": records,
    }
    (directory / "report.json").write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: {n: v for n, v in r.items() if n not in ("target", "raw_target")}
                for k, r in summary.items()
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    run()
