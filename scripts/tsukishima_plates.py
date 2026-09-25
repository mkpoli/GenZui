# /// script
# requires-python = ">=3.12"
# dependencies = ["opencv-python-headless>=4.10", "numpy>=2"]
# ///
"""Per-form crops from the 假名字體表 plates of 築島裕 1986.

築島裕『平安時代訓點本論考 ヲコト點圖假名字體表』(汲古書院, 1986; CiNii
BN00675782) prints one plate per dated manuscript: a gojūon grid of five bands,
each a printed label strip over a glyph area, with every attested shape of a
kana set side by side in its cell. The book is in copyright, so the scans and
everything cut from them stay under `build/` as private drawing references.

Input: the page images extracted with `pdfimages -j` into
`build/katakana-work/tenzu/pages/` (`a-NNN` = volume 1–2, book page = NNN + 87;
`b-NNN` = volume 3–4, book page = NNN + 413). Output: one PNG per form under
`build/katakana-work/tenzu/forms/<kana>/` and `manifest.json` beside them.

    uv run scripts/tsukishima_plates.py
"""
import json
import shutil
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / 'build/katakana-work/tenzu'
PAGES = WORK / 'pages'

# The ten gojūon columns, right to left, for each band. 'yi', 'wu' and 'ye' are
# the ya-row i, wa-row u and ya-row e cells; the book heads ア-row e with 衣 and
# ya-row e with 江.
BANDS = [
    ['a', 'ka', 'sa', 'ta', 'na', 'ha', 'ma', 'ya', 'ra', 'wa'],
    ['i', 'ki', 'si', 'ti', 'ni', 'hi', 'mi', 'yi', 'ri', 'wi'],
    ['u', 'ku', 'su', 'tu', 'nu', 'hu', 'mu', 'yu', 'ru', 'wu'],
    ['e', 'ke', 'se', 'te', 'ne', 'he', 'me', 'ye', 're', 'we'],
    ['o', 'ko', 'so', 'to', 'no', 'ho', 'mo', 'yo', 'ro', 'wo'],
]
PITCH = (62, 95)      # column pitch in pixels at the scans' 233 ppi
SPECK = 12            # smallest ink component kept, in pixels
JOIN = 13             # widest gap bridged inside one letter, in pixels
LETTER = (62, 68)     # largest width and height of one written form
FRAGMENT = 30         # widest gap bridged from a stroke fragment to its letter


def binarize(img):
    grey = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return cv2.adaptiveThreshold(grey, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 41, 18)


def runs(mask, gap):
    """(first, last) index of each run of True, bridging gaps up to `gap`."""
    out = []
    for i in np.flatnonzero(mask):
        if out and i - out[-1][1] <= gap:
            out[-1][1] = i
        else:
            out.append([i, i])
    return [(int(a), int(b)) for a, b in out]


def skew(ink):
    rules = cv2.morphologyEx(ink, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (60, 1)))
    lines = cv2.HoughLinesP(rules, 1, np.pi / 1800, 200, minLineLength=400, maxLineGap=10)
    if lines is None:
        return 0.0
    s = lines.reshape(-1, 4)
    return float(np.median(np.degrees(np.arctan2(s[:, 3] - s[:, 1], s[:, 2] - s[:, 0]))))


def load(name):
    """Deskewed page, its ink mask and the rotation applied."""
    img = cv2.imread(str(PAGES / name))
    angle = skew(binarize(img))
    if abs(angle) > 0.05:
        h, w = img.shape[:2]
        m = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
        img = cv2.warpAffine(img, m, (w, h), flags=cv2.INTER_CUBIC, borderValue=(255, 255, 255))
    return img, binarize(img), angle


