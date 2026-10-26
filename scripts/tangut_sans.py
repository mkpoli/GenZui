"""Build GenZui Sans Tangut Regular from the pinned Tangut and Sans sources."""

import argparse
import copy
import hashlib
import json
import os
import shutil
from concurrent.futures import ProcessPoolExecutor
from importlib.metadata import version
from pathlib import Path

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont

from sources import ROOT, verify
from tangut_geometry import draw_glyph, initialize

OUT = ROOT / "build/tangut-sans"
SERIF = ROOT / "sources/upstream/NotoSerifTangut/NotoSerifTangut-Regular.ttf"
SANS = ROOT / "sources/upstream/NotoSansCJKjp/NotoSansCJKjp-Regular.otf"
VERSION = "0.001"
FAMILY = "GenZui Sans Tangut"
FAMILY_JA = "源萃ゴシック西夏文字"
STEM = "GenZuiSansTangut-Regular"
EPOCH = 1792972800  # 2026-10-26, UTC.
SAMPLES = [
    0x17000,
    0x17134,
    0x17F07,
    0x17403,
    0x17C2E,
    0x18509,
    0x17549,
    0x17323,
    0x17C2D,
    0x174DF,
    0x177D5,
    0x17DD6,
    0x187F7,
    0x18D05,
    0x18800,
    0x18801,
    0x18802,
    0x18808,
    0x18810,
    0x1888C,
    0x18929,
    0x16FE0,
]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def target(font):
    return sorted(
        cp
        for cp in font.getBestCmap()
        if cp == 0x16FE0 or 0x17000 <= cp <= 0x18AFF or 0x18D00 <= cp <= 0x18DFF
    )


