"""Build the local Okinawan type comparison from the current font.

Funatsu's chart is the shape and sizing reference. It embeds his own letters as
an end-user-defined TrueType font, which `mutool trace` reports together with
the position and size of every character on the page; each letter is cropped
from a high-resolution rendering of that page, so what is compared is the
letter as he set it, beside the Mincho around it, rather than a re-tracing.

Optional reference fonts are read from a local directory. They are only copied
into the ignored study output; they are not packaged with GenZui or its site.
"""
import argparse
import html
import json
import re
import shutil
import subprocess
import time
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from fontTools import subset
from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont

from okinawan import ENTRIES
from okinawan_drawings import BASES, RAISED
from sources import ROOT

OUT = ROOT/'build/okinawan'
STEM = 'GenZuiSerif-Regular'

# Funatsu's chart, by the glyph id the PDF uses for each letter.
CHART_GLYPHS = {2: 'tu', 3: 'du', 4: 'ti', 5: 'di', 6: 'kwa', 7: 'gwa', 8: 'kwi', 9: 'gwi',
                10: 'kwe', 11: 'gwe', 18: 'hwa', 19: 'hwi', 20: 'hwe', 21: "'ya", 22: "'yu",
                23: "'yo", 24: "'wa", 25: "'wi", 26: "'we", 27: "'n", 34: 'yi', 35: 'wu',
                36: 'ye', 40: 'si', 41: 'zi', 42: 'tsi', 43: 'dzi'}
CHART_DPI = 600
CHART_PAGE = 842        # A4 height in points, for the top-down crop
CHART_BODY_PT = 10.5    # the chart's body size; its letters are set at the same size


def code_of(entry):
    return int((entry.get('legacy') or entry['output'])[0], 16)


def page_layout(pdf):
    """Every character on the chart's page, with its face, size and position."""
    trace = subprocess.run(['mutool', 'trace', str(pdf)], check=True, capture_output=True, text=True).stdout
    lines = {}
    for span in re.finditer(r'<span font="([^"]+)"[^>]*trm="([0-9.]+) 0 0 [0-9.]+">(.*?)</span>', trace, re.S):
        face, size, body = span.groups()
        for glyph in re.finditer(r'<g unicode="([^"]*)" glyph="([0-9]+)" x="([0-9.]+)" y="([0-9.]+)"', body):
            ch, gid = glyph.group(1), int(glyph.group(2))
            x, y = float(glyph.group(3)), float(glyph.group(4))
            lines.setdefault(round(y, 1), []).append(dict(face=face, ch=ch, gid=gid, x=x, y=y, size=float(size)))
    return lines


def headwords(lines):
    """The leftmost occurrence of each letter is its entry in the table."""
    found = {}
    for y, items in lines.items():
        for item in sorted(items, key=lambda i: i['x']):
            if item['face'].startswith('AGMDAD+EUDC') and item['gid'] in CHART_GLYPHS:
                key = item['gid']
                if key not in found or item['x'] < found[key]['x']:
                    found[key] = dict(item, following=[])
    for y, items in lines.items():
        for item in sorted(items, key=lambda i: i['x']):
            for head in found.values():
                if head['y'] == item['y'] and item is not head and item['x'] > head['x']:
                    head['following'].append(item)
    for head in found.values():
        head['following'].sort(key=lambda i: i['x'])
    return found


def render_page(pdf):
    tmp = Path(tempfile.mkdtemp())
    subprocess.run(['pdftoppm', '-r', str(CHART_DPI), '-png', '-f', '1', '-l', '1', str(pdf),
                    str(tmp/'page')], check=True, capture_output=True)
    return Image.open(next(tmp.glob('page*.png'))).convert('RGB')


def chart_crops(pdf, out):
    """Each letter alone, for the cards' reference column."""
    out.mkdir(parents=True, exist_ok=True)
    heads = headwords(page_layout(pdf))
    page = render_page(pdf)
    scale = CHART_DPI / 72
    em = CHART_BODY_PT * scale
    for gid, head in heads.items():
        x, y = head['x'], head['y']
        box = ((x - .12 * CHART_BODY_PT) * scale, (CHART_PAGE - y - 1.0 * CHART_BODY_PT) * scale,
               (x + 1.12 * CHART_BODY_PT) * scale, (CHART_PAGE - y + .30 * CHART_BODY_PT) * scale)
        page.crop(tuple(round(v) for v in box)).save(out/(CHART_GLYPHS[gid].replace("'", 'glottal-')+'.png'))
    return sorted(CHART_GLYPHS[gid] for gid in heads)


