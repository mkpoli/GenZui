"""Summarize the Sans geometry audit and build its local comparison page."""
import json
import shutil
from collections import defaultdict
from statistics import median
from zipfile import ZipFile

import numpy as np
from sans_weight_audit import OUT, RELEASE, ROOT, dump, quantiles
from serif import font_path

HIRAGANA = 'あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわゐゑをん'
KATAKANA = ''.join(chr(ord(c)+0x60) for c in HIRAGANA)


def build():
    vectors = json.loads((OUT/'vectors.json').read_text())
    strokes = json.loads((OUT/'strokes.json').read_text())
    provenance = json.loads((OUT/'provenance.json').read_text())
    lookup = {(r['style'], r['origin'], r['text'], r['pixels']): r for r in strokes}
    for r in strokes:
        if r['pixels'] != 1024:
            continue
        low = lookup[r['style'],r['origin'],r['text'],512]
        r['direction_stable'] = {d: bool(r['directions'][d] and low['directions'][d] and
            abs(r['directions'][d]['q50']/low['directions'][d]['q50']-1) <= .1)
            for d in ('horizontal','vertical','diagonal')}
    summary = dict(release=provenance['release'], native={}, groups=[], forms=[], components=[], sensitivity={}, calibration=provenance['calibration'])
    for style in ('Regular', 'Bold'):
        native = {}
        for label, chars in [('Hiragana', HIRAGANA), ('Katakana', KATAKANA)]:
            rows = [lookup[style, 'Noto', c, 1024] for c in chars]
            native_glyphs = {r['text']:r['glyph'] for r in vectors if r['style']==style and r['origin']=='Noto'}
            assert len({native_glyphs[r['text']] for r in rows}) == len(rows), 'Reference cohort has aliases'
            native[label] = dict(count=len(rows), glyph_medians=quantiles([r['stroke']['q50'] for r in rows]),
                                 directions={d: quantiles([r['directions'][d]['q50'] for r in rows if r['direction_stable'][d]])
                                             for d in ('horizontal','vertical','diagonal')})
        summary['native'][style] = native
        groups = defaultdict(list)
        changes = []
        for r in strokes:
            if r['style'] != style or r['pixels'] != 1024:
                continue
            low = lookup[style, r['origin'], r['text'], 512]
            change = 100*(r['stroke']['q50']/low['stroke']['q50']-1) if low['stroke'] and r['stroke'] else None
            if change is not None:
                changes.append(abs(change))
            if r['origin'] != 'GenZui':
                continue
            if r['stroke']:
                groups[r['group']].append(r['stroke']['q50'])
            donor_rows = [lookup[style, 'Noto', c, 1024] for c in r['donors'] if (style, 'Noto', c, 1024) in lookup]
            donor_mid = median(x['stroke']['q50'] for x in donor_rows) if donor_rows else None
            row = dict(r, resolution_change_pct=change,
                       donor_median=donor_mid, donor_glyph_medians={x['text']:x['stroke']['q50'] for x in donor_rows},
                       donor_difference_pct=100*(r['stroke']['q50']/donor_mid-1) if donor_mid and r['stroke'] else None)
            summary['forms'].append(row)
            if 'parts' in r:
                vowel = r['parts']['vowel']['stroke']['q50']
                fu = r['parts']['fu']['stroke']['q50']
                summary['components'].append(dict(style=style, label=r['label'], vowel=vowel, fu=fu,
                                                   difference_pct=100*(vowel/fu-1)))
        for group, values in groups.items():
            summary['groups'].append(dict(style=style, group=group, count=len(values), glyph_medians=quantiles(values)))
        summary['sensitivity'][style] = dict(median_absolute_change_pct=median(changes),
            p95_absolute_change_pct=float(np.percentile(changes,95)), max_absolute_change_pct=max(changes))
    # Native vector ranges deduplicate cmap aliases. Scripts are descriptive,
    # never common design targets for kana, Han, Latin and marks.
    census = defaultdict(dict)
    for r in vectors:
        if r['origin'] == 'Noto' and r['area']:
            census[r['style'],r['group']][r['glyph']] = r['effective_width']
    summary['native_vector_groups'] = [dict(style=style, script=group, glyphs=len(values), effective_width=quantiles(list(values.values())))
                                      for (style,group),values in census.items()]
    paired = {(r['style'],r['text']):r for r in summary['forms']}
    for r in summary['forms']:
        regular = paired.get(('Regular',r['text']))
        bold = paired.get(('Bold',r['text']))
        r['bold_regular_ratio'] = None
        if regular and bold and regular['stroke'] and bold['stroke']:
            r['bold_regular_ratio'] = bold['stroke']['q50']/regular['stroke']['q50']
    dump('summary.json', summary)
    # Keep the reproducible finding record small; raw rows live with the report.
    record = {k:v for k,v in summary.items() if k != 'forms'}
    record['funatsu'] = [r for r in summary['forms'] if r['group']=='funatsu']
    record['font_sha256'] = {k:v['font_sha256'] for k,v in provenance['faces'].items()}
    record['native_sha256'] = provenance['source_sha256']
    (ROOT/'research/sans-weight-audit.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
    for style in ('Regular','Bold'):
        shutil.copyfile(RELEASE/f'GenZuiSans-{style}.woff2',OUT/f'{style}.woff2')
    shutil.copyfile(font_path('NotoSansJP'),OUT/'NotoSansJP.ttf')
    with ZipFile(ROOT/'releases/v0.118/GenZuiSerifOkinawan-0.118.zip') as archive:
        for style in ('Regular','Bold'):
            (OUT/f'Serif-{style}.woff2').write_bytes(archive.read(f'GenZuiSerifOkinawan-{style}.woff2'))
    (OUT/'index.html').write_text(PAGE)
    if (OUT/'serif/provenance.json').exists():
        from parallel_weight_report import build as build_parallel
        build_parallel()
    print(json.dumps({k:v for k,v in summary.items() if k in ('native','groups','components','sensitivity')},ensure_ascii=False,indent=2))


PAGE = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>GenZui Sans · weight measurements</title><style>
@font-face{font-family:G;src:url(Regular.woff2);font-weight:400}@font-face{font-family:G;src:url(Bold.woff2);font-weight:700}
@font-face{font-family:N;src:url(NotoSansJP.ttf);font-weight:100 900}
@font-face{font-family:S;src:url(Serif-Regular.woff2);font-weight:400}@font-face{font-family:S;src:url(Serif-Bold.woff2);font-weight:700}
:root{color:#183d35;background:#f4f5ef;font-family:system-ui,sans-serif}*{box-sizing:border-box}body{margin:0}main{max-width:1320px;margin:auto;padding:36px 24px 80px}
h1{font-size:clamp(28px,4vw,48px);margin:8px 0 16px;letter-spacing:-.04em}h2{margin:40px 0 18px;font-size:24px}p{line-height:1.65;max-width:85ch}.muted{color:#5d716b;font-size:14px}.tag{letter-spacing:.12em;font-size:12px;text-transform:uppercase}
a{color:inherit}button,select,input{font:inherit;border:1px solid #bdcbc3;background:white;color:inherit;border-radius:7px;padding:9px 12px}button{cursor:pointer}button.active{background:#214e40;color:white}nav{display:flex;gap:10px;flex-wrap:wrap;margin:20px 0}.grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}.panel,article{border:1px solid #d0dbd3;background:white;border-radius:12px;padding:22px;min-width:0}.stats{display:flex;gap:35px;flex-wrap:wrap}.stat strong{font-size:30px;display:block}.stat span{font-size:13px}.tablewrap{overflow:auto}table{border-collapse:collapse;font-variant-numeric:tabular-nums;width:100%;font-size:14px}th,td{border-bottom:1px solid #e1e7e0;padding:10px 12px;text-align:right;white-space:nowrap}th:first-child,td:first-child{text-align:left}th{font-weight:600;background:#f4f7f1}details{margin:24px 0}summary{cursor:pointer;font-size:20px;font-weight:600}.glyph{font-family:G;font-synthesis:none}.native{font-family:N}.serif{font-family:S;font-size:28px}.specimen{font-size:clamp(50px,7vw,112px);line-height:1.7;white-space:nowrap;border-bottom:1px solid #d6dfd6;display:flex;justify-content:center;gap:.12em;margin:8px 0 14px}.specimen .target{background:#f6f7f1}.reading{font-size:28px;line-height:1.6;margin:10px 0}.metrics{display:flex;gap:18px;flex-wrap:wrap;font-size:13px}.metrics strong{font-size:20px;display:block}.warn{color:#965125}.bar{height:13px;background:#eaf0e7;border-radius:9px;position:relative;margin:12px 0 24px}.band{position:absolute;background:#b6d3b7;height:13px}.pin{position:absolute;height:23px;width:3px;background:#173e33;top:-5px}.cardtitle{display:flex;justify-content:space-between;gap:12px}.cardtitle strong{font-size:19px}svg{width:100%;max-height:450px}.legend{display:flex;gap:20px;font-size:13px}.smallglyph{font-size:25px}footer{margin-top:40px}.hidden{display:none}
@media(max-width:700px){main{padding:22px 14px}.grid{grid-template-columns:1fr}.specimen{font-size:clamp(42px,16vw,64px)}.panel,article{padding:16px}.stats{gap:20px}}
</style><main><div class="tag">GenZui Sans 0.104 / geometry audit</div><h1>Where the weight differs</h1>
<p>Stroke widths measured from the published Regular and Bold fonts, alongside native Noto Sans JP. Widths use a 1,000-unit em. A letter’s shape, size and spacing also affect its apparent weight.</p>
<nav><button class="active" data-style="Regular">Regular</button><button data-style="Bold">Bold</button><a href="vectors.csv">Full native census · CSV</a><a href="summary.json">Measurements · JSON</a></nav>
<div id="baseline" class="panel"></div><h2>Weight differences to examine</h2><div id="priorities" class="tablewrap panel"></div><p class="muted">These are geometric comparisons with full-size comparison kana. Component size, spacing and stroke direction require visual review before choosing correction amounts.</p><h2>Okinawan forms</h2><p class="muted">Each card shows native comparison kana, the constructed form, reading-size context and a small Serif reference. The green band is the middle 80% of full-size native hiragana glyph medians. It is a reference range; compact components need separate optical judgment.</p>
<div class="grid" id="forms"></div><h2>Detached ふ forms</h2><p>The vowel and the remaining ふ strokes are measured separately. The retained ふ omits its native right stroke and includes a reduced left dot. A negative difference means the vowel’s median stroke is thinner. These components have different proportions; the figures describe the mismatch without prescribing equal widths. Bold HWE’s retained ふ median changes 4.6% between resolutions, so small component differences require particular care.</p><div id="components" class="tablewrap panel"></div>
<details><summary>All historical and specialist forms</summary><p class="muted">Search by character, Unicode number or label. Reduced kana, tone marks and symbols have their own size conventions.</p><nav><input id="search" aria-label="Search characters" placeholder="Character, U+1B000, HWA…"><select id="group" aria-label="Character group"><option value="">All groups</option></select></nav><div id="all" class="tablewrap panel"></div></details>
<details><summary>Native ranges and measurement method</summary><div id="groups" class="tablewrap panel"></div><p>Local stroke diameter is twice the distance from the medial axis to the nearest ink boundary. Samples near junctions and endpoints are excluded, and quantiles are weighted by axis length. The <a href="https://scikit-image.org/docs/stable/api/skimage.morphology.html#skimage.morphology.medial_axis">scikit-image medial-axis implementation</a> provides the skeleton and distance transform. Some terminal branches remain; some narrow parts near junctions are excluded.</p>
<p>Every detailed measurement runs at 512 and 1,024 pixels per em. Synthetic straight strokes and rings check numerical bias. Median sensitivity is shown above; individual cards flag changes exceeding 5%. This threshold flags sampling sensitivity, not an acceptable design tolerance.</p>
<p>The whole-outline measure 2 × area / perimeter and ink coverage are available in the CSV. They vary with stroke length, terminals, counters and joins, so equal values do not establish equal perceived weight. Native script distributions deduplicate aliases. Unencoded alternates are outside the vector census; the 35 Okinawan output sequences are explicitly shaped.</p>
<p>Comparison summaries use full-size kana, which can differ from the actual construction donors. SI and N use small ぃ strokes in their construction; the comparison uses full-size い. Glottal WA also includes わ as a structural comparison, although its drawing derives from ゐ and こ. Different component proportions can move this ratio even when their individual strokes match. Direction-specific widths and 10th–90th percentiles are retained in the JSON. Direction bins are flagged when they change by more than 10% between resolutions. A dash indicates insufficient stable axis support, as for the isolated underdot.</p>
<p><a href="provenance.json">Font hashes, numerical calibration and environment</a> · <a href="strokes.json">Detailed stroke measurements</a> · <a href="vectors.json">Vector census</a></p></details><footer class="muted">GenZui Sans 0.104 · Noto Sans JP 400 / 700 · Serif reference 0.118</footer></main>
<script>
let data,style='Regular';const $=s=>document.querySelector(s),n=x=>x==null?'—':x.toFixed(1),esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])),pct=x=>x==null?'—':(x>=0?'+':'')+x.toFixed(1)+'%';
function table(head,rows){return '<table><thead><tr>'+head.map(x=>'<th>'+x+'</th>').join('')+'</tr></thead><tbody>'+rows.map(r=>'<tr>'+r.map(x=>'<td>'+x+'</td>').join('')+'</tr>').join('')+'</tbody></table>'}
function render(){const base=data.native[style].Hiragana.glyph_medians,sens=data.sensitivity[style];$('#baseline').innerHTML='<div class="stats"><div class="stat"><strong>'+n(base.q50)+'</strong><span>Native hiragana · median stroke</span></div><div class="stat"><strong>'+n(base.q10)+'–'+n(base.q90)+'</strong><span>Middle 80% of glyph medians</span></div><div class="stat"><strong>'+n(sens.median_absolute_change_pct)+'%</strong><span>Median 512 → 1,024 px sensitivity</span></div></div><p class="muted">48 full-size hiragana reference letters, equally weighted. Both resolutions and all percentile values are available in the data.</p>';
const targets=style==='Regular'?['KWE','SI','HWA','HWE']:['Glottal WA','Glottal WI','Glottal WE','HWA','HWE'];$('#priorities').innerHTML=table(['Form','Stroke median','Comparison median','Difference'],targets.map(label=>{const r=data.forms.find(r=>r.style===style&&r.label===label);return [label,n(r.stroke.q50),n(r.donor_median),pct(r.donor_difference_pct)]}));
$('#forms').innerHTML=data.forms.filter(r=>r.style===style&&['funatsu','prefecture'].includes(r.group)).map(r=>{const q=r.stroke;const range=180;return '<article><div class="cardtitle"><strong>'+esc(r.label)+'</strong><span class="muted">'+style+'</span></div><div class="specimen" style="font-weight:'+(style==='Bold'?700:400)+'"><span class="native">'+esc(r.donors[0]||'')+'</span><span class="glyph target">'+esc(r.text)+'</span><span class="native">'+esc(r.donors.slice(1)||r.donors[0]||'')+'</span></div><div class="metrics"><span><strong>'+n(q.q50)+'</strong>Median stroke</span><span><strong>'+n(q.q10)+'–'+n(q.q90)+'</strong>Thin–thick range</span><span><strong>'+pct(r.donor_difference_pct)+'</strong>vs comparison median</span></div><div class="bar" aria-label="Native width reference"><span class="band" style="left:'+100*base.q10/range+'%;width:'+100*(base.q90-base.q10)/range+'%"></span><span class="pin" style="left:'+Math.min(99,100*q.q50/range)+'%"></span></div><div class="glyph reading" style="font-weight:'+(style==='Bold'?700:400)+'">'+esc((r.donors[0]||'')+r.text+(r.donors.slice(-1)||''))+'</div><div class="muted">Serif <span class="serif" style="font-weight:'+(style==='Bold'?700:400)+'">'+esc((r.donors[0]||'')+r.text+r.donors.slice(-1))+'</span></div><p class="muted '+(Math.abs(r.resolution_change_pct)>5?'warn':'')+'">512 → 1,024 px: '+pct(r.resolution_change_pct)+' · Bold / Regular: '+r.bold_regular_ratio.toFixed(2)+'×</p></article>'}).join('');
$('#components').innerHTML=table(['Form','ふ stroke','Vowel stroke','Difference'],data.components.filter(r=>r.style===style).map(r=>[r.label,n(r.fu),n(r.vowel),pct(r.difference_pct)]));
$('#groups').innerHTML=table(['Group','Letters','Median','Middle 80%'],data.groups.filter(r=>r.style===style).map(r=>[esc(r.group),r.count,n(r.glyph_medians.q50),n(r.glyph_medians.q10)+'–'+n(r.glyph_medians.q90)]));renderAll();}
function renderAll(){const q=$('#search').value.toLowerCase().replace('u+',''),group=$('#group').value;const rows=data.forms.filter(r=>r.style===style&&(!group||r.group===group)&&(!q||(r.text+' '+r.cp+' '+r.label).toLowerCase().includes(q)));$('#all').innerHTML=table(['Character','Label','Group','Median','10th–90th','B/R','Resolution Δ'],rows.map(r=>['<span class="glyph smallglyph" style="font-weight:'+(style==='Bold'?700:400)+'">'+esc(r.text)+'</span>',esc(r.label),esc(r.group),n(r.stroke?.q50),n(r.stroke?.q10)+'–'+n(r.stroke?.q90),r.bold_regular_ratio?.toFixed(2)||'—',pct(r.resolution_change_pct)]));}
document.querySelectorAll('[data-style]').forEach(b=>b.onclick=()=>{style=b.dataset.style;document.querySelectorAll('[data-style]').forEach(x=>x.classList.toggle('active',x===b));render()});$('#search').oninput=renderAll;$('#group').onchange=renderAll;
fetch('summary.json').then(r=>r.json()).then(d=>{data=d;$('#group').innerHTML+=[...new Set(d.forms.map(r=>r.group))].map(g=>'<option>'+esc(g)+'</option>').join('');render();document.documentElement.dataset.ready='true'}).catch(e=>{$('#baseline').textContent='Could not load measurements: '+e.message});
</script></html>'''


if __name__ == '__main__':
    build()
