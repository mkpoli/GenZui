"""Shape-correlation test of hentaigana drawings between fonts.

Usage: check_provenance.py NOTO_HENTAIGANA.ttf GENSEKI.ttf SUKIMA_MAIN.ttf GENSEKI_README.md

Each glyph is rendered at 160 px on a baseline, cropped to its ink, resized to
96 x 96, blurred (Gaussian radius 4) and compared by Pearson correlation.
GenSeki's README origin table (A Shokaki, B Sukima, C its own) selects the
glyph sets. Prints a Markdown table.
"""
import re
import statistics
import sys

import numpy as np
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFilter, ImageFont

SIZE, BOX, BLUR = 160, 96, 4


def origin_table(readme):
    """Map code point to A, B or C from the rows `| U+1B00x | A | B | ...`."""
    table = {}
    for line in open(readme, encoding='utf-8'):
        m = re.match(r'\|\s*U\+([0-9A-F]+)x\s*\|(.*)\|\s*$', line)
        if m:
            for col, cell in enumerate(m.group(2).split('|')):
                if cell.strip() in ('A', 'B', 'C'):
                    table[int(m.group(1), 16) * 16 + col] = cell.strip()
    return table


class Face:
    def __init__(self, path):
        self.cmap = TTFont(path).getBestCmap()
        self.font = ImageFont.truetype(path, SIZE)

    def signature(self, cp):
        """Blurred, ink-cropped, 96 px bitmap as a float vector, or None."""
        if cp not in self.cmap:
            return None
        canvas = Image.new('L', (SIZE * 3, SIZE * 3), 0)
        ImageDraw.Draw(canvas).text((SIZE, SIZE * 2), chr(cp), font=self.font, fill=255, anchor='ls')
        box = canvas.getbbox()
        if not box:
            return None
        image = canvas.crop(box).resize((BOX, BOX), Image.LANCZOS).filter(ImageFilter.GaussianBlur(BLUR))
        return np.asarray(image, dtype=float).ravel()


def compare(left, right, cps):
    scores = []
    for cp in cps:
        a, b = left.signature(cp), right.signature(cp)
        if a is not None and b is not None and a.std() and b.std():
            scores.append(float(np.corrcoef(a, b)[0, 1]))
    return scores


def main(noto, genseki, sukima, readme):
    noto, genseki, sukima = Face(noto), Face(genseki), Face(sukima)
    origin = origin_table(readme)
    a_rows = sorted(cp for cp, o in origin.items() if o == 'A')
    b_rows = sorted(cp for cp, o in origin.items() if o == 'B')
    pairs = [('GenSeki glyphs its README credits to Sukima (B) ↔ Sukima Gothic Main', genseki, sukima, b_rows),
             ('GenSeki glyphs its README credits to Shokaki (A) ↔ Sukima Gothic Main', genseki, sukima, a_rows),
             ('Noto Sans Hentaigana Regular ↔ Sukima Gothic Main, U+1B002–1B0FF', noto, sukima, range(0x1B002, 0x1B100)),
             ('Noto Sans Hentaigana Regular ↔ GenSeki glyphs credited to Shokaki (A)', noto, genseki, a_rows)]
    print('| Pair | Characters | Median | Above 0.95 |\n| --- | --- | --- | --- |')
    for name, left, right, cps in pairs:
        s = compare(left, right, cps)
        print(f'| {name} | {len(s)} | {statistics.median(s):.3f} | {sum(x > .95 for x in s)} |')


if __name__ == '__main__':
    if len(sys.argv) != 5:
        sys.exit(__doc__)
    main(*sys.argv[1:])
