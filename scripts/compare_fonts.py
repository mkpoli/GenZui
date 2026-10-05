"""Measure the fonts of the comparison page.

Reads the pinned fonts listed in sources/compare-manifest.json and writes
research/font-comparison.json (numbers, provenance, similarity) and
research/font-comparison-glyphs.json (glyph outlines as SVG path data).
The page build reads only those two files.
"""
import argparse
import hashlib
import json
import math
import re
import sys
from collections import Counter, defaultdict
from importlib.metadata import version as package_version
from zipfile import ZipFile

import numpy as np
import uharfbuzz as hb
from fontTools.pens.basePen import BasePen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

from compare_sources import member, verify
from sources import ROOT

OUT = ROOT/'research/font-comparison.json'
GLYPHS = ROOT/'research/font-comparison-glyphs.json'
IMAGES = ROOT/'research/font-comparison-images'
# GenZui's own outlines stay vector; every other font is shown as a raster mask.
VECTOR = {'genzui-serif', 'genzui-sans'}
CELL = 152
UNICODE = ROOT/'data/unicode'

# The fonts of the page, in display order. `install` are the files a reader installs;
# `outline` are the files searched, in order, for a code point's drawing.
SPECS = [
    {'id': 'genzui-serif', 'name': 'GenZui Serif', 'ja': '源萃明朝', 'style': 'Serif',
     'install': ['GenZuiSerif-Regular.ttf', 'GenZuiSerif-Bold.ttf'], 'outline': ['GenZuiSerif-Regular.ttf']},
    {'id': 'genzui-sans', 'name': 'GenZui Sans', 'ja': '源萃ゴシック', 'style': 'Sans',
     'install': ['GenZuiSans-Regular.ttf', 'GenZuiSans-Bold.ttf'], 'outline': ['GenZuiSans-Regular.ttf']},
    {'id': 'sukima', 'name': 'Sukima Gothic', 'ja': 'すきまゴシック', 'style': 'Sans',
     'install': ['SukimaGothic-Regular ver11.41.ttf', 'SukimaGothicSub-Regular ver11.41.ttf'],
     'outline': ['SukimaGothic-Regular ver11.41.ttf', 'SukimaGothicSub-Regular ver11.41.ttf']},
    {'id': 'noto-serif-hentaigana', 'name': 'Noto Serif Hentaigana', 'ja': 'Noto Serif Hentaigana', 'style': 'Serif',
     'install': ['NotoSerifHentaigana[wght].ttf'], 'outline': ['NotoSerifHentaigana-Regular.ttf']},
    {'id': 'genseki', 'name': 'GenSeki Hentaigana Gothic', 'ja': '源石変体仮名ゴシック', 'style': 'Sans',
     'install': ['GenSekiHentaiganaGothic.ttf', 'GenSekiHentaiganaGothic-Bold.ttf'], 'outline': ['GenSekiHentaiganaGothic.ttf']},
    {'id': 'ninjal', 'name': 'NINJAL Hentaigana', 'ja': 'NINJAL変体仮名', 'style': 'Serif',
     'install': ['ninjal_hentaigana.ttf'], 'outline': ['ninjal_hentaigana.ttf']},
    {'id': 'jigmo', 'name': 'Jigmo', 'ja': '字雲', 'style': 'Serif',
     'install': ['Jigmo.ttf', 'Jigmo2.ttf', 'Jigmo3.ttf'], 'outline': ['Jigmo.ttf', 'Jigmo2.ttf', 'Jigmo3.ttf']},
]
WEIGHT_NAMES = {100: 'Thin', 200: 'ExtraLight', 300: 'Light', 400: 'Regular', 500: 'Medium', 600: 'SemiBold',
                700: 'Bold', 800: 'ExtraBold', 900: 'Black'}

KANA_BLOCKS = ['Hiragana', 'Katakana', 'Katakana Phonetic Extensions', 'Kana Supplement', 'Kana Extended-A',
               'Small Kana Extension', 'Kana Extended-B']
OTHER_BLOCKS = ['CJK Symbols and Punctuation', 'Kanbun', 'CJK Unified Ideographs',
                *(f'CJK Unified Ideographs Extension {x}' for x in 'ABCDEFGHIJ'),
                'CJK Compatibility Ideographs', 'CJK Compatibility Ideographs Supplement',
                'Private Use Area', 'Supplementary Private Use Area-A']
