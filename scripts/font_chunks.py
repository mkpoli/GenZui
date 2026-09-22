"""Split a family's webfont into unicode-range chunks for the public pages.

The kana chunk carries every kana-script character, the historical additions,
combining marks and Latin, so any kana text shapes inside one font file. The
remaining characters, mostly ideographs, are sliced into chunks of roughly
equal size; a browser fetches a slice only when a page uses one of its
characters.
"""
import hashlib
import io

from fontTools import subset
from fontTools.ttLib import TTFont

KANA_RANGES = [(0x0000, 0x052F), (0x0300, 0x036F), (0x2000, 0x2BFF), (0x2FF0, 0x2FFF),
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
    return ','.join(out)


def plan(cmap):
    kana = sorted(cp for cp in cmap if any(a <= cp <= b for a, b in KANA_RANGES))
    rest = sorted(set(cmap) - set(kana))
    chunks = [('kana', kana)]
    for index in range(0, len(rest), SLICE):
        chunks.append((f'cjk{index//SLICE:02d}', rest[index:index+SLICE]))
    return chunks


def subset_woff2(path, points):
    font = TTFont(path, recalcTimestamp=False)
    font.flavor = None
    options = subset.Options(flavor='woff2', layout_features=['*'], notdef_outline=True,
                             name_IDs=['*'], hinting=False)
    subsetter = subset.Subsetter(options)
    subsetter.populate(unicodes=points)
    subsetter.subset(font)
    font.flavor = 'woff2'
    stream = io.BytesIO()
    font.save(stream)
    return stream.getvalue()


def build(path, family, stem, out_dir):
    """Write the chunks under out_dir and return (css, [chunk file names])."""
    cmap = TTFont(path).getBestCmap()
    faces, files = [], []
    for name, points in plan(cmap):
        data = subset_woff2(path, points)
        filename = f'{stem}-{name}-{hashlib.sha256(data).hexdigest()[:16]}.woff2'
        (out_dir/filename).write_bytes(data)
        files.append(filename)
        # Kana text waits briefly for its small chunk; ideograph slices swap in.
        display = 'block' if name == 'kana' else 'swap'
        faces.append(f"@font-face{{font-family:{family};src:url(assets/{filename}) format('woff2');"
                     f"font-weight:400;font-style:normal;font-display:{display};unicode-range:{ranges(points)}}}")
    return '\n'.join(faces), files
