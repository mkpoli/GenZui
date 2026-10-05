"""HWA proof alternatives. Main font drawings remain unchanged until selection."""
import hashlib,json
from functools import lru_cache
import numpy as np
import pathops
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from serif import contours,transform,glyph
from kugyol import rename,parent_name
import okinawan_sans as S
import okinawan_outline as O

LABELS=('わの曲線','低い曲線','高い曲線')

@lru_cache(maxsize=6)
def drawing(weight,choice):
    f=S.source(weight)
    def native(ids,sx=1,sy=1,dx=0,dy=0):
        return transform(contours(f,ord('ふ'),ids),(sx,0,0,sy,dx,dy))
    parts=[native([0],dx=-100),native([1],dx=-100),native([3],sx=.85,sy=.85,dx=20,dy=10 if weight==400 else 70)]
    # Retain native わ's bowl, upright and rising diagonal. Its second
    # contour also carries the unwanted crossbar: retain only the lower
    # diagonal, closing it inside the upright so no cut terminal is visible.
    donor=S.source(800 if weight==400 else 900)
    bowl,diagonal,upright=O.rings(contours(donor,ord('わ')))
    assert [len(bowl),len(diagonal),len(upright)]==[21,28,25]
    from okinawan_bold import line
    diagonal=diagonal[15:26]+[line(diagonal[26][0],diagonal[15][0])]
    sx=.43 if weight==400 else .40
    sy=(.43,.38,.47)[choice]
    dx=600 if weight==400 else 620
    vowel=[transform(O.draw([bowl]),(sx,0,0,sy,dx,10)),
           transform(O.draw([diagonal,upright]),(sx,0,0,.43,dx,10))]
    if weight==700:
        original=union(vowel)
        border=pathops.Path(original)
        border.stroke(14,pathops.LineCap.ROUND_CAP,pathops.LineJoin.ROUND_JOIN,4)
        border.convertConicsToQuads(.05)
        expanded=pathops.op(original,border,pathops.PathOp.UNION)
        pen=RecordingPen();expanded.draw(pen);vowel=[pen]
    parts+=vowel
    box=S.bounds(parts);dx=500-(box[0]+box[2])/2
    return [transform(p,(1,0,0,1,dx,0)) for p in parts]

def union(parts):
    result=pathops.Path()
    for part in parts:
        p=pathops.Path();part.replay(p.getPen());result=pathops.op(result,p,pathops.PathOp.UNION)
    return result

def build(out,version):
    dest=out/'hwa-candidates';dest.mkdir(exist_ok=True);records=[]
    for style,weight in (('Regular',400),('Bold',700)):
        for choice,letter in enumerate('ABC'):
            f=TTFont(out/f'GenZuiSansOkinawan-{style}.ttf',recalcTimestamp=False)
            pen=RecordingPen();union(drawing(weight,choice)).draw(pen)
            g=glyph([pen]);name=f.getBestCmap()[0xF45A];f['glyf'][name]=g;g.recalcBounds(f['glyf'])
            f['hmtx'][name]=(1000,g.xMin);f['vmtx'][name]=(1000,880-g.yMax)
            face=f'GenZui Sans Okinawan HWA {letter}';stem=f'GenZuiSansOkinawanHWA{letter}-{style}'
            rename(f,face,face,style,stem,version,*[parent_name(f,n) for n in (0,13,14)])
            f.save(dest/f'{stem}.ttf');f.flavor='woff2';f.save(dest/f'{stem}.woff2')
            file=f'hwa-candidates/{stem}.woff2'
            records.append(dict(family=face,style=style,letter=letter,file=file,sha256=hashlib.sha256((out/file).read_bytes()).hexdigest()))
    (dest/'manifest.json').write_text(json.dumps(records,indent=2)+'\n')
    render(out)
    return records

def render(out):
    from PIL import Image,ImageDraw,ImageFont
    im=Image.new('RGB',(1800,1230),'white');d=ImageDraw.Draw(im);label=ImageFont.truetype('DejaVuSans.ttf',24)
    for row,letter in enumerate('ABC'):
        for col,style in enumerate(('Regular','Bold')):
            x=20+col*900;y=20+row*400;file=out/'hwa-candidates'/f'GenZuiSansOkinawanHWA{letter}-{style}.ttf'
            d.text((x,y),f'HWA {letter} / {style}',font=label,fill='#233d34')
            for size,baseline in ((170,205),(48,290),(24,345)):
                d.text((x,y+baseline),'ふ\uf45a\uf45b\uf45cわ',font=ImageFont.truetype(str(file),size),anchor='ls',fill='#233d34')
            d.line((x,y+210,x+850,y+210),fill='#d5ded8')
    im.save(out/'hwa-candidates/overview.png')

