"""Reproducible geometric weight census of the immutable Sans 0.104 release.

Run with the repository Python environment. No fonts are rebuilt or modified.
"""
import csv
import hashlib
import importlib.metadata
import json
import math
import platform
import time
import unicodedata
from collections import Counter
from pathlib import Path
from zipfile import ZipFile

import numpy as np
from PIL import Image, ImageDraw, ImageFont, features
from scipy import ndimage
from skimage.morphology import medial_axis
from fontTools.ttLib import TTFont
import uharfbuzz as hb

from sources import ROOT
from serif import font_path
from repertoire import repertoire
from okinawan import ENTRIES
from okinawan_weight_audit import vector, shaped, script, DONORS

OUT = ROOT / 'build/sans-weight-audit'
RELEASE = ROOT / 'releases/sans-v0.104'
RESOLUTIONS = (512, 1024)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')


def quantiles(values, weights=None):
    if not len(values):
        return None
    values = np.asarray(values)
    weights = np.ones(len(values)) if weights is None else np.asarray(weights)
    ix = np.argsort(values)
    values, weights = values[ix], weights[ix]
    cdf = (np.cumsum(weights) - weights / 2) / weights.sum()
    return dict(zip(('q10', 'q25', 'q50', 'q75', 'q90'),
                    map(float, np.interp([.1, .25, .5, .75, .9], cdf, values))))


def measure_mask(mask, pixels):
    """Local diameters, length weighted, with terminal/junction exclusion.

    The output describes binary geometry. Rasterization and skeleton topology
    contribute bias; both resolutions and analytical fixtures quantify it.
    """
    if not mask.any():
        return None
    mask = np.pad(mask, 4)
    skel, dist = medial_axis(mask, return_distance=True, rng=0)
    neighbours = ndimage.convolve(skel.astype('uint8'), np.ones((3, 3), dtype='uint8')) - skel
    unstable = skel & ((neighbours > 2) | (neighbours < 2))
    stable = skel & ~ndimage.binary_dilation(unstable, iterations=max(1, round(pixels / 256)))
    kernel = np.array([[2**.5, 1, 2**.5], [1, 0, 1], [2**.5, 1, 2**.5]]) / 2
    lengths = ndimage.convolve(skel.astype(float), kernel)[stable]
    widths = 2 * dist[stable] * 1000 / pixels
    # Window moments give the local principal axis without one PCA per pixel.
    radius = max(3, round(pixels / 100))
    yy, xx = np.indices(skel.shape, dtype=float)
    size = 2*radius+1
    count = ndimage.uniform_filter(skel.astype(float), size=size, mode='constant')
    def moment(k):
        return ndimage.uniform_filter(skel*k, size=size, mode='constant')[stable] / np.maximum(count[stable], 1e-12)
    mx, my = moment(xx), moment(yy)
    vx, vy, cov = moment(xx*xx)-mx*mx, moment(yy*yy)-my*my, moment(xx*yy)-mx*my
    delta = np.sqrt((vx-vy)**2+4*cov**2)
    reliable = (count[stable]*size*size >= 2.99) & ((vx+vy+delta) >= 3*np.maximum(vx+vy-delta, .002))
    angle = np.abs(np.degrees(.5*np.arctan2(2*cov, vx-vy)))
    bins = {'horizontal': angle < 22.5, 'vertical': angle > 67.5,
            'diagonal': (angle >= 22.5) & (angle <= 67.5)}
    directions, support = {}, {}
    for name, condition in bins.items():
        take = condition & reliable
        support[name] = float(lengths[take].sum()*1000/pixels)
        directions[name] = quantiles(widths[take], lengths[take]) if support[name] >= 60 else None
    return dict(stroke=quantiles(widths, lengths), directions=directions,
                axis_units=float(lengths.sum()*1000/pixels), direction_axis_units=support,
                retained_fraction=float(stable.sum()/max(1, skel.sum())),
                ink_em_fraction=float(mask.sum()/pixels**2))


def raster(face, text, pixels, regions=False):
    # Dynamic bounds preserve a common em scale and prevent clipping tall marks.
    left, top, right, bottom = face.getbbox(text, anchor='ls')
    pad = 12
    im = Image.new('L', (right-left+2*pad, bottom-top+2*pad))
    ImageDraw.Draw(im).text((pad-left, pad-top), text, font=face, anchor='ls', fill=255)
    mask = np.asarray(im) > 127
    result = measure_mask(mask, pixels)
    if result is None:
        return None
    if regions:
        # HWA/HWI/HWE have detached vowels wholly to the right of x=500.
        # Only complete connected components are selected, never cut strokes.
        labels, count = ndimage.label(mask)
        vowel = np.zeros_like(mask)
        body = np.zeros_like(mask)
        for i in range(1, count+1):
            ys, xs = np.nonzero(labels == i)
            units_min_x = (xs.min()+left-pad)*1000/pixels
            (vowel if units_min_x > 500 else body)[labels == i] = True
        assert vowel.any() and body.any(), text
        result['parts'] = {'vowel': measure_mask(vowel, pixels), 'fu': measure_mask(body, pixels)}
    return result


