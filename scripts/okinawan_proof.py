"""Build the local Okinawan type comparison from the current font.

Optional reference fonts are read from a local directory. They are only copied
into the ignored study output; they are not packaged with GenZui or its site.
"""
import argparse
import html
import json
import shutil
from pathlib import Path
from fontTools import subset
from fontTools.ttLib import TTFont
from okinawan import ENTRIES
from sources import ROOT

OUT = ROOT/'build/okinawan'


def build(reference_dir=None):
    OUT.mkdir(parents=True, exist_ok=True)
    fonts = OUT/'fonts'; fonts.mkdir(exist_ok=True)
    home = OUT/'home'
    if not home.exists() and not home.is_symlink():
        home.symlink_to(Path('../site'), target_is_directory=True)
    shutil.copyfile(ROOT/'build/serif/GenZuiSerif-Regular.woff2', fonts/'genzui.woff2')
    shutil.copyfile(ROOT/'releases/v0.114/GenZuiSerif-Regular.woff2', fonts/'previous.woff2')
    references = {}
    if reference_dir:
        for key, filename in [('fk', 'FK-Okinawa-reference.ttf'),
                              ('nishiki', 'nishiki-teki.ttf'),
                              ('mgen', 'mgenkanaplus.woff2'),
                              ('xim', 'Xim-Sans-Handwritten.ttf')]:
            source = reference_dir/filename
            if not source.is_file():
                continue
            font = TTFont(source, recalcTimestamp=False)
            covered = set(font.getBestCmap())
            points = set(range(0xF450, 0xF46B)) | {int(e['output'][0], 16) for e in ENTRIES}
            options = subset.Options(); options.recalc_timestamp = False
            sub = subset.Subsetter(options=options); sub.populate(unicodes=points & covered); sub.subset(font)
            font.flavor = 'woff2'; font.save(fonts/(key+'.woff2'))
            references[key] = sorted(points & covered)
        image = reference_dir/'frokinawa-sample.jpg'
        if image.is_file():shutil.copyfile(image, OUT/'frokinawa-sample.jpg')
    groups = {'funatsu': [], 'prefecture': []}
    for entry in ENTRIES:
        text = ''.join(chr(int(cp,16)) for cp in entry['output'])
        label = entry['label'] if entry['system']=='funatsu' else entry['label'].replace('Raised ', '')
        groups[entry['system']].append(
            f'<article class="letter" data-id="{html.escape(entry["id"],quote=True)}">'
            f'<header><strong>{html.escape(label)}</strong><span>{html.escape(entry.get("kana") or "")}</span></header>'
            '<div class="pair">'
            f'<div><span class="glyph new" lang="ryu">{text}</span><small>GenZui</small></div>'
            '<div><span class="glyph reference" lang="ryu"></span><small class="reference-label"></small></div>'
            '</div>'
            f'<p class="codes">{" + ".join("U+"+cp for cp in entry["output"])}</p></article>')
    page = (ROOT/'templates/okinawan.html').read_text()
    if not (OUT/'frokinawa-sample.jpg').is_file():
        start = page.index('<figure>')
        end = page.index('</figure>', start) + len('</figure>')
        page = page[:start] + page[end:]
    for key, value in {'{{FUNATSU}}': ''.join(groups['funatsu']),
                       '{{RAISED}}': ''.join(groups['prefecture']),
                       '{{DATA}}': json.dumps({'entries':ENTRIES,'references':references},ensure_ascii=False).replace('<','\\u003c')}.items():
        page=page.replace(key,value)
    (OUT/'index.html').write_text(page)
    print(f'Okinawan comparison: {len(ENTRIES)} forms; {len(references)} reference fonts.')
    return OUT


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--references',type=Path)
    build(parser.parse_args().references)
