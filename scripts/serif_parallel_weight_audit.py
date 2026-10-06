"""Measure Serif 0.118 with exactly the same method and form set as Sans."""
import csv
import json
import time
import unicodedata
from zipfile import ZipFile

from PIL import ImageFont
from fontTools.ttLib import TTFont
import uharfbuzz as hb

from sans_weight_audit import ROOT, OUT as SANS_OUT, digest, raster, RESOLUTIONS
from okinawan_weight_audit import vector, shaped, script
from serif import font_path

OUT = SANS_OUT / 'serif'
RELEASE = ROOT / 'releases/v0.118'


def dump(name, value):
    (OUT/name).write_text(json.dumps(value,ensure_ascii=False,separators=(',',':'))+'\n')


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    start = time.monotonic()
    source = font_path('NotoSerifJP')
    manifest = json.loads((ROOT/'sources/manifest.json').read_text())
    pin = next(x['sha256'] for x in manifest['files'] if x['path']==str(source.relative_to(ROOT)))
    assert digest(source)==pin
    native = TTFont(source); ncmap = native.getBestCmap()
    sans_vectors = json.loads((SANS_OUT/'vectors.json').read_text())
    entries = [{k:r[k] for k in ('text','label','cp','group','donors')}
               for r in sans_vectors if r['origin']=='GenZui' and r['style']=='Regular']
    assert len(entries)==375
    sans_strokes = json.loads((SANS_OUT/'strokes.json').read_text())
    refs = [{k:r[k] for k in ('text','label','cp','group','donors')}
            for r in sans_strokes if r['origin']=='Noto' and r['style']=='Regular' and r['pixels']==1024]
    assert all(ord(r['text']) in ncmap for r in refs)
    vectors, strokes, faces = [], [], {}
    with ZipFile(RELEASE/'GenZuiSerif-0.118.zip') as archive:
        for style,weight in [('Regular',400),('Bold',700)]:
            path=RELEASE/f'GenZuiSerif-{style}.ttf'
            assert path.read_bytes()==archive.read(path.name)
            faces[style]=dict(font_sha256=digest(path))
            font=TTFont(path); gs=font.getGlyphSet(); ngs=native.getGlyphSet(location={'wght':weight})
            assert font['head'].unitsPerEm==native['head'].unitsPerEm==1000
            cache={}
            for index,(cp,name) in enumerate(sorted(ncmap.items())):
                if name not in cache: cache[name]=vector(ngs,[(name,0,0)])
                vectors.append(dict(style=style,origin='Noto',group=script(cp),cp=f'{cp:04X}',
                                    text=chr(cp),label=chr(cp),glyph=name,**cache[name]))
                if index%5000==0:print(style,'native vector',index,flush=True)
            engine=hb.Font(hb.Face(path.read_bytes()));engine.scale=(1000,1000)
            for e in entries:
                glyphs,advance=shaped(font,engine,e['text'])
                vectors.append(dict(style=style,origin='GenZui',**e,advance=advance,
                                    glyph=' '.join(g[0] for g in glyphs),**vector(gs,glyphs)))
            for pixels in RESOLUTIONS:
                reference=ImageFont.truetype(str(source),pixels,layout_engine=ImageFont.Layout.BASIC)
                reference.set_variation_by_axes([weight])
                face=ImageFont.truetype(str(path),pixels,layout_engine=ImageFont.Layout.RAQM)
                isolated=ImageFont.truetype(str(path),pixels,layout_engine=ImageFont.Layout.BASIC)
                for origin,collection,renderer in [('Noto',refs,reference),('GenZui',entries,face)]:
                    for index,e in enumerate(collection):
                        selected=isolated if origin=='GenZui' and len(e['text'])==1 and unicodedata.category(e['text']).startswith('M') else renderer
                        # Serif has connected fu outlines: the Sans x=500
                        # detached-component separation cannot apply here.
                        result=raster(selected,e['text'],pixels)
                        if result:strokes.append(dict(style=style,origin=origin,pixels=pixels,**e,**result))
                        if index%100==0:print(style,pixels,origin,index,'/',len(collection),flush=True)
                dump('strokes.json',strokes)
            print(style,'complete',round(time.monotonic()-start),'seconds',flush=True)
    dump('vectors.json',vectors)
    fields=['style','origin','group','cp','text','label','glyph','area','perimeter','effective_width','bbox_density','ink_em_fraction']
    with (OUT/'vectors.csv').open('w') as stream:
        writer=csv.DictWriter(stream,fields,extrasaction='ignore');writer.writeheader();writer.writerows(vectors)
    environment=json.loads((SANS_OUT/'provenance.json').read_text())
    dump('provenance.json',dict(release='v0.118',source_sha256=pin,faces=faces,native_encoded=len(ncmap),
        resolutions=RESOLUTIONS,matched_forms=375,environment=environment['environment'],
        calibration=environment['calibration'],scope='All encoded native glyphs; the 375 Sans comparison forms. Serif-only repertoire is excluded.'))
    print('Finished',round(time.monotonic()-start),'seconds',flush=True)


if __name__=='__main__':
    main()