def chart_typesetting(pdf, out, font):
    """Each letter with the words that follow it in the chart, at the printed size.

    The table sets a headword as `letter [romaji]` and then again at the start
    of every example, so the run is taken from the occurrence that is followed
    by kana rather than by the romaji label. Both strips are one em tall in
    pixels, which is the size the chart itself uses for the letter and for the
    Mincho around it.
    """
    out.mkdir(parents=True, exist_ok=True)
    heads = headwords(page_layout(pdf))
    page = render_page(pdf)
    scale = CHART_DPI / 72
    em = CHART_BODY_PT * scale
    # A voiced letter is its base followed by U+3099; the font composes the pair.
    letters = {e['id']: ''.join(chr(int(c, 16)) for c in e['output']) for e in ENTRIES}
    runs = []
    for gid, head in sorted(heads.items(), key=lambda kv: (-kv[1]['y'], kv[1]['x'])):
        label = CHART_GLYPHS[gid]
        if label not in letters:
            continue
        # The example run starts at the occurrence whose next character is
        # kana; the headword's own next character is its romaji label.
        def is_word(ch):
            return ('\u3000' <= ch <= 'ヿ') or ('\u4e00' <= ch <= '鿿') or ch in '（）、'

        run = None
        for start_at in [head] + [i for i in head['following'] if i['gid'] == gid]:
            after = [i for i in head['following'] if i['x'] > start_at['x']]
            if not after or not is_word(after[0]['ch']):
                continue
            words = []
            for item in after:
                if item['gid'] == gid and words:
                    break
                if not is_word(item['ch']):
                    if words:
                        break
                    continue
                words.append(item)
            if words:
                run = (start_at, words[:5])
                break
        if not run:
            continue
        start_at, words = run
        text = letters[label] + ''.join(w['ch'] for w in words)
        x0 = (start_at['x'] - .10 * CHART_BODY_PT) * scale
        x1 = (words[-1]['x'] + words[-1]['size'] * 1.04) * scale
        y0 = (CHART_PAGE - start_at['y'] - 1.02 * CHART_BODY_PT) * scale
        y1 = (CHART_PAGE - start_at['y'] + .34 * CHART_BODY_PT) * scale
        width, height = round(x1 - x0), round(y1 - y0)
        page.crop((round(x0), round(y0), round(x0) + width, round(y0) + height)).save(out/f'chart-{label}.png')
        strip = Image.new('RGB', (width, height), 'white')
        # The crop's top is 1.02 em above the printed baseline; anchor the
        # same text on that baseline so the two strips share a scale.
        ImageDraw.Draw(strip).text((round(.10 * em), round(1.02 * em)), text, anchor='ls',
                                   font=ImageFont.truetype(str(font), round(em), layout_engine=ImageFont.Layout.RAQM), fill='#15291f')
        strip.save(out/f'genzui-{label}.png')
        runs.append(dict(id=label, text=''.join(w['ch'] for w in words)))
    return runs


def ink_boxes(pdf, font_path):
    """Ink box of each letter as a fraction of the em: the chart's, ours, Noto's."""
    codes = {e['id']: e for e in ENTRIES}
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(['mutool', 'extract', str(pdf)], cwd=tmp, check=True, capture_output=True)
        face = TTFont(str(next(Path(tmp).glob('font-0040.ttf'))))
        glyphs, order = face.getGlyphSet(), face.getGlyphOrder()
        upm = face['head'].unitsPerEm
        built = TTFont(str(font_path))
        cmap, bset = built.getBestCmap(), built.getGlyphSet()
        rows = []
        for gid, label in CHART_GLYPHS.items():
            # Voiced forms are a base plus dakuten and share its size, and YI
            # and YE are Noto's own composition, so the drawings are the
            # single-code-point letters.
            if label not in codes or len(codes[label]['output']) != 1:
                continue
            pen = BoundsPen(glyphs)
            glyphs[order[gid]].draw(pen)
            if not pen.bounds:
                continue
            box = lambda pen, d: [round(v / d, 2) for v in pen.bounds]
            chart = box(pen, upm)
            entry = codes[label]
            pen = BoundsPen(bset)
            bset[cmap[int(entry['output'][0], 16)]].draw(pen)
            mine = box(pen, 1000)
            base = BASES.get(int(entry['output'][0], 16)) or entry.get('kana') or 'と'
            pen = BoundsPen(bset)
            bset[cmap[ord(base[0])]].draw(pen)
            plain = box(pen, 1000)
            rows.append(dict(id=label, label=entry['label'], base=base[0],
                             chart=chart, genzui=mine, noto=plain))
        return rows


def fmt(box):
    """Ink box as height × width in em."""
    return f'{box[3] - box[1]:.2f} × {box[2] - box[0]:.2f}'


