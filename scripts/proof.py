"""Build two experimental sans treatments for a representative hentaigana set.

These are design proofs, not finished fonts. The source outlines are from
Noto Serif Hentaigana; the surrounding kana are Noto Sans JP Regular.
"""
import base64
import copy
import html
import io
import json
from pathlib import Path

import numpy as np
import pathops
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import gaussian_filter1d
from skimage.measure import approximate_polygon
from skimage.morphology import skeletonize

from fontTools import subset
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.roundingPen import RoundingPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont, newTable
from fontTools.varLib.instancer import instantiateVariableFont

from repertoire import font_path
from sources import ROOT, verify

SAMPLES = [
    (0x1B001, "え"), (0x1B002, "あ"), (0x1B003, "あ"), (0x1B006, "い"),
    (0x1B00B, "う"), (0x1B017, "か"), (0x1B032, "け"), (0x1B03C, "さ"),
    (0x1B044, "し"), (0x1B052, "せ"), (0x1B069, "つ"), (0x1B092, "ね"),
    (0x1B0B0, "ふ"), (0x1B0C2, "ま"), (0x1B0F1, "り"), (0x1B10D, "ゐ"),
]
OUT = ROOT / "build/proof"


def instance(family, weight, codepoints):
    font = TTFont(font_path(family), recalcTimestamp=False)
    options = subset.Options()
    options.recalc_timestamp = False
    options.name_IDs = ["*"]
    options.name_legacy = True
    options.name_languages = ["*"]
    sub = subset.Subsetter(options=options)
    sub.populate(unicodes=codepoints)
    sub.subset(font)
    instantiateVariableFont(font, {"wght": weight}, inplace=True)
    return font


def rename(font, family):
    # Clear localized and variable-family names together, so no menu advertises
    # the derivative as an upstream Noto release.
    for nid in (1, 2, 3, 4, 5, 6, 16, 17, 18, 21, 22, 25):
        font["name"].removeNames(nameID=nid)
    for nid, value in {
        1: family, 2: "Regular", 3: f"0.001;{family.replace(' ', '')}-Regular",
        4: f"{family} Regular", 5: "Version 0.001",
        6: f"{family.replace(' ', '')}-Regular", 16: family, 17: "Regular",
    }.items():
        font["name"].setName(value, nid, 3, 1, 0x409)
    for tag in ("STAT", "DSIG"):
        if tag in font:
            del font[tag]
    font["head"].fontRevision = 0.001
    font["OS/2"].usWeightClass = 400


def glyph_from_path(path):
    pen = TTGlyphPen(None)
    path.draw(Cu2QuPen(pen, max_err=0.4, reverse_direction=True))
    return pen.glyph()


def expand_outline(glyph, glyphset, amount=21):
    shape = pathops.Path()
    glyph.draw(shape.getPen(), glyphset)
    edge = pathops.Path(shape)
    edge.stroke(amount * 2, pathops.LineCap.ROUND_CAP, pathops.LineJoin.ROUND_JOIN, 4)
    edge.convertConicsToQuads(0.1)
    return glyph_from_path(pathops.op(shape, edge, pathops.PathOp.UNION))


