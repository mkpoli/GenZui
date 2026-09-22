"""The Serif/Sans switch shared by the two family pages."""
import base64
import io

from fontTools import subset
from fontTools.ttLib import TTFont

from sources import ROOT

LABELS = {'serif': ('源萃明朝', 'SERIF', 'index.html', ROOT/'build/serif/GenZuiSerif-Regular.woff2'),
          'sans': ('源萃ゴシック', 'SANS', 'sans.html', ROOT/'build/sans/GenZuiSans-Regular.woff2')}


def label_face(path, text):
    """A few-kilobyte subset so each label can be set in its own family."""
    font = TTFont(path, recalcTimestamp=False)
    font.flavor = None
    options = subset.Options(flavor='woff2', hinting=False, layout_features=[], name_IDs=[0, 1, 2, 3, 4, 5, 6, 13, 14])
    subsetter = subset.Subsetter(options)
    subsetter.populate(text=text)
    subsetter.subset(font)
    font.flavor = 'woff2'
    stream = io.BytesIO()
    font.save(stream)
    return 'data:font/woff2;base64,' + base64.b64encode(stream.getvalue()).decode()


def css():
    faces = ''.join(f"@font-face{{font-family:GenZuiLabel-{key};src:url({label_face(path, text)}) format('woff2');font-weight:400;font-display:block}}\n"
                    for key, (text, _, _, path) in LABELS.items())
    return faces + (ROOT/'site/family-switch.css').read_text()


def html(current):
    assert current in LABELS
    items = []
    for key, (text, kind, href, _) in LABELS.items():
        current_attr = ' aria-current="page"' if key == current else ''
        items.append(f'<a href="{href}"{current_attr} data-family="{key}"><span lang="ja">{text}</span><small>{kind}</small></a>')
    # A div, not nav: the header's mobile rules hide its nav element.
    return '<div class="family-switch" role="group" aria-label="Font family">' + ''.join(items) + '</div>'
