"""Split a family's webfont into unicode-range chunks for the public pages.

The text chunk carries every kana-script character, the historical additions,
combining marks, Latin and every ideograph the site's own pages set, so a page
renders from one file. The remaining characters, mostly ideographs a visitor
reaches by typing or browsing the inventory, are sliced into chunks of roughly
equal size and fetched only when their characters appear.

Variation sequences are kept: each chunk also carries the variant glyphs whose
base character it holds, so an IVS behaves as it does in the whole font.
"""
import hashlib
import io

from fontTools import subset
from fontTools.ttLib import TTFont

KANA_RANGES = [(0x0000, 0x052F), (0x2000, 0x2BFF), (0x2FF0, 0x2FFF),
               (0x3000, 0x30FF), (0x31C0, 0x31FF), (0x3200, 0x33FF), (0xE000, 0xF8FF),
               (0xFF00, 0xFFEF), (0x1AFF0, 0x1AFFF), (0x1B000, 0x1B16F), (0x1D372, 0x1D376),
               (0x2A708, 0x2A708), (0x2CEFF, 0x2CF02)]
SLICE = 1200


def ranges(points):
    """Compact unicode-range syntax for a sorted list of code points."""
    out, start, previous = [], None, None
    for cp in sorted(points) + [None]:
        if start is None:
            start = previous = cp
        elif cp is not None and cp == previous + 1:
            previous = cp
        else:
            out.append(f'U+{start:04X}' if start == previous else f'U+{start:04X}-{previous:04X}')
            start = previous = cp
    assert out, 'A font-face needs a non-empty unicode-range.'
    return ','.join(out)


def plan(cmap, text_points=()):
    text = sorted({cp for cp in cmap
                   if any(a <= cp <= b for a, b in KANA_RANGES) or cp in text_points})
    rest = sorted(set(cmap) - set(text))
    chunks = [('text', text)]
    for index in range(0, len(rest), SLICE):
        chunks.append((f'cjk{index//SLICE:02d}', rest[index:index+SLICE]))
    return chunks


def variants(font):
    """(base code point -> selected glyphs, the variation selectors used)."""
    result, selectors = {}, set()
    for table in font['cmap'].tables:
        if table.format == 14:
            for selector, pairs in table.uvsDict.items():
                selectors.add(selector)
                for cp, name in pairs:
                    if name:
                        result.setdefault(cp, set()).add(name)
    return result, sorted(selectors)


def subset_woff2(path, points, variant_glyphs=(), selectors=()):
    font = TTFont(path, recalcTimestamp=False)
    font.flavor = None
    options = subset.Options(flavor='woff2', layout_features=['*'], notdef_outline=True,
                             name_IDs=['*'], hinting=False)
    subsetter = subset.Subsetter(options)
    # fontTools keeps a variation sequence only when its selector is requested
    # and its glyph survives, so both go in alongside the chunk's characters.
    # The selectors stay out of the declared unicode-range: a browser applies a
    # sequence from the font that provides its base character.
    subsetter.populate(unicodes=list(points)+list(selectors), glyphs=sorted(variant_glyphs))
    subsetter.subset(font)
    font.flavor = 'woff2'
    stream = io.BytesIO()
    font.save(stream)
    return stream.getvalue()


def build(path, family, stem, out_dir, text_points=(), weight=400):
    """Write the chunks under out_dir and return (css, [chunk file names])."""
    font = TTFont(path)
    cmap = font.getBestCmap()
    uvs, selectors = variants(font)
    faces, files = [], []
    for name, points in plan(cmap, text_points):
        data = subset_woff2(path, points, {g for cp in points for g in uvs.get(cp, ())}, selectors)
        filename = f'{stem}-{name}-{hashlib.sha256(data).hexdigest()[:16]}.woff2'
        (out_dir/filename).write_bytes(data)
        files.append(filename)
        # The page waits briefly for its own Regular text; further slices, and
        # every Bold slice, which loads only when bold text appears, swap in.
        display = 'block' if name == 'text' and weight == 400 else 'swap'
        faces.append(f"@font-face{{font-family:{family};src:url(assets/{filename}) format('woff2');"
                     f"font-weight:{weight};font-style:normal;font-display:{display};unicode-range:{ranges(points)}}}")
    return '\n'.join(faces), files