def calibration():
    results = []
    for pixels in RESOLUTIONS:
        y, x = np.mgrid[:pixels, :pixels] * 1000 / pixels
        for width in (40, 70, 110):
            for label, mask in [
                ('horizontal', (abs(y-500) < width/2) & (x > 100) & (x < 900)),
                ('vertical', (abs(x-500) < width/2) & (y > 100) & (y < 900)),
                ('diagonal', (abs(y-x)/math.sqrt(2) < width/2) & (x+y > 250) & (x+y < 1750)),
                ('ring', abs(np.hypot(x-500, y-500)-300) < width/2),
            ]:
                measured = measure_mask(mask, pixels)['stroke']['q50']
                error = abs(measured-width)
                assert error < 5, (label, pixels, width, measured)
                results.append(dict(shape=label, pixels=pixels, width=width, measured=measured, error=error))
    return results


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    source = font_path('NotoSansJP')
    manifest = json.loads((ROOT/'sources/manifest.json').read_text(encoding='utf-8'))
    pin = next(x['sha256'] for x in manifest['files'] if x['path'] == str(source.relative_to(ROOT)))
    assert digest(source) == pin
    native = TTFont(source)
    ncmap = native.getBestCmap()
    groups = {ord(e['character']): e['group'] for e in repertoire()}
    vectors, details, provenance = [], [], {}
    with ZipFile(RELEASE/'GenZuiSans-0.104.zip') as archive:
        for style, weight in [('Regular', 400), ('Bold', 700)]:
            path = RELEASE/f'GenZuiSans-{style}.ttf'
            assert path.read_bytes() == archive.read(path.name)
            sources = json.loads(archive.read('sources.json' if weight == 400 else 'sources-bold.json'))
            provenance[style] = dict(font_sha256=digest(path), source_kinds=sources['source_kinds'])
            font = TTFont(path)
            assert font['head'].unitsPerEm == native['head'].unitsPerEm == 1000
            cmap, gs = font.getBestCmap(), font.getGlyphSet()
            ngs = native.getGlyphSet(location={'wght': weight})
            cache = {}
            for index, (cp, name) in enumerate(sorted(ncmap.items())):
                if name not in cache:
                    cache[name] = vector(ngs, [(name, 0, 0)])
                vectors.append(dict(style=style, origin='Noto', group=script(cp), cp=f'{cp:04X}',
                                    text=chr(cp), label=chr(cp), glyph=name, **cache[name]))
                if index % 5000 == 0:
                    print(style, 'native vector census', index, flush=True)
            added = sorted(set(cmap)-set(ncmap))
            # Include historical targets even when an upstream mapping exists.
            points = sorted(set(added) | (set(groups) & set(cmap)))
            entries = []
            entry_points = {int(e['output'][0], 16) for e in ENTRIES}
            for cp in points:
                if cp in entry_points:
                    continue
                entries.append(dict(text=chr(cp), label=f'U+{cp:04X}', cp=f'{cp:04X}',
                                    group=groups.get(cp, 'other'), donors=''))
            for e in ENTRIES:
                text = ''.join(chr(int(cp, 16)) for cp in e['output'])
                entries.append(dict(text=text, label=e['label'], cp=' '.join(e['output']),
                                    group=e['system'], donors=DONORS.get(e['label'], chr(int(e['base'],16)) if e.get('base') else '')))
            engine = hb.Font(hb.Face(path.read_bytes())); engine.scale = (1000, 1000)
            for e in entries:
                glyphs, advance = shaped(font, engine, e['text'])
                vectors.append(dict(style=style, origin='GenZui', **e, advance=advance,
                                    glyph=' '.join(g[0] for g in glyphs), **vector(gs, glyphs)))
            # Native kana plus comparable short strokes, not Han skeletons.
            refs = [dict(text=chr(cp), label=chr(cp), cp=f'{cp:04X}', group=script(cp), donors='')
                    for cp in ncmap if (0x3041 <= cp <= 0x30FF or cp in (0x4E00, 0x4E8C, 0x4E09))]
            for pixels in RESOLUTIONS:
                # BASIC renders isolated native combining marks without a dotted circle.
                reference = ImageFont.truetype(str(source), pixels, layout_engine=ImageFont.Layout.BASIC)
                reference.set_variation_by_axes([weight])
                face = ImageFont.truetype(str(path), pixels, layout_engine=ImageFont.Layout.RAQM)
                isolated = ImageFont.truetype(str(path), pixels, layout_engine=ImageFont.Layout.BASIC)
                for origin, collection, renderer in [('Noto', refs, reference), ('GenZui', entries, face)]:
                    for index, e in enumerate(collection):
                        selected = isolated if origin == 'GenZui' and len(e['text']) == 1 and unicodedata.category(e['text']).startswith('M') else renderer
                        result = raster(selected, e['text'], pixels, e['label'] in ('HWA','HWI','HWE'))
                        if result:
                            details.append(dict(style=style, origin=origin, pixels=pixels, **e, **result))
                        if index % 100 == 0:
                            print(style, pixels, origin, index, '/', len(collection), flush=True)
                dump('strokes.json', details)
            print(style, 'complete', round(time.monotonic()-started), 'seconds', flush=True)
    dump('vectors.json', vectors)
    fields = ['style','origin','group','cp','text','label','glyph','area','perimeter','effective_width','bbox_density','ink_em_fraction']
    with (OUT/'vectors.csv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fields, extrasaction='ignore'); writer.writeheader(); writer.writerows(vectors)
    dump('provenance.json', dict(release='sans-v0.104', source_sha256=pin, native_encoded=len(ncmap),
         resolutions=RESOLUTIONS, faces=provenance, calibration=calibration(),
         environment=dict(python=platform.python_version(), packages={p:importlib.metadata.version(p) for p in
             ('numpy','scipy','scikit-image','Pillow','fonttools','skia-pathops','uharfbuzz')},
             freetype=features.version('freetype2'), raqm=features.version('raqm'))))
    print('Finished in', round(time.monotonic()-started), 'seconds', flush=True)


if __name__ == '__main__':
    main()
