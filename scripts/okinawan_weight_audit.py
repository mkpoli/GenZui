"""Measure native Noto outlines and Okinawan drawings without changing them.

2A/P is an effective-width proxy, not a visual-weight target. Detailed kana
measurements use distance-to-boundary diameters along the medial axis.
"""
import argparse
import importlib.metadata
import platform
import csv
import hashlib
import json
import math
import shutil
from pathlib import Path

import numpy as np
import pathops
import uharfbuzz as hb
from scipy import ndimage
from skimage.morphology import medial_axis
from PIL import Image, ImageDraw, ImageFont, features
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.perimeterPen import PerimeterPen
from fontTools.pens.transformPen import TransformPen

from sources import ROOT
from serif import font_path
from okinawan import ENTRIES

OUT = ROOT / 'build/okinawan-weight-audit'
DONORS = {
    'TU':'とつ','DU':'どつ','TI':'てい','DI':'でい','KWA':'くわ','GWA':'ぐわ',
    'KWI':'くい','GWI':'ぐい','KWE':'くえ','GWE':'ぐえ','HWA':'ふわ',
    'HWI':'ふい','HWE':'ふえ','WU':'をつ','SI':'すい','ZI':'ずい','TSI':'つい','DZI':'づい',
    'Glottal YA':'やは','Glottal YU':'ゆは','Glottal YO':'よは','Glottal WA':'ゐわこ',
    'Glottal WI':'ゐこ','Glottal WE':'ゑこ','Glottal N':'んい','YI':'い','YE':'え',
}


def script(cp):
    from fontTools.unicodedata import script as unicode_script
    tag=unicode_script(chr(cp))
    return {'Hira':'Hiragana','Kana':'Katakana','Hani':'Han','Hang':'Hangul',
            'Latn':'Latin','Zyyy':'Common','Zinh':'Inherited'}.get(tag,tag)


def vector(gs, glyphs):
    path = pathops.Path()
    for name,x,y in glyphs:
        rec=DecomposingRecordingPen(gs)
        gs[name].draw(rec)
        rec.replay(TransformPen(path.getPen(),(1,0,0,1,x,y)))
    path=pathops.simplify(path)
    area=abs(path.area)
    if not area: return dict(area=0.,perimeter=0.,effective_width=0.,bbox=[0,0,0,0],bbox_density=0.)
    pen=PerimeterPen(tolerance=.001)
    path.draw(pen)
    b=list(path.bounds); bw,bh=b[2]-b[0],b[3]-b[1]
    return dict(area=area,perimeter=pen.value,effective_width=2*area/pen.value,
                bbox=b,bbox_density=area/(bw*bh),ink_em_fraction=area/1e6)


def shaped(font, face, text):
    buf=hb.Buffer();buf.add_str(text);buf.guess_segment_properties()
    hb.shape(face,buf)
    x=y=0;out=[]
    for g,p in zip(buf.glyph_infos,buf.glyph_positions):
        assert g.codepoint, ('Missing glyph',text)
        out.append((font.getGlyphName(g.codepoint),x+p.x_offset,y+p.y_offset))
        x+=p.x_advance;y+=p.y_advance
    return out,x