HENTAIGANA = range(0x1B001, 0x1B11F)
# Chart sets of the page, in code point order of their blocks.
CHART_SETS = {
    'hentaigana': ('Hentaigana', range(0x1B001, 0x1B11F)),
    'extended-a': ('Kana Extended-A', range(0x1B100, 0x1B130)),
    'small': ('Small Kana Extension', range(0x1B130, 0x1B170)),
    'extended-b': ('Kana Extended-B', range(0x1AFF0, 0x1B000)),
}
LIGATURES = [0x2A708, 0x2CEFF, 0x2CF00, 0x2CF02]
HERO = 'いろはにほへと　𛀙𛂦𛁈𛃶𛂁　アイウエオ　永字八法'
# Example surnames from Sukima Gothic's own usage list (使用例.txt): rare character, the quoted name.
NAMES = [('𭓽', '𭓽山ささやま'), ('𮌦', '黒𮌦くろはばき'), ('𪶉', '𪶉田はまだ'), ('㐲', '㐲里ふしざと'),
         ('𨓉', '渡𨓉わたなべ'), ('𭘾', '千𭘾原ちとせはら'), ('𫟎', '𫟎木あらき'), ('𩾛', '𩾛山はとやま'),
         ('𠔥', '𠔥平かねひら'), ('㳬', '玉㳬寺')]
VERTICAL = '、。「」ーゃっ'
KANA_BASE = [*range(0x3041, 0x3097), *range(0x30A1, 0x30FB)]


def flat(text):
    return re.sub(r'\s+', ' ', text.replace('﻿', '')).strip()


# --- Unicode -------------------------------------------------------------------

def unicode_data():
    blocks = {}
    for line in (UNICODE/'Blocks.txt').read_text().splitlines():
        match = re.match(r'([0-9A-F]+)\.\.([0-9A-F]+); (.*)', line)
        if match:
            blocks[match[3]] = (int(match[1], 16), int(match[2], 16))
    names, assigned, first = {}, set(), None
    for line in (UNICODE/'UnicodeData.txt').read_text().splitlines():
        fields = line.split(';')
        cp, name = int(fields[0], 16), fields[1]
        if name.endswith(', First>'):
            first = cp
        elif name.endswith(', Last>'):
            assigned.update(range(first, cp + 1))
        else:
            assigned.add(cp)
            names[cp] = name
    ages = {}
    for line in (UNICODE/'DerivedAge.txt').read_text().splitlines():
        match = re.match(r'([0-9A-F]+)(?:\.\.([0-9A-F]+))?\s*;\s*([0-9.]+)', line)
        if match:
            for cp in range(int(match[1], 16), int(match[2] or match[1], 16) + 1):
                ages[cp] = match[3]
    return blocks, assigned, names, ages


# --- Fonts ---------------------------------------------------------------------

class Face:
    """One font file: cmap, outlines scaled to a 1000-unit em and drawn y-down."""

    def __init__(self, path):
        self.path = path
        self.font = TTFont(path, lazy=True)
        self.cmap = self.font.getBestCmap()
        self.upm = self.font['head'].unitsPerEm
        self.glyphs = self.font.getGlyphSet()

    def draw(self, cp):
        pen = RelativePen()
        scale = 1000/self.upm
        self.glyphs[self.cmap[cp]].draw(TransformPen(pen, (scale, 0, 0, -scale, 0, 0)))
        return pen.path()

    def advance(self, cp):
        return round(self.glyphs[self.cmap[cp]].width*1000/self.upm)


class RelativePen(BasePen):
    """SVG path data in whole units, relative after the first point of each contour."""

    def __init__(self):
        super().__init__(None)
        self.parts, self.at = [], (0, 0)

    def _step(self, *points):
        rounded = [(round(x), round(y)) for x, y in points]
        deltas = [f'{x - self.at[0]} {y - self.at[1]}' for x, y in rounded]
        self.at = rounded[-1]
        return ' '.join(deltas)

    def _moveTo(self, pt):
        self.at = (round(pt[0]), round(pt[1]))
        self.parts.append(f'M{self.at[0]} {self.at[1]}')
        self.start = self.at

    def _lineTo(self, pt):
        self.parts.append('l' + self._step(pt))

    def _curveToOne(self, a, b, c):
        self.parts.append('c' + self._step(a, b, c))

    def _qCurveToOne(self, a, b):
        self.parts.append('q' + self._step(a, b))

    def _closePath(self):
        self.parts.append('z')
        self.at = self.start

    def path(self):
        return ''.join(self.parts).replace(' -', '-')