def skeleton_paths(mask):
    """Trace a pruned one-pixel skeleton into polylines in font coordinates."""
    pixels = set(map(tuple, np.argwhere(skeletonize(mask))))

    def neighbors(p):
        y, x = p
        result = []
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                q = (y + dy, x + dx)
                if (dx or dy) and q in pixels:
                    # Avoid triangular edges around a right-angle pixel corner.
                    if dx and dy and ((y, x + dx) in pixels or (y + dy, x) in pixels):
                        continue
                    result.append(q)
        return result

    # Remove short terminal spurs introduced by serif details; preserve detached
    # short strokes. This is deliberately limited to the review sample set.
    for _ in range(3):
        remove = set()
        for start in sorted(pixels):
            if len(neighbors(start)) != 1:
                continue
            chain, previous, current = [start], None, start
            for _ in range(38):
                following = [p for p in neighbors(current) if p != previous]
                if len(following) != 1:
                    if len(following) > 1:
                        remove.update(chain[:-1])
                    break
                previous, current = current, following[0]
                chain.append(current)
        if not remove:
            break
        pixels.difference_update(remove)

    adjacency = {p: neighbors(p) for p in sorted(pixels)}
    visited, paths = set(), []

    def trace(start, nxt):
        points = [start]
        previous, current = start, nxt
        visited.add(frozenset((start, nxt)))
        while True:
            points.append(current)
            if len(adjacency[current]) != 2:
                break
            following = next(p for p in adjacency[current] if p != previous)
            edge = frozenset((current, following))
            if edge in visited:
                break
            visited.add(edge)
            previous, current = current, following
        if len(points) > 1:
            # Source rendering has its baseline at y=1000 and origin at x=100.
            paths.append(np.array([(x - 100, 1000 - y) for y, x in points], dtype=float))

    for start in adjacency:
        if len(adjacency[start]) == 2:
            continue
        for nxt in adjacency[start]:
            if frozenset((start, nxt)) not in visited:
                trace(start, nxt)
    for start in adjacency:
        for nxt in adjacency[start]:
            if frozenset((start, nxt)) not in visited:
                trace(start, nxt)
    return paths


def monoline_glyph(paths, width=64):
    shape = pathops.Path()
    for points in paths:
        if np.linalg.norm(np.diff(points, axis=0), axis=1).sum() < 3:
            continue
        if len(points) > 6:
            smoothed = gaussian_filter1d(points, sigma=2, axis=0, mode="nearest")
            smoothed[0], smoothed[-1] = points[0], points[-1]
            points = approximate_polygon(smoothed, tolerance=1.6)
        shape.moveTo(*points[0])
        for i in range(len(points) - 1):
            a, b = points[i], points[i + 1]
            before, after = points[max(0, i - 1)], points[min(len(points) - 1, i + 2)]
            c1, c2 = a + (b - before) / 6, b - (after - a) / 6
            shape.cubicTo(*c1, *c2, *b)
        if len(points) > 3 and np.linalg.norm(points[0] - points[-1]) < 2:
            shape.close()
    shape.stroke(width, pathops.LineCap.BUTT_CAP, pathops.LineJoin.ROUND_JOIN, 4)
    shape.convertConicsToQuads(0.1)
    try:
        shape.simplify()
    except pathops.PathOpsError:
        # Skia can fail on nearly coincident floating-point control points.
        # The final TrueType coordinates are integers in either case.
        rounded = pathops.Path()
        shape.draw(RoundingPen(rounded.getPen()))
        rounded.simplify()
        shape = rounded
    return glyph_from_path(shape)


def save(font, name, reference):
    rename(font, name)
    font["hhea"].ascent = reference["hhea"].ascent
    font["hhea"].descent = reference["hhea"].descent
    font["hhea"].lineGap = reference["hhea"].lineGap
    for attr in ("sTypoAscender", "sTypoDescender", "sTypoLineGap", "usWinAscent", "usWinDescent"):
        setattr(font["OS/2"], attr, getattr(reference["OS/2"], attr))
    # Hentaigana's upstream font has no vertical metrics; match Noto JP's origin.
    if "vmtx" not in font:
        font["vhea"] = copy.deepcopy(reference["vhea"])
        font["vmtx"] = newTable("vmtx")
        font["vmtx"].metrics = {}
        classes = font["GDEF"].table.GlyphClassDef.classDefs if "GDEF" in font else {}
        for g in font.getGlyphOrder():
            glyph = font["glyf"][g]
            glyph.recalcBounds(font["glyf"])
            font["vmtx"][g] = (0 if classes.get(g) == 3 else 1000, 880 - getattr(glyph, "yMax", 0))
    stem = name.replace(" ", "")
    font.flavor = None
    font.save(OUT / f"{stem}.ttf")
    font.flavor = "woff2"
    font.save(OUT / f"{stem}.woff2")


