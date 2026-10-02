"""Build the Sans Okinawan proof and sentence-ready subset.

The full faces extend the immutable Sans 0.103 release. This preserves its
published repertoire and avoids including unrelated, unreleased donor changes.
"""
import hashlib
import html
import json
import shutil
from zipfile import ZipFile, ZIP_DEFLATED
from fontTools import subset
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont
from sources import ROOT
from serif import add, glyph, contours, transform, add_feature
from okinawan import ENTRIES, add_okinawan
import okinawan_sans
from okinawan_subset import repertoire
from kugyol import rename, parent_name
from okinawan_sns import SENTENCES, compose

OUT=ROOT/'build/sans-okinawan'
BASE=ROOT/'releases/sans-v0.103'
VERSION='0.104'
FAMILY='GenZui Sans Okinawan'
PREFIX='GenZuiSansOkinawan'
SERIF_ARCHIVE=ROOT/'releases/v0.118/GenZuiSerifOkinawan-0.118.zip'
SERIF_FILES=[f'GenZuiSerifOkinawan-{style}.woff2' for style in ('Regular','Bold')]+[
    'OFL.txt','NOTICE.txt','FRB-OFL.txt','FRB-README.md','Unicode-LICENSE.txt',
    'checks.json','sources.json','source-manifest.json','okinawan-mappings.json']

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def build():
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'full').mkdir(exist_ok=True)
    (OUT/'checks.json').unlink(missing_ok=True)
    source_manifest=json.loads((ROOT/'sources/manifest.json').read_text())
    for entry in source_manifest['files']:
        if entry['path'].startswith(('sources/upstream/NotoSansJP/','sources/upstream/NotoSerifJP/')):
            assert digest(ROOT/entry['path'])==entry['sha256'],entry['path']
    baseline_checks={}
    with ZipFile(BASE/'GenZuiSans-0.103.zip') as archive:
        for style,name in [('Regular','checks.json'),('Bold','checks-bold.json')]:
            baseline_checks[style]=json.loads(archive.read(name))
        for name in ('OFL.txt','NotoSansHentaigana-OFL.txt','GenSeki-OFL.txt','GenSeki-README.md',
                     'NotoSansCJK-OFL.txt','FRB-OFL.txt','FRB-README.md','Unicode-LICENSE.txt',
                     'source-manifest.json','sans-source-manifest.json'):
            (OUT/name).write_bytes(archive.read(name))
        (OUT/'full'/'NOTICE.txt').write_bytes(archive.read('NOTICE.txt')+b'\nOkinawan forms: GenZui drawings from Noto Sans JP masters.\n')
    (OUT/'NOTICE.txt').write_text('GenZui Sans Okinawan / 源萃ゴシック 沖縄文字\n\n'
        'Kana, Latin, punctuation and new Okinawan drawings derive from Noto Sans JP.\n'
        'Retained combining marks derive from FRB Taiwanese Kana.\n'
        'Regular and Bold use the native Noto masters at weights 400 and 700; reduced\n'
        'components use optical donor weights 450–600 and 750–900. The 27 Funatsu forms\n'
        'and eight raised katakana use the same private-use conventions as GenZui Serif.\n'
        'No outlines were imported from the fonts defining those mappings.\n\n'
        'Proof references and optical alternatives for GenZui Serif derive from\n'
        'Noto Serif JP. Their notices and licenses are in the serif/ directory.\n\n'
        'Licensed under SIL Open Font License 1.1. Original notices are retained.\n')
    records=[]
    for style in ('Regular','Bold'):
        path=BASE/f'GenZuiSans-{style}.ttf'
        assert baseline_checks[style]['status']=='passed'
        assert digest(path)==baseline_checks[style]['ttf_sha256'],style
        font=TTFont(path,recalcTimestamp=False)
        add_okinawan(font,add,glyph,contours,transform,add_feature,bold=style=='Bold',provider=okinawan_sans)
        notice,license_text,license_url=[parent_name(font,n) for n in (0,13,14)]
        rename(font,'GenZui Sans','源萃ゴシック',style,f'GenZuiSans-{style}',VERSION,notice,license_text,license_url)
        font['OS/2'].recalcUnicodeRanges(font)
        full=OUT/'full'/f'GenZuiSans-{style}.ttf';font.save(full)
        font.flavor='woff2';font.save(full.with_suffix('.woff2'));font.flavor=None
        points=repertoire(font)
        options=subset.Options();options.recalc_timestamp=False;options.notdef_outline=True;options.layout_features=['*']
        sub=subset.Subsetter(options=options);sub.populate(unicodes=points);sub.subset(font)
        stem=f'{PREFIX}-{style}'
        rename(font,FAMILY,'源萃ゴシック 沖縄文字',style,stem,VERSION,notice,license_text,license_url)
        font.save(OUT/f'{stem}.ttf');font.flavor='woff2';font.save(OUT/f'{stem}.woff2')
        records.append(dict(style=style,base_sha256=digest(path),full_sha256=digest(full),encoded_characters=len(points),
                            **{ext+'_sha256':digest(OUT/f'{stem}.{ext}') for ext in ('ttf','woff2')}))
        print(style,len(points),flush=True)
    (OUT/'sources.json').write_text(json.dumps(dict(family=FAMILY,version=VERSION,baseline='GenZui Sans 0.103',faces=records),indent=2)+'\n')
    (OUT/'genzui-sans-okinawan.css').write_text('\n'.join(f"@font-face {{ font-family: '{FAMILY}'; src: url('./{PREFIX}-{style}.woff2') format('woff2'); font-weight: {weight}; font-style: normal; font-display: swap; }}" for style,weight in [('Regular',400),('Bold',700)])+'\n')
    shutil.copyfile(ROOT/'data/okinawan/mappings.json',OUT/'okinawan-mappings.json')
    (OUT/'README.txt').write_text((ROOT/'templates/sans-okinawan-README.txt').read_text().replace('{{VERSION}}',VERSION))
    proof()