def raster(face, text, pixels):
    # Actual em size is held constant. Padding does not resize glyph bounds.
    im=Image.new('L',(pixels*2,pixels*2));draw=ImageDraw.Draw(im)
    draw.text((pixels//3,round(pixels*1.2)),text,font=face,anchor='ls',fill=255)
    mask=np.asarray(im)>127
    if not mask.any():return None
    yy,xx=np.nonzero(mask); mask=mask[max(0,yy.min()-8):yy.max()+9,max(0,xx.min()-8):xx.max()+9]
    skel,dist=medial_axis(mask,return_distance=True,rng=0)
    neighbours=ndimage.convolve(skel.astype('uint8'),np.ones((3,3),dtype='uint8'))-skel
    # Omit a narrow neighbourhood of branch junctions and terminals. This
    # can also exclude nearby thin strokes. Remaining samples are weighted
    # by local axis length; this is a diagnostic, not a perceptual model.
    unstable=skel & ((neighbours>2)|(neighbours<2))
    stable=skel & ~ndimage.binary_dilation(unstable,iterations=max(1,round(pixels/256)))
    sy,sx=np.nonzero(stable)
    widths=2*dist[sy,sx]*1000/pixels
    kernel=np.array([[2**.5,1,2**.5],[1,0,1],[2**.5,1,2**.5]])/2
    lengths=ndimage.convolve(skel.astype(float),kernel)[sy,sx]
    bins={'horizontal':[],'vertical':[],'diagonal':[]}
    radius=max(3,round(pixels/100))
    for y,x,w,length in zip(sy,sx,widths,lengths):
        ys,xs=np.nonzero(skel[max(0,y-radius):y+radius+1,max(0,x-radius):x+radius+1])
        if len(xs)<3: continue
        cov=np.cov(np.array([xs,ys]));vals,vecs=np.linalg.eigh(cov)
        if vals[-1]<3*max(vals[0],.001): continue
        v=vecs[:,-1];angle=abs(math.degrees(math.atan2(v[1],v[0])))%180
        orientation='horizontal' if angle<22.5 or angle>157.5 else 'vertical' if 67.5<angle<112.5 else 'diagonal'
        bins[orientation].append((float(w),float(length)))
    def quant(values,weights):
        if not len(values):return None
        ix=np.argsort(values);v=np.asarray(values)[ix];w=np.asarray(weights)[ix]
        c=(np.cumsum(w)-w/2)/w.sum()
        return dict(zip(('q10','q25','q50','q75','q90'),map(float,np.interp([.1,.25,.5,.75,.9],c,v))))
    return dict(pixels=pixels,axis_samples=len(widths),stroke=quant(widths,lengths),
                directions={k:quant(*zip(*v)) if sum(w for _,w in v)*1000/pixels>=60 else None for k,v in bins.items()},
                direction_samples={k:len(v) for k,v in bins.items()},
                direction_axis_units={k:sum(w for _,w in v)*1000/pixels for k,v in bins.items()},
                raster_ink_fraction=float(mask.sum()/pixels**2))


def dump(name,value):
    (OUT/name).write_text(json.dumps(value,ensure_ascii=False,separators=(',',':'))+'\n')


def native(pixels, strokes_only=False):
    path=font_path('NotoSerifJP');font=TTFont(path);cmap=font.getBestCmap()
    assert font['head'].unitsPerEm==1000
    rows=[];detailed=[]
    for style,weight in [('Regular',400),('Bold',700)]:
        gs=font.getGlyphSet(location={'wght':weight});cache={}
        # Measure the encoded native glyph directly; RAQM inserts a dotted
        # circle when a combining dakuten is rendered by itself.
        face=ImageFont.truetype(str(path),pixels,layout_engine=ImageFont.Layout.BASIC)
        face.set_variation_by_axes([weight])
        for n,(cp,name) in enumerate(sorted(cmap.items())):
            if not strokes_only:
                if name not in cache:cache[name]=vector(gs,[(name,0,0)])
                r=dict(style=style,cp=f'{cp:04X}',text=chr(cp),glyph=name,script=script(cp),advance=gs[name].width,**cache[name]);rows.append(r)
            if script(cp) in ('Hiragana','Katakana') or 0x3099<=cp<=0x309a:
                detailed.append(dict(style=style,text=chr(cp),cp=f'{cp:04X}',**raster(face,chr(cp),pixels)))
            if n%4000==0:print(style,n,'native characters measured',flush=True)
        print(style,'complete:',len(cmap),'encoded characters;',len(set(cmap.values())),'unique encoded glyphs',flush=True)
    dump(f'native-strokes-{pixels}.json',detailed)
    if strokes_only:return
    dump('native-vector.json',rows)
    dump('native-source.json',dict(sha256=hashlib.sha256(path.read_bytes()).hexdigest(),weights=[400,700],encoded_characters=len(cmap),total_glyphs=len(font.getGlyphOrder()),units_per_em=1000))
    keys=['style','cp','text','glyph','script','advance','area','perimeter','effective_width','bbox_density','ink_em_fraction']
    with (OUT/'native-all.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=keys,extrasaction='ignore');w.writeheader();w.writerows(rows)


def custom(phase,pixels,reuse_snapshot=False):
    rows=[]; hashes={}
    for style in ('Regular','Bold'):
        path=ROOT/'build/serif'/f'GenZuiSerif-{style}.ttf'
        saved=OUT/f'{phase}-{style}.ttf'
        if saved.exists() and not reuse_snapshot:
            assert hashlib.sha256(saved.read_bytes()).digest()==hashlib.sha256(path.read_bytes()).digest(), 'Snapshot differs from current font: use a new phase or explicitly --reuse-snapshot'
        if not saved.exists():shutil.copyfile(path,saved)
        hashes[style]=hashlib.sha256(saved.read_bytes()).hexdigest()
        font=TTFont(saved);gs=font.getGlyphSet();hfont=hb.Font(hb.Face(saved.read_bytes()));hfont.scale=(1000,1000)
        face=ImageFont.truetype(str(saved),pixels,layout_engine=ImageFont.Layout.RAQM)
        for e in ENTRIES:
            if e['system']!='funatsu':continue
            text=''.join(chr(int(c,16)) for c in e['output']);glyphs,advance=shaped(font,hfont,text)
            rows.append(dict(style=style,label=e['label'],text=text,codepoints=e['output'],donors=DONORS[e['label']],advance=advance,
                             glyph_count=len(glyphs),**vector(gs,glyphs),**raster(face,text,pixels)))
        print(style,phase,'27 forms measured',flush=True)
    dump(f'{phase}-{pixels}.json',rows)
    dump(f'{phase}-source.json',dict(font_sha256=hashes,pixels=pixels,snapshot=phase))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--native',action='store_true');ap.add_argument('--strokes-only',action='store_true');ap.add_argument('--phase',default='before');ap.add_argument('--reuse-snapshot',action='store_true');ap.add_argument('--pixels',type=int,default=512)
    args=ap.parse_args();OUT.mkdir(parents=True,exist_ok=True)
    dump('environment.json',dict(python=platform.python_version(),packages={p:importlib.metadata.version(p) for p in ('numpy','scipy','scikit-image','Pillow','fonttools','skia-pathops','uharfbuzz')},freetype=features.version('freetype2'),raqm=features.version('raqm')))
    if args.native or args.strokes_only:native(args.pixels,args.strokes_only)
    custom(args.phase,args.pixels,args.reuse_snapshot)
