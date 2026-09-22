"""Render the site's share card: both families, from the distributed fonts' outlines."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont

from serif import OUT, STEM, VERSION
from sans_site import OUT as SANS_OUT, STEM as SANS_STEM, checked as sans_checked

ALT = ('源萃 / GenZui: GenZui Serif 源萃明朝 and GenZui Sans 源萃ゴシック. Archaic WU, KOTO and alternate NE '
       'in both families. {serif} and {sans} characters; 286 hentaigana; Unicode 18.0. '
       'Based on Noto Serif JP, Noto Sans JP and Noto Hentaigana. genzui.mkpo.li.')


def build_card(destination):
    sans_version, _, _ = sans_checked()
    scale = 2
    image = Image.new('RGB', (1200*scale, 630*scale), '#f7f8f2')
    draw = ImageDraw.Draw(image)
    serif, sans = str(OUT/(STEM+'.ttf')), str(SANS_OUT/(SANS_STEM+'.ttf'))
    ink, green, muted = '#25382e', '#214e3c', '#63776a'

    def rect(box, fill):
        draw.rectangle(tuple(round(x*scale) for x in box), fill=fill)

    def text(x, y, value, size, color=ink, face=None, features=None):
        font = ImageFont.truetype(face or 'DejaVuSans.ttf', round(size*scale))
        draw.text((x*scale, y*scale), value, font=font, fill=color, anchor='ls', features=features)

    counts = {name: f'{len(TTFont(path).getBestCmap()):,}' for name, path in (('serif', serif), ('sans', sans))}
    rect((628, 0, 1200, 630), green)
    text(58, 64, 'GENZUI', 20, green)
    text(435, 64, 'Unicode 18.0', 17, green)
    text(58, 198, '源萃', 120, ink, serif)
    text(62, 256, '源萃明朝', 36, ink, serif)
    text(262, 256, '源萃ゴシック', 36, ink, sans)
    text(65, 295, 'げんずい · Serif & Sans', 20, muted, sans)
    text(60, 355, counts['serif'], 40, green)
    text(60, 385, 'SERIF CHARACTERS', 13, muted)
    text(300, 355, counts['sans'], 40, green)
    text(300, 385, 'SANS CHARACTERS', 13, muted)
    text(60, 434, '286', 40, green)
    text(60, 464, 'HENTAIGANA', 13, muted)
    rect((60, 490, 570, 491), '#cdd7cb')
    text(60, 521, 'BASED ON  Noto Serif JP · Noto Sans JP · Noto Hentaigana', 15, ink)
    text(60, 589, 'genzui.mkpo.li', 24, green)

    # GenZui's own drawings in both families.
    points = [('𛄟', 'WU', None), ('𛄣', 'KOTO', None), ('𛄧', 'NE', None)]
    for row, (face, label) in enumerate(((serif, 'SERIF · 源萃明朝'), (sans, 'SANS · 源萃ゴシック'))):
        y = 236+row*232
        text(666, y-142, label, 15, '#bdd1c0', face)
        for i, (character, name, features) in enumerate(points):
            x = 666+i*174
            text(x, y, character, 128, '#f4f6ed', face, features)
            text(x+30, y+40, name, 15, '#bdd1c0')
    text(666, 63, 'HISTORICAL KANA', 17, '#bdd1c0')
    rect((666, 540, 1160, 541), '#4d725e')
    text(666, 588, '源萃', 21, '#f4f6ed', serif)
    text(1000, 588, f'{VERSION} · {sans_version}', 16, '#bdd1c0')
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    image.save(destination/'genzui-social-2x.png', optimize=True)
    image.resize((1200, 630), Image.Resampling.LANCZOS).save(destination/'genzui-social.png', optimize=True)
    return ALT.format(serif=counts['serif'], sans=counts['sans'])


if __name__ == '__main__':
    print(build_card(OUT.parent/'release/media'))