def source_text(e):
    if e.get('kana'):
        text=e['kana'];return text[0]+{'ぅ':'つ','ぃ':'い','ぇ':'え','ゎ':'わ'}.get(text[-1],text[-1])
    if e.get('base'):return chr(int(e['base'],16))
    return {'\'ya':'や','\'yu':'ゆ','\'yo':'よ','\'wa':'ゐ','\'wi':'ゐ','\'we':'ゑ','\'n':'ん','yi':'い','ye':'え'}[e['id']]

def proof():
    reference=OUT/'serif';reference.mkdir(exist_ok=True)
    with ZipFile(SERIF_ARCHIVE) as archive:
        checks=json.loads(archive.read('checks.json'));assert checks['status']=='passed'
        for name in SERIF_FILES:(reference/name).write_bytes(archive.read(name))
        for face in checks['faces']:
            assert digest(reference/f"GenZuiSerifOkinawan-{face['style']}.woff2")==face['woff2_sha256']
    from sans_okinawan_variants import build as proof_variants
    variants=proof_variants(OUT,ROOT,VERSION)
    sections=[];accepted=[];other=[]
    active_ids={'tu','du','hwe',"'yu","'yo","'we",'wu'}
    previous=all((OUT/'previous'/f'{style}.woff2').exists() for style in ('Regular','Bold'))
    for e in ENTRIES:
        text=''.join(chr(int(c,16)) for c in e['output']);src=source_text(e)
        cards=[]
        for style,weight in [('Regular',400),('Bold',700)]:
            context=src[0]+text+src[-1] if len(src)>1 else src+text+src
            history=(f'<details><summary>前の字形と比較</summary><div class="previous">{context}</div></details>' if previous else '')
            serif_face='GenZui Serif Okinawan Optical' if e['system']=='prefecture' else 'GenZui Serif Okinawan'
            cards.append(f'<article style="--weight:{weight}"><h3>{style}</h3><div class="context">{context}</div><div class="sizes"><span style="font-size:24px">{context}</span><span style="font-size:48px">{context}</span></div><div class="serif-row"><small>Serif</small><span class="serif" data-family="{serif_face}" style="font-family:{serif_face}">{context}</span></div>{history}</article>')
        row=f'<section data-form="{html.escape(e["id"],quote=True)}"><h2>{html.escape(e["label"])}</h2><div class="columns">{"".join(cards)}</div></section>'
        (sections if e['id'] in active_ids else other if e['id'] in ('yi','ye') else accepted).append(row)
    sentences=[]
    for style,weight in [('Regular',400),('Bold',700)]:
        sentences.append(f'<article style="--weight:{weight}"><h3>{style}</h3>'+''.join(f'<p class="sentence" contenteditable="true">{html.escape(compose(s["text"]))}</p>' for s in SENTENCES)+'</article>')
    page='''<!doctype html><html lang="ja"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>GenZui Sans Okinawan</title><link rel="stylesheet" href="genzui-sans-okinawan.css"><style>
*{box-sizing:border-box}body{margin:0;background:#f7f8f2;color:#233d34;font-family:system-ui,sans-serif}main{max-width:1440px;margin:auto;padding:40px 24px}h1{font-size:32px;margin-bottom:8px}header p{color:#64746b}section{margin:30px 0}h2{font-size:19px}h3{font-size:15px;margin:0 0 25px}.columns{display:grid;grid-template-columns:1fr 1fr;gap:18px}article{background:white;border:1px solid #d5ded8;border-radius:10px;padding:24px;overflow:hidden}.context,.sizes,.sentence,.previous,.serif,.raised-sample{font-family:'GenZui Sans Okinawan';font-weight:var(--weight);font-synthesis:none}.context{font-size:clamp(60px,8.9vw,128px);line-height:1.2;border-bottom:1px solid #d5ded8;white-space:nowrap}.previous{font-family:'GenZui Sans Okinawan Previous';font-size:clamp(60px,8.9vw,128px);line-height:1.2;white-space:nowrap}details{margin-top:24px;border-top:1px solid #d5ded8;padding-top:16px}.approved-group>summary,.other-group>summary{font-size:18px;font-weight:600;padding:12px 0}.approved-group,.other-group{margin-top:32px}summary{cursor:pointer;font-size:13px;color:#64746b}.serif-row{display:flex;align-items:center;gap:18px;margin-top:20px}.serif-row small{font-size:12px;color:#64746b}.serif{font-family:'GenZui Serif Okinawan';font-size:30px;line-height:1.5;white-space:nowrap}.raised-sample{line-height:1.8}.raised-sample span{display:inline-block;margin-right:.3em}.sizes{display:flex;gap:25px;align-items:baseline;margin-top:30px}.sentence{font-size:30px;line-height:1.9;overflow-wrap:anywhere}a{color:inherit}footer{font-size:13px;line-height:1.8}@media(max-width:650px){main{padding:24px 12px}article{padding:14px}.columns{gap:10px}.context,.previous{font-size:8.5vw}.serif-row{gap:6px;flex-wrap:wrap}.serif{font-size:24px}.sizes{flex-direction:column;gap:10px}.sizes span{font-size:20px!important}.sentence{font-size:21px}}
</style><main><header><h1>GenZui Sans Okinawan</h1><p>Regular / Bold · 船津式沖縄文字 27字・上付きカタカナ 8字</p><p>字形見本：元の仮名 / 沖縄文字 / 元の仮名</p></header>'''
    serif_faces=''.join(f"@font-face{{font-family:'GenZui Serif Okinawan';src:url('serif/GenZuiSerifOkinawan-{style}.woff2');font-weight:{weight};font-display:swap}}" for style,weight in [('Regular',400),('Bold',700)])
    page=page.replace('</style>','</style><style>'+serif_faces+'</style>',1)
    variant_faces=''.join(f"@font-face{{font-family:'{v['family']}';src:url('{v['file']}');font-weight:{400 if v['style']=='Regular' else 700};font-display:swap}}" for v in variants)
    page=page.replace('</style>','</style><style>'+variant_faces+'</style>',1)
    if previous:
        faces=''.join(f"@font-face{{font-family:'GenZui Sans Okinawan Previous';src:url('previous/{style}.woff2');font-weight:{weight};font-display:swap}}" for style,weight in [('Regular',400),('Bold',700)])
        page=page.replace('</style>','</style><style>'+faces+'</style>',1)
    raised=[e for e in ENTRIES if e['system']=='prefecture']
    pairs=''.join(f'<span>{chr(int(e["base"],16))}{chr(int(e["output"][0],16))}</span>' for e in raised)
    optical_cards=[]
    for family in ('Serif','Sans'):
        rows=[]
        for style,weight in [('Regular',400),('Bold',700)]:
            face='GenZui Serif Okinawan Optical' if family=='Serif' else 'GenZui Sans Okinawan'
            samples=''.join(f'<div class="raised-sample" data-family="{face}" style="font-family:{face};--weight:{weight};font-size:{size}px">{pairs}</div>' for size in (24,32))
            rows.append(f'<h3>{style}</h3>'+samples)
        optical_cards.append(f'<article><h2>{family}</h2>'+''.join(rows)+'</article>')
    optical_section='<section id="raised-comparison"><h2>上付きカタカナ · 24 / 32 px</h2><div class="columns">'+''.join(optical_cards)+'</div></section>'
    page+=''.join(sections)
    page+='<section><h2>組見本</h2><div class="columns">'+''.join(sentences)+'</div></section>'
    page+='<details class="approved-group"><summary>確認済み · 26字</summary>'+optical_section+''.join(accepted)+'</details>'
    page+='<details class="other-group"><summary>YI / YE</summary>'+''.join(other)+'</details>'
    page+='<footer>組見本の出典：<a href="https://repository.ninjal.ac.jp/record/3226/files/20210312Uchinaaguchi_e.pdf">沖縄語辞典</a>、121・123頁。<br>私用領域の文字を含みます。対応フォントと入力方法が必要です。</footer></main></html>'
    (OUT/'index.html').write_text(page)
    # Raster overview uses the exact TTFs with HarfBuzz shaping.
    im=Image.new('RGB',(1400,len(ENTRIES)*175+60),'#f7f8f2');d=ImageDraw.Draw(im)
    label=ImageFont.truetype('DejaVuSans.ttf',17)
    for row,e in enumerate(ENTRIES):
        text=''.join(chr(int(c,16)) for c in e['output']);src=source_text(e)
        context=src[0]+text+src[-1] if len(src)>1 else src+text+src
        for col,style in enumerate(('Regular','Bold')):
            x=20+col*700;y=row*175+25
            f=ImageFont.truetype(str(OUT/f'{PREFIX}-{style}.ttf'),125)
            d.text((x,y),e['label']+' / '+style,font=label,fill='#456054')
            d.text((x+160,y+127),context,font=f,fill='#111111',anchor='ls')
    im.save(OUT/'overview.png')

