"""Cut GenZui Serif Kugyol and GenZui Sans Kugyol from the full GenZui faces.

Each subset keeps exactly the 구결자 the parent draws at U+F67E-U+F77C (the
`gugyeol` registry's drawable set, never a hard-coded count), plus SPACE and
IDEOGRAPHIC SPACE when the parent has them. The parent TTFs must already be
built (see README) — this script only reads and cuts them.
"""
from fontTools import subset
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

from gugyeol import PUA as GUGYEOL_PUA
from sources import ROOT

OUT = ROOT / 'build/kugyol'
SPACES = (0x20, 0x3000)

FACES = (
    {'root': ROOT / 'build/serif', 'family': 'GenZui Serif Kugyol',
     'family_ja': '源萃明朝 口訣',
     'styles': {'Regular': ('GenZuiSerif-Regular', 'GenZuiSerifKugyol-Regular'),
                'Bold': ('GenZuiSerif-Bold', 'GenZuiSerifKugyol-Bold')}},
    {'root': ROOT / 'build/sans', 'family': 'GenZui Sans Kugyol',
     'family_ja': '源萃ゴシック 口訣',
     'styles': {'Regular': ('GenZuiSans-Regular', 'GenZuiSansKugyol-Regular'),
                'Bold': ('GenZuiSans-Bold', 'GenZuiSansKugyol-Bold')}},
)


def repertoire(parent):
    """The kept code points: the drawable 구결자 plus the parent's spaces."""
    cmap = parent.getBestCmap()
    missing = set(GUGYEOL_PUA) - set(cmap)
    assert not missing, f'parent is missing {[hex(c) for c in sorted(missing)]}'
    return set(GUGYEOL_PUA) | {cp for cp in SPACES if cp in cmap}


def parent_name(parent, nid):
    return next(r.toUnicode() for r in parent['name'].names
                if r.nameID == nid and r.platformID == 3 and r.platEncID == 1 and r.langID == 0x409)


def parent_version(parent):
    text = next(r.toUnicode() for r in parent['name'].names
                if r.nameID == 5 and r.platformID == 3 and r.platEncID == 1)
    assert text.startswith('Version ')
    return text.removeprefix('Version ')


def cut(parent_path, points):
    font = TTFont(parent_path, recalcTimestamp=False)
    options = subset.Options()
    options.recalc_timestamp = False
    options.notdef_outline = True
    sub = subset.Subsetter(options=options)
    sub.populate(unicodes=points)
    sub.subset(font)
    # None of the kept glyphs (PUA 구결자 and the two spaces) carry layout
    # features, so GSUB/GPOS are left as empty skeletons; drop them outright.
    for tag in ('GSUB', 'GPOS'):
        if tag in font and not font[tag].table.FeatureList.FeatureRecord:
            del font[tag]
    return font


def rename(font, family, family_ja, style, stem, version, notice, license_text, license_url):
    """Mirror the parent's name-table pattern: English and Japanese records,
    no other localizations, no Korean record. Copyright and licence strings
    are carried from the parent verbatim."""
    font['name'].names = []
    en = {0: notice, 1: family, 2: style, 3: f'{version};{stem}',
          4: f'{family} {style}', 5: f'Version {version}', 6: stem,
          13: license_text, 14: license_url, 16: family, 17: style}
    for nid, value in en.items():
        font['name'].setName(value, nid, 3, 1, 0x409)
    ja = {1: family_ja, 2: style, 4: f'{family_ja} {style}', 16: family_ja, 17: style}
    for nid, value in ja.items():
        font['name'].setName(value, nid, 3, 1, 0x411)
    font['head'].fontRevision = float(version)


def save(font, stem):
    OUT.mkdir(parents=True, exist_ok=True)
    font.save(OUT / f'{stem}.ttf')
    font.flavor = 'woff2'
    font.save(OUT / f'{stem}.woff2')


def build_face(root, family, family_ja, style, parent_stem, kugyol_stem):
    parent_path = root / f'{parent_stem}.ttf'
    with TTFont(parent_path) as parent:
        points = repertoire(parent)
        notice = parent_name(parent, 0)
        license_text = parent_name(parent, 13)
        license_url = parent_name(parent, 14)
        version = parent_version(parent)
    font = cut(parent_path, points)
    rename(font, family, family_ja, style, kugyol_stem, version, notice, license_text, license_url)
    save(font, kugyol_stem)
    print(f'Built {family} {style} {version}: {len(font.getBestCmap())} encoded characters.')


def build():
    for face in FACES:
        for style, (parent_stem, kugyol_stem) in face['styles'].items():
            build_face(face['root'], face['family'], face['family_ja'], style, parent_stem, kugyol_stem)
    proof()


def proof():
    """Contact sheet of all 181 구결자 in each of the four cut fonts."""
    cols, cell, label_h = 20, 46, 22
    rows = -(-len(GUGYEOL_PUA) // cols)
    width = cols * cell
    section_h = label_h + rows * cell
    label_font = ImageFont.truetype('DejaVuSans.ttf', 15)
    image = Image.new('RGB', (width, len(FACES) * 2 * section_h + 10), '#f7f5ef')
    draw = ImageDraw.Draw(image)
    y = 5
    for face in FACES:
        for style, (_, kugyol_stem) in face['styles'].items():
            draw.text((6, y + 3), f'{face["family"]} {style}', font=label_font, fill='#182620')
            glyph_font = ImageFont.truetype(str(OUT / f'{kugyol_stem}.ttf'), 34)
            for i, cp in enumerate(GUGYEOL_PUA):
                x = (i % cols) * cell
                gy = y + label_h + (i // cols) * cell
                draw.text((x + 6, gy + 2), chr(cp), font=glyph_font, fill='#182620')
            y += section_h
    image.save(OUT / 'proof.png')
    print(f'Wrote {OUT / "proof.png"}')


if __name__ == '__main__':
    build()
