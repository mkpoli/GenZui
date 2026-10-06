"""Compile and import calibrated hentaigana donors for Sans 0.105."""
import hashlib
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

from sources import ROOT

OUT=ROOT/'build/sans-weight-donors'
AXES={'Regular':410,'Bold':770}
POINTS=set(range(0x1B001,0x1B11F))


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def donor_path(style):return OUT/f'NotoSansHentaigana-Balanced{style}.ttf'


def prepare():
    """Use the pinned source archive and the Sans compiler environment."""
    from glyphsLib import GSFont, GSInstance
    import importlib.metadata
    manifest=json.loads((ROOT/'sources/sans-manifest.json').read_text(encoding='utf-8'))
    item=next(x for x in manifest['files'] if x['filename']=='hentaigana.zip')
    archive=ROOT/'build/sans-work/hentaigana.zip'
    if not archive.exists():
        from urllib.request import urlopen
        archive.parent.mkdir(parents=True,exist_ok=True)
        data=urlopen(item['url'],timeout=120).read()
        assert hashlib.sha256(data).hexdigest()==item['sha256']
        archive.write_bytes(data)
    assert digest(archive)==item['sha256']
    OUT.mkdir(parents=True,exist_ok=True)
    inputs=dict(source_sha256=item['sha256'],axes=AXES,epoch='1749081600',
                compiler={p:importlib.metadata.version(p) for p in ('fontmake','fonttools','glyphsLib','ufo2ft')})
    stamp=OUT/'sources.json'
    if stamp.exists():
        record=json.loads(stamp.read_text(encoding='utf-8'))
        if record['inputs']==inputs and all(donor_path(s).exists() and digest(donor_path(s))==record['fonts'][s] for s in AXES):return
    prefix='hentaigana-3aa4d30ee04254d3d0a69c500de7fda494e3b302/sources/'
    with ZipFile(archive) as z:
        for member in z.namelist():
            if member.startswith(prefix+'NotoSansHentaigana.glyphspackage/') and not member.endswith('/'):
                relative=Path(member.removeprefix(prefix));assert '..' not in relative.parts
                target=OUT/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(member))
    source=GSFont(str(OUT/'NotoSansHentaigana.glyphspackage'))
    for style,axis in AXES.items():
        instance=GSInstance();instance.name='Balanced'+style;instance.axes=[axis];instance.weight=400 if style=='Regular' else 700
        source.instances.append(instance)
    study=OUT/'Balanced.glyphs';source.save(str(study))
    code="from fontmake.font_project import FontProject; import sys; FontProject().run_from_glyphs(sys.argv[1],output=['ttf'],interpolate='.* Balanced(Regular|Bold)$',master_dir='{tmp}',instance_dir='{tmp}',output_dir=sys.argv[2])"
    result=subprocess.run([sys.executable,'-c',code,str(study),str(OUT)],capture_output=True,text=True,
                          env={**os.environ,'SOURCE_DATE_EPOCH':inputs['epoch']})
    (OUT/'compiler.log').write_text((result.stdout+result.stderr).replace(str(Path.home()),'~'), encoding='utf-8')
    assert result.returncode==0,'Hentaigana compilation failed; see build/sans-weight-donors/compiler.log'
    from fontTools.ttLib import TTFont
    for style in AXES:
        font=TTFont(donor_path(style),recalcTimestamp=False)
        for table in font['cmap'].tables:
            if table.isUnicode() and table.format==12:table.cmap[0x1B001]='archaicYehiragana'
        font.save(donor_path(style))
    stamp.write_text(json.dumps(dict(inputs=inputs,fonts={s:digest(donor_path(s)) for s in AXES}),indent=2)+'\n', encoding='utf-8')
    print('Compiled hentaigana donors:',AXES,flush=True)


def apply(font,style):
    from fontTools.ttLib import TTFont
    record=json.loads((OUT/'sources.json').read_text(encoding='utf-8'))
    manifest=json.loads((ROOT/'sources/sans-manifest.json').read_text(encoding='utf-8'))
    pinned=next(x['sha256'] for x in manifest['files'] if x['filename']=='hentaigana.zip')
    assert record['inputs']['source_sha256']==pinned,'Hentaigana donor source does not match the pinned manifest'
    assert record['inputs']['axes']==AXES and digest(donor_path(style))==record['fonts'][style]
    donor=TTFont(donor_path(style));dc=donor.getBestCmap();fc=font.getBestCmap()
    assert POINTS<=dc.keys() and POINTS<=fc.keys()
    for cp in sorted(POINTS):
        g=copy.deepcopy(donor['glyf'][dc[cp]])
        assert not g.isComposite() and not g.program.getBytecode(),(style,hex(cp),'unexpected donor dependencies')
        name=fc[cp];font['glyf'][name]=g
        font['hmtx'][name]=(font['hmtx'][name][0],g.xMin)
        font['vmtx'][name]=(font['vmtx'][name][0],880-g.yMax)
    return record


if __name__=='__main__':prepare()