def page():
    css = []
    for family in ("ContextSans", "SerifReference", "SansStudyA", "SansStudyB"):
        data = base64.b64encode((OUT / f"{family}.woff2").read_bytes()).decode()
        css.append(f"@font-face{{font-family:{family};src:url(data:font/woff2;base64,{data}) format('woff2')}}")
    rows = []
    for cp, modern in SAMPLES:
        char = chr(cp)
        cells = "".join(
            f'<div class="cell {family}"><div class="large">{char}</div>'
            f'<div class="context">かな{char}かな</div></div>'
            for family in ("SerifReference", "SansStudyA", "SansStudyB")
        )
        rows.append(f'<section><div class="label">U+{cp:05X}<span class="modern">{modern}</span></div>{cells}</section>')
    licenses = []
    for family in ("NotoSansJP", "NotoSerifHentaigana"):
        text = (ROOT / "sources/upstream" / family / "OFL.txt").read_text()
        licenses.append(f'<h3>{family}</h3><pre>{html.escape(text)}</pre>')
    source = '''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Hentaigana · Sans studies</title><style>FONT_CSS
:root{color:#292824;background:#f7f5ef;font:15px/1.6 system-ui,sans-serif}
*{box-sizing:border-box}body{max-width:1160px;margin:0 auto;padding:40px 28px}
h1{font-size:32px;font-weight:550;letter-spacing:-.025em;margin:0 0 12px}
p{max-width:780px}.intro{color:#5b5b54}header{margin-bottom:32px}
.controls{display:flex;gap:24px;align-items:center;margin:24px 0;flex-wrap:wrap}
button{font:inherit;border:1px solid #aaa79e;background:transparent;border-radius:4px;padding:5px 12px;cursor:pointer}
section,.head{display:grid;grid-template-columns:115px repeat(3,1fr);gap:12px}
.head{position:sticky;top:0;background:#f7f5ef;padding:14px 0;border-bottom:1px solid #aaa79e;z-index:1}
section{border-bottom:1px solid #d8d5cb;padding:18px 0}
.label{font-size:12px;color:#6a685f;padding-top:12px;font-variant-numeric:tabular-nums}
.modern{display:block;font:44px ContextSans;margin-top:4px;color:#292824}
.cell{text-align:center;min-width:0}.large{font-size:88px;line-height:1.5}
.context{font-size:var(--size,28px);white-space:nowrap;line-height:1.8}
.SerifReference{font-family:SerifReference,ContextSans}.SansStudyA{font-family:SansStudyA,ContextSans}.SansStudyB{font-family:SansStudyB,ContextSans}
body.vertical .context{writing-mode:vertical-rl;text-orientation:upright;margin:auto;height:10em}
footer{margin-top:40px;color:#68665d;font-size:13px}a{color:inherit}pre{white-space:pre-wrap;font-size:11px}
@media(max-width:700px){body{padding:20px 12px}section,.head{grid-template-columns:65px repeat(3,1fr);gap:4px}.large{font-size:58px}.context{font-size:18px}.label{font-size:10px}}
</style><header><h1>Hentaigana · Sans studies</h1>
<p class="intro">Sixteen forms beside Noto Sans JP Regular. The serif reference is Noto Serif Hentaigana Regular. A and B are experimental sans treatments; neither is a finished typeface.</p>
<p>Compare stroke weight, open spaces and terminals at reading size. Use the large forms to inspect the construction. The ordinary kana at the left gives the reading.</p>
<div class="controls"><label>Text size <input id="size" type="range" min="20" max="44" value="28"> <output id="value">28 px</output></label><button id="direction" type="button" aria-pressed="false">Vertical text</button></div>
</header><div class="head"><div>Reading</div><div>Serif reference</div><div>Sans A</div><div>Sans B</div></div>
ROWS
<footer><p>Outline sources: <a href="https://github.com/notofonts/hentaigana">Noto Serif Hentaigana</a>. Context: <a href="https://github.com/notofonts/noto-cjk">Noto Sans JP</a>. Fonts and derived outlines are licensed under SIL OFL 1.1.</p>
<details><summary>Font licences</summary>LICENSES</details></footer>
<script>const s=document.getElementById('size');s.addEventListener('input',()=>{document.documentElement.style.setProperty('--size',s.value+'px');document.getElementById('value').textContent=s.value+' px'});document.getElementById('direction').addEventListener('click',e=>{let v=document.body.classList.toggle('vertical');e.currentTarget.setAttribute('aria-pressed',String(v));e.currentTarget.textContent=v?'Horizontal text':'Vertical text'});</script></html>'''
    (OUT / "index.html").write_text(source.replace("FONT_CSS", "\n".join(css)).replace("ROWS", "\n".join(rows)).replace("LICENSES", "\n".join(licenses)))


