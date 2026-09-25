"""Render the card announcing Bold for both families, each weight above the other."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from sans_site import BOLD_STEM as SANS_BOLD, OUT as SANS_OUT, STEM as SANS_REGULAR, checked
from serif import BOLD_STEM as SERIF_BOLD, OUT as SERIF_OUT, STEM as SERIF_REGULAR, VERSION as SERIF_VERSION

SAMPLE = 'あ𛀂 い𛀆 う𛀋　𛄣𛄤𪜈'
ALT = ('GenZui, Regular and Bold. 源萃明朝 GenZui Serif and 源萃ゴシック GenZui Sans, each set in '
       'Regular above Bold with the sample “あ𛀂 い𛀆 う𛀋 𛄣𛄤𪜈”: kana beside hentaigana, then the '
       'ligatures KOTO, TOKI and TOMO. genzui.mkpo.li.')


def build_card(destination):
    scale = 2
    image = Image.new('RGB', (1200*scale, 630*scale), '#f7f8f2')
    draw = ImageDraw.Draw(image)
    ink, green, muted, line = '#25382e', '#214e3c', '#63776a', '#cdd7cb'

    def text(x, y, value, size, color=ink, font=None, anchor='ls'):
        face = ImageFont.truetype(str(font) if font else 'DejaVuSans.ttf', round(size*scale))
        draw.text((x*scale, y*scale), value, font=face, fill=color, anchor=anchor)

    def rule(y):
        draw.rectangle((60*scale, y*scale, 1140*scale, y*scale+scale), fill=line)

    text(60, 64, 'GENZUI', 20, green)
    text(1140, 64, 'Regular · Bold', 17, green, anchor='rs')
    rows = [('源萃明朝', 'SERIF · '+SERIF_VERSION, SERIF_OUT/(SERIF_REGULAR+'.ttf'), SERIF_OUT/(SERIF_BOLD+'.ttf')),
            ('源萃ゴシック', 'SANS · '+checked()[0], SANS_OUT/(SANS_REGULAR+'.ttf'), SANS_OUT/(SANS_BOLD+'.ttf'))]
    for i, (name, kind, regular, bold) in enumerate(rows):
        top = 96 + i*238
        rule(top)
        text(60, top+36, kind, 14, muted)
        for j, (style, font) in enumerate((('REGULAR', regular), ('BOLD', bold))):
            y = top + 112 + j*96
            text(60, y-8, style, 13, muted)
            text(170, y, name, 50, ink, font)
            text(530, y, SAMPLE, 50, ink, font)
    rule(572)
    text(60, 610, 'genzui.mkpo.li', 22, green)
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    image.save(destination/'genzui-bold-2x.png', optimize=True)
    image.resize((1200, 630), Image.Resampling.LANCZOS).save(destination/'genzui-bold.png', optimize=True)
    return ALT


if __name__ == '__main__':
    print(build_card(SANS_OUT.parent/'social'))
