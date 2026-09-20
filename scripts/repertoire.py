"""Audit historical kana against pinned Unicode data and font cmaps."""
import json
from collections import Counter

from fontTools.ttLib import TTFont

from sources import ROOT, verify

FAMILIES = ("NotoSansJP", "NotoSerifJP", "NotoSerifHentaigana")


def font_path(family):
    return ROOT / "sources/upstream" / family / f"{family}[wght].ttf"


def properties(filename):
    result = {}
    for line in (ROOT / "data/unicode" / filename).read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        points, value = (part.strip() for part in line.split(";", 1))
        bounds = [int(p, 16) for p in points.split("..")]
        for cp in range(bounds[0], bounds[-1] + 1):
            result[cp] = value
    return result


def repertoire():
    ages = properties("DerivedAge.txt")
    orientation = properties("VerticalOrientation.txt")
    result = []
    for line in (ROOT / "data/unicode/UnicodeData.txt").read_text().splitlines():
        fields = line.split(";")
        cp, name = int(fields[0], 16), fields[1]
        if 0x1B001 <= cp <= 0x1B11E:
            group = "hentaigana"
        elif cp == 0x1B000 or 0x1B11F <= cp <= 0x1B128:
            group = "historic-kana"
        elif 0x1B130 <= cp <= 0x1B16F:
            group = "small-kana"
        elif cp in (0x309F, 0x30FF):
            group = "bmp-digraph"
        else:
            continue
        result.append({
            "codepoint": f"U+{cp:04X}", "character": chr(cp), "name": name,
            "age": ages[cp], "group": group,
            "decomposition": fields[5], "vertical_orientation": orientation[cp],
        })
    return result


def audit():
    verify()
    chars = repertoire()
    coverage = {}
    for family in FAMILIES:
        with TTFont(font_path(family)) as font:
            cmap = font.getBestCmap()
            coverage[family] = set(cmap)
    for item in chars:
        cp = ord(item["character"])
        item["upstream"] = {name: cp in cmap for name, cmap in coverage.items()}
    new = [item for item in chars if item["age"] == "18.0"]
    report = {
        "unicode_version": "18.0.0", "families": list(FAMILIES),
        "groups": dict(Counter(item["group"] for item in chars)),
        "unicode18": [item["codepoint"] for item in new], "characters": chars,
    }
    out = ROOT / "research/repertoire.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(f"Audited {len(chars)} historical kana; {len(new)} Unicode 18 additions.")
    for item in new:
        print(item["codepoint"], item["name"])
    for name, cmap in coverage.items():
        print(name, sum(ord(item["character"]) in cmap for item in chars), "covered")
    return report


if __name__ == "__main__":
    audit()
