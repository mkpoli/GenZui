"""Render the GenZui Sans release card from the distributed font's outlines."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont

from sans_site import OUT, STEM, checked

ALT = ('源萃ゴシック / GenZui Sans. Archaic WU, then GenZui drawings: refitted KOTO, alternate NE and small archaic YE, '
       'SQUARE PAATU and a tally mark. {count} characters; 286 hentaigana; Unicode 18.0. Based on Noto Sans JP, '
       'Noto Sans Hentaigana and GenSeki Hentaigana Gothic. genzui.mkpo.li/sans.')


def build_card(destination):
    version, checks, _ = checked()
    scale = 2
    image = Image.new('RGB', (1200*scale, 630*scale), '#f7f8f2')
    draw = ImageDraw.Draw(image)
    font = str(OUT/(STEM+'.ttf'))
    ink, green, muted = '#25382e', '#214e3c', '#63776a'

    def rect(box, fill):
        draw.rectangle(tuple(round(x*scale) for x in box), fill=fill)

    def text(x, y, value, size, color=ink, sans=False, features=None):
        face = ImageFont.truetype('DejaVuSans.ttf' if sans else font, round(size*scale))
        draw.text((x*scale, y*scale), value, font=face, fill=color, anchor='ls', features=features)

    count = f"{len(TTFont(font).getBestCmap()):,}"
    rect((628, 0, 1200, 630), green)
    text(58, 64, 'GENZUI SANS', 20, green, True)
    text(435, 64, 'Unicode 18.0', 17, green, True)
    text(58, 222, '源萃ゴシック', 84)
    text(65, 275, 'げんずい', 24, muted)
    text(60, 369, count, 46, green)
    text(357, 369, '286', 46, green)
    text(62, 401, 'CHARACTERS', 14, muted, True)
    text(360, 401, 'HENTAIGANA', 14, muted, True)
    rect((60, 434, 570, 435), '#cdd7cb')
    text(60, 465, 'BASED ON', 12, muted, True)
    text(60, 494, 'Noto Sans JP · Noto Sans Hentaigana', 17, ink, True)
    text(60, 521, 'GenSeki Hentaigana Gothic', 17, ink, True)
    text(60, 589, 'genzui.mkpo.li/sans', 24, green, True)

    # Archaic WU, the three refitted kana and two drawn transcription symbols.
    points = [('𛄟', 'WU', None), ('𛄣', 'KOTO', None), ('𛄧', 'NE', None),
              ('𛅨', 'SMALL YE', None), ('㌬', 'PAATU', None), ('𝍵', 'TALLY', None)]
    for i, (character, label, features) in enumerate(points):
        x, y = 666+(i%3)*174, 238+(i//3)*232
        text(x, y, character, 142, '#f4f6ed', features=features)
        text(x+36, y+44, label, 16, '#bdd1c0', True)
    text(666, 63, 'HISTORICAL KANA · DRAWINGS', 17, '#bdd1c0', True)
    rect((666, 540, 1160, 541), '#4d725e')
    text(666, 588, '源萃ゴシック', 21, '#f4f6ed')
    text(1060, 588, version, 18, '#bdd1c0', True)
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    image.save(destination/'genzui-sans-social-2x.png', optimize=True)
    image.resize((1200, 630), Image.Resampling.LANCZOS).save(destination/'genzui-sans-social.png', optimize=True)
    return ALT.format(count=count)


if __name__ == '__main__':
    print(build_card(OUT.parent/'release/media'))
