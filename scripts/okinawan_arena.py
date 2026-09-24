"""A cull round of variants for one Okinawan letter, as a self-contained page.

    okinawan_arena.py <slug> <round> [--kept result.json]

Variants are the letter's merge builder sampled around its defaults: a
Latin-hypercube sample over each parameter's range, plus the defaults
themselves. Round N > 1 takes the cull result of round N - 1 (the JSON the
page copies) and samples again around the kept forms with the ranges halved.
Each variant is a small font, the GenZui build cut down to the page's text
with that variant in place of the letter; every font is embedded, so the page
opens from disk. Output stays in the ignored build directory.
"""
import argparse
import base64
import hashlib
import html
import io
import json
import random

import pathops
from fontTools import subset
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont

import okinawan_merge
from serif import contours
from sources import ROOT

BASE = ROOT/'build/serif/GenZuiSerif-Regular.ttf'
V1 = ROOT/'build/okinawan/fonts/rev-cf0bee0.woff2'
OUT = ROOT/'build/okinawan/arena'
TEMPLATES = ROOT/'templates/arena'

LETTERS = {
    'glottal-ya': dict(
        code=0xF45D, label='Glottal YA', build=okinawan_merge.glottal_ya,
        defaults=okinawan_merge.YA_DEFAULTS,
        ranges=dict(shift=(35, 95), arm_cut=(245, 315), mark_cut=(430, 530), mark_x=(-30, 30),
                    mark_dy=(-30, 30), mark_len=(0.82, 1.12), outer_drop=(10, 80),
                    outer_k=(0.35, 0.75), inner_k=(0.28, 0.62)),
        chart='glottal-ya',
        big='やや', vertical='ー、やー。',
        passages=[('Beside や', 'やや　やゆよ　ゆよ'),
                  ('Among kana', 'あいうえお　かきく'),
                  ('Chart word', 'ー（君、お前）　ーー')],
    ),
}


def sample(ranges, n, seed):
    rng = random.Random(seed)
    cols = {}
    for key, (lo, hi) in ranges.items():
        cells = list(range(n)); rng.shuffle(cells)
        cols[key] = [lo + (hi - lo) * (c + rng.random()) / n for c in cells]
    return [{k: (round(cols[k][i], 3) if isinstance(ranges[k][0], float) else round(cols[k][i])) for k in ranges}
            for i in range(n)]


def around(centres, ranges, n, seed):
    """Samples around kept forms, each range halved and centred on a kept form."""
    out = []
    for i in range(n):
        c = centres[i % len(centres)]
        local = {}
        for k, (lo, hi) in ranges.items():
            half = (hi - lo) / 4
            local[k] = (max(lo, c[k] - half), min(hi, c[k] + half))
            if isinstance(lo, int):
                local[k] = (round(local[k][0]), round(local[k][1]))
        out += sample(local, 1, seed + i)
    return out


def text_of(letter):
    return letter['big'] + letter['vertical'] + ''.join(t for _, t in letter['passages']) + 'あいうえおかきくけこやゆよ'


def cut_font(path, text):
    font = TTFont(path)
    options = subset.Options(); options.layout_features = ['*']; options.name_IDs = ['*']
    sub = subset.Subsetter(options=options)
    sub.populate(text=text + '（）、。　ー')
    sub.subset(font)
    return font


def with_variant(font, code, pen):
    shape = pathops.Path()
    part = RecordingPen()
    for op, args in pen.value:
        part.value.append((op, args))
        if op == 'closePath':
            piece = pathops.Path(); part.replay(piece.getPen())
            shape = pathops.op(shape, piece, pathops.PathOp.UNION)
            part = RecordingPen()
    tt = TTGlyphPen(None)
    shape.draw(Cu2QuPen(tt, max_err=0.5, reverse_direction=False))
    name = font.getBestCmap()[code]
    font['glyf'][name] = glyph = tt.glyph()
    glyph.recalcBounds(font['glyf'])
    font['hmtx'][name] = (1000, glyph.xMin)
    if 'vmtx' in font:
        font['vmtx'][name] = (1000, 880 - glyph.yMax)
    font.flavor = 'woff2'
    data = io.BytesIO(); font.save(data)
    return data.getvalue()