def horizontals(ink):
    rules = cv2.morphologyEx(ink, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (ink.shape[1] // 12, 1)))
    profile = rules.sum(1).astype(float)
    return [(a + b) // 2 for a, b in runs(profile > profile.max() * 0.25, gap=6)]


def bands(ys):
    """Five (label top, label bottom, band bottom) triples, or None.

    A band is a 38–62 px label strip over a 180–320 px glyph area, and each
    band's strip starts on the previous band's bottom rule. Sub-row rules inside
    a band and the double rule under the grid do not fit that chain.
    """
    ys = sorted(set(ys))

    def chain(top, depth):
        for b in ys:
            if 38 <= b - top <= 62:
                for c in ys:
                    if 180 <= c - b <= 320:
                        rest = [] if depth == 1 else chain(c, depth - 1)
                        if rest is not None:
                            return [(top, b, c)] + rest
        return None

    for top in ys:
        if found := chain(top, 5):
            return found
    return None


def verticals(ink, top, bottom, cover=0.85):
    """x of the rules that run through `cover` of one band's height."""
    band = cv2.dilate(ink[top:bottom], np.ones((1, 5), np.uint8))
    return [(a + b) // 2 for a, b in runs((band > 0).mean(0) >= cover, gap=4)]


def regular(xs):
    """Longest run of rules at the grid's column pitch."""
    best, cur = [], xs[:1]
    for a, b in zip(xs, xs[1:]):
        if PITCH[0] <= b - a <= PITCH[1]:
            cur.append(b)
        else:
            best, cur = max(best, cur, key=len), [b]
    return max(best, cur, key=len)


def columns(ink, found):
    """Eleven rules per band bounding the ten gojūon cells, right edge last.

    The right end of the regular run is the edge of the plate's title panel.
    Band 5 continues into the panel's own narrow columns, and the page's
    curvature drifts the edge by up to ~15 px from band to band, so each
    band is cut at the edge fitted through bands 1–4. A band whose rules are
    broken borrows the nearest good band's rules, shifted by the drift.
    """
    rules = [verticals(ink, a, c) for a, _, c in found]
    runs_ = [regular(r) for r in rules]
    # A faintly printed rule next to the title panel ends the run one column
    # early. Extend the run where the next rule sits two pitches away and a
    # faint rule is found near the middle, if bands 1-4 agree.
    ext = []
    for (a, b, c), r, run in zip(found, rules, runs_):
        pitch = float(np.mean(np.diff(run[-3:]))) if len(run) > 2 else 0
        nxt = [x for x in r if x > run[-1]] if run else []
        faint = verticals(ink, b, c, cover=0.5)
        mid = [x for x in faint if nxt and abs(x - (run[-1] + nxt[0]) / 2) <= 8]
        ext.append(bool(nxt and pitch and abs(nxt[0] - run[-1] - 2 * pitch) <= 8 and mid) and (mid[0], nxt[0]))
    if sum(bool(e) for e in ext[:4]) >= 3:
        runs_ = [run + list(e) if e else run for run, e in zip(runs_, ext)]
    good = [i for i in range(4) if len(runs_[i]) >= 11]
    if len(good) < 2:
        return None
    slope, base = np.polyfit(good, [runs_[i][-1] for i in good], 1)
    edges = [base + slope * i for i in range(5)]
    cut = []
    for i, r in enumerate(runs_):
        r = [x for x in r if x <= edges[i] + 12]
        cut.append(r[-11:] if len(r) >= 11 and abs(r[-1] - edges[i]) <= 12 else None)
    out = []
    for i, r in enumerate(cut):
        if r is None:
            j = min((j for j in range(5) if cut[j]), key=lambda j: abs(j - i), default=None)
            if j is None:
                return None
            r = [round(x + edges[i] - edges[j]) for x in cut[j]]
        out.append([int(x) for x in r])
    return out


def without_rules(cell):
    """The cell's ink with printed rules removed.

    A cell's box can clip the rule above or beside it where the page curves.
    """
    hor = cv2.morphologyEx(cell, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (45, 1)))
    ver = cv2.morphologyEx(cell, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (1, 110)))
    return cv2.subtract(cell, cv2.dilate(hor | ver, np.ones((3, 3), np.uint8)))


def gap(a, b):
    return max(max(a[0], b[0]) - min(a[2], b[2]), max(a[1], b[1]) - min(a[3], b[3]), 0)


def ink_in(cell, b):
    return int(np.count_nonzero(cell[b[1]:b[3], b[0]:b[2]]))


def absorb(cell, boxes, typical, extent):
    """Merge stroke fragments left over by `forms` into whole letters.

    The two strokes of ハ, or a dot set off from its letter, can stand further
    apart than JOIN. A box is a fragment when it holds less than half the
    plate's typical ink per form and is also well under a letter's typical
    size; a whole but lightly inked letter such as ツ or ヘ is neither. A
    fragment joins its nearest box within FRAGMENT px when the union still
    fits one letter, nearest pair first. Two parts that each stand 15 px or
    taller one above the other are separate forms and never join.
    """
    cell = without_rules(cell)
    boxes = [list(b) for b in boxes]

    def fragment(b):
        return ink_in(cell, b) < typical / 2 and max(b[2] - b[0], b[3] - b[1]) < extent * 0.6

    def stacked(a, b):
        return max(a[1], b[1]) - min(a[3], b[3]) >= 4 and min(a[3] - a[1], b[3] - b[1]) >= 15

    while True:
        best = None
        for i, a in enumerate(boxes):
            if not fragment(a):
                continue
            for j, b in enumerate(boxes):
                if i == j or stacked(a, b):
                    continue
                g = gap(a, b)
                u = [min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3])]
                if g <= FRAGMENT and u[2] - u[0] <= LETTER[0] and u[3] - u[1] <= LETTER[1] and (best is None or g < best[0]):
                    best = (g, i, j, u)
        if best is None:
            return [tuple(b) for b in boxes]
        _, i, j, u = best
        boxes[min(i, j)] = u
        del boxes[max(i, j)]


