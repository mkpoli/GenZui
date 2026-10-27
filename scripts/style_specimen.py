"""Build an offline proof of the paired-style pilot and Tangut transfer."""

import json
import shutil
from io import BytesIO
from pathlib import Path

import numpy as np
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont
from style_common import OUT, ROOT, dataset, digest, verify_binding, verify_predictions
from style_data import BASE, EM, PAD, SANS, SERIF, SIZE, TANGUT
from style_vectors import field_path, font_path, svg

from sources import verify

MODELS = ("dual-style", "no-latent")


def build():
    data = dataset()
    sources = verify(manifest="style-manifest.json")
    metrics = json.loads((OUT / "metrics.json").read_text())
    verify_binding(metrics)
    structure = json.loads((OUT / "tangut-structure.json").read_text())
    verify_binding(structure)
    for name in MODELS:
        verify_predictions(name)
        if (
            digest(OUT / name / "inference.json")
            != metrics["prediction_manifests"][name]
        ):
            raise ValueError("Metrics belong to different predictions")
        if (
            digest(OUT / name / "inference.json")
            != structure["prediction_manifests"][name]
        ):
            raise ValueError("Tangut screen belongs to different predictions")
    cleanup = json.loads((OUT / "cleanup/report.json").read_text())
    verify_binding(cleanup)
    for name in MODELS:
        if cleanup["prediction_manifests"][name] != digest(
            OUT / name / "inference.json"
        ):
            raise ValueError("Cleanup belongs to different predictions")
    for name, expected in cleanup["scripts"].items():
        if digest(ROOT / "scripts" / name) != expected:
            raise ValueError("Cleanup implementation changed")
    cleanup_by_cp = {}
    for row in cleanup["records"]:
        if digest(OUT / "cleanup" / row["svg"]) != row["sha256"]:
            raise ValueError("Fitted outline changed")
        if (
            digest(OUT / "cleanup" / row["svg"].replace(".svg", ".png"))
            != row["raster_sha256"]
        ):
            raise ValueError("Fitted raster changed")
        cleanup_by_cp.setdefault(row["cp"], {})[row["model"]] = row
    directory = OUT / "proof"
    directory.mkdir(exist_ok=True)
    assets = directory / "glyphs"
    assets.mkdir(exist_ok=True)
    paths = {
        "serif": SERIF,
        "sans": SANS,
        "heuristic": OUT / "baseline.ttf",
        "tangut-serif": TANGUT,
        "tangut-heuristic": ROOT / "build/tangut-sans/GenZuiSansTangut-Regular.ttf",
        "lorchin": ROOT / "sources/upstream/LorchinSans/LorchinSansP0.woff2",
    }
    baseline = json.loads((OUT / "baseline.json").read_text())
    if digest(OUT / "baseline.json") != metrics["baseline_sha256"]:
        raise ValueError("Metrics belong to another baseline")
    if digest(paths["heuristic"]) != baseline["font_sha256"]:
        raise ValueError("Baseline outline file changed")
    if digest(paths["tangut-heuristic"]) != structure["heuristic_font_sha256"]:
        raise ValueError("Tangut screen belongs to another heuristic font")
    fonts = {name: TTFont(path) for name, path in paths.items()}
    notices = []
    for name, font in fonts.items():
        copyrights = sorted(
            {record.toUnicode() for record in font["name"].names if record.nameID == 0}
        )
        notices.append(name + "\n" + "\n".join(copyrights))
    (directory / "NOTICE.txt").write_text(
        "Source font copyright notices\n\n"
        + "\n\n".join(notices)
        + "\n\nFont source URLs, SHA-256 hashes and licenses: sources.json.\nNoto and derived GenZui glyph artwork: SIL OFL 1.1. Lorchin: upstream WTFPL.\n"
    )
    raster_fonts = {}
    for name, font in fonts.items():
        stream = BytesIO()
        flavor = font.flavor
        font.flavor = None
        font.save(stream)
        font.flavor = flavor
        stream.seek(0)
        raster_fonts[name] = ImageFont.truetype(stream, EM)
    records = []
    metrics_by_cp = {row["cp"]: row for row in metrics["records"]}
    structure_by_cp = {row["cp"]: row["methods"] for row in structure["records"]}
    raster_checks = []
    font_checks = []
    cleanup_checks = []
    for script in ("cjk", "tangut"):
        fields = {
            name: np.load(OUT / name / f"{script}-field.npy", mmap_mode="r")
            for name in MODELS
        }
        rows = (
            data["cjk"]
            if script == "cjk"
            else [{"cp": cp, "split": "tangut"} for cp in data["tangut"]]
        )
        for i, row in enumerate(rows):
            if row["split"] in ("train", "validation"):
                continue
            cp = row["cp"]
            sources_for_row = (
                ("serif", "heuristic", "sans")
                if script == "cjk"
                else ("tangut-serif", "tangut-heuristic", "lorchin")
            )
            glyphs = {}
            for name in (*sources_for_row, *MODELS):
                outline = (
                    field_path(fields[name][i])
                    if name in MODELS
                    else font_path(fonts[name], cp)
                )
                if outline is None:
                    glyphs[name] = None
                    continue
                filename = f"{cp:X}-{name}.svg"
                (assets / filename).write_text(svg(outline, field=name in MODELS))
                glyphs[name] = f"glyphs/{filename}"
                if name in MODELS and len(raster_checks) < (
                    24 if script == "cjk" else 48
                ):
                    mask = (fields[name][i] > 0).astype(np.uint8) * 255
                    reference = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
                    reference.putalpha(Image.fromarray(mask))
                    reference_name = f"{cp:X}-{name}-mask.png"
                    reference.save(assets / reference_name)
                    raster_checks.append(
                        {"svg": glyphs[name], "mask": f"glyphs/{reference_name}"}
                    )
                if name not in MODELS and len(font_checks) < (
                    36 if script == "cjk" else 72
                ):
                    reference = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
                    ImageDraw.Draw(reference).text(
                        (PAD, BASE),
                        chr(cp),
                        font=raster_fonts[name],
                        fill=(0, 0, 0, 255),
                        anchor="ls",
                    )
                    reference_name = f"{cp:X}-{name}-raster.png"
                    reference.save(assets / reference_name)
                    font_checks.append(
                        {"svg": glyphs[name], "mask": f"glyphs/{reference_name}"}
                    )
            for name in MODELS:
                fitted = cleanup_by_cp[cp][name]
                filename = fitted["svg"]
                shutil.copyfile(OUT / "cleanup" / filename, assets / filename)
                glyphs[name + "-fitted"] = f"glyphs/{filename}"
                if len(cleanup_checks) < (24 if script == "cjk" else 48):
                    pixels = Image.open(
                        OUT / "cleanup" / filename.replace(".svg", ".png")
                    )
                    reference = Image.new("RGBA", pixels.size, (0, 0, 0, 0))
                    reference.putalpha(pixels)
                    reference_name = filename.replace(".svg", "-mask.png")
                    reference.save(assets / reference_name)
                    cleanup_checks.append(
                        {
                            "svg": glyphs[name + "-fitted"],
                            "mask": f"glyphs/{reference_name}",
                        }
                    )
            records.append(
                {
                    **metrics_by_cp.get(cp, row),
                    "glyphs": glyphs,
                    "structure": structure_by_cp.get(cp),
                    "cleanup": cleanup_by_cp[cp],
                }
            )
    for font in fonts.values():
        font.close()
    experiment = {
        "summary": metrics["summary"],
        "cleanup_summary": cleanup["summary"],
        "structure_summary": structure["summary"],
        "records": records,
        "training": {
            name: json.loads((OUT / name / "training.json").read_text())
            for name in MODELS
        },
        "inference": {
            name: json.loads((OUT / name / "inference.json").read_text())
            for name in MODELS
        },
    }
    template = (ROOT / "browser/style-specimen.html").read_text()
    (directory / "index.html").write_text(
        template.replace("__DATA__", json.dumps(experiment))
    )
    (directory / "vector-checks.json").write_text(json.dumps(raster_checks) + "\n")
    (directory / "cleanup-checks.json").write_text(json.dumps(cleanup_checks) + "\n")
    shutil.copyfile(OUT / "cleanup/report.json", directory / "cleanup-report.json")
    (directory / "font-checks.json").write_text(json.dumps(font_checks) + "\n")
    for name in ("dataset.json", "metrics.json", "tangut-structure.json"):
        shutil.copyfile(OUT / name, directory / name)
    for name, path in (
        ("Noto-CJK-OFL.txt", SERIF.with_name("OFL.txt")),
        ("Noto-Tangut-OFL.txt", TANGUT.with_name("OFL.txt")),
        ("Lorchin-LICENSE.txt", paths["lorchin"].with_name("LICENSE.txt")),
        ("GenZui-NOTICE.txt", ROOT / "build/tangut-sans/NOTICE.txt"),
        ("GenZui-OFL.txt", ROOT / "build/tangut-sans/OFL.txt"),
    ):
        shutil.copyfile(path, directory / name)
    record = {
        "sources": sources["files"],
        "display_fonts": {
            name: {"path": str(path.relative_to(ROOT)), "sha256": digest(path)}
            for name, path in paths.items()
        },
        "dataset_sha256": digest(OUT / "dataset.json"),
        "metrics_sha256": digest(OUT / "metrics.json"),
        "scripts": {
            p.name: digest(p)
            for p in (
                Path(__file__),
                Path(__file__).with_name("style_vectors.py"),
                ROOT / "browser/style-specimen.html",
            )
        },
        "heuristic_provenance_sha256": digest(ROOT / "build/tangut-sans/sources.json"),
        "cleanup_sha256": digest(OUT / "cleanup/report.json"),
        "rendering": "Noto, heuristic and Lorchin use original vector contours at a shared em origin. Learned outlines are zero contours of a 256px predicted field, without hinting. The fitted comparison smooths and fits those zero contours with bounded displacement and raster region checks; its parameters and results are recorded in cleanup-report.json.",
        "lorchin": "Comparison only. WTFPL repository license; exact upstream Tangut glyph revisions are unverified. The release history mentions HanaGothLiteTangut.otf extracted from KAGE fonts.",
    }
    (directory / "sources.json").write_text(json.dumps(record, indent=2) + "\n")
    print(
        json.dumps(
            {
                "cjk": len(metrics["records"]),
                "tangut": len(data["tangut"]),
                "svg_files": len(list(assets.glob("*.svg"))),
            }
        )
    )


if __name__ == "__main__":
    build()
