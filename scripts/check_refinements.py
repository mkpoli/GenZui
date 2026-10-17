"""Check the joins, stem weight and baseline of the ten revised kana."""
from collections import deque
from PIL import Image, ImageDraw, ImageFont

from serif_forms import REVISED


def mask(path, cp, size):
    image = Image.new('L', (size+40, size+40))
    ImageDraw.Draw(image).text((20, size*.88+20), chr(cp),
                              font=ImageFont.truetype(str(path), size),
                              anchor='ls', fill=255)
    return image


def components(image):
    width, height = image.size
    ink = {(x, y) for y in range(height) for x in range(width)
           if image.getpixel((x, y)) >= 64}
    counts = []
    while ink:
        first = ink.pop()
        queue, count = deque([first]), 1
        while queue:
            x, y = queue.popleft()
            for dx, dy in ((-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)):
                p = (x+dx, y+dy)
                if p in ink:
                    ink.remove(p); queue.append(p); count += 1
        if count >= 2:
            counts.append(count)
    return len(counts)


def runs(image, y, start, end):
    spans, opening = [], None
    for x in range(start, end+1):
        black = x < end and image.getpixel((x, y)) >= 128
        if black and opening is None: opening = x
        if not black and opening is not None:
            spans.append(x-opening); opening = None
    return spans


def check_refinements(path, font):
    # TOTE retains its separate upper bar; YORI keeps three components;
    # katakana NARI keeps its separate upper stroke. The other joins must hold.
    expected = {cp: 1 for cp in REVISED}
    expected.update({0x1B125: 2, 0x1B126: 3, 0x2CEFF: 2})
    joins = []
    for size in (48, 128):
        for cp, count in expected.items():
            actual = components(mask(path, cp, size))
            assert actual == count, (f'U+{cp:X}', size, actual, count)
            joins.append({'codepoint':f'U+{cp:X}', 'size_px':size, 'components':actual})

    # At 1000 px, one pixel is one design unit. Scan the RI stems at y=400,
    # below their entry terminals and above the curved descent.
    native = runs(mask(path, 0x30EA, 1000), 500, 250, 800)
    revised = runs(mask(path, 0x1B126, 1000), 500, 590, 980)
    assert len(native) == len(revised) == 2, (native, revised)
    assert all(0.9 <= new/old <= 1.15 for new, old in zip(revised, native)), (native, revised)
    cmap = font.getBestCmap()
    nari = font['glyf'][cmap[0x2CF02]]
    n = font['glyf'][cmap[0x3093]]
    assert nari.yMin == n.yMin == -32
    assert all(font['glyf'][cmap[cp]].xMin >= 0 and
               font['glyf'][cmap[cp]].xMax <= 1000 for cp in REVISED)
    return {'connectivity_checks':joins, 'ri_stems_native_units':native,
            'ri_stems_revised_units':revised, 'nari_baseline_y_min':nari.yMin}