def forms(cell):
    """Boxes (x0, y0, x1, y1) of the separate written forms in one cell's ink.

    Strokes of one letter lie closer together than neighbouring forms: across
    the plates, gaps inside a letter are mostly under 14 px and gaps between
    forms 18 px or more. Ink components are merged closest pair first while
    their boxes are at most JOIN px apart and the result still fits one letter,
    so ハ, ツ and ヲ stay whole while forms stacked in a crowded cell stay apart.
    """
    cell = without_rules(cell)
    n, _, stats, _ = cv2.connectedComponentsWithStats(cell, connectivity=8)
    boxes = [[s[0], s[1], s[0] + s[2], s[1] + s[3]] for s in stats[1:] if s[4] >= SPECK]
    while True:
        best = None
        for i, a in enumerate(boxes):
            for j in range(i + 1, len(boxes)):
                b = boxes[j]
                g = gap(a, b)
                u = [min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3])]
                if g <= JOIN and u[2] - u[0] <= LETTER[0] and u[3] - u[1] <= LETTER[1] and (best is None or g < best[0]):
                    best = (g, i, j, u)
        if best is None:
            break
        _, i, j, u = best
        boxes[i] = u
        del boxes[j]
    return [tuple(int(v) for v in b) for b in boxes if not stray(b, cell.shape)]


def stray(b, shape):
    """A box that holds no written form.

    Rule ends the mask missed are 1–3 px thin and sit on the cell's edge;
    specks are at most 6 px across; long thin slivers are rule remnants.
    """
    h, w = b[3] - b[1], b[2] - b[0]
    on_edge = b[1] <= 2 or b[3] >= shape[0] - 2 or b[0] <= 2 or b[2] >= shape[1] - 2
    return ((min(h, w) <= 3 and on_edge) or max(h, w) <= 6
            or (h <= 5 and w >= 20) or (w <= 5 and h >= 60))


def page_image(img, ink):
    """Greyscale page with printed rules painted out, for cropping."""
    hor = cv2.morphologyEx(ink, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (45, 1)))
    ver = cv2.morphologyEx(ink, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (1, 110)))
    grey = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    paper = int(np.percentile(grey, 90))
    grey[cv2.dilate(hor | ver, np.ones((5, 5), np.uint8)) > 0] = paper
    return grey


