"""Proof-only HWE/WE choices; approved production drawings remain unchanged."""
from functools import lru_cache
import hashlib
import json
import numpy as np
import pathops
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.svgLib.path import parse_path
from serif import contours, transform, glyph
from kugyol import rename, parent_name
import okinawan_sans as S
import okinawan_outline as O

@lru_cache(maxsize=2)
def base_drawings(weight):
    return S.drawings(weight)

LABELS={'hwe':('角を残す','角をやわらげる','丸く返す','弧を広くする'),"'we":('細め','中間','太め')}

def bounds(parts):
    b=BoundsPen(None)
    for p in parts:p.replay(b)
    return b.bounds

def edge_y(segments,x):
    hits=[O.point(segments[i],t)[1] for i,t in O.crossings(segments,0,x)]
    assert hits,(x,len(segments))
    return sum(hits)/len(hits)

def section(part,x):
    ys=[O.point(r[i],t)[1] for r in O.rings(part) for i,t in O.crossings(r,0,x)]
    assert len(ys)==2,(x,ys)
    return min(ys),max(ys)

def we(weight,choice):
    # Measure each mark against its underlying head bar. The accepted WI is
    # the reference; its outline and metrics are never altered by this study.
    ref=base_drawings(weight)[0xF461]
    body=base_drawings(weight)[0xF462][0]
    wi=O.rings(ref[0])[0];we=O.rings(body)[0]
    wl,wr=wi[0][0][0],wi[7][3][0]
    el,er=we[0][0][0],we[10][3][0]
    ratio=(er-el)/(wr-wl)
    rb=bounds([ref[1]]);length=(rb[2]-rb[0])*ratio
    left=el+(rb[0]-wl)*ratio
    mid=(rb[0]+rb[2])/2
    gap=section(ref[1],mid)[0]-edge_y(wi[:7],mid)
    def head_slope(r,upper,lower,l,rgt):
        xs=[l+(rgt-l)*t for t in (.2,.4)]
        ys=[(edge_y(r[:upper],x)+edge_y(r[lower[0]:lower[1]],x))/2 for x in xs]
        return (ys[1]-ys[0])/(xs[1]-xs[0])
    def mark_slope(p):
        b=bounds([p]);xs=[b[0]+(b[2]-b[0])*t for t in (.25,.75)]
        ys=[sum(section(p,x))/2 for x in xs]
        return (ys[1]-ys[0])/(xs[1]-xs[0])
    angle=np.arctan(mark_slope(ref[1]))+np.arctan(head_slope(we,10,(98,103),el,er))-np.arctan(head_slope(wi,7,(71,75),wl,wr))
    donor=((435,475,500) if weight==400 else (635,725,800))[choice]
    mark=contours(S.source(donor),ord('こ'),[0]);b=bounds([mark])
    mark=transform(mark,(length/(b[2]-b[0]),0,0,.72,0,0))
    mark=transform(mark,(1,float(np.tan(angle)-mark_slope(mark)),0,1,0,0))
    b=bounds([mark]);mark=transform(mark,(1,0,0,1,left-b[0],0))
    x=left+length/2
    mark=transform(mark,(1,0,0,1,0,edge_y(we[:10],x)+gap-section(mark,x)[0]))
    return [body,mark]

def hwe(weight,choice):
    f=S.source(weight)
    def native(ids,sx=1,sy=1,dx=0,dy=0):
        return transform(contours(f,ord('ふ'),ids),(sx,0,0,sy,dx,dy))
    parts=[native([0],dx=-100),native([1],dx=-100),
           native([3],sx=.85,sy=.85,dx=20,dy=10 if weight==400 else 70)]
    # Separate masters keep the Bold shoulder lower to allow for stroke width.
    width=76 if weight==400 else 116
    branch=('M704 100 C742 169 789 190 819 140 C846 94 844 51 873 24 C893 4 940 0 975 5'
            if weight==400 else
            'M710 100 C749 167 806 180 834 131 C857 87 863 47 892 24 C914 6 959 0 990 5')
    paths_regular=(
        'M640 305 C700 309 760 312 815 312 L652 0',
        'M635 307 C687 315 758 331 798 321 C816 316 805 298 791 274 L645 0',
        'M630 308 C694 331 769 352 790 314 C809 280 767 220 745 182 L635 0',
        'M580 375 C653 412 735 424 770 358 C794 312 780 284 755 242 L628 0')
    paths_bold=(
        'M661 282 C735 286 815 289 885 289 L652 0',
        'M657 282 C725 290 814 308 852 295 C873 287 854 263 832 235 L645 0',
        'M650 283 C726 310 816 332 840 294 C862 259 804 207 777 171 L642 0',
        'M610 361 C682 397 759 405 795 342 C817 303 798 265 777 230 L646 0')
    p=pathops.Path();parse_path((paths_regular if weight==400 else paths_bold)[choice],p.getPen())
    p.stroke(width,pathops.LineCap.BUTT_CAP,pathops.LineJoin.MITER_JOIN if choice==0 else pathops.LineJoin.ROUND_JOIN,2)
    p.convertConicsToQuads(.05);pen=RecordingPen();p.draw(pen)
    return parts+[pen,S.stroke(branch,width)]

def centered(parts):
    b=bounds(parts);return [transform(p,(1,0,0,1,500-(b[0]+b[2])/2,0)) for p in parts]