def package():
    checks=json.loads((OUT/'checks.json').read_text());assert checks['status']=='passed'
    for record in checks['faces']:
        for ext in ('ttf','woff2'):
            assert record[ext+'_sha256']==digest(OUT/f'{PREFIX}-{record["style"]}.{ext}')
        assert record['full_sha256']==digest(OUT/'full'/f'GenZuiSans-{record["style"]}.ttf')
    names=[f'{PREFIX}-{style}.{ext}' for style in ('Regular','Bold') for ext in ('ttf','woff2')]
    names+=['genzui-sans-okinawan.css','index.html','README.txt','NOTICE.txt','OFL.txt','FRB-OFL.txt',
            'FRB-README.md','Unicode-LICENSE.txt','source-manifest.json','sources.json','checks.json','okinawan-mappings.json']
    names += ['serif/'+name for name in SERIF_FILES]
    variants=json.loads((OUT/'variants/manifest.json').read_text())
    for v in variants:assert digest(OUT/v['file'])==v['sha256']
    names += [v['file'] for v in variants]+['variants/manifest.json']
    if all((OUT/'previous'/f'{style}.woff2').exists() for style in ('Regular','Bold')):
        names += [f'previous/{style}.woff2' for style in ('Regular','Bold')]
    archive=ROOT/'dist'/f'{PREFIX}-{VERSION}.zip';archive.parent.mkdir(exist_ok=True)
    with ZipFile(archive,'w',compression=ZIP_DEFLATED) as z:
        for name in names:z.write(OUT/name,name)
    with ZipFile(archive) as z:
        assert z.testzip() is None
        for name in names:assert z.read(name)==(OUT/name).read_bytes()
    print(f'Packaged {archive.name}: {len(names)} files.')

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--package',action='store_true');args=parser.parse_args()
    package() if args.package else build()
