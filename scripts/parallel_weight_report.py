"""Pair the released Sans and Serif forms at identical sizes and resolutions."""
import json
import shutil
from collections import defaultdict
from statistics import median

import numpy as np
from sans_weight_audit import OUT, ROOT, quantiles
from sans_weight_report import HIRAGANA, KATAKANA
from serif import font_path


def analyze(folder):
    strokes=json.loads((folder/'strokes.json').read_text())
    vectors=json.loads((folder/'vectors.json').read_text())
    provenance=json.loads((folder/'provenance.json').read_text())
    lookup={(r['style'],r['origin'],r['text'],r['pixels']):r for r in strokes}
    vlookup={(r['style'],r['origin'],r['text']):r for r in vectors}
    output=dict(release=provenance['release'],native={},forms=[],groups=[],font_sha256={k:v['font_sha256'] for k,v in provenance['faces'].items()},native_sha256=provenance['source_sha256'])
    for style in ('Regular','Bold'):
        output['native'][style]={}
        for name,chars in [('Hiragana',HIRAGANA),('Katakana',KATAKANA)]:
            rows=[lookup[style,'Noto',ch,1024] for ch in chars]
            assert len({vlookup[style,'Noto',ch]['glyph'] for ch in chars})==len(chars)
            output['native'][style][name]={q:quantiles([r['stroke'][q] for r in rows]) for q in ('q10','q50','q75','q90')}
        groups=defaultdict(list)
        for r in strokes:
            if r['style']!=style or r['origin']!='GenZui' or r['pixels']!=1024:continue
            low=lookup[style,'GenZui',r['text'],512]
            refs=[lookup[style,'Noto',c,1024] for c in r['donors'] if (style,'Noto',c,1024) in lookup]
            # Use the same full-size comparison letters in both families.
            # Historical forms without donor labels use a native script cohort.
            if not refs and r['group']=='hentaigana':refs=[lookup[style,'Noto',c,1024] for c in HIRAGANA]
            row={k:r[k] for k in ('style','group','text','label','cp','donors','stroke')}
            row['reference']={q:median(x['stroke'][q] for x in refs) for q in ('q10','q50','q75','q90')} if refs else None
            row['relative']={q:r['stroke'][q]/row['reference'][q] for q in row['reference']} if row['reference'] and r['stroke'] else None
            row['resolution_delta']={q:100*(r['stroke'][q]/low['stroke'][q]-1) for q in ('q50','q75','q90')} if r['stroke'] and low['stroke'] else None
            row['reference_resolution_delta']={q:100*(row['reference'][q]/median(lookup[style,'Noto',x['text'],512]['stroke'][q] for x in refs)-1) for q in ('q50','q75','q90')} if refs else None
            row['ink_coverage']=vlookup[style,'GenZui',r['text']]['ink_em_fraction']
            row['effective_width']=vlookup[style,'GenZui',r['text']]['effective_width']
            row['bold_regular']={q:lookup['Bold','GenZui',r['text'],1024]['stroke'][q]/lookup['Regular','GenZui',r['text'],1024]['stroke'][q] for q in ('q50','q75','q90')} if lookup['Bold','GenZui',r['text'],1024]['stroke'] and lookup['Regular','GenZui',r['text'],1024]['stroke'] else None
            output['forms'].append(row)
            groups[r['group']].append(row)
        for group,rows in groups.items():
            result=dict(style=style,group=group,count=len(rows),metrics={})
            for q in ('q50','q75','q90'):
                raw=[r['stroke'][q] for r in rows if r['stroke']]
                rel=[r['relative'][q] for r in rows if r['relative']]
                # Relative IQR describes between-letter spread after reference
                # normalization. It is not a visual quality or goodness score.
                dist=quantiles(rel)
                result['metrics'][q]=dict(widths=quantiles(raw),relative=dist,
                    relative_iqr_pct=100*(dist['q75']-dist['q25'])/dist['q50'] if dist else None,
                    median_resolution_change_pct=median(abs(r['resolution_delta'][q]) for r in rows if r['resolution_delta']))
            output['groups'].append(result)
    return output


