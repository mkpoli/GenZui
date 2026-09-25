"""A cull round of variants for one Okinawan letter, as a self-contained page.

    okinawan_arena.py <slug> <round> [--kept previous-cull.json]
    okinawan_arena.py <slug> <round> --compare this-cull.json
    okinawan_arena.py <slug> <round> --axes <earlier round>:<token>

Variants are the letter's merge builder sampled around its defaults: a
Latin-hypercube sample over each parameter's range, plus the defaults
themselves. Round N > 1 takes the cull result of round N - 1 (the JSON the
page copies) and samples again around the kept forms with the ranges halved.
Each variant is a small font, the GenZui build cut down to the page's text
with that variant in place of the letter; every font is embedded, so the page
opens from disk. Output stays in the ignored build directory.
"""
import argparse
import functools
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
        # narrowed after round 1: joints are now curvature-fair, and the kept
        # forms moved や further right and cut the arm later
        ranges=dict(shift=(45, 100), arm_cut=(250, 300), mark_cut=(460, 500), mark_x=(-25, 20),
                    mark_dy=(-5, 20), mark_len=(0.82, 1.1), outer_full=(0.8, 1.2), inner_full=(0.8, 1.2)),
        # one factor at a time: seven steps, the base in the middle; each step
        # changes only the listed parameters, by these amounts
        axes=[
            ('gap', 'Gap between the mark and や', 'The mark moves toward or away from や; や stays.', {'mark_x': 15}),
            ('position', 'Position of the whole letter', 'Mark and や move together within the em.', {'mark_x': 20, 'shift': 20}),
            ('mark_len', 'Length of the mark', 'The mark grows or shrinks above the turn.', {'mark_len': 0.05}),
            ('mark_height', 'Height of the mark', 'The mark moves up or down; the turn follows.', {'mark_dy': 15}),
            ('arm_join', 'Where the turn meets the arm', 'The turn joins the arm nearer to or further from the start.', {'arm_cut': 14}),
            ('mark_join', 'Where the mark enters the turn', 'The mark is cut higher or lower above the turn.', {'mark_cut': 14}),
            ('turn', 'Fullness of the turn', 'Both curves of the turn together, tighter to fuller.', {'outer_full': 0.07, 'inner_full': 0.07}),
        ],
        # the same, for the thickness of each part of the mark
        thickness=[
            ('mark_w', 'Width of the whole mark', 'The mark is thinner or thicker from the turn to its head.', {'neck_w': 0.09, 'head_w': 0.09}),
            ('head_w', 'Width of the head', 'Only the upper mark and its head; the neck stays.', {'head_w': 0.1}),
            ('neck_w', 'Width of the neck', 'Only where the mark enters the turn; the head stays.', {'neck_w': 0.1}),
            ('turn_w', 'Thickness of the turn', 'The outer curve swells as the inner corner tightens, or the reverse.', {'outer_full': 0.13, 'inner_full': -0.13}),
        ],
        # the angle of the mark, with a check on its thickness
        angle=[
            ('angle_neck', 'Angle of the mark, turning about its foot', 'The head swings left or right; the join stays.', {'mark_angle': 4.0}),
            ('angle_head', 'Angle of the mark, turning about its head', 'The foot and the join swing; the head stays.', {'mark_angle': 4.0, 'mark_x': 20}),
            ('mark_w', 'Width of the whole mark', 'A finer check around the chosen widths.', {'neck_w': 0.05, 'head_w': 0.05}),
        ],
        chart='glottal-ya',
        big='やや', vertical='ー、やー。',
        passages=[('Beside や', 'やや　やゆよ　ゆよ'),
                  ('Among kana', 'あいうえお　かきく'),
                  ('Chart word', 'ー（君、お前）　ーー')],
    ),
}

# After the round-1 cull of YU: the kept marks stood upright or leant left
# (angle -1 to 4), and the note asked for a smaller mark, as in YA, beside a
# bigger ゆ, the two roughly parallel.
BESIDE_RANGES = dict(mark_len=(0.75, 0.95), mark_scale=(0.65, 0.9), gap=(30, 90), mark_dy=(20, 110),
                     mark_angle=(-1.0, 4.0), kana_sx=(0.8, 0.92), kana_sy=(0.94, 1.0))
