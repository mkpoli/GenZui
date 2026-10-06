"""Measure staged Sans with the same baseline and method as release 0.104."""
import json
import shutil
import unicodedata
from PIL import ImageFont
from fontTools.ttLib import TTFont
import uharfbuzz as hb
from sans_weight_audit import OUT as AUDIT, ROOT, raster, digest
from okinawan_weight_audit import shaped, vector
from sans_okinawan import OUT as PROOF, VERSION

OUT=AUDIT/'revision'


def measure():
    OUT.mkdir(parents=True,exist_ok=True)
    original=json.loads((AUDIT/'vectors.json').read_text())
    entries=[{k:r[k] for k in ('text','label','cp','group','donors')} for r in original if r['origin']=='GenZui' and r['style']=='Regular']
    vectors=[r for r in original if r['origin']=='Noto']
    strokes=[r for r in json.loads((AUDIT/'strokes.json').read_text()) if r['origin']=='Noto']
    provenance=json.loads((AUDIT/'provenance.json').read_text());provenance['release']='sans-v'+VERSION
    for style in ('Regular','Bold'):
        path=PROOF/'full'/f'GenZuiSans-{style}.ttf'
        provenance['faces'][style]['font_sha256']=digest(path)
        font=TTFont(path);gs=font.getGlyphSet();engine=hb.Font(hb.Face(path.read_bytes()));engine.scale=(1000,1000)
        for e in entries:
            glyphs,advance=shaped(font,engine,e['text'])
            vectors.append(dict(style=style,origin='GenZui',**e,advance=advance,glyph=' '.join(g[0] for g in glyphs),**vector(gs,glyphs)))
        for pixels in (512,1024):
            face=ImageFont.truetype(str(path),pixels,layout_engine=ImageFont.Layout.RAQM)
            isolated=ImageFont.truetype(str(path),pixels,layout_engine=ImageFont.Layout.BASIC)
            for i,e in enumerate(entries):
                renderer=isolated if len(e['text'])==1 and unicodedata.category(e['text']).startswith('M') else face
                result=raster(renderer,e['text'],pixels,e['label'] in ('HWA','HWI','HWE'))
                assert result is not None,e['label']
                strokes.append(dict(style=style,origin='GenZui',pixels=pixels,**e,**result))
                if i%100==0:print(style,pixels,i,'/',len(entries),flush=True)
        shutil.copyfile(path.with_suffix('.woff2'),AUDIT/f'Revised-{style}.woff2')
    # Use current provenance for the hentaigana donors, not the 0.104 strings.
    from sans_weight_correction import AXES,POINTS
    for style in ('Regular','Bold'):
        provenance['faces'][style]['source_kinds'].update({f'U+{cp:04X}':f'Noto Sans Hentaigana instance at weight axis {AXES[style]}' for cp in POINTS})
    for name,value in [('vectors',vectors),('strokes',strokes),('provenance',provenance)]:
        (OUT/f'{name}.json').write_text(json.dumps(value,ensure_ascii=False,separators=(',',':'))+'\n')
    from parallel_weight_report import analyze
    result=analyze(OUT)
    (AUDIT/'revision.json').write_text(json.dumps(result,ensure_ascii=False,separators=(',',':'))+'\n')
    print('Measured staged Sans',VERSION,flush=True)


if __name__=='__main__':measure()
