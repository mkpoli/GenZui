"""Render the release card from the distributed font's actual outlines."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from serif import OUT, STEM, VERSION


def build_card(destination):
    scale = 2
    image = Image.new('RGB', (1200*scale, 630*scale), '#f7f8f2')
    draw = ImageDraw.Draw(image)
    font = str(OUT/(STEM+'.ttf'))
    ink, green, muted = '#25382e', '#214e3c', '#63776a'

    def rect(box, fill):
        draw.rectangle(tuple(round(x*scale) for x in box), fill=fill)

    def text(x, y, value, size, color=ink, sans=False):
        face = ImageFont.truetype('DejaVuSans.ttf' if sans else font, round(size*scale))
        draw.text((x*scale, y*scale), value, font=face, fill=color, anchor='ls')

    rect((628, 0, 1200, 630), green)
    text(58, 64, 'GENZUI SERIF', 20, green, True)
    text(435, 64, 'Unicode 18.0', 17, green, True)
    text(58, 222, '源萃明朝', 116)
    text(65, 275, 'げんずい', 24, muted)
    text(60, 369, '17,064', 46, green)
    text(357, 369, '286', 46, green)
    text(62, 401, 'CHARACTERS', 14, muted, True)
    text(360, 401, 'HENTAIGANA', 14, muted, True)
    rect((60, 434, 570, 435), '#cdd7cb')
    text(60, 465, 'BASED ON', 12, muted, True)
    text(60, 494, 'Noto Serif JP · Noto Serif Hentaigana', 17, ink, True)
    text(60, 521, 'FRB Taiwanese Kana', 17, ink, True)
    text(60, 589, 'genzui.mkpo.li', 24, green, True)

    points = [('𛄣', 'KOTO'), ('𛄤', 'TOKI'), ('𪜈', 'TOMO'),
              ('𛄥', 'TOTE'), ('𛄧', 'NE'), ('𛄨', 'WI')]
    for i, (character, label) in enumerate(points):
        x, y = 666+(i%3)*174, 238+(i//3)*232
        text(x, y, character, 142, '#f4f6ed')
        text(x+36, y+44, label, 16, '#bdd1c0', True)
    text(666, 63, 'HISTORICAL KANA', 17, '#bdd1c0', True)
    rect((666, 540, 1160, 541), '#4d725e')
    text(666, 588, '源萃明朝', 21, '#f4f6ed')
    text(1060, 588, VERSION, 18, '#bdd1c0', True)
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    image.save(destination/'genzui-social-2x.png', optimize=True)
    image.resize((1200, 630), Image.Resampling.LANCZOS).save(destination/'genzui-social.png', optimize=True)


if __name__ == '__main__':
    build_card(OUT.parent/'release/media')