def levels(crop):
    """Stretch a crop so its darkest ink is black and its paper white.

    Some plates are printed faintly; this keeps every crop comparable.
    """
    lo, hi = np.percentile(crop, 1), np.percentile(crop, 92)
    if hi - lo < 10:
        return crop
    out = (crop.astype(np.float32) - lo) * (255 / (hi - lo))
    return np.clip(out, 0, 255).astype(np.uint8)


def plate(name):
    img, ink, angle = load(name)
    found = bands(horizontals(ink))
    if not found:
        return name, None
    grid = columns(ink, found)
    if not grid:
        return name, {'angle': angle, 'bands': found, 'error': 'columns'}
    out = WORK / 'forms'
    grey = page_image(img, ink)
    raw = []
    for band, ((top, label, bottom), xs) in enumerate(zip(found, grid)):
        keys = BANDS[band][::-1]  # xs ascend left to right; the band's list runs right to left
        for k, (x0, x1) in enumerate(zip(xs, xs[1:])):
            box = (x0 + 5, label + 5, x1 - 5, bottom - 5)
            sub = ink[box[1]:box[3], box[0]:box[2]]
            raw.append((keys[k], box, sub, forms(sub)))
    areas = [ink_in(without_rules(sub), b) for _, _, sub, fs in raw for b in fs]
    typical = float(np.median(areas)) if areas else 0
    sizes = [max(b[2] - b[0], b[3] - b[1]) for _, _, _, fs in raw for b in fs]
    extent = float(np.median(sizes)) if sizes else LETTER[1]
    cells = []
    for kana, box, sub, fs in raw:
        found_forms = absorb(sub, fs, typical, extent)
        entry = {'kana': kana, 'cell': box, 'forms': []}
        for i, (a, b, c, d) in enumerate(found_forms):
            pad = 4
            crop = grey[max(box[1] + b - pad, 0):box[1] + d + pad, max(box[0] + a - pad, 0):box[0] + c + pad]
            path = out / kana / f'{Path(name).stem}-{kana}-{i + 1}.png'
            path.parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(path), levels(crop))
            entry['forms'].append({'box': [box[0] + a, box[1] + b, box[0] + c, box[1] + d],
                                   'file': str(path.relative_to(WORK))})
        cells.append(entry)
    for band, ((top, label, bottom), xs) in enumerate(zip(found, grid)):
        # The column left of ア…ワ: ン on many plates, a ligature or kanji on others.
        x_extra = regular(verticals(ink, top, bottom))
        x_extra = [x for x in x_extra if x < xs[0]]
        if x_extra and PITCH[0] <= xs[0] - x_extra[-1] <= PITCH[1]:
            extra = (x_extra[-1] + 5, top + 3, xs[0] - 5, bottom - 5)
            path = out / '_extra' / f'{Path(name).stem}-band{band + 1}.png'
            path.parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(path), cv2.cvtColor(img[extra[1]:extra[3], extra[0]:extra[2]], cv2.COLOR_BGR2GRAY))
    return name, {'angle': angle, 'bands': found, 'columns': grid, 'cells': cells}


def main():
    names = sorted(p.name for p in PAGES.glob('*.jpg'))
    if not names:
        sys.exit(f'No page images in {PAGES.relative_to(ROOT)}; extract them with pdfimages -j')
    shutil.rmtree(WORK / 'forms', ignore_errors=True)
    with ProcessPoolExecutor() as pool:
        results = dict(pool.map(plate, names, chunksize=8))
    plates = {k: v for k, v in results.items() if v}
    (WORK / 'manifest.json').write_text(json.dumps(plates, ensure_ascii=False, indent=1))
    bad = [k for k, v in plates.items() if 'error' in v]
    total = sum(len(c['forms']) for v in plates.values() for c in v.get('cells', []))
    print(f'{len(plates)} plates, {len(bad)} without a column grid {bad}, {total} forms')


if __name__ == '__main__':
    main()
