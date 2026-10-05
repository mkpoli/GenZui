"""Build the font comparison page from research/font-comparison*.json."""
import html
import json
import re

from compare_sources import member
from family_switch import html as switch_html, label_face, LABELS
from sources import ROOT
from compare_sources import verify

DATA = ROOT/'research/font-comparison.json'
GLYPHS = ROOT/'research/font-comparison-glyphs.json'
OUT = ROOT/'build/site'
REPO = 'https://github.com/mkpoli/GenZui'
OTF_REGISTRY = 'https://learn.microsoft.com/en-us/typography/opentype/spec/featurelist'
FEATURES = {
    'aalt': 'Access all alternates', 'ccmp': 'Glyph composition and decomposition', 'chws': 'Contextual half-width spacing',
    'dlig': 'Discretionary ligatures', 'fwid': 'Full widths', 'halt': 'Alternate half widths', 'hist': 'Historical forms',
    'hwid': 'Half widths', 'jp78': 'JIS78 forms', 'jp83': 'JIS83 forms', 'jp90': 'JIS90 forms', 'kern': 'Kerning',
    'liga': 'Standard ligatures', 'locl': 'Localized forms', 'mark': 'Mark positioning', 'mkmk': 'Mark-to-mark positioning',
    'nlck': 'NLC kanji forms', 'ordn': 'Ordinals', 'palt': 'Proportional alternate widths', 'pwid': 'Proportional widths',
    'ruby': 'Ruby notation forms', 'salt': 'Stylistic alternates', 'ss01': 'Stylistic set 1', 'vchw': 'Vertical contextual half-width spacing',
    'vert': 'Vertical alternates', 'vhal': 'Alternate vertical half widths', 'vkrn': 'Vertical kerning',
    'vpal': 'Proportional alternate vertical widths', 'vrt2': 'Vertical alternates and rotation',
}
SERIES = ('genzui-serif', 'genzui-sans')


def esc(text):
    return html.escape(str(text), quote=True)


def mb(size):
    return f'{size/1048576:.1f} MB' if size >= 104858 else f'{size/1024:.0f} KB'


def number(value):
    return f'{value:,}'


