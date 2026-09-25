# /// script
# requires-python = ">=3.12"
# dependencies = ["pillow>=11"]
# ///
"""Build the static files and the database seed for the katakana review.

Reads the crops and baseline families written by `tsukishima_plates.py`
(`build/katakana-work/tenzu/`) and writes

- `build/kata-review/kata/`: the page, one WebP sprite sheet and one JSON
  index per kana (with each form's place on its plate), the reduced plate
  images, and the plate register the page cites from;
- `build/kata-review-seed.sql`: rows for the D1 database, including any
  earlier review decisions given with `--history`.

The crops come from a book in copyright; everything written here stays under
`build/`, which is not committed.

    uv run scripts/katakana_review_build.py [--history build/katakana-work/tenzu/local-history.json]
"""
import argparse
import json
import re
import shutil
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / 'build/katakana-work/tenzu'
OUT = ROOT / 'build/kata-review'
SEED = ROOT / 'build/kata-review-seed.sql'
SHEET_WIDTH = 2048
GAP = 2


def sql(v):
    if v is None:
        return 'NULL'
    if isinstance(v, int):
        return str(v)
    return "'" + str(v).replace("'", "''") + "'"


def places():
    """Where each form stands on its reduced plate image: form box and cell box."""
    manifest = json.loads((WORK / 'manifest.json').read_text())
    out = {}
    for page, plate in manifest.items():
        s = plate['scale']
        for cell in plate['cells']:
            c = [round(v * s) for v in cell['cell']]
            for f in cell['forms']:
                out[Path(f['file']).stem] = [round(v * s) for v in f['box']] + c
    return out


def sprites(families, where):
    """One sheet per kana, with each form's rectangle and its place on the plate."""
    by_kana = {}
    for form in families:
        by_kana.setdefault(form.split('-')[2], []).append(form)
    target = OUT / 'kata/sprites'
    target.mkdir(parents=True, exist_ok=True)
    for kana, forms in sorted(by_kana.items()):
        images = [(f, Image.open(WORK / 'forms' / kana / f'{f}.png').convert('L')) for f in sorted(forms)]
        # Shelf packing: fill rows left to right, row height = tallest crop in it.
        rects, x, y, row = {}, 0, 0, 0
        for f, im in images:
            if x + im.width > SHEET_WIDTH:
                x, y, row = 0, y + row + GAP, 0
            rects[f] = [x, y, im.width, im.height]
            x += im.width + GAP
            row = max(row, im.height)
        sheet = Image.new('L', (SHEET_WIDTH, y + row), 255)
        for f, im in images:
            sheet.paste(im, tuple(rects[f][:2]))
        sheet.save(target / f'{kana}.webp', quality=82, method=6)
        index = {'size': list(sheet.size), 'forms': rects, 'where': {f: where[f] for f in rects}}
        (target / f'{kana}.json').write_text(json.dumps(index, separators=(',', ':')))
    return by_kana


def register():
    source = json.loads((ROOT / 'data/historical-katakana/tsukishima-plates.json').read_text())
    plates = {}
    for p in source['plates']:
        m = re.search(r'\((\d{3,4})', p['annotated']) or re.match(r'(\d{3,4})', p['code'])
        plates[p['page']] = {
            'cite': f"({p['group']}){p['number']} {p['title']}・{p['holder']}・{p['annotated']}",
            'year': int(m.group(1)) if m else None,
        }
    s = source['source']
    citation = f"{s['creator']}『{s['title']}』{s['publisher']}、{s['date']}年（CiNii {s['ncid']}）"
    (OUT / 'kata/plates.json').write_text(json.dumps({'source': citation, 'plates': plates}, ensure_ascii=False, separators=(',', ':')))


def seed(families, history):
    labels = json.loads((ROOT / 'data/historical-katakana/shape-families.json').read_text())
    state = {f: [fam, None, 0] for f, fam in families.items()}   # family, flag, revision
    names = {k: [v, 0] for k, v in labels.items()}               # name, revision
    lines = ['DELETE FROM events;', 'DELETE FROM batches;', 'DELETE FROM kana_counts;', 'DELETE FROM labels;', 'DELETE FROM forms;']
    for e in history:
        t, field = e['target'], e['field']
        if field == 'label':
            cur = names.get(t, [None, 0])
            assert cur[0] == e['old'], f'{t}: history expects {e["old"]!r}, baseline has {cur[0]!r}'
            names[t] = [e['new'], cur[1] + 1]
            rev = names[t][1]
        else:
            cur = state[t]
            i = 0 if field == 'family' else 1
            assert cur[i] == e['old'], f'{t}: history expects {e["old"]!r}, baseline has {cur[i]!r}'
            cur[i], cur[2] = e['new'], cur[2] + 1
            rev = cur[2]
        lines.append(f"INSERT INTO batches (id, actor, at) VALUES ({sql(e['batch'])}, {sql(e.get('actor', 'local review'))}, {sql(e['at'])});")
        lines.append(f"INSERT INTO events (batch, target, field, old, new, revision, at) VALUES "
                     f"({sql(e['batch'])}, {sql(t)}, {sql(field)}, {sql(e['old'])}, {sql(e['new'])}, {rev}, {sql(e['at'])});")
    rows = [f"({sql(f)}, {sql(f.split('-')[2])}, {sql(fam)}, {sql(flag)}, {rev})" for f, (fam, flag, rev) in sorted(state.items())]
    for i in range(0, len(rows), 400):
        lines.append('INSERT INTO forms (id, kana, family, flag, revision) VALUES\n' + ',\n'.join(rows[i:i + 400]) + ';')
    lab = [f"({sql(k)}, {sql(k.split('.')[0])}, {sql(v)}, {rev})" for k, (v, rev) in sorted(names.items()) if v]
    lines.append('INSERT INTO labels (id, kana, name, revision) VALUES\n' + ',\n'.join(lab) + ';')
    counts = {}
    for f, (fam, _, _) in state.items():
        c = counts.setdefault(f.split('-')[2], [0, 0])
        c[0] += 1
        c[1] += fam == '?'
    lines.append('INSERT INTO kana_counts (kana, forms, unsorted) VALUES\n'
                 + ',\n'.join(f'({sql(k)}, {a}, {b})' for k, (a, b) in sorted(counts.items())) + ';')
    SEED.write_text('\n'.join(lines) + '\n')
    return len(state), len(history)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--history', type=Path, help='earlier review events to carry into the seed')
    args = ap.parse_args()
    families = {k.removesuffix('.png'): v for k, v in json.loads((WORK / 'categories.json').read_text()).items()}
    history = json.loads(args.history.read_text()) if args.history else []
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / 'kata').mkdir(parents=True)
    by_kana = sprites(families, places())
    register()
    shutil.copytree(WORK / 'plates', OUT / 'kata/plates')
    shutil.copy(ROOT / 'review/public/index.html', OUT / 'kata/index.html')
    (OUT / '_headers').write_text('/kata/*\n  X-Robots-Tag: noindex, nofollow\n  Cache-Control: no-cache\n')
    forms, events = seed(families, history)
    print(f'{len(by_kana)} sprite sheets, {forms} forms, {events} earlier events → {OUT.relative_to(ROOT)}, {SEED.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