def build(workers=1, sample=False):
    manifest = verify(fetch=True, manifest="tangut-manifest.json")
    os.environ["SOURCE_DATE_EPOCH"] = str(EPOCH)
    OUT.mkdir(parents=True, exist_ok=True)
    serif, sans = TTFont(SERIF), TTFont(SANS)
    assert serif["head"].unitsPerEm == sans["head"].unitsPerEm == 1000
    cps = sorted(SAMPLES) if sample else target(serif)
    pen = TTGlyphPen(None)
    sans.getGlyphSet()[".notdef"].draw(
        Cu2QuPen(pen, max_err=0.4, reverse_direction=True)
    )
    glyphs = {".notdef": pen.glyph(), "space": TTGlyphPen(None).glyph()}
    metrics = {".notdef": (1000, 100), "space": (250, 0)}
    cmap = {0x20: "space", 0xA0: "space"}
    provenance = {}
    print(
        f"Building {len(cps):,} Tangut characters with {workers} workers.", flush=True
    )
    with ProcessPoolExecutor(
        max_workers=workers, initializer=initialize, initargs=(SERIF, SANS)
    ) as pool:
        for i, (cp, outline, details) in enumerate(
            pool.map(draw_glyph, cps, chunksize=8), 1
        ):
            name = f"u{cp:05X}"
            glyphs[name], metrics[name], cmap[cp] = outline, (1000, outline.xMin), name
            provenance[f"U+{cp:05X}"] = details
            if i % 200 == 0 or i == len(cps):
                print(f"{i:,}/{len(cps):,} glyphs", flush=True)
    for outline in glyphs.values():
        outline.recalcBounds(None)
    vmetrics = {
        name: (1000, 880 - getattr(outline, "yMax", 0))
        for name, outline in glyphs.items()
    }
    notices = "\n".join(
        dict.fromkeys(
            record.toUnicode()
            for donor in (serif, sans)
            for record in donor["name"].names
            if record.nameID == 0
        )
    )
    notices += "\nCopyright 2026 GenZui project authors."
    fb = FontBuilder(1000, isTTF=True)
    fb.setupGlyphOrder(list(glyphs))
    fb.setupCharacterMap(cmap)
    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=1160, descent=-288)
    fb.setupVerticalMetrics(vmetrics)
    fb.setupVerticalHeader(ascent=500, descent=-500)
    fb.setupNameTable(
        {
            "copyright": notices,
            "familyName": FAMILY,
            "styleName": "Regular",
            "uniqueFontIdentifier": VERSION + ";" + STEM,
            "fullName": FAMILY + " Regular",
            "psName": STEM,
            "version": "Version " + VERSION,
            "typographicFamily": FAMILY,
            "typographicSubfamily": "Regular",
            "description": "Tangut in square-terminal sans strokes. Development version "
            + VERSION
            + ".",
            "licenseDescription": "Licensed under the SIL Open Font License, Version 1.1. See OFL.txt.",
            "licenseInfoURL": "https://openfontlicense.org/open-font-license-official-text/",
        }
    )
    for name_id, text in {
        1: FAMILY_JA,
        4: FAMILY_JA + " Regular",
        16: FAMILY_JA,
    }.items():
        fb.font["name"].setName(text, name_id, 3, 1, 0x411)
    panose = copy.copy(sans["OS/2"].panose)
    panose.bProportion = 9
    fb.setupOS2(
        version=4,
        usWeightClass=400,
        achVendID="NONE",
        fsType=0,
        fsSelection=64,
        sTypoAscender=880,
        sTypoDescender=-120,
        sTypoLineGap=0,
        usWinAscent=1160,
        usWinDescent=288,
        panose=panose,
    )
    fb.setupPost(keepGlyphNames=False, isFixedPitch=0)
    fb.font["head"].fontRevision = float(VERSION)
    fb.font["head"].created = fb.font["head"].modified = EPOCH + 2082844800
    fb.font.recalcTimestamp = False
    fb.font.save(OUT / (STEM + ".ttf"))
    fb.font.flavor = "woff2"
    fb.font.save(OUT / (STEM + ".woff2"))
    methods = {
        "family": FAMILY,
        "version": VERSION,
        "development": True,
        "sample": sample,
        "tangut_characters": len(cps),
        "source_manifest": manifest,
        "geometry_sha256": digest(ROOT / "scripts/tangut_geometry.py"),
        "builder_sha256": digest(Path(__file__)),
        "environment": {
            name: version(name)
            for name in (
                "fonttools",
                "Pillow",
                "aggdraw",
                "numpy",
                "scipy",
                "scikit-image",
                "skia-pathops",
            )
        },
        "glyphs": provenance,
    }
    (OUT / "sources.json").write_text(
        json.dumps(methods, ensure_ascii=False, indent=2) + "\n"
    )
    for family, name in (
        ("NotoSerifTangut", "NotoSerifTangut-OFL.txt"),
        ("NotoSansCJKjp", "NotoSansCJK-OFL.txt"),
    ):
        shutil.copyfile(ROOT / "sources/upstream" / family / "OFL.txt", OUT / name)
    licence = (ROOT / "sources/upstream/NotoSerifTangut/OFL.txt").read_text()
    licence = notices + "\n\n" + licence[licence.index("This Font Software") :]
    (OUT / "OFL.txt").write_text(licence)
    (OUT / "NOTICE.txt").write_text(
        notices
        + "\n\n"
        + "Noto Serif Tangut 2.168: character geometry and repertoire.\n"
        + "https://github.com/notofonts/tangut\n"
        + "Noto Sans CJK JP Regular 2.004: horizontal and vertical stroke outlines.\n"
        + "https://github.com/notofonts/noto-cjk/tree/main/Sans\n"
        + "GenZui: square-terminal curve reconstruction, stroke fitting and spacing.\n"
        + "https://github.com/mkpoli/GenZui\n\n"
        + "All font outlines are distributed under SIL OFL 1.1.\n"
        + "Source URLs, hashes and per-character construction records are in sources.json.\n"
    )
    (OUT / "genzui-sans-tangut.css").write_text(
        '@font-face {\n  font-family: "GenZui Sans Tangut";\n'
        + f'  src: url("{STEM}.woff2") format("woff2");\n'
        + "  font-style: normal;\n  font-weight: 400;\n  font-display: swap;\n"
        + "  unicode-range: U+16FE0, U+17000-18AFF, U+18D00-18DFF;\n}\n"
    )
    serif.close()
    sans.close()
    print("Wrote build/tangut-sans/" + STEM + ".ttf and .woff2", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, choices=range(1, 5), default=1)
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Build the 22-character design specimen only.",
    )
    args = parser.parse_args()
    build(args.workers, args.sample)
