"""Validate GenZui Sans Tangut coverage, outlines, metrics and shaping."""

import json

import numpy as np
import pathops
import uharfbuzz as hb
from PIL import Image, ImageDraw, ImageFont
from fontTools.pens.areaPen import AreaPen
from fontTools.ttLib import TTFont

from sources import verify
from tangut_geometry import groups_for, initialize
from tangut_sans import FAMILY, OUT, ROOT, SANS, SERIF, STEM, VERSION, digest, target


def audit_structure(source, result, cps):
    """Catch whole lost regions; these permissive thresholds are not proofreading."""
    source_glyphs, result_glyphs = source.getGlyphSet(), result.getGlyphSet()
    source_cmap, result_cmap = source.getBestCmap(), result.getBestCmap()
    counts = {"substantial_counters": 0, "substantial_ink_regions": 0}

    def area(path):
        pen = AreaPen(None)
        path.draw(pen)
        return abs(pen.value)

    for cp in cps:
        original, output = pathops.Path(), pathops.Path()
        source_glyphs[source_cmap[cp]].draw(original.getPen())
        result_glyphs[result_cmap[cp]].draw(output.getPen())
        for records, _ in groups_for(cp):
            region = pathops.Path()
            for record in records:
                record.replay(region.getPen())
            original_ink = area(region)
            if original_ink >= 1000:
                counts["substantial_ink_regions"] += 1
                retained = pathops.op(region, output, pathops.PathOp.INTERSECTION)
                assert area(retained) >= original_ink * 0.10, (
                    f"Lost source ink region: U+{cp:X}"
                )
            for record in records[1:]:
                hole = pathops.Path()
                record.replay(hole.getPen())
                # Other source contours can overlap a nominal counter.
                void = pathops.op(hole, original, pathops.PathOp.DIFFERENCE)
                original_void = area(void)
                if original_void >= 2000:
                    counts["substantial_counters"] += 1
                    retained = pathops.op(void, output, pathops.PathOp.DIFFERENCE)
                    assert area(retained) >= original_void * 0.10, (
                        f"Closed source counter: U+{cp:X}"
                    )
    return counts