def face(name, data):
    return f'@font-face{{font-family:{name};src:url(data:font/woff2;base64,{base64.b64encode(data).decode()}) format("woff2")}}'


def build(slug, round_no, kept=None):
    letter = LETTERS[slug]
    text = text_of(letter)
    source = TTFont(BASE)
    if kept:
        centres = [kept[t] for t in kept]
        params = centres + around(centres, letter['ranges'], 24 - len(centres), 1000 * round_no)
    else:
        params = [dict(letter['defaults'])] + sample(letter['ranges'], 23, 1000 * round_no)
    fonts, forms = {}, {}
    for p in params:
        try:
            pen = letter['build'](source, contours, **p)
        except Exception as error:   # a sample whose cuts do not meet the stroke
            print(f'skipped {p}: {error}')
            continue
        token = 't' + hashlib.sha1(json.dumps(p, sort_keys=True).encode()).hexdigest()[:16]
        fonts[token] = with_variant(cut_font(BASE, text), letter['code'], pen)
        forms[token] = p
    context = cut_font(BASE, text); context.flavor = 'woff2'
    ctx = io.BytesIO(); context.save(ctx)
    faces = face('GenZuiContext', ctx.getvalue()) + ''.join(face(t, d) for t, d in fonts.items())
    references = ''
    if V1.is_file():
        v1 = cut_font(V1, text); v1.flavor = 'woff2'; b = io.BytesIO(); v1.save(b)
        faces += face('V1Reference', b.getvalue())
        references += f'<div><small>Earlier drawing (v1)</small><div class="reference-glyph" style="font-family:V1Reference">{chr(letter["code"])}</div></div>'
    chart = ROOT/'build/okinawan/chart'/f'{letter["chart"]}.png'
    if chart.is_file():
        references += (f'<div><small>Funatsu’s chart</small><img alt="The letter in Funatsu’s chart" style="height:120px" '
                       f'src="data:image/png;base64,{base64.b64encode(chart.read_bytes()).decode()}"></div>')
    experiment = f'okinawan-{slug}-{round_no}'
    config = dict(EXPERIMENT=experiment, CANDIDATES=list(fonts), PASSAGES=[t for _, t in letter['passages']],
                  PASSAGE_LABELS=[l for l, _ in letter['passages']], BIG=letter['big'], VERTICAL=letter['vertical'])
    config_js = ''.join(f'const {k}={json.dumps(v, ensure_ascii=False)};' for k, v in config.items())
    body = (TEMPLATES/'cull.html').read_text()
    body = body.replace('__GLYPH__', f'<span class="glyph">{html.escape(letter["label"])}</span>')
    body = body.replace('__FOOTER__', f'Round {round_no} · {len(fonts)} forms · GenZui Serif with each variant of {html.escape(letter["label"])}.')
    if references:
        body = body.replace('<section id="tools">', f'<details class="font-references" open><summary>References</summary>'
                            f'<div class="reference-fonts">{references}</div></details><section id="tools">')
    js = (TEMPLATES/'cull.js').read_text()
    page = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{html.escape(letter["label"])} — GenZui arena</title><style>{faces}{(TEMPLATES/"arena.css").read_text()}'
            f'{(TEMPLATES/"cull.css").read_text()}</style></head><body>{body}<script>{config_js}\n{js}</script></body></html>')
    out = OUT/slug; out.mkdir(parents=True, exist_ok=True)
    (out/f'round{round_no}.html').write_text(page)
    (out/f'round{round_no}-forms.json').write_text(json.dumps(forms, indent=1) + '\n')
    print(f'{slug} round {round_no}: {len(fonts)} forms -> {out/f"round{round_no}.html"}')
    return out/f'round{round_no}.html'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('slug', choices=sorted(LETTERS))
    parser.add_argument('round', type=int)
    parser.add_argument('--kept', help='the previous round’s copied cull result (JSON file)')
    args = parser.parse_args()
    kept = None
    if args.kept:
        result = json.loads(open(args.kept).read())
        forms = json.loads((OUT/args.slug/f'round{args.round - 1}-forms.json').read_text())
        kept = {t: forms[t] for t in result['kept']}
    build(args.slug, args.round, kept)
