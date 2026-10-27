"""Small spatial encoder/decoder for paired serif/sans style experiments."""

import argparse
import json
import time
from pathlib import Path

import numpy as np
import torch
from style_common import dataset, digest
from torch import nn
from torch.nn import functional as F

OUT = Path(__file__).resolve().parents[1] / "build/style-transfer"


class Block(nn.Module):
    def __init__(self, incoming, outgoing):
        super().__init__()
        self.layers = nn.Sequential(
            nn.Conv2d(incoming, outgoing, 3, padding=1),
            nn.GroupNorm(4, outgoing),
            nn.SiLU(),
            nn.Conv2d(outgoing, outgoing, 3, padding=1),
            nn.GroupNorm(4, outgoing),
            nn.SiLU(),
        )

    def forward(self, x):
        return self.layers(x)


class StyleNet(nn.Module):
    """Spatial content features plus target-style modulation in the decoder.

    The representation is a learned hypothesis. Paired-feature regularization
    encourages, but does not prove, separation of structure and style.
    """

    def __init__(self, width=16):
        super().__init__()
        channels = [width, width * 2, width * 4, width * 6]
        self.encoders = nn.ModuleList(
            Block(a, b) for a, b in zip([2] + channels[:-1], channels)
        )
        self.decoders = nn.ModuleList(
            [Block(channels[i + 1] + channels[i], channels[i]) for i in (2, 1, 0)]
        )
        self.modulators = nn.ModuleList(nn.Linear(2, c * 2) for c in reversed(channels))
        for layer in self.modulators:
            nn.init.zeros_(layer.weight)
            nn.init.zeros_(layer.bias)
        self.output = nn.Conv2d(width, 1, 1)

    def encode(self, x):
        features = []
        for layer in self.encoders:
            x = layer(x)
            features.append(x)
            x = F.avg_pool2d(x, 2)
        return features

    def modulate(self, x, style, index):
        scale, shift = self.modulators[index](style).chunk(2, dim=1)
        return x * (1 + scale[:, :, None, None]) + shift[:, :, None, None]

    def decode(self, features, style):
        x = self.modulate(features[-1], style, 0)
        for i, (layer, skip) in enumerate(
            zip(self.decoders, reversed(features[:-1])), 1
        ):
            x = F.interpolate(
                x, size=skip.shape[-2:], mode="bilinear", align_corners=False
            )
            x = self.modulate(layer(torch.cat([x, skip], dim=1)), style, i)
        return self.output(x).tanh()

    def forward(self, x, style):
        return self.decode(self.encode(x), style)


def loss(pred, fields, ink):
    near = (fields.abs() < 0.95).float()
    distance = (
        F.smooth_l1_loss(pred, fields, reduction="none") * (1 + near * 3)
    ).mean()
    probability = (pred * 12).sigmoid()
    dice = 1 - (2 * (probability * ink).sum((1, 2, 3)) + 1) / (
        probability.sum((1, 2, 3)) + ink.sum((1, 2, 3)) + 1
    )
    edge = F.binary_cross_entropy_with_logits(pred * 12, ink)
    return distance * 4 + dice.mean() + edge


def batch(images, fields, ids, domain, device):
    ink = (
        torch.from_numpy(np.asarray(images[ids, domain], dtype=np.float32) / 255)
        .unsqueeze(1)
        .to(device)
    )
    distance = (
        torch.from_numpy(np.asarray(fields[ids, domain], dtype=np.float32))
        .unsqueeze(1)
        .to(device)
    )
    return torch.cat([ink, distance], dim=1), distance, ink


@torch.no_grad()
def evaluate(model, images, fields, ids, device):
    model.eval()
    values = []
    for start in range(0, len(ids), 16):
        group = ids[start : start + 16]
        x, _, _ = batch(images, fields, group, 0, device)
        _, _, ink = batch(images, fields, group, 1, device)
        style = F.one_hot(
            torch.ones(len(group), device=device, dtype=torch.long), 2
        ).float()
        with torch.autocast("cuda", dtype=torch.bfloat16):
            pred = model(x, style)
        p, t = pred > 0, ink >= 0.5
        iou = (p & t).sum((1, 2, 3)) / (p | t).sum((1, 2, 3)).clamp_min(1)
        values.extend(iou.cpu().tolist())
    model.train()
    return float(np.mean(values))