def preview():
    image = Image.new("RGB", (1280, 1080), "#f7f5ef")
    draw = ImageDraw.Draw(image)
    font_paths = [OUT / (s + ".ttf") for s in ("SerifReference", "SansStudyA", "SansStudyB")]
    faces = [ImageFont.truetype(str(p), 100) for p in font_paths]
    context = ImageFont.truetype(str(OUT / "ContextSans.ttf"), 32)
    label = ImageFont.truetype(str(OUT / "ContextSans.ttf"), 20)
    for j, title in enumerate(("Serif reference", "Sans A", "Sans B")):
        draw.text((35 + j * 420, 24), title, font=label, fill="#292824")
    for i, (cp, modern) in enumerate(SAMPLES[:8]):
        y = 95 + i * 120
        for j, face in enumerate(faces):
            x = 35 + j * 420
            draw.text((x, y), modern, font=context, fill="#888880")
            draw.text((x + 62, y - 24), chr(cp), font=face, fill="#22221f")
            draw.text((x + 186, y), "かな", font=context, fill="#22221f")
            draw.text((x + 275, y), f"{cp:05X}", font=label, fill="#888880")
    image.save(OUT / "preview.png")


def main():
    verify()
    OUT.mkdir(parents=True, exist_ok=True)
    cps = [cp for cp, _ in SAMPLES]
    context = instance("NotoSansJP", 400, [*range(0x20, 0x7F), *range(0x3000, 0x3100)])
    serif = instance("NotoSerifHentaigana", 400, cps)
    thin = instance("NotoSerifHentaigana", 200, cps)
    raw = io.BytesIO()
    thin.save(raw)
    rasterfont = ImageFont.truetype(io.BytesIO(raw.getvalue()), 1000)
    a, b = copy.deepcopy(thin), copy.deepcopy(thin)
    cmap = thin.getBestCmap()
    # GPOS anchors and mark alternates from the serif design are unsuitable for
    # these experimental outlines. The proof contains unmarked forms only.
    for font in (a, b):
        for table in ("GPOS", "GSUB"):
            if table in font:
                del font[table]
    for cp in cps:
        name = cmap[cp]
        a["glyf"][name] = expand_outline(thin["glyf"][name], thin["glyf"])
        mask = Image.new("L", (1200, 1250))
        ImageDraw.Draw(mask).text((100, 1000), chr(cp), font=rasterfont, anchor="ls", fill=255)
        paths = skeleton_paths(np.array(mask) > 127)
        if not paths:
            raise ValueError(f"Empty skeleton for U+{cp:05X}")
        b["glyf"][name] = monoline_glyph(paths)
        for font in (a, b):
            glyph = font["glyf"][name]
            glyph.recalcBounds(font["glyf"])
            font["hmtx"][name] = (1000, glyph.xMin)
        print(f"Drew proof U+{cp:05X}", flush=True)
    for font, name in ((serif, "Serif Reference"), (a, "Sans Study A"), (b, "Sans Study B")):
        save(font, name, context)
    save(context, "Context Sans", context)
    (OUT / "sources.json").write_text(json.dumps({
        "samples": [f"U+{cp:05X}" for cp in cps],
        "reference": "Noto Serif Hentaigana wght=400",
        "context": "Noto Sans JP wght=400",
        "A": "Noto Serif Hentaigana wght=200, outline expansion 21 units",
        "B": "Noto Serif Hentaigana wght=200, pruned skeleton, 64-unit monoline stroke with flat terminals",
        "status": "Experimental proofs; no claim of completed sans designs",
    }, indent=2) + "\n")
    page()
    preview()
    print("Built build/proof/index.html and preview.png")


if __name__ == "__main__":
    main()