for _slug, _code, _label, _kana, _vowels in (('glottal-yu', 0xF45E, 'Glottal YU', 'ゆ', 'やゆよ'),
                                             ('glottal-yo', 0xF45F, 'Glottal YO', 'よ', 'やゆよ')):
    _g = chr(_code)
    LETTERS[_slug] = dict(
        code=_code, label=_label, build=functools.partial(okinawan_merge.glottal_beside, kana=_kana),
        defaults=okinawan_merge.BESIDE_DEFAULTS, ranges=BESIDE_RANGES, chart=_slug,
        big=f'{_kana}{_g}{_kana}', vertical=f'{chr(0xF45D)}{_g}{chr(0xF45F if _kana == "ゆ" else 0xF45E)}、{_kana}{_g}。',
        passages=[(f'Beside {_kana}', f'{_kana}{_g}{_kana}　{_vowels}'),
                  ('Among kana', f'あいう{_g}えお　かきく'),
                  ('The glottal set', f'{chr(0xF45D)}{chr(0xF45E)}{chr(0xF45F)}　い{_g}は{_g}')],
        axes=[
            ('mark_height', 'Height of the mark', 'The mark moves up or down; ゆ stays.', {'mark_dy': 25}),
            ('mark_size', 'Size of the mark', 'The whole mark grows or shrinks about its foot.', {'mark_scale': 0.05}),
            ('mark_len', 'Length of the mark', 'The mark is stretched or shortened upward only.', {'mark_len': 0.05}),
            ('mark_angle', 'Angle of the mark', 'Positive steps lean the mark left.', {'mark_angle': 2.0}),
            ('gap', 'Gap between the mark and the kana', 'The mark moves toward or away from the kana.', {'gap': 12}),
            ('kana_w', 'Width of the kana', 'The kana is narrower or wider; the mark stays.', {'kana_sx': 0.03}),
            ('kana_h', 'Height of the kana', 'The kana is shorter or taller; the mark stays.', {'kana_sy': 0.02}),
        ],
        # the rows still open once the mark's height is settled, in finer steps
        refine=[
            ('mark_height', 'Height of the mark', 'Finer steps around the chosen height.', {'mark_dy': 12}),
            ('mark_size', 'Size of the mark', 'The whole mark grows or shrinks about its foot.', {'mark_scale': 0.04}),
            ('mark_len', 'Length of the mark', 'The mark is stretched or shortened upward only.', {'mark_len': 0.05}),
            ('mark_angle', 'Angle of the mark', 'Positive steps lean the mark left.', {'mark_angle': 2.0}),
            ('gap', 'Gap between the mark and the kana', 'The mark moves toward or away from the kana.', {'gap': 9}),
            ('kana_w', 'Width of the kana', 'The kana is narrower or wider; the mark stays.', {'kana_sx': 0.025}),
        ],
        # YO starts from YU: the mark keeps YU's shape, so only its place and
        # the kana beside it change
        start=[
            ('mark_height', 'Height of the mark', 'The mark moves up or down; the kana stays.', {'mark_dy': 20}),
            ('mark_size', 'Size of the mark', 'The whole mark grows or shrinks about its foot.', {'mark_scale': 0.04}),
            ('gap', 'Gap between the mark and the kana', 'The mark moves toward or away from the kana.', {'gap': 10}),
            ('kana_w', 'Width of the kana', 'The kana is narrower or wider; the mark stays.', {'kana_sx': 0.03}),
            ('kana_h', 'Height of the kana', 'The kana is shorter or taller; the mark stays.', {'kana_sy': 0.02}),
            ('kana_bold', 'Weight of the kana', 'Width given back to the kana’s strokes, sideways only; -3 is none.', {'kana_bold': 2}),
        ],
        # where the mark sits: one row per height, the gap to the kana across
        # (Funatsu sets YO's mark high, above よ's loop)
        position=[(f'h{dy}', f'Mark raised {dy}', 'Across the row the mark moves from close to far from the kana.',
                   {'gap': 15}, {'mark_dy': dy}) for dy in (150, 210, 270, 330, 390)],
        # weight of the narrowed kana and of the mark beside it
        weight=[
            ('kana_bold', 'Weight of the kana', 'Width given back to the kana’s strokes, sideways only; -3 is none.', {'kana_bold': 4}),
            ('mark_w', 'Weight of the mark', 'The mark is thinner or thicker from foot to head.', {'neck_w': 0.05, 'head_w': 0.05}),
            ('kana_w', 'Width of the kana', 'The kana is narrower or wider; the mark stays.', {'kana_sx': 0.025}),
        ],
    )


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
    """The font with the letter replaced. A builder returns one pen, whose
    contours are united one by one, or a list of parts, each a whole shape."""
    shape = pathops.Path()
    if isinstance(pen, list):
        for part in pen:
            piece = pathops.Path(); part.replay(piece.getPen())
            shape = pathops.op(shape, piece, pathops.PathOp.UNION)
    else:
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