class FlattenPen(BasePen):
    """Contours as point lists, curves sampled finely, for rasterising a glyph."""

    def __init__(self):
        super().__init__(None)
        self.contours, self.current = [], []

    def _moveTo(self, pt):
        self.current = [pt]

    def _lineTo(self, pt):
        self.current.append(pt)

    def _curveToOne(self, a, b, c):
        p0 = self.current[-1]
        for i in range(1, 13):
            t = i/12
            u = 1 - t
            self.current.append(tuple(u**3*p0[k] + 3*u*u*t*a[k] + 3*u*t*t*b[k] + t**3*c[k] for k in (0, 1)))

    def _qCurveToOne(self, a, b):
        p0 = self.current[-1]
        for i in range(1, 11):
            t = i/10
            u = 1 - t
            self.current.append(tuple(u*u*p0[k] + 2*u*t*a[k] + t*t*b[k] for k in (0, 1)))

    def _closePath(self):
        if self.current:
            self.contours.append(self.current)
        self.current = []


def feature_tags(font, table):
    if table not in font:
        return []
    records = font[table].table.FeatureList
    return sorted({r.FeatureTag for r in records.FeatureRecord}) if records else []


def name_record(font, name_id):
    record = font['name'].getName(name_id, 3, 1, 0x409) or font['name'].getName(name_id, 1, 0, 0)
    return record.toUnicode() if record else None


def variation_sequences(font):
    return sum(len(v) for table in font['cmap'].tables if table.format == 14 for v in table.uvsDict.values())


def font_facts(spec, entry, paths):
    """File-level facts of the installed files of one font."""
    files, glsub, ggpos, scripts, weights = [], set(), set(), set(), []
    cmaps, upm, morx, vertical_tables = set(), set(), False, set()
    parts, first = [], None
    for name, path in paths.items():
        font = TTFont(path, lazy=True)
        first = first or font
        own = set(font.getBestCmap())
        cmaps |= own
        parts.append({'name': name, 'glyphs': font['maxp'].numGlyphs, 'codepoints': len(own),
                      'variation_sequences': variation_sequences(font) if 'cmap' in font else 0,
                      'cmap': own})
        upm.add(font['head'].unitsPerEm)
        glsub |= set(feature_tags(font, 'GSUB'))
        ggpos |= set(feature_tags(font, 'GPOS'))
        morx = morx or 'morx' in font
        vertical_tables |= {t for t in ('vmtx', 'VORG') if t in font}
        if 'fvar' in font:
            axis = font['fvar'].axes[0]
            instances = sorted({int(i.coordinates[axis.axisTag]) for i in font['fvar'].instances})
            weights.append({'file': name, 'variable': True, 'axis': axis.axisTag, 'min': int(axis.minValue),
                            'max': int(axis.maxValue), 'named': [WEIGHT_NAMES[w] for w in instances]})
        else:
            weights.append({'file': name, 'variable': False, 'class': font['OS/2'].usWeightClass,
                            'style': name_record(font, 2)})
        members = {m['path'].rsplit('/', 1)[-1]: m for m in entry['members']}
        files.append({'name': name, 'size': members[name]['size'], 'sha256': members[name]['sha256'],
                      'role': members[name]['role'], 'format': 'TrueType'})
    for m in entry['members']:
        if m['role'] == 'web':
            files.append({'name': m['path'], 'size': m['size'], 'sha256': m['sha256'], 'role': 'web', 'format': 'WOFF2'})
    scripts = set()
    for path in paths.values():
        font = TTFont(path, lazy=True)
        for table in ('GSUB', 'GPOS'):
            if table in font and font[table].table.ScriptList:
                scripts |= {r.ScriptTag for r in font[table].table.ScriptList.ScriptRecord}
    shared = len({cp for cp in cmaps if sum(cp in part['cmap'] for part in parts) > 1})
    for part in parts:
        part.pop('cmap')
    return {'files': files, 'weights': weights, 'parts': parts, 'shared_codepoints': shared, 'codepoints': len(cmaps),
            'upm': sorted(upm), 'gsub': sorted(glsub), 'gpos': sorted(ggpos), 'scripts': sorted(scripts),
            'morx': morx, 'vertical_tables': sorted(vertical_tables),
            'version_string': name_record(first, 5), 'copyright': name_record(first, 0),
            'designer': name_record(first, 9), 'licence_field': name_record(first, 13),
            'cmap': cmaps}