def train(name, steps=2400, seconds=900, regularize=0.02):
    torch.set_num_threads(2)
    torch.manual_seed(20261027)
    np.random.seed(20261027)
    if not torch.cuda.is_available():
        raise RuntimeError("This experiment requires a verified CUDA device")
    torch.cuda.set_per_process_memory_fraction(0.25)
    torch.backends.cudnn.benchmark = True
    device = torch.device("cuda")
    metadata = dataset()
    script_hash = digest(Path(__file__))
    dataset_hash = digest(OUT / "dataset.json")
    images = np.load(OUT / "cjk.npy", mmap_mode="r")
    fields = np.load(OUT / "cjk-sdf.npy", mmap_mode="r")
    train_ids = np.array(
        [i for i, r in enumerate(metadata["cjk"]) if r["split"] == "train"]
    )
    valid_ids = np.array(
        [i for i, r in enumerate(metadata["cjk"]) if r["split"] == "validation"]
    )
    model = StyleNet().to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.001, weight_decay=0.0001)
    rng = np.random.default_rng(20261027)
    started = time.monotonic()
    history = []
    best = -1
    output = OUT / name
    if output.exists():
        raise ValueError(f"Run directory already exists: {name}")
    output.mkdir(exist_ok=True)
    print(
        json.dumps(
            {
                "parameters": sum(p.numel() for p in model.parameters()),
                "torch": torch.__version__,
                "device": torch.cuda.get_device_name(),
                "regularize": regularize,
            }
        ),
        flush=True,
    )
    for step in range(1, steps + 1):
        ids = rng.choice(train_ids, 12, replace=False)
        source_domain = rng.integers(0, 2, len(ids))
        target_domain = 1 - source_domain
        if step % 5 == 0:
            target_domain = source_domain.copy()
        x, _, _ = batch(images, fields, ids, source_domain, device)
        other, target, ink = batch(images, fields, ids, target_domain, device)
        style = F.one_hot(torch.from_numpy(target_domain).to(device), 2).float()
        optimizer.zero_grad(set_to_none=True)
        with torch.autocast("cuda", dtype=torch.bfloat16):
            features = model.encode(x)
            pred = model.decode(features, style)
            value = loss(pred, target, ink)
            if regularize and step % 5:
                other_features = model.encode(other)
                # Paired glyphs differ in placement too; this is a soft constraint.
                latent = F.l1_loss(features[-1], other_features[-1])
                value = value + regularize * latent
        value.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 5)
        optimizer.step()
        elapsed = time.monotonic() - started
        if step == 1 or step % 100 == 0 or step == steps or elapsed >= seconds:
            score = evaluate(model, images, fields, valid_ids, device)
            row = {
                "step": step,
                "seconds": round(elapsed, 1),
                "loss": round(float(value.detach()), 5),
                "validation_iou": round(score, 6),
                "peak_vram_mib": round(torch.cuda.max_memory_allocated() / 2**20),
            }
            history.append(row)
            print(json.dumps(row), flush=True)
            if score > best:
                best = score
                torch.save(
                    {
                        "model": model.state_dict(),
                        "step": step,
                        "width": 16,
                        "dataset_sha256": dataset_hash,
                        "script_sha256": script_hash,
                    },
                    output / "best.pt",
                )
            record = {
                "name": name,
                "history": history,
                "regularization": regularize,
                "identity_fraction": 0.2,
                "max_steps": steps,
                "max_seconds": seconds,
                "torch": torch.__version__,
                "device": torch.cuda.get_device_name(),
                "seed": 20261027,
                "dataset_sha256": dataset_hash,
                "script_sha256": script_hash,
                "checkpoint_sha256": digest(output / "best.pt"),
                "determinism": "Fixed sampling and initialization seeds; CUDA benchmark mode may be nondeterministic",
            }
            (output / "training.json").write_text(json.dumps(record, indent=2) + "\n")
        if elapsed >= seconds:
            break
    print("finished", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", default="dual-style")
    parser.add_argument("--steps", type=int, default=2400)
    parser.add_argument("--seconds", type=int, default=900)
    parser.add_argument("--regularize", type=float, default=0.02)
    args = parser.parse_args()
    train(args.name, args.steps, args.seconds, args.regularize)
