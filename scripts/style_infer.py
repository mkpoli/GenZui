"""Evaluate a validation-selected style checkpoint on fixed glyph coordinates."""

import argparse
import json
from pathlib import Path

import numpy as np
import torch
from style_common import dataset, digest, verify_binding
from style_network import OUT, StyleNet
from torch.nn import functional as F


@torch.no_grad()
def run(name):
    torch.set_num_threads(2)
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for this experiment")
    torch.cuda.set_per_process_memory_fraction(0.25)
    output = OUT / name
    dataset()
    training = json.loads((output / "training.json").read_text())
    verify_binding(training)
    if (
        digest(Path(__file__).with_name("style_network.py"))
        != training["script_sha256"]
    ):
        raise ValueError("Network implementation changed since training")
    if digest(output / "best.pt") != training["checkpoint_sha256"]:
        raise ValueError("Checkpoint changed since training")
    checkpoint = torch.load(output / "best.pt", map_location="cpu", weights_only=True)
    verify_binding(checkpoint)
    if checkpoint["script_sha256"] != training["script_sha256"]:
        raise ValueError("Checkpoint implementation binding differs")
    model = StyleNet(checkpoint["width"]).cuda().eval()
    model.load_state_dict(checkpoint["model"])
    counts = {}
    for script in ("cjk", "tangut"):
        images = np.load(OUT / f"{script}.npy", mmap_mode="r")
        fields = np.load(OUT / f"{script}-sdf.npy", mmap_mode="r")
        if script == "cjk":
            images, fields = images[:, 0], fields[:, 0]
        prediction = np.lib.format.open_memmap(
            output / f"{script}-field.npy",
            mode="w+",
            dtype=np.float16,
            shape=images.shape,
        )
        ink = np.lib.format.open_memmap(
            output / f"{script}-pred.npy", mode="w+", dtype=np.uint8, shape=images.shape
        )
        for start in range(0, len(images), 16):
            source = np.stack(
                [
                    np.asarray(images[start : start + 16], dtype=np.float32) / 255,
                    np.asarray(fields[start : start + 16], dtype=np.float32),
                ],
                axis=1,
            )
            x = torch.from_numpy(source).cuda()
            style = F.one_hot(
                torch.ones(len(x), device="cuda", dtype=torch.long), 2
            ).float()
            with torch.autocast("cuda", dtype=torch.bfloat16):
                pred = model(x, style).float()[:, 0]
            if not torch.isfinite(pred).all():
                raise ValueError("Non-finite prediction")
            prediction[start : start + len(x)] = pred.cpu().numpy()
            # Preserve validation's strict pred > 0, including exact zero logits.
            ink[start : start + len(x)] = (
                ((pred * 12).sigmoid() * 255).round().byte().cpu().numpy()
            )
            view = ink[start : start + len(x)]
            view[pred.cpu().numpy() <= 0] = np.minimum(
                view[pred.cpu().numpy() <= 0], 127
            )
        prediction.flush()
        ink.flush()
        counts[script] = len(images)
        print(json.dumps({"script": script, "glyphs": len(images)}), flush=True)
    record = {
        "checkpoint_step": checkpoint["step"],
        "checkpoint_sha256": digest(output / "best.pt"),
        "dataset_sha256": digest(OUT / "dataset.json"),
        "selection": "Highest validation IoU; test and Tangut excluded from selection",
        "counts": counts,
        "script_sha256": digest(Path(__file__)),
        "output_sha256": {p.name: digest(p) for p in sorted(output.glob("*.npy"))},
    }
    (output / "inference.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("name")
    run(parser.parse_args().name)