def build(out,version):
    dest=out/'candidates';dest.mkdir(exist_ok=True);records=[]
    for style,weight in (('Regular',400),('Bold',700)):
        for choice,letter in enumerate('ABCD'):
            f=TTFont(out/f'GenZuiSansOkinawan-{style}.ttf',recalcTimestamp=False)
            replacements={0xF45C:hwe(weight,choice)}
            if choice<3:replacements[0xF462]=we(weight,choice)
            for cp,parts in replacements.items():
                merged=pathops.Path()
                for part in centered(parts):
                    p=pathops.Path();part.replay(p.getPen());merged=pathops.op(merged,p,pathops.PathOp.UNION)
                pen=RecordingPen();merged.draw(pen);g=glyph([pen]);name=f.getBestCmap()[cp]
                f['glyf'][name]=g;g.recalcBounds(f['glyf'])
                f['hmtx'][name]=(1000,g.xMin);f['vmtx'][name]=(1000,880-g.yMax)
            face=f'GenZui Sans Okinawan Candidate {letter}';stem=f'GenZuiSansOkinawanCandidate{letter}-{style}'
            rename(f,face,face,style,stem,version,*[parent_name(f,n) for n in (0,13,14)])
            f.save(dest/f'{stem}.ttf');f.flavor='woff2';f.save(dest/f'{stem}.woff2')
            file=f'candidates/{stem}.woff2'
            records.append(dict(family=face,style=style,letter=letter,file=file,sha256=hashlib.sha256((out/file).read_bytes()).hexdigest()))
    (dest/'manifest.json').write_text(json.dumps(records,indent=2)+'\n')
    render(out)
    return records

def check(out):
    """Check readable gaps, font parity and preservation of every other glyph."""
    from scipy.spatial import cKDTree
    from check_okinawan_subset import outline
    def shape(parts):
        merged=pathops.Path()
        for part in parts:
            p=pathops.Path();part.replay(p.getPen());merged=pathops.op(merged,p,pathops.PathOp.UNION)
        return merged
    def points(parts):
        return np.array([O.point(s,t) for p in parts for r in O.rings(p)
                         for s in r for t in np.linspace(0,1,31)])
    records=json.loads((out/'candidates/manifest.json').read_text())
    assert len(records)==8
    for r in records:
        path=out/r['file'];assert hashlib.sha256(path.read_bytes()).hexdigest()==r['sha256']
        web=TTFont(path);ttf=TTFont(path.with_suffix('.ttf'))
        original=TTFont(out/f"GenZuiSansOkinawan-{r['style']}.ttf")
        weight=400 if r['style']=='Regular' else 700;choice=ord(r['letter'])-65
        assert web['name'].getDebugName(1)==r['family']
        assert web.getBestCmap()==ttf.getBestCmap()==original.getBestCmap()
        assert web.getGlyphOrder()==ttf.getGlyphOrder()==original.getGlyphOrder()
        changed=set()
        for name in web.getGlyphOrder():
            assert outline(web,name)==outline(ttf,name),(r['file'],name,'web parity')
            for tag in ('hmtx','vmtx'):assert web[tag][name]==ttf[tag][name]
            if outline(web,name)!=outline(original,name):changed.add(name)
            else:
                for tag in ('hmtx','vmtx'):assert web[tag][name]==original[tag][name]
        cps=(0xF45C,0xF462) if choice<3 else (0xF45C,)
        assert changed=={web.getBestCmap()[cp] for cp in cps},(r['file'],changed)
        gaps={}
        for cp,parts,split,minimum in [(0xF45C,hwe(weight,choice),3,30)]+(
            [(0xF462,we(weight,choice),1,35)] if choice<3 else []):
            a,b=parts[:split],parts[split:]
            assert pathops.op(shape(a),shape(b),pathops.PathOp.INTERSECTION).area<.01
            gap=float(cKDTree(points(a)).query(points(b))[0].min());assert gap>=minimum,(r['file'],hex(cp),gap)
            box=bounds(centered(parts));assert box[0]>=0 and box[2]<=1000,(r['file'],box)
            name=web.getBestCmap()[cp];assert web['hmtx'][name][0]==1000
            gaps[f'U+{cp:04X}']=round(gap,2)
        r['clearances']=gaps
    (out/'candidates/checks.json').write_text(json.dumps(dict(status='passed',faces=records),indent=2)+'\n')
    return records


def render(out):
    from PIL import Image, ImageDraw, ImageFont
    rows=[('HWE',letter,'ふ\uf45a\uf45b\uf45cえ') for letter in 'ABCD']+[
          ('WE',letter,'こゑ\uf460\uf461\uf462') for letter in 'ABC']
    im=Image.new('RGB',(1600,len(rows)*285+20),'#f7f8f2');d=ImageDraw.Draw(im)
    label=ImageFont.truetype('DejaVuSans.ttf',20)
    for row,(name,letter,chars) in enumerate(rows):
        for col,style in enumerate(('Regular','Bold')):
            x=20+col*800;y=20+row*285
            file=out/'candidates'/f'GenZuiSansOkinawanCandidate{letter}-{style}.ttf'
            d.text((x,y),f'{name} {letter} / {style}',font=label,fill='#233d34')
            for size,baseline in ((145,180),(24,220),(36,267)):
                font=ImageFont.truetype(str(file),size)
                d.text((x,y+baseline),chars,font=font,fill='#233d34',anchor='ls')
            d.line((x,y+185,x+755,y+185),fill='#d5ded8')
    im.save(out/'candidates/overview.png')