def build(reference_dir=None):
    OUT.mkdir(parents=True, exist_ok=True)
    fonts = OUT/'fonts'
    fonts.mkdir(exist_ok=True)
    home = OUT/'home'
    if not home.exists() and not home.is_symlink():
        home.symlink_to(Path('../site'), target_is_directory=True)
    shutil.copyfile(ROOT/'build/serif'/f'{STEM}.woff2', fonts/'genzui.woff2')
    shutil.copyfile(ROOT/'releases'/f'v{0.114}'/f'{STEM}.woff2', fonts/'previous.woff2')
    references = {}
    runs, boxes = [], []
    if reference_dir:
        for key, filename in [('fk', 'FK-Okinawa-reference.ttf'), ('nishiki', 'nishiki-teki.ttf'),
                              ('mgen', 'mgenkanaplus.woff2'), ('xim', 'Xim-Sans-Handwritten.ttf')]:
            source = reference_dir/filename
            if not source.is_file():
                continue
            font = TTFont(source, recalcTimestamp=False)
            covered = set(font.getBestCmap())
            points = set(range(0xF450, 0xF46B)) | {code_of(e) for e in ENTRIES}
            options = subset.Options()
            options.recalc_timestamp = False
            sub = subset.Subsetter(options=options)
            sub.populate(unicodes=points & covered)
            sub.subset(font)
            font.flavor = 'woff2'
            font.save(fonts/(key+'.woff2'))
            references[key] = sorted(points & covered)
        chart = reference_dir/'funatsu-chart.pdf'
        if chart.is_file():
            references['chart'] = chart_crops(chart, OUT/'chart')
            runs = chart_typesetting(chart, OUT/'runs', ROOT/'build/serif'/f'{STEM}.ttf')
            boxes = ink_boxes(chart, ROOT/'build/serif'/f'{STEM}.ttf')
        image = reference_dir/'frokinawa-sample.jpg'
        if image.is_file():
            shutil.copyfile(image, OUT/'frokinawa-sample.jpg')
    revisions_file = fonts/'revisions.json'
    revisions = json.loads(revisions_file.read_text()) if revisions_file.is_file() else []
    groups = {'funatsu': [], 'prefecture': []}
    for entry in ENTRIES:
        text = ''.join(chr(int(cp, 16)) for cp in entry['output'])
        label = entry['label'] if entry['system'] == 'funatsu' else entry['label'].replace('Raised ', '')
        first = int(entry['output'][0], 16)
        plain = (chr(RAISED[first][0]) if entry['system'] == 'prefecture'
                 else entry.get('kana') or BASES.get(first) or chr(first))
        groups[entry['system']].append(
            f'<article class="letter" data-id="{html.escape(entry["id"], quote=True)}">'
            f'<header><strong>{html.escape(label)}</strong><span>{html.escape(entry.get("kana") or "")}</span></header>'
            '<div class="pair">'
            f'<div><span class="glyph new" lang="ryu">{text}</span><small>GenZui</small></div>'
            '<div><span class="glyph reference" lang="ryu"></span><img class="crop" alt="" hidden>'
            '<small class="reference-label"></small></div>'
            f'<div><span class="glyph new plain" lang="ja">{html.escape(plain)}</span><small>Ordinary kana</small></div>'
            '</div>'
            + ''.join(f'<div class="revision"><span class="glyph" style="font-family:{r["key"]}" lang="ryu">{text}</span>'
                      f'<small>{html.escape(r["label"])}</small></div>' for r in revisions)
            + f'<p class="codes">{" + ".join("U+" + cp for cp in entry["output"])}</p></article>')
    page = (ROOT/'templates/okinawan.html').read_text()
    if not (OUT/'frokinawa-sample.jpg').is_file():
        start = page.index('<figure>')
        end = page.index('</figure>', start) + len('</figure>')
        page = page[:start] + page[end:]
    stamp = f'?v={int(time.time())}'
    faces = ''.join(f"@font-face{{font-family:{r['key']};src:url(fonts/{r['key']}.woff2)}}" for r in revisions)
    values = {
        '{{REVISION_FACES}}': faces,
        '{{FUNATSU}}': ''.join(groups['funatsu']),
        '{{RAISED}}': ''.join(groups['prefecture']),
        '{{TYPESETTING}}': ''.join(
            f'<figure class="run"><img src="runs/chart-{r["id"]}.png{stamp}" alt="Funatsu’s chart, {html.escape(r["id"])} set beside its examples">'
            f'<img src="runs/genzui-{r["id"]}.png{stamp}" alt="GenZui, the same text at the same size">'
            f'<figcaption><strong>{html.escape(next(e["label"] for e in ENTRIES if e["id"] == r["id"]))}</strong> '
            f'<code>{html.escape(r["text"])}</code></figcaption></figure>' for r in runs),
        '{{BOXES}}': ''.join(
            f'<tr><th scope="row">{html.escape(b["label"])}</th><td>{html.escape(b["base"])}</td>'
            f'<td>{fmt(b["chart"])}</td><td>{fmt(b["genzui"])}</td><td>{fmt(b["noto"])}</td></tr>' for b in boxes),
        '{{DATA}}': json.dumps({'entries': ENTRIES, 'references': references, 'revisions': revisions,
                                'boxes': boxes, 'runs': runs}, ensure_ascii=False).replace('<', '\\u003c'),
    }
    for key, value in values.items():
        page = page.replace(key, value)
    (OUT/'index.html').write_text(page)
    print(f'Okinawan comparison: {len(ENTRIES)} forms; {len(references)} references; '
          f'{len(runs)} typesetting runs; {len(boxes)} measured letters.')
    return OUT


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--references', type=Path)
    build(parser.parse_args().references)