def variants(letter, params):
    """One small font per parameter set, keyed by an anonymous token."""
    source, text = TTFont(BASE), text_of(letter)
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
    return fonts, forms


def page(slug, round_no, stage, fonts, extra=None):
    """The cull or compare page for a round, with every font embedded."""
    letter = LETTERS[slug]
    text = text_of(letter)
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
    config = dict(EXPERIMENT=f'okinawan-{slug}-{round_no}', CANDIDATES=list(fonts),
                  PASSAGES=[t for _, t in letter['passages']], PASSAGE_LABELS=[l for l, _ in letter['passages']],
                  BIG=letter['big'], VERTICAL=letter['vertical'], LETTER=chr(letter['code']), **(extra or {}))
    config_js = ''.join(f'const {k}={json.dumps(v, ensure_ascii=False)};' for k, v in config.items())
    body = (TEMPLATES/f'{stage}.html').read_text()
    body = body.replace('__GLYPH__', f'<span class="glyph">{html.escape(letter["label"])}</span>')
    body = body.replace('__FOOTER__', f'Round {round_no} · {len(fonts)} forms · GenZui Serif with each variant of {html.escape(letter["label"])}.')
    if references:
        body = body.replace('<section id="tools">', f'<details class="font-references" open><summary>References</summary>'
                            f'<div class="reference-fonts">{references}</div></details><section id="tools">')
    page = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{html.escape(letter["label"])} — GenZui arena</title><style>{faces}{(TEMPLATES/"arena.css").read_text()}'
            f'{(TEMPLATES/f"{stage}.css").read_text()}</style></head><body>{body}'
            f'<script>{config_js}\n{(TEMPLATES/f"{stage}.js").read_text()}</script></body></html>')
    out = OUT/slug; out.mkdir(parents=True, exist_ok=True)
    name = f'round{round_no}.html' if stage == 'cull' else f'round{round_no}-{stage}.html'
    (out/name).write_text(page)
    print(f'{slug} round {round_no} {stage}: {len(fonts)} forms -> {out/name}')
    return out/name


def build(slug, round_no, kept=None):
    letter = LETTERS[slug]
    if kept:
        # forms from an earlier round keep their shared parameters; new ones take defaults
        centres = [{k: kept[t].get(k, v) for k, v in letter['defaults'].items()} for t in kept]
        params = centres + around(centres, letter['ranges'], 24 - len(centres), 1000 * round_no)
    else:
        params = [dict(letter['defaults'])] + sample(letter['ranges'], 23, 1000 * round_no)
    fonts, forms = variants(letter, params)
    (OUT/slug).mkdir(parents=True, exist_ok=True)
    (OUT/slug/f'round{round_no}-forms.json').write_text(json.dumps(forms, indent=1) + '\n')
    return page(slug, round_no, 'cull', fonts)


def compare(slug, round_no, cull):
    """Pairwise comparison of the forms a round's cull kept."""
    forms = json.loads((OUT/slug/f'round{round_no}-forms.json').read_text())
    kept = [forms[t] for t in cull['kept']]
    fonts, _ = variants(LETTERS[slug], kept)
    assert list(fonts) == cull['kept'], 'rebuilt forms must keep their tokens'
    return page(slug, round_no, 'compare', fonts)