def reserved_name(entry, paths):
    """The Reserved Font Name statement of the font's copyright field or licence file."""
    texts = [name_record(TTFont(p, lazy=True), 0) or '' for p in paths.values()]
    for item in entry['members']:
        if item['role'] == 'licence':
            texts.append((member_path(entry, item['path'])).read_text(errors='ignore'))
    for text in texts:
        found = re.search(r"Reserved Font Names?\s+['\"“‘]([^'\"”’]+)['\"”’]", flat(text))
        if found:
            return found[1]
    return None


def member_path(entry, path):
    from compare_sources import font_dir
    return font_dir(entry)/path


# --- Provenance ------------------------------------------------------------------

def cited_text(entry, spec_paths, where):
    """The text a provenance row cites: a file inside the entry, a file in its package, or a name-table field."""
    if where.startswith('name:'):
        return ' '.join(name_record(TTFont(p, lazy=True), int(where[5:])) or '' for p in spec_paths.values())
    if '!' in where:
        archive, inner = where.split('!')
        with ZipFile(member_path(entry, archive)) as package:
            return package.read(inner).decode()
    return member_path(entry, where).read_text(encoding='utf-8-sig')


def checked_provenance(entry, spec_paths):
    rows = []
    for row in entry['provenance']:
        text = flat(cited_text(entry, spec_paths, row['member']))
        assert flat(row['quote']) in text, f"Quote not found in {entry['id']}: {row['member']}: {row['quote']}"
        rows.append(dict(row))
    return rows


def genseki_origins(entry):
    """Count the A/B/C origin letters of GenSeki's README tables."""
    text = member_path(entry, 'README.md').read_text()
    counts = Counter()
    for line in text.splitlines():
        match = re.match(r'\| U\+(1B[01][0-9A-F])x \|(.*)\|', line)
        if match:
            counts.update(c.strip() for c in match[2].split('|') if c.strip() in 'ABC' and c.strip())
    legend = {'A': 'Shokaki Hentaigana Gothic', 'B': 'Sukima Gothic', 'C': 'GenSeki additions'}
    return {legend[k]: counts[k] for k in 'ABC'}


def genzui_sources(entry, package_name, member_name):
    """Counts by source of the character provenance record inside a GenZui package."""
    with ZipFile(member_path(entry, package_name)) as package:
        record = json.loads(package.read(member_name))
    kinds = Counter(v.split(';')[0] for v in record['source_kinds'].values())
    return dict(kinds.most_common())


# --- Rendering and similarity ---------------------------------------------------------

CANVAS, ORIGIN = 260, (30, 206)


class Raster:
    """Renders code points at 200 px on a shared baseline from one font's files."""

    def __init__(self, faces):
        self.faces = faces
        self.fonts = {f.path: ImageFont.truetype(str(f.path), 200) for f in faces}
        self.cache = {}

    def has(self, cp):
        return any(cp in f.cmap for f in self.faces)

    def mask(self, cp):
        for face in self.faces:
            if cp in face.cmap:
                image = Image.new('L', (CANVAS, CANVAS), 0)
                ImageDraw.Draw(image).text(ORIGIN, chr(cp), font=self.fonts[face.path], fill=255, anchor='ls')
                return image.point(lambda v: 255 if v > 127 else 0)
        return None

    def bits(self, cp):
        if cp not in self.cache:
            image = self.mask(cp)
            self.cache[cp] = None if image is None else np.packbits(np.asarray(image) > 0)
        return self.cache[cp]

    def shape(self, cp):
        """Ink cropped, scaled to 96 px and blurred, as a unit-length centred vector."""
        image = self.mask(cp)
        box = image.getbbox() if image else None
        if box is None:
            return None
        vector = np.asarray(image.crop(box).resize((96, 96), Image.BILINEAR).filter(ImageFilter.GaussianBlur(2)),
                            dtype=np.float32).ravel()
        vector -= vector.mean()
        norm = np.linalg.norm(vector)
        return vector/norm if norm else None


