"""Swatches for the Regular/Bold switch: 源 in each weight of the page's family."""
from family_switch import label_face

SWATCH = '源'


def css(regular, bold):
    """Few-kilobyte faces, so drawing the Bold swatch never loads the Bold webfont."""
    return ''.join(f"@font-face{{font-family:GenZuiSwatch;src:url({label_face(path, SWATCH)}) format('woff2');"
                   f"font-weight:{weight};font-display:block}}\n"
                   for path, weight in ((regular, 400), (bold, 700)))