def check():
    verify(manifest="tangut-manifest.json")
    data = json.loads((OUT / "sources.json").read_text())
    assert data["version"] == VERSION and not data["sample"], (
        "A full build is required."
    )
    assert data["geometry_sha256"] == digest(ROOT / "scripts/tangut_geometry.py"), (
        "Rebuild after geometry changes."
    )
    assert data["builder_sha256"] == digest(ROOT / "scripts/tangut_sans.py"), (
        "Rebuild after builder changes."
    )
    source = TTFont(SERIF)
    cps = target(source)
    source.close()
    expected = set(cps) | {0x20, 0xA0}
    fonts = {ext: TTFont(OUT / (STEM + "." + ext)) for ext in ("ttf", "woff2")}
    binaries = {}
    for ext, font in fonts.items():
        assert set(font.getBestCmap()) == expected
        assert font["head"].unitsPerEm == 1000
        assert font["name"].getDebugName(1) == FAMILY
        assert font["name"].getDebugName(2) == "Regular"
        assert font["name"].getDebugName(6) == STEM
        assert "Open Font License" in font["name"].getDebugName(13)
        assert font["OS/2"].fsType == 0 and font["OS/2"].usWeightClass == 400
        glyphset = font.getGlyphSet()
        for name in font.getGlyphOrder():
            outline = font["glyf"][name]
            if outline.numberOfContours:
                assert font["vmtx"][name][1] + outline.yMax == 880, (
                    f"Wrong vertical origin: {name}"
                )
        for cp in cps:
            name = font.getBestCmap()[cp]
            outline = font["glyf"][name]
            assert outline.numberOfContours > 0, f"Empty U+{cp:05X}"
            assert (
                -font["OS/2"].usWinDescent
                <= outline.yMin
                < outline.yMax
                <= font["OS/2"].usWinAscent
            )
            assert -100 <= outline.xMin < outline.xMax <= 1100, f"Overwide U+{cp:05X}"
            assert font["hmtx"][name] == (1000, outline.xMin)
            assert font["vmtx"][name] == (1000, 880 - outline.yMax)
            area = AreaPen(glyphset)
            glyphset[name].draw(area)
            assert area.value < -1, f"Incorrect winding or zero ink: U+{cp:05X}"
        binaries[ext] = {
            cp: font["glyf"][font.getBestCmap()[cp]].compile(font["glyf"]) for cp in cps
        }
    assert binaries["ttf"] == binaries["woff2"], "TTF and WOFF2 outlines differ."
    ttf = fonts["ttf"]
    # This short diagonal is part of the crossing, rather than a serif spur.
    crossed = pathops.Path()
    ttf.getGlyphSet()[ttf.getBestCmap()[0x1888C]].draw(crossed.getPen())
    assert crossed.contains((310, 270)), (
        "The middle falling stroke lost its left continuation."
    )
    assert data["glyphs"]["U+18802"]["recovered_stems"] == 0, (
        "A falling stroke acquired a vertical peg."
    )
    assert data["glyphs"]["U+1888C"]["recovered_stems"] == 0, (
        "A crossing acquired a vertical peg."
    )
    # Three upright stems must survive above the shared bar in the dense U+177D5 header.
    image = Image.new("L", (1100, 1100))
    face = ImageFont.truetype(str(OUT / (STEM + ".ttf")), 1000)
    ImageDraw.Draw(image).text(
        (40, 920), chr(0x177D5), font=face, fill=255, anchor="ls"
    )
    row = np.asarray(image)[920 - 780, 40:840] > 127
    assert int((np.diff(np.r_[False, row, False].astype(int)) == 1).sum()) == 3
    initialize(SERIF, SANS)
    for cp in (0x173AC, 0x17CB6, 0x17EEB, 0x1807A):
        for records, _ in groups_for(cp):
            boundary = pathops.Path()
            records[0].replay(boundary.getPen())
            for hole in records[1:]:
                points = [
                    args[-1] for op, args in hole.value if args and args[-1] is not None
                ]
                assert all(boundary.contains(point) for point in points), (
                    f"Wrong hole parent: U+{cp:X}"
                )
    # A bar joins offset uprights in this component. Recovery must not bridge
    # their differing x positions and close the left grid counter.
    for cp, point in ((0x18A46, (413, 535)), (0x17837, (566, 535))):
        result = pathops.Path()
        ttf.getGlyphSet()[ttf.getBestCmap()[cp]].draw(result.getPen())
        assert not result.contains(point), f"Closed grid counter: U+{cp:X}"
        holes = []
        for records, _ in groups_for(cp):
            for rec in records[1:]:
                hole = pathops.Path()
                rec.replay(hole.getPen())
                if hole.contains(point):
                    holes.append(hole)
        assert len(holes) == 1
        remaining = pathops.op(holes[0], result, pathops.PathOp.DIFFERENCE)
        assert abs(remaining.area) > abs(holes[0].area) * 0.5
    with TTFont(SERIF) as source:
        structure_counts = audit_structure(source, ttf, cps)
    raw = (OUT / (STEM + ".ttf")).read_bytes()
    hbfont = hb.Font(hb.Face(raw))
    hb.ot_font_set_funcs(hbfont)
    hbfont.scale = (1000, 1000)
    for gid, name in enumerate(ttf.getGlyphOrder()):
        assert hbfont.get_glyph_v_origin(gid) == (ttf["hmtx"][name][0] // 2, 880)
    text = "".join(map(chr, cps))
    for direction in ("ltr", "ttb"):
        buffer = hb.Buffer()
        buffer.add_str(text)
        buffer.guess_segment_properties()
        buffer.direction = direction
        hb.shape(hbfont, buffer)
        assert len(buffer.glyph_infos) == len(cps)
        assert all(g.codepoint != 0 for g in buffer.glyph_infos)
        assert all(
            (p.x_advance, p.y_advance)
            == ((1000, 0) if direction == "ltr" else (0, -1000))
            for p in buffer.glyph_positions
        )
    report = {
        "status": "passed",
        "version": VERSION,
        "family": FAMILY,
        "tangut_characters": len(cps),
        "ideographs": sum(
            0x17000 <= cp <= 0x187FF or 0x18D00 <= cp <= 0x18D7F for cp in cps
        ),
        "components": sum(0x18800 <= cp <= 0x18AFF for cp in cps),
        "iteration_mark": 0x16FE0 in cps,
        "structure_audit": structure_counts,
        "encoded_characters": len(expected),
        "ttf_sha256": digest(OUT / (STEM + ".ttf")),
        "woff2_sha256": digest(OUT / (STEM + ".woff2")),
        "checks": [
            "exact source repertoire",
            "nonempty outlines and clockwise winding",
            "line metrics and full-width advances",
            "TTF/WOFF2 parity",
            "horizontal and vertical HarfBuzz shaping",
            "counter containment",
            "crossing continuation",
            "diagonal-terminal pegs",
            "three-stem header",
            "offset-stem grid counters",
            "whole-repertoire substantial ink and counter retention",
        ],
    }
    (OUT / "checks.json").write_text(json.dumps(report, indent=2) + "\n")
    for font in fonts.values():
        font.close()
    print(
        f"Passed: {len(cps):,} Tangut characters, outline parity, metrics, shaping and geometry regressions."
    )
    return report


if __name__ == "__main__":
    check()
