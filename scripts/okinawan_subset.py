"""Build GenZui Serif Okinawan from the checked full Serif faces."""
import hashlib
import json
import shutil
from zipfile import ZipFile, ZIP_DEFLATED
from fontTools import subset
from fontTools.ttLib import TTFont
from sources import ROOT
from serif import OUT as PARENT, VERSION
from okinawan import ENTRIES
from kugyol import rename, parent_name

OUT=ROOT/'build/okinawan'
FAMILY='GenZui Serif Okinawan'
FAMILY_JA='源萃明朝 沖縄文字'
PREFIX='GenZuiSerifOkinawan'
PACKAGE=f'{PREFIX}-{VERSION}.zip'
RANGES=((0x20,0x24f),(0x300,0x36f),(0x2000,0x206f),(0x3000,0x30ff),(0x31f0,0x31ff),(0xff00,0xffef))

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def repertoire(font):
    cmap=set(font.getBestCmap())
    forms={int(cp,16) for e in ENTRIES for cp in e['output']}
    assert forms<=cmap
    return forms | ({0x25cc}&cmap) | {cp for cp in cmap if any(lo<=cp<=hi for lo,hi in RANGES)}

def checked_assets():
    checks=json.loads((OUT/'checks.json').read_text());assert checks['status']=='passed'
    paths=[]
    for record in checks['faces']:
        assert record['parent_sha256']==digest(PARENT/f'GenZuiSerif-{record["style"]}.ttf')
        for ext in ('ttf','woff2'):
            path=OUT/f'{PREFIX}-{record["style"]}.{ext}'
            assert digest(path)==record[ext+'_sha256']
            paths.append(path)
    archive=ROOT/'dist'/PACKAGE
    with ZipFile(archive) as z:
        assert z.testzip() is None
        for path in paths:assert z.read(path.name)==path.read_bytes()
        assert json.loads(z.read('checks.json'))==checks
        assert z.read('genzui-okinawan.css')==(OUT/'genzui-okinawan.css').read_bytes()
    return paths+[OUT/'genzui-okinawan.css',archive]

def build():
    OUT.mkdir(parents=True,exist_ok=True)
    records=[]
    for style in ('Regular','Bold'):
        path=PARENT/f'GenZuiSerif-{style}.ttf'
        checks=json.loads((PARENT/('checks.json' if style=='Regular' else 'checks-bold.json')).read_text())
        assert checks['status']=='passed' and checks['ttf_sha256']==digest(path)
        parent=TTFont(path,recalcTimestamp=False);points=repertoire(parent)
        font=TTFont(path,recalcTimestamp=False)
        options=subset.Options();options.recalc_timestamp=False;options.notdef_outline=True;options.layout_features=['*']
        sub=subset.Subsetter(options=options);sub.populate(unicodes=points);sub.subset(font)
        stem=f'{PREFIX}-{style}'
        rename(font,FAMILY,FAMILY_JA,style,stem,VERSION,*[parent_name(parent,n) for n in (0,13,14)])
        font.save(OUT/f'{stem}.ttf');font.flavor='woff2';font.save(OUT/f'{stem}.woff2')
        records.append(dict(style=style,parent_sha256=digest(path),encoded_characters=len(points),
                            codepoints=[f'{cp:04X}' for cp in sorted(points)],
                            **{ext+'_sha256':digest(OUT/f'{stem}.{ext}') for ext in ('ttf','woff2')}))
    css='\n'.join(f"@font-face {{ font-family: '{FAMILY}'; src: url('./{PREFIX}-{style}.woff2') format('woff2'); font-weight: {weight}; font-style: normal; font-display: swap; }}" for style,weight in [('Regular',400),('Bold',700)])+'\n'
    (OUT/'genzui-okinawan.css').write_text(css)
    for name in ('OFL.txt','FRB-OFL.txt','FRB-README.md','Unicode-LICENSE.txt','source-manifest.json','okinawan-mappings.json'):
        shutil.copyfile(PARENT/name,OUT/name)
    (OUT/'NOTICE.txt').write_text((ROOT/'templates/okinawan-NOTICE.txt').read_text())
    (OUT/'NotoSerifCJK-OFL.txt').unlink(missing_ok=True)
    (OUT/'sources.json').write_text(json.dumps(dict(family=FAMILY,version=VERSION,parent='GenZui Serif',
        funatsu_forms=27,raised_katakana=8,faces=records),ensure_ascii=False,indent=2)+'\n')
    text=(ROOT/'templates/okinawan-README.txt').read_text().replace('{{VERSION}}',VERSION).replace('{{COUNT}}',str(len(points)))
    (OUT/'README.txt').write_text(text)
    proof()
    print(f'{FAMILY} {VERSION}: {len(points)} encoded characters in Regular and Bold.')

def proof():
    from okinawan_sns import SENTENCES,compose
    import html
    rows=[]
    for style in ('Regular','Bold'):
        cells=''.join(f'<div><span>{html.escape("".join(chr(int(c,16)) for c in e["output"]))}</span><small>{html.escape(e["label"])}</small></div>' for e in ENTRIES)
        paragraphs=''.join(f'<p contenteditable="true" spellcheck="false">{html.escape(compose(s["text"]))}</p>' for s in SENTENCES)
        rows.append(f'<section style="font-weight:{400 if style=="Regular" else 700}"><h2>{style}</h2><div class="glyphs">{cells}</div><div class="sentences">{paragraphs}</div></section>')
    page=(ROOT/'templates/okinawan-subset.html').read_text().replace('{{VERSION}}',VERSION).replace('{{SPECIMENS}}',''.join(rows))
    (OUT/'index.html').write_text(page)

def package():
    checks=json.loads((OUT/'checks.json').read_text());assert checks['status']=='passed'
    for r in checks['faces']:
        for ext in ('ttf','woff2'):assert r[ext+'_sha256']==digest(OUT/f'{PREFIX}-{r["style"]}.{ext}')
    names=[f'{PREFIX}-{style}.{ext}' for style in ('Regular','Bold') for ext in ('ttf','woff2')]
    names+=['genzui-okinawan.css','index.html','README.txt','checks.json','sources.json','OFL.txt','NOTICE.txt',
            'FRB-OFL.txt','FRB-README.md','Unicode-LICENSE.txt','source-manifest.json','okinawan-mappings.json']
    archive=ROOT/'dist'/PACKAGE;archive.parent.mkdir(exist_ok=True)
    with ZipFile(archive,'w',compression=ZIP_DEFLATED) as z:
        for name in names:z.write(OUT/name,name)
    with ZipFile(archive) as z:
        assert z.testzip() is None and set(z.namelist())==set(names)
    print(f'Packaged {PACKAGE}: {len(names)} files.')

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--package',action='store_true');args=p.parse_args()
    package() if args.package else build()
