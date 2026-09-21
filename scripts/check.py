"""Check source integrity, historical coverage and the generated design proof."""
from io import BytesIO
import json

import uharfbuzz as hb
from fontTools.ttLib import TTFont

from proof import OUT, SAMPLES
from repertoire import repertoire
from sources import ROOT, verify


def check():
    verify()
    chars = repertoire()
    assert len(chars) == 329
    assert sum(c["group"] == "hentaigana" for c in chars) == 286
    expected_new = {0x1B123, 0x1B124, 0x1B125, 0x1B126, 0x1B127, 0x1B128, 0x1B168}
    assert {ord(c["character"]) for c in chars if c["age"] == "18.0"} == expected_new
    # Scan the complete UCD independently: additions outside the chosen blocks
    # must not disappear from a supposedly exhaustive Unicode 18 kana inventory.
    from repertoire import properties
    ages = properties("DerivedAge.txt")
    found = set()
    for line in (ROOT / "data/unicode/UnicodeData.txt").read_text().splitlines():
        fields = line.split(";")
        cp = int(fields[0], 16)
        if ages[cp] == "18.0" and any(s in fields[1] for s in ("HIRAGANA", "KATAKANA", "HENTAIGANA")):
            found.add(cp)
    assert found == expected_new
    audit = json.loads((ROOT / "research/repertoire.json").read_text())
    assert len(audit["characters"]) == len(chars)
    assert all(not any(c["upstream"].values()) for c in audit["characters"] if c["age"] == "18.0")

    outlines = {}
    for stem in ("SerifReference", "SansStudyA", "SansStudyB"):
        originals = None
        for suffix in ("ttf", "woff2"):
            font = TTFont(OUT / f"{stem}.{suffix}")
            cm = font.getBestCmap()
            assert {cp for cp, _ in SAMPLES} <= set(cm)
            assert not expected_new.intersection(cm), "Proof must not advertise undrawn glyphs"
            assert "Noto" not in font["name"].getDebugName(1)
            assert "Open Font License" in font["name"].getDebugName(13)
            assert "fvar" not in font and "gvar" not in font
            font.flavor = None
            data = BytesIO()
            font.save(data)
            hb_font = hb.Font(hb.Face(data.getvalue()))
            hb_font.scale = (1000, 1000)
            order = font.getGlyphOrder()
            for cp, _ in SAMPLES:
                name = cm[cp]
                glyph = font["glyf"][name]
                assert glyph.numberOfContours > 0
                assert -120 <= glyph.xMin < glyph.xMax <= 1120, (stem, hex(cp), "width")
                assert -200 <= glyph.yMin < glyph.yMax <= 1000, (stem, hex(cp), "height")
                assert font["hmtx"][name] == (1000, glyph.xMin)
                assert font["vmtx"][name][0] == 1000
                for direction in ("ltr", "ttb"):
                    buf = hb.Buffer()
                    buf.add_str(chr(cp))
                    buf.guess_segment_properties()
                    buf.direction = direction
                    hb.shape(hb_font, buf)
                    assert len(buf.glyph_infos) == 1
                    assert order[buf.glyph_infos[0].codepoint] != ".notdef"
                    pos = buf.glyph_positions[0]
                    assert (pos.x_advance, pos.y_advance) == ((1000, 0) if direction == "ltr" else (0, -1000))
            packed = {cp: font["glyf"][cm[cp]].compile(font["glyf"]) for cp, _ in SAMPLES}
            if originals is None:
                originals = packed
            else:
                assert packed == originals, "WOFF2 changes an outline"
        outlines[stem] = originals
    for cp, _ in SAMPLES:
        assert len({outlines[stem][cp] for stem in outlines}) == 3
    page = (OUT / "index.html").read_text()
    assert page.count("data:font/woff2;base64,") == 4
    assert page.count("<section>") == len(SAMPLES)
    assert "/home/" not in page
    assert "SIL OPEN FONT LICENSE" in page
    print("Checks passed: pinned sources, 329-character audit, all seven Unicode 18 additions,")
    print("16 distinct study forms, TTF/WOFF2 equivalence, HarfBuzz horizontal/vertical shaping, embedded licences.")


if __name__ == "__main__":
    check()
