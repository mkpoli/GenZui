"""Render the card announcing Bold for both families in the landing's colours.

Each family shows nine forms GenZui drew or refitted, in Regular above Bold.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from sans_site import BOLD_STEM as SANS_BOLD, OUT as SANS_OUT, STEM as SANS_REGULAR, checked
from serif import BOLD_STEM as SERIF_BOLD, OUT as SERIF_OUT, STEM as SERIF_REGULAR, VERSION as SERIF_VERSION

FIELD, PANEL, GREEN, MINT, GLOW, WHITE = '#06241a', '#0b3326', '#1f634d', '#86b09a', '#3fae84', '#f4f7f1'
# Serif: archaic WU, KOTO, TOKI, TOTE, YORI, alternate NE and WI, TOMO, NARI.
SERIF_FORMS = '𛄟𛄣𛄤𛄥𛄦𛄧𛄨𪜈𬼂'
# Sans: refitted KOTO, alternate NE and small YE, PAATU, two tally marks and
# three ideographic description characters.
SANS_FORMS = '𛄣𛄧𛅨㌬𝍴𝍶⿾⿿㇯'
ALT = ('GenZui, Regular and Bold, on a dark green grid. 源萃明朝 GenZui Serif, on a light card, shows archaic WU, '
       'KOTO, TOKI, TOTE, YORI, the alternate NE and WI, TOMO and NARI in Regular above Bold. 源萃ゴシック GenZui '
       'Sans, on a dark card, shows the refitted KOTO, alternate NE and small archaic YE, SQUARE PAATU, two tally '
       'marks, and three ideographic description characters in Regular above Bold. genzui.mkpo.li.')


def build_card(destination):
    s = 2
    image = Image.new('RGB', (1200*s, 630*s), FIELD)
    draw = ImageDraw.Draw(image)
    for x in range(0, 1200, 32):
        draw.line((x*s, 0, x*s, 630*s), fill='#0a2d21', width=s)
    for y in range(0, 630, 32):
        draw.line((0, y*s, 1200*s, y*s), fill='#0a2d21', width=s)

    def text(x, y, value, size, color, font=None, anchor='ls', spacing=0):
        face = ImageFont.truetype(str(font) if font else 'DejaVuSans.ttf', round(size*s))
        if not spacing:
            draw.text((x*s, y*s), value, font=face, fill=color, anchor=anchor)
            return
        width = sum(face.getlength(c) for c in value)/s + spacing*(len(value)-1)
        x = x - width if anchor == 'rs' else x
        for c in value:
            draw.text((x*s, y*s), c, font=face, fill=color, anchor='ls')
            x += face.getlength(c)/s + spacing

    def brackets(box, color):
        x0, y0, x1, y1 = box
        for (x, y, dx, dy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
            draw.line((x*s, y*s, (x+18*dx)*s, y*s), fill=color, width=2*s)
            draw.line((x*s, y*s, x*s, (y+18*dy)*s), fill=color, width=2*s)

    text(60, 62, '源萃', 26, WHITE, SERIF_OUT/(SERIF_BOLD+'.ttf'))
    text(118, 60, 'GENZUI', 13, MINT, spacing=4)
    text(1140, 60, 'REGULAR / BOLD', 13, GLOW, anchor='rs', spacing=4)
    families = [('源萃明朝', f'SERIF · {SERIF_VERSION}', SERIF_FORMS, SERIF_OUT/(SERIF_REGULAR+'.ttf'),
                 SERIF_OUT/(SERIF_BOLD+'.ttf'), WHITE, GREEN, '#5f7d6e', GREEN),
                ('源萃ゴシック', f'SANS · {checked()[0]}', SANS_FORMS, SANS_OUT/(SANS_REGULAR+'.ttf'),
                 SANS_OUT/(SANS_BOLD+'.ttf'), PANEL, WHITE, MINT, GLOW)]
    for i, (name, kind, forms, regular, bold, fill, ink, label, accent) in enumerate(families):
        top = 88 + i*250
        box = (60, top, 1140, top+236)
        draw.rectangle(tuple(v*s for v in box), fill=fill, outline=None if fill == WHITE else GREEN, width=s)
        brackets((54, top-6, 1146, top+242), GLOW)
        text(88, top+46, name, 32, ink, bold)
        text(88, top+68, kind, 11, label, spacing=3)
        for j, (style, font) in enumerate((('REGULAR', regular), ('BOLD', bold))):
            y = top + 132 + j*84
            text(88, y-20, style, 11, label, spacing=3)
            for k, form in enumerate(forms):
                text(262 + k*96, y, form, 58, ink, font)
        draw.line((88*s, (top+151)*s, 1112*s, (top+151)*s), fill=accent, width=s)
    text(60, 610, 'genzui.mkpo.li', 18, MINT, spacing=1)
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    image.save(destination/'genzui-bold-2x.png', optimize=True)
    image.resize((1200, 630), Image.Resampling.LANCZOS).save(destination/'genzui-bold.png', optimize=True)
    return ALT


if __name__ == '__main__':
    print(build_card(SANS_OUT.parent/'social'))