def overlap(a, b):
    both = int(np.bitwise_count(a & b).sum())
    either = int(np.bitwise_count(a | b).sum())
    return both/either if either else 1.0


def similarity(rasters, cps):
    """Per pair: the shares of identical outlines (overlap of 0.90 or more) and the median shape correlation."""
    ids = list(rasters)
    out, per_code = {}, {}
    shapes = {fid: {cp: rasters[fid].shape(cp) for cp in cps} for fid in ids}
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            ious, corrs, codes = [], [], {}
            for cp in cps:
                x, y = rasters[a].bits(cp), rasters[b].bits(cp)
                if x is None or y is None:
                    continue
                value = overlap(x, y)
                ious.append(value)
                codes[f'{cp:X}'] = round(value*100)
                sa, sb = shapes[a][cp], shapes[b][cp]
                if sa is not None and sb is not None:
                    corrs.append(float(sa @ sb))
            out[f'{a}|{b}'] = {
                'n': len(ious),
                'same': sum(v >= 0.9 for v in ious),
                'iou_median': round(float(np.median(ious)), 3) if ious else None,
                'corr_median': round(float(np.median(corrs)), 3) if corrs else None}
            per_code[f'{a}|{b}'] = codes
    return out, per_code


# --- Vertical text -------------------------------------------------------------------

def vertical_column(face_path, text):
    """Shape `text` top to bottom as a browser's HarfBuzz does, returning outlines placed in a column."""
    face = Face(face_path)
    blob = hb.Blob.from_file_path(str(face_path))
    font = hb.Font(hb.Face(blob))
    scale = 1000/face.upm
    buffer = hb.Buffer()
    buffer.add_str(text)
    buffer.direction, buffer.script, buffer.language = 'ttb', 'Kana', 'ja'
    hb.shape(font, buffer)
    gids = {name: i for i, name in enumerate(face.font.getGlyphOrder())}
    order = face.font.getGlyphOrder()
    cells, pen_y = [], 0
    for info, pos in zip(buffer.glyph_infos, buffer.glyph_positions):
        name = order[info.codepoint]
        pen, flat_pen = RelativePen(), FlattenPen()
        shift = (pos.x_offset*scale, -(pen_y + pos.y_offset*scale))
        matrix = (scale, 0, 0, -scale, shift[0], shift[1])
        face.glyphs[name].draw(TransformPen(pen, matrix))
        face.glyphs[name].draw(TransformPen(flat_pen, matrix))
        cells.append({'glyph': name, 'path': pen.path(), 'contours': flat_pen.contours,
                      'advance': round(-pos.y_advance*scale)})
        pen_y += pos.y_advance*scale
    return cells


def vertical_gsub_changes(face_path, text):
    """Glyph names the text maps to with and without OpenType shaping in the horizontal direction."""
    face = Face(face_path)
    font = hb.Font(hb.Face(hb.Blob.from_file_path(str(face_path))))
    out = []
    for direction in ('ltr', 'ttb'):
        buffer = hb.Buffer()
        buffer.add_str(text)
        buffer.direction, buffer.script, buffer.language = direction, 'Kana', 'ja'
        hb.shape(font, buffer)
        order = face.font.getGlyphOrder()
        out.append([order[i.codepoint] for i in buffer.glyph_infos])
    return out


# --- Raster images of third-party glyphs ----------------------------------------------------

_fonts = {}


def pil_font(path, size):
    if (path, size) not in _fonts:
        _fonts[(path, size)] = ImageFont.truetype(str(path), size)
    return _fonts[(path, size)]