def check(out):
    from scipy.spatial import cKDTree
    from check_okinawan_subset import outline
    def points(parts):return np.array([O.point(s,t) for p in parts for r in O.rings(p) for s in r for t in np.linspace(0,1,31)])
    records=json.loads((out/'hwa-candidates/manifest.json').read_text());assert len(records)==6
    for r in records:
        path=out/r['file'];assert hashlib.sha256(path.read_bytes()).hexdigest()==r['sha256']
        web=TTFont(path);ttf=TTFont(path.with_suffix('.ttf'));base=TTFont(out/f"GenZuiSansOkinawan-{r['style']}.ttf")
        assert web['name'].getDebugName(1)==r['family']
        assert web.getBestCmap()==ttf.getBestCmap()==base.getBestCmap()
        assert web.getGlyphOrder()==ttf.getGlyphOrder()==base.getGlyphOrder()
        changed=set()
        for name in web.getGlyphOrder():
            assert outline(web,name)==outline(ttf,name)
            for tag in ('hmtx','vmtx'):assert web[tag][name]==ttf[tag][name]
            if outline(web,name)!=outline(base,name):changed.add(name)
            else:
                for tag in ('hmtx','vmtx'):assert web[tag][name]==base[tag][name]
        assert changed=={web.getBestCmap()[0xF45A]}
        parts=drawing(400 if r['style']=='Regular' else 700,ord(r['letter'])-65)
        a,b=parts[:3],parts[3:]
        assert pathops.op(union(a),union(b),pathops.PathOp.INTERSECTION).area<.01
        gap=float(cKDTree(points(a)).query(points(b))[0].min());assert gap>=30,(r['file'],gap)
        box=S.bounds(parts);assert box[0]>=0 and box[2]<=1000,box
        assert web['hmtx'][web.getBestCmap()[0xF45A]][0]==1000
        r['clearance']=round(gap,2)
        neighbor=[transform(p,(1,0,0,1,1000,0)) for p in parts]
        assert pathops.op(union(parts),union(neighbor),pathops.PathOp.INTERSECTION).area<.01
        repeat_gap=float(cKDTree(points(parts)).query(points(neighbor))[0].min())
        assert repeat_gap>=20,(r['file'],'repeated HWA',repeat_gap)
        r['repeat_clearance']=round(repeat_gap,2)
    (out/'hwa-candidates/checks.json').write_text(json.dumps(dict(status='passed',faces=records),indent=2)+'\n')
    return records

CSS="""
.hwa-choice-title{margin:28px 0 12px}
.hwa-context,.hwa-family,.hwa-reading{font-family:var(--face);font-weight:var(--weight);font-synthesis:none;white-space:nowrap}
.hwa-context{font-size:clamp(60px,8.9vw,128px);line-height:1.3;border-bottom:1px solid #d5ded8}
.hwa-family{font-size:min(96px,5.8vw);line-height:1.5}
.hwa-label{font-size:12px;color:#64746b;margin:22px 0 0}
.hwa-reading{margin-top:16px;font-size:min(var(--sample-size),4vw)}
.hwa-serif{font-family:'GenZui Serif Okinawan';font-weight:var(--weight);font-size:30px;font-synthesis:none}
@media(max-width:650px){.hwa-context{font-size:8.5vw}.hwa-serif{font-size:24px}}
"""

def cards():
    result=[]
    for letter,label in zip('ABC',LABELS):
        result.append(f'<h3 class="hwa-choice-title">{letter} · {label}</h3><div class="columns">')
        for style,weight in (('Regular',400),('Bold',700)):
            face=f'GenZui Sans Okinawan HWA {letter}'
            result.append(f'''<article class="hwa-choice" style="--weight:{weight};--face:'{face}'">
<h3>{style} {letter}</h3><div class="hwa-context" data-family="{face}">ふ\uf45aわ</div>
<p class="hwa-label">ふ / HWA / HWI / HWE / わ</p><div class="hwa-family" data-family="{face}">ふ\uf45a\uf45b\uf45cわ</div>
<div class="hwa-reading" data-family="{face}" style="--sample-size:24px">ふゎ \uf45a\uf45a\uf45a</div>
<div class="hwa-reading" data-family="{face}" style="--sample-size:48px">ふゎ \uf45a\uf45a\uf45a</div>
<div class="serif-row"><small>Serif</small><span class="hwa-serif" data-family="GenZui Serif Okinawan">ふ\uf45aわ</span></div></article>''')
        result.append('</div>')
    return ''.join(result)