class Page:
    def __init__(self):
        self.data = json.loads(DATA.read_text())
        self.glyphs = json.loads(GLYPHS.read_text())
        self.fonts = {f['id']: f for f in self.data['fonts']}
        self.order = [f['id'] for f in self.data['fonts']]
        self.blocks = {b['name']: b for b in self.data['blocks']}
        self.face_text = set('源萃明朝ゴシック')

    # --- small pieces -----------------------------------------------------------------

    def face(self, text):
        """Japanese text set in the site's own face; the subset covers exactly these characters."""
        self.face_text.update(text)
        return f'<span class="face" lang="ja">{esc(text)}</span>'

    def head(self, fid, extra=''):
        font = self.fonts[fid]
        cls = ' class="gz"' if fid in SERIES else ''
        return f'<th scope="col"{cls}>{esc(font["name"])}<small>{esc(font["version"])}{extra}</small></th>'

    def cells(self, render, label=True):
        out = []
        for fid in self.order:
            cls = ' gz' if fid in SERIES else ''
            out.append(f'<td class="c{cls}" data-label="{esc(self.fonts[fid]["name"])}">{render(self.fonts[fid])}</td>')
        return ''.join(out)

    def table(self, rows, caption, extra_class=''):
        head = '<th scope="col"><span class="sr-only">Property</span></th>' + ''.join(self.head(i) for i in self.order)
        return (f'<table class="rt {extra_class}"><caption class="sr-only">{esc(caption)}</caption>'
                f'<thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table>')

    def path(self, fid, cp, cls='', size=None):
        """An inline SVG outline, or a dashed box where the font has no drawing."""
        entry = self.glyphs['glyphs'][fid].get(f'{cp:X}')
        if not entry:
            return f'<svg class="g tofu {cls}" viewBox="0 -880 1000 1000" aria-hidden="true"><rect x="140" y="-700" width="720" height="780"/></svg>'
        return f'<svg class="g {cls}" viewBox="0 -880 1000 1000" aria-hidden="true"><path d="{entry[1]}"/></svg>'

    def text_svg(self, fid, text, label):
        """A line of text from outlines, advancing by each glyph's own width."""
        x, parts = 0, []
        for char in text:
            cp = ord(char)
            entry = self.glyphs['glyphs'][fid].get(f'{cp:X}')
            if char == '　':
                x += 500
            elif entry:
                parts.append(f'<path transform="translate({x} 0)" d="{entry[1]}"/>')
                x += entry[0]
            else:
                parts.append(f'<rect class="tofu" x="{x + 140}" y="-700" width="720" height="780"/>')
                x += 1000
        return (f'<svg class="line" viewBox="0 -880 {x} 1000" role="img" aria-label="{esc(label)}">{"".join(parts)}</svg>')

    # --- sections ------------------------------------------------------------------------

    def hero_rows(self):
        rows = []
        for fid in self.order:
            font = self.fonts[fid]
            cls = ' gz' if fid in SERIES else ''
            rows.append(f'<div class="row{cls}"><span class="who">{esc(font["name"])}<small>{esc(font["version"])}</small></span>'
                        f'{self.text_svg(fid, self.data["hero"], font["name"] + " " + self.data["hero"])}</div>')
        return ''.join(rows)

    def glance(self):
        def weights(font):
            names = []
            for w in font['weights']:
                if w['variable']:
                    names.append(f'Variable {w["min"]}–{w["max"]}<small>{esc(w["named"][0])} to {esc(w["named"][-1])}</small>')
                else:
                    names.append(esc(w['style']))
            return '<br>'.join(dict.fromkeys(names))

        def features(font):
            if not font['gsub'] and not font['gpos']:
                return 'None' + ('<small>Apple morx table only</small>' if font['morx'] else '')
            return f'{len(font["gsub"])} in GSUB<br>{len(font["gpos"])} in GPOS'

        def vertical(font):
            tags = {'vert', 'vrt2'} & set(font['gsub'])
            if tags:
                return 'Yes<small>' + ', '.join(sorted(tags)) + '</small>'
            if font['morx']:
                return 'AAT only<small>morx table</small>'
            return 'No'

        def licence(font):
            return f'<a href="{esc(font["licence_url"])}">{esc(font["licence"])}</a>'

        total = {f['id']: sum(x['size'] for x in f['files'] if x['format'] == 'TrueType') for f in self.data['fonts']}
        spec = [
            ('Style', lambda f: esc(f['style'])),
            ('Version', lambda f: esc(f['version']) + ('' if f['version'] == f['date'] else f'<small>{esc(f["date"])}</small>')),
            ('Weights', weights),
            ('Licence', licence),
            ('Reserved font name', lambda f: esc(f['reserved_name']) if f['reserved_name'] else 'None stated'),
            ('Installed size', lambda f: f'{mb(total[f["id"]])}<small>{len([x for x in f["files"] if x["format"] == "TrueType"])} TTF</small>'),
            ('Mapped code points', lambda f: number(f['codepoints'])),
            ('Glyphs', lambda f: number(f['glyphs'])),
            ('Hentaigana', lambda f: f'{f["hentaigana"]} of {self.data["milestones"]["hentaigana"]}'),
            ('Unicode 18 kana', lambda f: f'{f["unicode18_kana"]} of {self.data["milestones"]["unicode18_kana"]}'),
            ('GSUB and GPOS features', features),
            ('Vertical forms', vertical),
            ('Variation sequences', lambda f: number(f['variation_sequences']) if f['variation_sequences'] else '0'),
            ('Units per em', lambda f: ' · '.join(str(u) for u in f['upm'])),
        ]
        rows = ''.join(f'<tr><th scope="row">{esc(name)}</th>{self.cells(fn)}</tr>' for name, fn in spec)
        return self.table(rows, 'Fonts compared by version, licence, size and repertoire')

    def coverage(self):
        rows = []
        for block in self.data['blocks']:
            name = block['name']
            private = 'Private Use' in name

            def cell(font, name=name, block=block, private=private):
                count = font['coverage'].get(name, 0)
                if private:
                    return f'<span class="n">{number(count)} mapped</span>' if count else '<span class="n none">0</span>'
                share = count/block['assigned']
                fill = f'<span class="bar"><i style="--w:{share*100:.2f}%"></i></span>' if count else '<span class="bar"></span>'
                return f'{fill}<span class="n{"" if count else " none"}">{number(count)}<small>/ {number(block["assigned"])}</small></span>'

            label = f'{esc(name)}<small>U+{block["first"]:04X}–{block["last"]:04X}</small>'
            rows.append(f'<tr><th scope="row">{label}</th>{self.cells(cell)}</tr>')
        return self.table(''.join(rows), 'Assigned Unicode characters mapped by each font, by block', 'cov')

    def chart_json(self):
        used = {}
        for fid in self.order:
            font = self.fonts[fid]
            used[fid] = {'name': font['name'], 'credit': font['credit'], 'licence': font['licence'],
                         'licence_url': font['licence_url'], 'glyphs': self.glyphs['glyphs'][fid]}
        sets = {k: {'name': v['name'], 'codepoints': v['codepoints']} for k, v in self.data['chart_sets'].items()}
        payload = {'fonts': used, 'order': self.order, 'sets': sets, 'names': self.data['names'],
                   'overlap': self.data['chart_overlap']}
        return json.dumps(payload, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c')

    def chart_controls(self):
        hentaigana = [i for i in self.order if self.fonts[i]['hentaigana']]
        def options(selected):
            return ''.join(f'<option value="{i}"{" selected" if i == selected else ""}>{esc(self.fonts[i]["name"])}</option>' for i in hentaigana)
        sets = ''.join(f'<button type="button" data-set="{k}" aria-pressed="{"true" if k == "hentaigana" else "false"}">{esc(v["name"])} <span>{len(v["codepoints"])}</span></button>'
                       for k, v in self.data['chart_sets'].items())
        return (f'<div class="chart-tools">'
                f'<label class="pick a"><span class="control-label">FIRST FONT</span><select id="font-a">{options("genzui-sans")}</select></label>'
                f'<label class="pick b"><span class="control-label">SECOND FONT</span><select id="font-b">{options("sukima")}</select></label>'
                f'<div class="pick"><span class="control-label" id="overlay-label">VIEW</span><button type="button" class="toggle" id="overlay" aria-pressed="false" aria-describedby="overlay-label">Overlay</button></div>'
                f'</div>'
                f'<div class="inventory-filters chart-sets" role="group" aria-label="Character set">{sets}</div>')

    def similarity(self):
        sim = self.data['similarity']['hentaigana']
        ids = self.data['similarity']['hentaigana_ids']

        def value(a, b):
            record = sim.get(f'{a}|{b}') or sim.get(f'{b}|{a}')
            return record

        head = '<th scope="col"><span class="sr-only">Font</span></th>' + ''.join(f'<th scope="col">{esc(self.fonts[i]["name"])}</th>' for i in ids)
        rows = []
        for a in ids:
            cells = []
            for b in ids:
                if a == b:
                    cells.append('<td class="diag" aria-label="same font">·</td>')
                    continue
                record = value(a, b)
                corr = record['corr_median']
                tone = 'high' if corr >= 0.95 else 'mid' if corr >= 0.7 else ''
                cells.append(f'<td class="m {tone}" data-label="{esc(self.fonts[b]["name"])}">{corr:.3f}</td>')
            rows.append(f'<tr><th scope="row">{esc(self.fonts[a]["name"])}</th>{"".join(cells)}</tr>')
        return f'<table class="rt matrix"><caption class="sr-only">Median shape correlation of hentaigana drawings between fonts</caption><thead><tr>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table>'

    def similarity_notes(self):
        sim = self.data['similarity']['hentaigana']
        def pair(a, b):
            return sim.get(f'{a}|{b}') or sim[f'{b}|{a}']
        n = self.data['milestones']['hentaigana']
        nsh, gs, sk, ge = 'noto-serif-hentaigana', 'genzui-serif', 'sukima', 'genseki'
        serif = pair(gs, nsh)
        genseki = pair(ge, sk)
        sans = pair('genzui-sans', sk)
        mincho = pair('ninjal', 'jigmo')
        origins = self.data['origins']['genseki']
        return (
            f'<li><strong>GenZui Serif and Noto Serif Hentaigana</strong> correlate at {serif["corr_median"]:.3f}; '
            f'{serif["same"]} of {n} outlines overlap by 90% or more. GenZui Serif’s notice names Noto Serif Hentaigana as the source of its hentaigana.</li>'
            f'<li><strong>GenSeki Hentaigana Gothic and Sukima Gothic</strong> correlate at {genseki["corr_median"]:.3f} with a median overlap of {genseki["iou_median"]:.2f}: '
            f'the shapes agree and the size or position differs. GenSeki’s README marks {origins["Sukima Gothic"]} of its {sum(origins.values())} table entries as derived from Sukima Gothic.</li>'
            f'<li><strong>GenZui Sans and Sukima Gothic</strong> correlate at {sans["corr_median"]:.2f}, among the lowest values in the matrix. They are separate drawings.</li>'
            f'<li><strong>NINJAL and Jigmo</strong> correlate at {mincho["corr_median"]:.2f}, the highest value between two fonts without a documented link.</li>')

    def kana_similarity(self):
        sim = self.data['similarity']['kana']
        pair = sim['genzui-sans|sukima']
        base = sim['genzui-sans|genseki']
        return (f'Over the {self.data["similarity"]["kana_count"]} ordinary hiragana and katakana, GenZui Sans and Sukima Gothic overlap by 90% or more in {pair["same"]} and correlate at {pair["corr_median"]:.3f}. '
                f'GenSeki Hentaigana Gothic matches their shapes ({base["corr_median"]:.3f}) with a median overlap of {base["iou_median"]:.2f}.')

    def features(self):
        tags = sorted({t for f in self.data['fonts'] for t in (*f['gsub'], *f['gpos'])})
        rows = []
        for tag in tags:
            def cell(font, tag=tag):
                where = [t for t, tags_ in (('GSUB', font['gsub']), ('GPOS', font['gpos'])) if tag in tags_]
                return ' · '.join(where) if where else '<span class="none">—</span>'
            rows.append(f'<tr><th scope="row"><code>{tag}</code><small>{esc(FEATURES.get(tag, ""))}</small></th>{self.cells(cell)}</tr>')
        return self.table(''.join(rows), 'OpenType layout features present in each font', 'feat')

    def vertical(self):
        vertical, glyphs = self.data['vertical'], self.glyphs['vertical']
        columns = []
        for fid in self.order:
            if fid not in vertical:
                continue
            font = self.fonts[fid]
            info = vertical[fid]
            cells = ''.join(f'<path d="{d}"/>' for d in glyphs[fid])
            guides = ''.join(f'<rect x="-500" y="{i*1000}" width="1000" height="1000"/>' for i in range(len(info['advances'])))
            subs = f'vertical forms: {sum(info["substituted"])} of {len(info["substituted"])}'
            cls = ' gz' if fid in SERIES else ''
            columns.append(
                f'<figure class="vcol{cls}"><svg viewBox="-540 -20 1080 {len(info["advances"])*1000 + 40}" role="img" '
                f'aria-label="{esc(font["name"])}: {esc(self.data["vertical_text"])} set vertically">'
                f'<g class="guides">{guides}</g><g class="ink">{cells}</g></svg>'
                f'<figcaption>{esc(font["name"])}<small>{subs}</small></figcaption></figure>')
        return ''.join(columns)

    def files_table(self):
        rows = []
        for fid in self.order:
            font = self.fonts[fid]
            files = ''.join(
                f'<li><span class="file">{esc(x["name"])}</span><span class="size">{x["format"]} · {mb(x["size"])}</span></li>'
                for x in font['files'])
            weights = '<br>'.join(
                (f'{esc(w["file"].split("[")[0])}: variable, axis {w["axis"]} {w["min"]}–{w["max"]}' if w['variable'] else f'{esc(w["file"])}: {esc(w["style"])} ({w["class"]})')
                for w in font['weights'])
            link = font['url'] if font['url'].startswith(REPO) else font['page']
            access = (f'<a href="{esc(link)}">{esc(font["archive"])}</a><small>{esc(font["version"])}{"" if font["version"] == font["date"] else " · " + esc(font["date"])}'
                      f'{" · sha256 " + font["archive_sha256"][:12] + "…" if font["archive_sha256"] else ""}</small>')
            if font['local_only']:
                access += '<small>BOOTH download needs a login</small>'
            rows.append(
                f'<tr><th scope="row">{esc(font["name"])}<small>{self.face(font["ja"]) if font["ja"] != font["name"] else ""}</small></th>'
                f'<td data-label="Files"><ul class="files">{files}</ul></td>'
                f'<td data-label="Weight classes">{weights}</td>'
                f'<td data-label="Licence"><a href="{esc(font["licence_url"])}">{esc(font["licence"])}</a>'
                f'<small>{esc("Reserved font name “" + font["reserved_name"] + "”") if font["reserved_name"] else "No reserved font name stated"}</small></td>'
                f'<td data-label="Source">{access}</td></tr>')
        head = ''.join(f'<th scope="col">{h}</th>' for h in ('Font', 'Files', 'Weights', 'Licence', 'Pinned source'))
        return f'<table class="rt files-table"><caption class="sr-only">Files, weights and licences</caption><thead><tr>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table>'

    def provenance(self):
        out = []
        counts = self.data['origins']
        for fid in self.order:
            font = self.fonts[fid]
            rows = []
            for row in font['provenance']:
                where = row['member']
                label = {'name:0': 'name table, copyright', 'name:8': 'name table, manufacturer', 'name:9': 'name table, designer'}.get(where, where.replace('!', ' in '))
                rows.append(f'<div class="prow"><dt>{esc(row["topic"])}</dt><dd><p>{esc(row["text"])}</p>'
                            f'<blockquote lang="{"ja" if re.search("[぀-ヿ一-鿿]", row["quote"]) else "en"}">{esc(row["quote"])}</blockquote>'
                            f'<cite>{esc(label)}</cite></dd></div>')
            extra = ''
            if fid == 'genseki':
                origin = counts['genseki']
                parts = ', '.join(f'{esc(k)} {v}' for k, v in origin.items())
                extra = f'<div class="prow"><dt>Counted</dt><dd><p>Origin letters in the README tables for Kana Supplement and Kana Extended-A: {parts}.</p></dd></div>'
            if fid == 'genzui-sans':
                kinds = counts[fid]
                top = '; '.join(f'{esc(k)} {number(v)}' for k, v in list(kinds.items())[:5])
                extra = f'<div class="prow"><dt>Counted</dt><dd><p>Source records in the package’s sources.json, by outline source: {top}.</p></dd></div>'
            if fid == 'genzui-serif':
                kinds = counts[fid]
                top = ', '.join(f'{esc(k)} {number(v)}' for k, v in kinds.items())
                extra = f'<div class="prow"><dt>Counted</dt><dd><p>Characters the package’s sources.json lists as added to the Noto Serif JP base, by kind: {top}.</p></dd></div>'
            out.append(f'<article class="prov{" gz" if fid in SERIES else ""}"><h3>{esc(font["name"])} <small>{esc(font["version"])}</small></h3>'
                       f'<dl>{"".join(rows)}{extra}</dl></article>')
        return ''.join(out)

    def rare(self):
        shown = [i for i in self.order if self.fonts[i]['coverage'].get('CJK Unified Ideographs', 0) > 1000]
        cards = []
        for item in self.data['rare']:
            cp = ord(item['char'])
            glyphs = ''.join(f'<span class="rg" title="{esc(self.fonts[i]["name"])}">{self.path(i, cp)}<small>{esc(self.fonts[i]["name"])}</small></span>' for i in shown)
            cards.append(f'<li class="rare"><code>U+{cp:X}</code><div class="rgs">{glyphs}</div><p lang="ja">{esc(item["quoted"])}</p></li>')
        return ''.join(cards), shown

    def sources_list(self):
        items = []
        for fid in self.order:
            font = self.fonts[fid]
            items.append(f'<li><a href="{esc(font["page"])}">{esc(font["name"])} {esc(font["version"])}</a>, {esc(font["date"])}. {esc(font["archive"])}'
                         f'{", SHA-256 " + font["archive_sha256"] if font["archive_sha256"] else " (files in this repository)"}. '
                         f'<a href="{esc(font["licence_url"])}">{esc(font["licence"])}</a>.</li>')
        return ''.join(items)

    # --- assembly --------------------------------------------------------------------------

    def render(self):
        template = (ROOT/'templates/compare.html').read_text()
        rare_html, rare_fonts = self.rare()
        tools = self.data['tools']
        milestones = self.data['milestones']
        values = {
            '{{HERO_ROWS}}': self.hero_rows(),
            '{{GLANCE}}': self.glance(),
            '{{COVERAGE}}': self.coverage(),
            '{{CHART_CONTROLS}}': self.chart_controls(),
            '{{SIMILARITY}}': self.similarity(),
            '{{SIMILARITY_NOTES}}': self.similarity_notes(),
            '{{KANA_SIMILARITY}}': esc(self.kana_similarity()),
            '{{FEATURES}}': self.features(),
            '{{VERTICAL}}': self.vertical(),
            '{{FILES}}': self.files_table(),
            '{{PROVENANCE}}': self.provenance(),
            '{{RARE}}': rare_html,
            '{{SOURCES}}': self.sources_list(),
            '{{OTF_REGISTRY}}': OTF_REGISTRY,
            '{{REPO}}': REPO,
            '{{CHECKED}}': esc(self.data['checked']),
            '{{FONT_COUNT}}': str(len(self.order)),
            '{{HENTAIGANA_COUNT}}': str(milestones['hentaigana']),
            '{{UNICODE18_COUNT}}': str(milestones['unicode18_kana']),
            '{{TOOLS}}': esc(f'fontTools {tools["fonttools"]}, Pillow {tools["pillow"]}, NumPy {tools["numpy"]}, HarfBuzz {tools["harfbuzz"]} (uharfbuzz {tools["uharfbuzz"]}), Unicode {tools["unicode"]}'),
            '{{CHART_DATA}}': self.chart_json(),
            '{{CSS}}': (ROOT/'site/style.css').read_text(),
            '{{COMPARE_CSS}}': (ROOT/'site/compare.css').read_text(),
            '{{JS}}': (ROOT/'site/compare.js').read_text(),
        }
        page = template
        for token, value in values.items():
            page = page.replace(token, value)
        # The brand and the family switch need small subsets of the GenZui faces.
        manifest = verify()
        serif_woff2 = member(manifest, 'genzui-serif', name='GenZuiSerif-Regular.woff2')[0]
        sans_woff2 = member(manifest, 'genzui-sans', name='GenZuiSans-Regular.woff2')[0]
        faces = {'serif': serif_woff2, 'sans': sans_woff2}
        switch_css = ''.join(
            f"@font-face{{font-family:GenZuiLabel-{key};src:url({label_face(faces[key], text)}) format('woff2');font-weight:400;font-display:block}}\n"
            for key, (text, *_rest) in LABELS.items()) + (ROOT/'site/family-switch.css').read_text()
        page = page.replace('{{FAMILY_SWITCH_CSS}}', switch_css)
        page = page.replace('{{FAMILY_SWITCH}}', switch_html(None))
        page = page.replace('{{FACE_FONT}}', label_face(serif_woff2, ''.join(sorted(self.face_text))))
        assert '{{' not in page and '/home/' not in page
        return page


def build_compare():
    return Page().render()


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/'compare.html').write_text(build_compare())
    print(f'Built {OUT/"compare.html"}')