def build():
    data={'Sans':analyze(OUT),'Serif':analyze(OUT/'serif')}
    for style in ('Regular','Bold'):
        assert {r['text'] for r in data['Sans']['forms'] if r['style']==style}=={r['text'] for r in data['Serif']['forms'] if r['style']==style}
        shutil.copyfile(ROOT/f'releases/v0.118/GenZuiSerif-{style}.woff2',OUT/f'SerifFull-{style}.woff2')
    shutil.copyfile(font_path('NotoSerifJP'),OUT/'NotoSerifJP.ttf')
    record={name:{k:v for k,v in family.items() if k!='forms'} for name,family in data.items()}
    for name in record:record[name]['funatsu']=[r for r in data[name]['forms'] if r['group']=='funatsu']
    (ROOT/'research/parallel-weight-audit.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
    if (OUT/'revision/provenance.json').exists():
        from sans_weight_audit import digest
        revised=analyze(OUT/'revision')
        for style in ('Regular','Bold'):
            path=ROOT/'build/sans-okinawan/full'/f'GenZuiSans-{style}.ttf'
            assert digest(path)==revised['font_sha256'][style],'Revision measurements are stale'
        data['SansPrevious']=data['Sans'];data['Sans']=revised
    (OUT/'parallel.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n')
    (OUT/'index.html').write_text(PAGE)
    for name,family in data.items():
        for group in family['groups']:
            if group['group'] in ('funatsu','hentaigana'):print(name,json.dumps(group))


PAGE='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>GenZui · Sans and Serif weight comparison</title><style>
@font-face{font-family:GZSans;src:url(Regular.woff2);font-weight:400}@font-face{font-family:GZSans;src:url(Bold.woff2);font-weight:700}
@font-face{font-family:GZRevised;src:url(Revised-Regular.woff2);font-weight:400}@font-face{font-family:GZRevised;src:url(Revised-Bold.woff2);font-weight:700}
@font-face{font-family:GZSerif;src:url(SerifFull-Regular.woff2);font-weight:400}@font-face{font-family:GZSerif;src:url(SerifFull-Bold.woff2);font-weight:700}
@font-face{font-family:NativeSans;src:url(NotoSansJP.ttf);font-weight:100 900}@font-face{font-family:NativeSerif;src:url(NotoSerifJP.ttf);font-weight:100 900}
:root{font-family:system-ui,sans-serif;color:#193e35;background:#f4f5ef}*{box-sizing:border-box}body{margin:0}main{max-width:1380px;margin:auto;padding:32px 24px 80px}h1{font-size:clamp(28px,4vw,46px);letter-spacing:-.04em;margin:10px 0 18px}h2{font-size:24px;margin:32px 0 14px}p{max-width:90ch;line-height:1.6}.tag{font-size:12px;text-transform:uppercase;letter-spacing:.13em}.muted{font-size:13px;color:#5b7067}a{color:inherit}nav{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin:24px 0}button,input,select{font:inherit;padding:9px 12px;border:1px solid #baccc0;background:white;color:inherit;border-radius:7px}button{cursor:pointer}button.active{background:#214f40;color:white}.columns{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:18px}.panel,article{background:white;border:1px solid #d2ddd3;border-radius:12px;padding:22px;min-width:0}article{container-type:inline-size}.pair{margin-bottom:26px}.pair h3{font-size:18px;margin:0 0 10px}.family{font-size:18px;font-weight:600;display:flex;justify-content:space-between;gap:8px}.specimen{font-size:clamp(22px,21cqw,112px);display:flex;justify-content:center;gap:.12em;line-height:1.6;white-space:nowrap;border-bottom:1px solid #d7dfd5;margin:12px 0 18px;font-synthesis:none}.target{background:#f4f6ed}.Sans .target,.Sans .reading,.glyph.Sans{font-family:var(--sans-face,GZSans)}.Serif .target,.Serif .reading,.glyph.Serif{font-family:GZSerif}.Sans .native{font-family:NativeSans}.Serif .native{font-family:NativeSerif}.reading{font-size:clamp(20px,7cqw,36px);line-height:1.7;font-synthesis:none}.measures{display:flex;gap:24px;flex-wrap:wrap}.measure strong{display:block;font-size:24px}.measure span{font-size:12px;color:#64766b}.bar{height:10px;background:#e5eae1;position:relative;margin:18px 0 6px;border-radius:8px}.reference{position:absolute;left:50%;top:-4px;width:2px;height:18px;background:#839d87}.value{position:absolute;top:-3px;width:6px;height:16px;background:#214e40;border-radius:2px}.Serif .value{background:#aa643f}.scale{display:flex;justify-content:space-between;font-size:11px;color:#6a786e}.metrics-line{font-size:13px;line-height:1.7}.stats{display:flex;gap:24px;flex-wrap:wrap}.stats strong{font-size:27px;display:block}.stats span{font-size:12px}.tablewrap{overflow:auto}table{width:100%;border-collapse:collapse;font-size:14px;font-variant-numeric:tabular-nums}td,th{padding:10px 12px;border-bottom:1px solid #e1e7de;text-align:right;white-space:nowrap}td:first-child,th:first-child{text-align:left}th{background:#f5f7f0}summary{font-size:20px;cursor:pointer;font-weight:600}details{margin:30px 0}.glyph{font-size:29px;font-synthesis:none}.warn{color:#94512c}footer{margin-top:40px}#summary .Serif{border-top:3px solid #aa643f}#summary .Sans{border-top:3px solid #214e40}
@media(max-width:650px){main{padding:22px 12px}.columns{gap:10px}.panel,article{padding:12px;border-radius:8px}.family{font-size:14px;flex-wrap:wrap}.measures{gap:10px}.measure strong{font-size:19px}.metrics-line{font-size:11px}.stats{gap:14px}.stats strong{font-size:23px}.muted{font-size:12px}}
</style><main><div class="tag" id="versions">Sans / Serif</div><h1>Sans and Serif, side by side</h1><p>Identical forms at the same em size. Each family is measured against its own native Noto kana, so Serif’s thick–thin contrast remains part of the comparison.</p>
<nav><button data-style="Regular" class="active">Regular</button><button data-style="Bold">Bold</button><label id="edition-label" hidden>Sans <select id="edition"><option value="current">0.105</option><option value="previous">0.104</option></select></label><label>Stroke measure <select id="metric"><option value="q75">Thicker strokes · 75th percentile</option><option value="q50">Median · 50th percentile</option><option value="q90">Thickest region · 90th percentile</option></select></label></nav>
<div id="summary" class="columns"></div><p class="muted">The summary covers all 27 Funatsu forms. Relative width = form stroke percentile ÷ the median of the same percentile in its full-size comparison kana. Spread is the interquartile range of those ratios divided by their median. A smaller spread describes more uniform ratios; visual balance also depends on contrast, proportions and spacing.</p>
<details><summary>Numerical overview</summary><h2>Three measures of between-letter spread</h2><div id="dispersion" class="panel tablewrap"></div><p class="muted">These ratios describe geometric uniformity. The results vary by percentile; they do not establish a general visual-quality ranking.</p><h2>Selected form comparisons</h2><div id="findings" class="panel tablewrap"></div></details><h2>Okinawan forms</h2><p class="muted">Sans is on the left; Serif is on the right. Context, reading samples and metrics use the selected weight. The bar’s centre marks the comparison kana’s width. All 35 Okinawan forms are shown.</p><div id="forms"></div>
<details><summary>All 375 matched forms</summary><nav><input id="search" aria-label="Search characters" placeholder="Character, U+1B000, HWE…"><select id="group" aria-label="Character group"><option value="">All groups</option></select></nav><div id="all" class="panel tablewrap"></div></details>
<details><summary>Historical kana and other groups</summary><div id="groups" class="panel tablewrap"></div><p class="muted">Hentaigana compare with each family’s 48-letter native hiragana cohort. Marks and specialist symbols without a corresponding kana reference have no relative-width value. Groups retain their size conventions; their raw widths should not be equalized.</p></details>
<details><summary>Method, uncertainty and data</summary><p>Both families use the same medial-axis distance measurement at 512 and 1,024 pixels per em, with length weighting and exclusions near junctions and terminals. The 75th percentile helps examine the thicker strokes while the median and 90th percentile remain selectable. None is a perceptual quality score. Serif’s hairlines and terminals can influence the skeleton, so conclusions must agree with the visual comparison.</p>
<p>The vector censuses cover all 16,732 encoded Noto Sans JP characters and 16,726 encoded Noto Serif JP characters. Detailed measurements cover the same 375 GenZui forms and 192 native references per family, in both weights. Serif-only repertoire is outside the paired comparison. Unencoded alternates are excluded except for the explicitly shaped Okinawan sequences.</p>
<p>Comparison kana describe related full-size forms; they can differ from actual construction donors. SI and N use small ぃ strokes in their construction, and Glottal WA’s Sans drawing derives from ゐ and こ. Its わ comparison describes its structure. Component separation used for disconnected Sans ふ forms does not apply to connected Serif outlines.</p>
<p>Cards flag resolution changes over 5%. This is a sampling flag, not a design tolerance. Bold-to-Regular ratios are reported per percentile. A dash means the shape has insufficient stable axis support. Ink coverage is measured from the vector outline on a 1,000-unit em.</p>
<p><a href="parallel.json">Paired measurements</a> · <a href="vectors.csv">Sans native census</a> · <a href="serif/vectors.csv">Serif native census</a> · <a href="provenance.json">Sans sources</a> · <a href="serif/provenance.json">Serif sources</a> · <a href="https://scikit-image.org/docs/stable/api/skimage.morphology.html#skimage.morphology.medial_axis">Medial-axis method</a></p></details><footer class="muted">GenZui · released font measurements · units per em: 1,000</footer></main>
<script>
let data,currentSans,style='Regular',metric='q75';const $=s=>document.querySelector(s),num=x=>x==null?'—':x.toFixed(1),ratio=x=>x==null?'—':(100*x).toFixed(1)+'%',delta=x=>x==null?'—':(x>=0?'+':'')+x.toFixed(1)+'%',esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const rows=f=>data[f].forms.filter(r=>r.style===style);function table(head,rs){return '<table><thead><tr>'+head.map(v=>'<th>'+v+'</th>').join('')+'</tr></thead><tbody>'+rs.map(r=>'<tr>'+r.map(v=>'<td>'+v+'</td>').join('')+'</tr>').join('')+'</tbody></table>'}
function card(f,r){const w=style==='Bold'?700:400,q=r.stroke,rel=r.relative?.[metric];return '<article class="'+f+'"><div class="family">'+f+'<span class="muted">'+style+'</span></div><div class="specimen" style="font-weight:'+w+'"><span class="native">'+esc(r.donors[0]||'')+'</span><span class="target">'+esc(r.text)+'</span><span class="native">'+esc(r.donors.slice(1)||r.donors[0]||'')+'</span></div><div class="measures"><div class="measure"><strong>'+num(q?.[metric])+'</strong><span>Stroke width</span></div><div class="measure"><strong>'+ratio(rel)+'</strong><span>Relative to native kana</span></div></div><div class="bar"><span class="reference"></span>'+(rel==null?'':'<span class="value" style="left:'+Math.max(0,Math.min(99,100*(rel-.4)/1.2))+'%"></span>')+'</div><div class="scale"><span>40%</span><span>100%</span><span>160%</span></div><p class="metrics-line">Median '+num(q?.q50)+' · 75th '+num(q?.q75)+' · 90th '+num(q?.q90)+'<br>Ink '+ratio(r.ink_coverage)+' · Bold / Regular '+(r.bold_regular?.[metric]?.toFixed(2)||'—')+'×</p><div class="reading" style="font-weight:'+w+'">'+esc((r.donors[0]||'')+r.text+r.donors.slice(-1))+'</div><p class="muted '+(Math.abs(r.resolution_delta?.[metric]||0)>5?'warn':'')+'">512 → 1,024 px: '+delta(r.resolution_delta?.[metric])+'</p></article>'}
function render(){$('#versions').textContent=data.Sans.release+' / Serif 0.118';const a=rows('Sans'),b=rows('Serif'),bmap=new Map(b.map(r=>[r.text,r]));$('#summary').innerHTML=['Sans','Serif'].map(f=>{const m=data[f].groups.find(r=>r.style===style&&r.group==='funatsu').metrics[metric],base=data[f].native[style].Hiragana[metric];return '<div class="panel '+f+'"><div class="family">'+f+' <span class="muted">'+style+'</span></div><div class="stats"><div><strong>'+ratio(m.relative.q50)+'</strong><span>Median native-relative width</span></div><div><strong>'+num(m.relative_iqr_pct)+'%</strong><span>Between-letter spread</span></div></div><p class="muted">Native hiragana reference: '+num(base.q50)+' units<br>Middle 80% of native reference widths: '+num(base.q10)+'–'+num(base.q90)+'</p></div>'}).join('');
$('#dispersion').innerHTML=table(['Stroke measure','Sans spread','Serif spread'],[['q50','Median'],['q75','75th percentile'],['q90','90th percentile']].map(([q,label])=>[label,...['Sans','Serif'].map(f=>num(data[f].groups.find(r=>r.style===style&&r.group==='funatsu').metrics[q].relative_iqr_pct)+'%')]));
const keys=['KWE','SI','HWA','HWI','HWE','Glottal WA','Glottal WI','Glottal WE'];$('#findings').innerHTML=table(['Form','Sans relative','Serif relative','Sans width','Serif width'],keys.map(k=>{const x=a.find(r=>r.label===k),y=bmap.get(x.text);return [k,ratio(x.relative?.[metric]),ratio(y.relative?.[metric]),num(x.stroke?.[metric]),num(y.stroke?.[metric])]}));
$('#forms').innerHTML=a.filter(r=>['funatsu','prefecture'].includes(r.group)).map(r=>'<section class="pair"><h3>'+esc(r.label)+'</h3><div class="columns">'+card('Sans',r)+card('Serif',bmap.get(r.text))+'</div></section>').join('');
const bg=new Map(data.Serif.groups.filter(r=>r.style===style).map(r=>[r.group,r]));$('#groups').innerHTML=table(['Group','Forms','Sans width','Serif width','Sans relative','Serif relative'],data.Sans.groups.filter(r=>r.style===style).map(g=>{const x=g.metrics[metric],y=bg.get(g.group).metrics[metric];return [esc(g.group),g.count,num(x.widths?.q50),num(y.widths?.q50),ratio(x.relative?.q50),ratio(y.relative?.q50)]}));renderAll();}
function renderAll(){const q=$('#search').value.toLowerCase().replace('u+',''),group=$('#group').value,b=new Map(rows('Serif').map(r=>[r.text,r]));$('#all').innerHTML=table(['Form','Sans','Serif','Sans width','Serif width','Sans relative','Serif relative'],rows('Sans').filter(r=>(!group||r.group===group)&&(!q||(r.text+' '+r.cp+' '+r.label).toLowerCase().includes(q))).map(r=>{const s=b.get(r.text),w=style==='Bold'?700:400;return [esc(r.label),'<span class="glyph Sans" style="font-weight:'+w+'">'+esc(r.text)+'</span>','<span class="glyph Serif" style="font-weight:'+w+'">'+esc(s.text)+'</span>',num(r.stroke?.[metric]),num(s.stroke?.[metric]),ratio(r.relative?.[metric]),ratio(s.relative?.[metric])]}));}
document.querySelectorAll('[data-style]').forEach(b=>b.onclick=()=>{style=b.dataset.style;document.querySelectorAll('[data-style]').forEach(x=>x.classList.toggle('active',x===b));render()});$('#edition').onchange=()=>{const old=$('#edition').value==='previous';data.Sans=old?data.SansPrevious:currentSans;document.documentElement.style.setProperty('--sans-face',old?'GZSans':'GZRevised');render()};$('#metric').onchange=()=>{metric=$('#metric').value;render()};$('#search').oninput=renderAll;$('#group').onchange=renderAll;
fetch('parallel.json').then(r=>r.json()).then(d=>{data=d;currentSans=d.Sans;if(d.SansPrevious){$('#edition-label').hidden=false;document.documentElement.style.setProperty('--sans-face','GZRevised')}$('#group').innerHTML+=[...new Set(rows('Sans').map(r=>r.group))].map(g=>'<option>'+esc(g)+'</option>').join('');render();document.documentElement.dataset.ready='true'}).catch(e=>{$('#summary').textContent='Could not load measurements: '+e.message});
</script></html>'''


if __name__=='__main__':
    build()