def axes(slug, round_no, base, group='axes'):
    """One row per factor: seven steps around the base, only that factor changed."""
    letter = LETTERS[slug]
    rows, params = [], []
    for key, label, note, deltas, *fixed in letter[group]:
        steps = []
        row_base = {**base, **(fixed[0] if fixed else {})}
        for i in range(-3, 4):
            p = dict(row_base)
            for name, step in deltas.items():
                p[name] = round(row_base[name] + step * i, 3) if isinstance(step, float) else row_base[name] + step * i
            steps.append(p); params.append(p)
        rows.append((key, label, note, steps))
    unique = [dict(t) for t in {tuple(sorted(p.items())) for p in params}]
    fonts, forms = variants(letter, unique)
    token_of = {json.dumps(v, sort_keys=True): t for t, v in forms.items()}
    config = [dict(key=k, label=l, note=n, steps=[token_of.get(json.dumps(p, sort_keys=True)) for p in steps])
              for k, l, n, steps in rows]
    (OUT/slug).mkdir(parents=True, exist_ok=True)
    (OUT/slug/f'round{round_no}-forms.json').write_text(json.dumps(forms, indent=1) + '\n')
    (OUT/slug/f'round{round_no}-axes.json').write_text(json.dumps(dict(base=base, axes=config), indent=1) + '\n')
    return page(slug, round_no, 'axes', fonts, dict(AXES=config))


def svg_path(rings):
    return ' '.join(f'M{r[0][0][0]:.1f} {r[0][0][1]:.1f} ' + ' '.join(
        f'C{a[0]:.1f} {a[1]:.1f} {b[0]:.1f} {b[1]:.1f} {c[0]:.1f} {c[1]:.1f}' for _, a, b, c in r) + 'Z' for r in rings)


def tune(slug, round_no, base):
    """A page for placing the mark by hand beside a kana that stays put."""
    letter = LETTERS[slug]
    kana = letter['build'].keywords['kana']
    p = {**letter['defaults'], **base}
    mark, origin, body = okinawan_merge.beside_pieces(TTFont(BASE), contours, kana, p)
    if p.get('mark_x') is None:
        p['mark_x'] = round(okinawan_merge.gap_shift(okinawan_merge.sized(mark, origin, p), body, p['gap']))
    start = {k: p[k] for k in ('mark_x', 'mark_dy', 'mark_scale', 'mark_len')}
    g = chr(letter['code'])
    lines = [letter['big'], *(t for _, t in letter['passages'])]
    (OUT/slug).mkdir(parents=True, exist_ok=True)
    (OUT/slug/f'round{round_no}-tune.json').write_text(json.dumps(dict(base=p, start=start), indent=1) + '\n')
    return page(slug, round_no, 'tune', {}, dict(MARK_D=svg_path([mark]), KANA_D=svg_path(body), ORIGIN=list(origin),
                                                 START=start, LINES=lines))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('slug', choices=sorted(LETTERS))
    parser.add_argument('round', type=int)
    parser.add_argument('--kept', help='the previous round’s copied cull result (JSON file)')
    parser.add_argument('--compare', help='this round’s copied cull result: build the pairwise page')
    parser.add_argument('--axes', metavar='ROUND:TOKEN', help='one factor at a time around a form from an earlier round, '
                        'or around a shipped form named in okinawan_merge (YA, YU)')
    parser.add_argument('--tune', metavar='ROUND:TOKEN', help='place the mark by hand, starting from a form of an earlier round')
    parser.add_argument('--group', default='axes', help='which set of factors to vary (axes, thickness)')
    parser.add_argument('--set', nargs='*', default=[], metavar='NAME=VALUE', help='change the base form before varying it')
    args = parser.parse_args()
    if args.tune:
        source, token = args.tune.split(':')
        tune(args.slug, args.round, json.loads((OUT/args.slug/f'round{source}-forms.json').read_text())[token])
    elif args.axes:
        if ':' in args.axes:
            source, token = args.axes.split(':')
            base = json.loads((OUT/args.slug/f'round{source}-forms.json').read_text())[token]
        else:
            base = getattr(okinawan_merge, args.axes)
        base = {**LETTERS[args.slug]['defaults'], **base}
        for item in args.set:
            name, value = item.split('=')
            base[name] = type(base[name])(float(value)) if isinstance(base[name], int) else float(value)
        axes(args.slug, args.round, base, args.group)
    elif args.compare:
        compare(args.slug, args.round, json.loads(open(args.compare).read()))
    else:
        kept = None
        if args.kept:
            result = json.loads(open(args.kept).read())
            forms = json.loads((OUT/args.slug/f'round{args.round - 1}-forms.json').read_text())
            kept = {t: forms[t] for t in result['kept']}
        build(args.slug, args.round, kept)
