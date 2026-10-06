"""Stage the approved Sans 0.104 extension and its public Okinawan subset."""
import html
import json
import shutil
from zipfile import ZipFile, ZIP_DEFLATED, ZipInfo
from fontTools.ttLib import TTFont
from sans_okinawan import OUT as PROOF, BASE, VERSION, PREFIX, digest
from sources import ROOT
from okinawan import ENTRIES, DESCRIPTIONS
from okinawan_sns import SENTENCES, compose

FULL=ROOT/'build/sans-release'
SUB=ROOT/'build/sans-okinawan-release'


def write_json(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')


def specimen(folder,family,prefix):
    faces=''.join(f"@font-face{{font-family:Sample;src:url('{prefix}-{style}.woff2');font-weight:{weight}}}" for style,weight in [('Regular',400),('Bold',700)])
    columns=[]
    for style,weight in [('Regular',400),('Bold',700)]:
        groups=[]
        for system,title in [('funatsu','新沖縄文字'),('prefecture','上付きカタカナ')]:
            chars=''.join(f'<span title="{html.escape(e["label"])}">'+''.join(chr(int(cp,16)) for cp in e['output'])+'</span>' for e in ENTRIES if e['system']==system)
            groups.append(f'<h3>{title}</h3><div class="letters sample" data-family="{family}">{chars}</div>')
        sentence=compose(next(s['text'] for s in SENTENCES if s['style']==style))
        columns.append(f'<article style="font-weight:{weight}"><h2>{style}</h2>'+''.join(groups)+f'<p class="sample sentence" data-family="{family}" contenteditable="true">{sentence}</p></article>')
    page=f'''<!doctype html><html lang="ja"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{family} {VERSION}</title><style>{faces}
*{{box-sizing:border-box}}body{{margin:0;background:#f7f8f2;color:#233d34;font:16px/1.7 system-ui,sans-serif}}main{{max-width:1280px;margin:auto;padding:32px}}h1{{font-size:28px}}h2{{font-size:18px}}h3{{font-size:14px;font-weight:400}}.columns{{display:grid;grid-template-columns:1fr 1fr;gap:24px}}article{{background:white;border:1px solid #d5ded8;padding:24px;border-radius:10px}}.sample{{font-family:Sample;font-synthesis:none}}.letters{{display:flex;flex-wrap:wrap;font-size:48px;gap:8px}}.letters span{{min-width:1em}}.sentence{{font-size:28px;line-height:1.8;overflow-wrap:anywhere}}a{{color:inherit}}footer{{font-size:13px;margin-top:24px}}@media(max-width:650px){{main{{padding:16px}}.columns{{gap:10px}}article{{padding:12px}}.letters{{font-size:32px}}.sentence{{font-size:20px}}}}
</style><main><h1>{family} {VERSION}</h1><p>新沖縄文字27字・上付きカタカナ8字</p><div class="columns">{''.join(columns)}</div><footer><p>文章をクリックして試し書きできます。私用領域の文字は対応フォントが必要です。<a href="okinawan-mappings.json">文字コード表</a> · <a href="OFL.txt">SIL OFL 1.1</a></p><p>例文：宮良信詳『うちなーぐち活用辞典』(2021)、121・123頁。仮名の組み合わせを船津式の合字に置換。</p></footer></main></html>'''
    (folder/'index.html').write_text(page)


def stage():
    checks=json.loads((PROOF/'checks.json').read_text());assert checks['status']=='passed'
    for face in checks['faces']:
        style=face['style']
        assert digest(PROOF/'full'/f'GenZuiSans-{style}.ttf')==face['full_sha256']
        assert digest(PROOF/'full'/f'GenZuiSans-{style}.woff2')==face['full_woff2_sha256']
        for ext in ('ttf','woff2'):assert digest(PROOF/f'{PREFIX}-{style}.{ext}')==face[ext+'_sha256']
    for folder in (FULL,SUB):
        if folder.exists():shutil.rmtree(folder)
        folder.mkdir(parents=True)
    # Keep the original audit as an explicitly versioned record, never relabel it.
    with ZipFile(BASE/'GenZuiSans-0.103.zip') as archive:
        for name in archive.namelist():
            if name.endswith(('.txt','.md')) or name in ('source-manifest.json','sans-source-manifest.json'):
                (FULL/name).write_bytes(archive.read(name))
        for style,suffix in [('Regular',''),('Bold','-bold')]:
            provenance=json.loads(archive.read(f'sources{suffix}.json'))
            provenance.update(version=VERSION,encoded_characters=17096)
            provenance['source_kinds'].update({f'U+{cp:04X}':'GenZui Okinawan drawing: '+desc for cp,desc in DESCRIPTIONS.items()})
            write_json(FULL/f'sources{suffix}.json',provenance)
            (FULL/f'baseline-0.103-checks{suffix}.json').write_bytes(archive.read(f'checks{suffix}.json'))
        coverage=json.loads(archive.read('kana-coverage.json'));coverage.update(font_version=VERSION,font_sha256=checks['faces'][0]['full_sha256'])
        write_json(FULL/'kana-coverage.json',coverage)
    for style,suffix in [('Regular',''),('Bold','-bold')]:
        face=next(f for f in checks['faces'] if f['style']==style)
        for ext in ('ttf','woff2'):
            shutil.copy2(PROOF/'full'/f'GenZuiSans-{style}.{ext}',FULL)
            shutil.copy2(PROOF/f'{PREFIX}-{style}.{ext}',SUB)
        record=dict(status='passed',family='GenZui Sans',style=style,version=VERSION,encoded_characters=17096,
                    ttf_sha256=digest(FULL/f'GenZuiSans-{style}.ttf'),woff2_sha256=digest(FULL/f'GenZuiSans-{style}.woff2'),
                    baseline='0.103',preserved_glyphs=face['preserved_glyphs'],extension_validation='okinawan-checks.json')
        write_json(FULL/f'checks{suffix}.json',record)
    for folder,prefix,family in [(FULL,'GenZuiSans','GenZui Sans'),(SUB,PREFIX,'GenZui Sans Okinawan')]:
        (folder/'okinawan-checks.json').write_bytes((PROOF/'checks.json').read_bytes())
        shutil.copy2(PROOF/'okinawan-mappings.json',folder)
        css='genzui-sans.css' if folder==FULL else 'genzui-sans-okinawan.css'
        (folder/css).write_text(''.join(f"@font-face {{\n  font-family: '{family}';\n  src: url('./{prefix}-{style}.woff2') format('woff2');\n  font-weight: {weight};\n  font-style: normal;\n  font-display: swap;\n}}\n" for style,weight in [('Regular',400),('Bold',700)]))
        specimen(folder,family,prefix)
        for style in ('Regular','Bold'):
            font=TTFont(folder/f'{prefix}-{style}.ttf');assert font['name'].getDebugName(1)==family
    for name in ('OFL.txt','FRB-OFL.txt','FRB-README.md','Unicode-LICENSE.txt','source-manifest.json','sources.json'):
        shutil.copy2(PROOF/name,SUB/name)
    (FULL/'NOTICE.txt').write_bytes((PROOF/'full/NOTICE.txt').read_bytes())
    (SUB/'NOTICE.txt').write_text((PROOF/'NOTICE.txt').read_text().split('Proof references')[0]+'Licensed under SIL Open Font License 1.1. Original notices are retained.\n')
    (SUB/'README.txt').write_text((ROOT/'templates/sans-okinawan-README.txt').read_text().replace('{{VERSION}}',VERSION).replace('beside native kana ',''))
    (FULL/'README.txt').write_text(f'''GenZui Sans / 源萃ゴシック {VERSION}\nRegular and Bold · 17,096 encoded characters\n\nInstall the two TTF files, or load genzui-sans.css beside the WOFF2 files.\nOpen index.html for editable Okinawan samples.\n\nThis release preserves Sans 0.103 and adds 27 Funatsu forms and eight raised\nkatakana. Kana, kanji, hentaigana and historical forms remain available.\nThe separate GenZui Sans Okinawan subset contains 805 encoded characters\nfor kana sentences. It does not include kanji.\n\nPrivate-use characters require a compatible font: see okinawan-mappings.json.\nThe extension audit is in okinawan-checks.json; baseline-0.103-checks files\nrecord the original release's checks. Source notices accompany these OFL fonts.\n''')
    # Remove stale packages' browser status before checking this staged tree.
    (FULL/'browser-checks.json').unlink(missing_ok=True)
    (SUB/'browser-checks.json').unlink(missing_ok=True)
    for folder in (FULL,SUB):
        write_json(folder/'staged-assets.json',{p.name:digest(p) for p in sorted(folder.iterdir()) if p.is_file()})
    print('Staged full Sans 0.104 and sentence-ready subset from validated fonts.')


def package():
    for folder,prefix in [(FULL,'GenZuiSans'),(SUB,PREFIX)]:
        report=json.loads((folder/'browser-checks.json').read_text());assert report['status']=='passed'
        for style,key in [('Regular',''),('Bold','bold_')]:
            for ext in ('ttf','woff2'):assert digest(folder/f'{prefix}-{style}.{ext}')==report[key+ext+'_sha256']
        archive=ROOT/'dist'/f'{prefix}-{VERSION}.zip';archive.parent.mkdir(exist_ok=True)
        staged=json.loads((folder/'staged-assets.json').read_text())
        expected=set(staged)|{'staged-assets.json','browser-checks.json','preview.png'}
        assert {p.name for p in folder.iterdir()}==expected,'Unexpected staged files'
        for name,sha in staged.items():assert digest(folder/name)==sha,name
        files=[folder/name for name in sorted(expected)]
        with ZipFile(archive,'w',ZIP_DEFLATED,compresslevel=9) as z:
            for p in files:
                info=ZipInfo(p.name,(2026,10,6,0,0,0));info.compress_type=ZIP_DEFLATED;info.external_attr=0o644<<16
                z.writestr(info,p.read_bytes())
        with ZipFile(archive) as z:
            assert z.testzip() is None
            for p in files:assert z.read(p.name)==p.read_bytes()
        print(f'{archive.name}: {len(files)} verified files')

def checked_assets():
    """Public subset files, tied to both the validated stage and ZIP bytes."""
    report=json.loads((SUB/'browser-checks.json').read_text());assert report['status']=='passed'
    staged=json.loads((SUB/'staged-assets.json').read_text())
    audit=json.loads((SUB/'okinawan-checks.json').read_text());assert audit['status']=='passed'
    assert digest(SUB/'okinawan-checks.json')==staged['okinawan-checks.json']
    for face in audit['faces']:
        style=face['style'];key='' if style=='Regular' else 'bold_'
        assert digest(FULL/f'GenZuiSans-{style}.ttf')==face['full_sha256']
        assert digest(FULL/f'GenZuiSans-{style}.woff2')==face['full_woff2_sha256']
        for ext in ('ttf','woff2'):
            assert digest(SUB/f'{PREFIX}-{style}.{ext}')==face[ext+'_sha256']==report[key+ext+'_sha256']
    archive=ROOT/'dist'/f'{PREFIX}-{VERSION}.zip'
    files=[SUB/f'{PREFIX}-{style}.{ext}' for style in ('Regular','Bold') for ext in ('ttf','woff2')]
    files.append(SUB/'genzui-sans-okinawan.css')
    with ZipFile(archive) as z:
        for path in files:
            assert digest(path)==staged[path.name]
            assert path.read_bytes()==z.read(path.name)
    return files+[archive]


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--package',action='store_true');args=p.parse_args()
    package() if args.package else stage()