def save_mask(mask, fid, kind):
    """Write a transparent PNG whose alpha is the ink; the page colours it with a CSS mask."""
    image = Image.merge('LA', (Image.new('L', mask.size, 0), mask))
    from io import BytesIO
    buffer = BytesIO()
    image.save(buffer, 'PNG', optimize=True)
    name = f'{fid}-{kind}-{hashlib.sha256(buffer.getvalue()).hexdigest()[:8]}.png'
    IMAGES.mkdir(exist_ok=True)
    (IMAGES/name).write_bytes(buffer.getvalue())
    return {'file': name, 'width': mask.width, 'height': mask.height, 'bytes': len(buffer.getvalue())}


def face_for(faces, cp):
    return next((f for f in faces if cp in f.cmap), None)


def draw_cp(canvas, faces, cp, x, y_base, em):
    face = face_for(faces, cp)
    ImageDraw.Draw(canvas).text((x, y_base), chr(cp), font=pil_font(face.path, em), fill=255, anchor='ls')


def atlas(fid, faces, cps):
    """A sheet of CELL px cells: one glyph per cell on a 1000-unit em box with the baseline at 880."""
    cps = [cp for cp in cps if face_for(faces, cp)]
    cols = 16
    rows = math.ceil(len(cps)/cols)
    sheet = Image.new('L', (cols*CELL, rows*CELL), 0)
    for i, cp in enumerate(cps):
        cell = Image.new('L', (CELL, CELL), 0)
        draw_cp(cell, faces, cp, 0, round(.88*CELL), CELL)
        sheet.paste(cell, ((i % cols)*CELL, (i//cols)*CELL))
    meta = save_mask(sheet, fid, 'atlas')
    return {**meta, 'cell': CELL, 'cols': cols, 'rows': rows, 'index': {f'{cp:X}': i for i, cp in enumerate(cps)}}


def dashed_box(draw, left, top, right, bottom):
    for x in range(int(left), int(right), 10):
        for y in (top, bottom):
            draw.line([(x, y), (min(x + 6, right), y)], fill=170, width=3)
    for y in range(int(top), int(bottom), 10):
        for x in (left, right):
            draw.line([(x, y), (x, min(y + 6, bottom))], fill=170, width=3)


def hero_image(fid, faces, text):
    """The hero line at 0.1 px per unit, advancing by each glyph's width."""
    em, x, items = 100, 0, []
    for char in text:
        cp = ord(char)
        face = face_for(faces, cp)
        items.append((cp, x, face is not None))
        x += 500 if char == '　' else (face.advance(cp) if face else 1000)
    canvas = Image.new('L', (round(x*em/1000), em), 0)
    draw = ImageDraw.Draw(canvas)
    for cp, at, present in items:
        px = at*em/1000
        if chr(cp) == '　':
            continue
        if present:
            draw_cp(canvas, faces, cp, px, round(.88*em), em)
        else:
            dashed_box(draw, px + 14, 18, px + 86, 96)
    return save_mask(canvas, fid, 'hero')


def vertical_image(fid, cells):
    """A vertical column at 0.3 px per unit; contours are filled even-odd on a 4x grid."""
    scale, grid = 0.3, 4
    width, height = 1080, len(cells)*1000 + 40
    size = (round(width*scale*grid), round(height*scale*grid))
    column = Image.new('L', size, 0)
    for cell in cells:
        ink = Image.new('1', size, 0)
        for contour in cell['contours']:
            layer = Image.new('1', size, 0)
            ImageDraw.Draw(layer).polygon([((x + 540)*scale*grid, (y + 20)*scale*grid) for x, y in contour], fill=1)
            ink = ImageChops.logical_xor(ink, layer)
        column = ImageChops.lighter(column, ink.convert('L'))
    mask = column.resize((round(width*scale), round(height*scale)), Image.LANCZOS)
    return save_mask(mask, fid, 'vertical')


def genseki_letters(entry):
    letters = {}
    for line in member_path(entry, 'README.md').read_text().splitlines():
        match = re.match(r'\| U\+(1B[01][0-9A-F])x \|(.*)\|', line)
        if match:
            for i, cell in enumerate(match[2].split('|')):
                if cell.strip() in ('A', 'B', 'C'):
                    letters[int(match[1], 16)*16 + i] = cell.strip()
    return letters


# --- Main ------------------------------------------------------------------------------

def build(local=None):
    manifest = verify(local)
    entries = {e['id']: e for e in manifest['files']}
    blocks, assigned, names, ages = unicode_data()
    kana_cps = {cp for name in KANA_BLOCKS for cp in range(blocks[name][0], blocks[name][1] + 1) if cp in assigned}
    new_in_18 = sorted(cp for cp in kana_cps if ages.get(cp) == '18.0')

    fonts, faces, rasters = [], {}, {}
    glyph_cps = set(range(0x1AFF0, 0x1B170)) | set(LIGATURES) | set(map(ord, HERO)) | {ord(c) for c, _ in NAMES} | set(map(ord, VERTICAL))
    glyph_cps -= {0x3000}
    glyphs, hero_widths = {}, {}
    usage = member_path(entries['sukima'], '使用例.txt').read_text(encoding='utf-8-sig')
    for _, quoted in NAMES:
        assert quoted in usage, f'Name missing from the usage list: {quoted}'

    for spec in SPECS:
        entry = entries[spec['id']]
        by_name = {p.name: p for p in member(manifest, spec['id'])}
        install = {n: by_name[n] for n in spec['install']}
        facts = font_facts(spec, entry, install)
        cmap = facts.pop('cmap')
        outline_faces = [Face(by_name[n]) for n in spec['outline']]
        faces[spec['id']] = outline_faces
        rasters[spec['id']] = Raster(outline_faces)
        union = set().union(*(set(f.cmap) for f in outline_faces))
        coverage = {}
        for name in [*KANA_BLOCKS, *OTHER_BLOCKS]:
            lo, hi = blocks[name]
            coverage[name] = sum(1 for cp in cmap if lo <= cp <= hi and cp in assigned)
        private = {cp for cp in cmap if 0xE000 <= cp <= 0xF8FF or 0xF0000 <= cp <= 0xFFFFD}
        glyphs[spec['id']] = {}
        for cp in sorted(glyph_cps & union):
            face = next(f for f in outline_faces if cp in f.cmap)
            if spec['id'] in VECTOR:
                glyphs[spec['id']][f'{cp:X}'] = [face.advance(cp), face.draw(cp)]
        paths = {n: by_name[n] for n in spec['install']}
        record = {
            'id': spec['id'], 'name': spec['name'], 'ja': spec['ja'], 'style': spec['style'],
            'version': entry['version'], 'date': entry['date'], 'date_basis': entry['date_basis'],
            'licence': entry['licence'], 'licence_url': entry['licence_url'],
            'reserved_name': reserved_name(entry, paths), 'url': entry['url'], 'page': entry['page'],
            'archive': entry['filename'], 'archive_sha256': entry.get('sha256'), 'credit': entry['credit'],
            'local_only': bool(entry.get('local_only')),
            'coverage': coverage, 'private_use': len(private),
            'hentaigana': sum(cp in cmap for cp in HENTAIGANA),
            'unicode18_kana': sum(cp in cmap for cp in new_in_18),
            'provenance': checked_provenance(entry, paths),
            **facts}
        fonts.append(record)

    # Origin counts recorded by the GenZui packages and GenSeki's README.
    serif_entry, sans_entry = entries['genzui-serif'], entries['genzui-sans']
    origins = {
        'genzui-serif': genzui_sources(serif_entry, 'GenZuiSerif-0.118.zip', 'sources.json'),
        'genzui-sans': genzui_sources(sans_entry, 'GenZuiSans-0.103.zip', 'sources.json'),
        'genseki': genseki_origins(entries['genseki'])}
    letters = genseki_letters(entries['genseki'])
    with ZipFile(member_path(sans_entry, 'GenZuiSans-0.103.zip')) as package:
        sans_kinds = json.loads(package.read('sources.json'))['source_kinds']
    taken = [cp for cp in range(0x1B100, 0x1B130) if sans_kinds.get(f'U+{cp:04X}', '').startswith('GenSeki')]
    origins['sans_genseki_extended_a'] = {'total': len(taken), 'sukima_marked': sum(letters.get(cp) == 'B' for cp in taken),
                                          'codepoints': [f'{cp:X}' for cp in taken]}

    # Similarity of the drawings, over the 286 hentaigana and over ordinary kana.
    hentaigana_ids = [f['id'] for f in fonts if f['hentaigana']]
    chart_cps = sorted(set(range(0x1AFF0, 0x1B170)) & set(cp for cp in glyph_cps))
    hentaigana_pairs, _ = similarity({i: rasters[i] for i in hentaigana_ids}, list(HENTAIGANA))
    chart_pairs, per_code = similarity({i: rasters[i] for i in hentaigana_ids}, chart_cps)
    kana_ids = [f['id'] for f in fonts if f['coverage']['Hiragana'] > 80 and f['coverage']['Katakana'] > 80]
    kana_pairs, _ = similarity({i: rasters[i] for i in kana_ids}, KANA_BASE)

    # Vertical text of the fonts that have the punctuation.
    vertical = {}
    for spec in SPECS:
        face = faces[spec['id']][0]
        if all(ord(c) in face.cmap for c in VERTICAL):
            path = member(manifest, spec['id'], name=spec['outline'][0])[0]
            horizontal, upright = vertical_gsub_changes(path, VERTICAL)
            vertical[spec['id']] = {'cells': vertical_column(path, VERTICAL),
                                    'substituted': [h != v for h, v in zip(horizontal, upright)]}

    # Raster images of every non-GenZui font: glyph atlas, hero line and vertical column.
    for old in IMAGES.glob('*.png') if IMAGES.exists() else []:
        old.unlink()
    images = {}
    for spec in SPECS:
        fid = spec['id']
        if fid in VECTOR:
            continue
        images[fid] = {'atlas': atlas(fid, faces[fid], sorted(glyph_cps)), 'hero': hero_image(fid, faces[fid], HERO)}
        if fid in vertical:
            images[fid]['vertical'] = vertical_image(fid, vertical[fid]['cells'])

    # Rare kanji of the usage list in the fonts that cover any of them.
    rare = [{'char': c, 'quoted': q, 'fonts': [f['id'] for f in fonts
                                               if any(ord(c) in face.cmap for face in faces[f['id']])]}
            for c, q in NAMES]

    kana_blocks = [{'name': n, 'first': blocks[n][0], 'last': blocks[n][1],
                    'assigned': sum(1 for cp in assigned if blocks[n][0] <= cp <= blocks[n][1])}
                   for n in [*KANA_BLOCKS, *OTHER_BLOCKS]]
    data = {
        'tools': {'fonttools': package_version('fonttools'), 'pillow': package_version('pillow'),
                  'numpy': package_version('numpy'), 'uharfbuzz': package_version('uharfbuzz'),
                  'harfbuzz': hb.version_string(), 'unicode': '18.0.0'},
        'checked': manifest['checked'],
        'blocks': kana_blocks,
        'milestones': {'hentaigana': len(HENTAIGANA), 'unicode18_kana': len(new_in_18),
                       'unicode18_codepoints': [f'{cp:X}' for cp in new_in_18]},
        'fonts': fonts,
        'origins': origins,
        'similarity': {'hentaigana': hentaigana_pairs, 'kana': kana_pairs,
                       'hentaigana_ids': hentaigana_ids, 'kana_ids': kana_ids,
                       'kana_count': len(KANA_BASE)},
        'chart_overlap': per_code,
        'chart_sets': {k: {'name': n, 'codepoints': [f'{cp:X}' for cp in r if cp in assigned]} for k, (n, r) in CHART_SETS.items()},
        'names': {f'{cp:X}': names[cp].title() for cp in chart_cps if cp in names},
        'rare': rare,
        'vertical_text': VERTICAL,
        'vertical': {k: {'substituted': v['substituted'], 'advances': [c['advance'] for c in v['cells']],
                         'glyphs': [c['glyph'] for c in v['cells']]} for k, v in vertical.items()},
        'hero': HERO,
        'images': images,
    }
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1, default=sorted) + '\n')
    GLYPHS.write_text(json.dumps({'unit': 1000, 'glyphs': glyphs,
                                  'vertical': {k: [c['path'] for c in v['cells']] for k, v in vertical.items() if k in VECTOR}},
                                 ensure_ascii=False, separators=(',', ':')) + '\n')
    print(f'{OUT.relative_to(ROOT)}: {OUT.stat().st_size:,} bytes; {GLYPHS.relative_to(ROOT)}: {GLYPHS.stat().st_size:,} bytes')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sukima', help='local copy of sukima-gothic_ver11.41.zip')
    build(parser.parse_args().sukima)
