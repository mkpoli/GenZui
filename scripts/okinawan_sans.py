"""Okinawan drawings constructed for Noto Sans JP's native weight masters.

Native contours retain their terminals. New connecting strokes are drawn as
cubic skeletons at the master's kana stroke width, before component union.
"""
from functools import lru_cache
import numpy as np
import pathops
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.svgLib.path import parse_path
import okinawan_outline as O
from okinawan_bold import cut_keep, move, join, line, rounded_join
from serif import instance, contours, transform

@lru_cache(maxsize=8)
def source(weight):
    return instance('NotoSansJP', weight, set(map(ord, 'くてとつをふいぃわえやゆよゐゑんすはこぐでどずづアイウエオツフン')))

def stroke(path, width):
    p=pathops.Path(); parse_path(path,p.getPen())
    p.stroke(width,pathops.LineCap.BUTT_CAP,pathops.LineJoin.ROUND_JOIN,4)
    p.convertConicsToQuads(.05)
    out=RecordingPen(); p.draw(out)
    return out

def reverse(r): return [tuple(reversed(s)) for s in reversed(r)]

def attach(native, path, width, start):
    """Replace a stroke's flat starting cap with two tangent-matched joins."""
    rings=O.rings(stroke(path,width)); assert len(rings)==1
    r=rings[0]; target=np.array(start)
    i=min(range(len(r)),key=lambda i:np.linalg.norm((r[i][0]+r[i][3])/2-target))
    assert np.linalg.norm((r[i][0]+r[i][3])/2-target)<2
    arc=r[i+1:]+r[:i]
    score=lambda a:np.linalg.norm(native[-1][3]-a[0][0])+np.linalg.norm(a[-1][3]-native[0][0])
    if score(reverse(arc))<score(arc):arc=reverse(arc)
    return O.draw([join(native,arc)])

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

def fit_we_mark(body,ref,donor):
    # Measure each mark against its underlying head bar. The accepted WI is
    # the reference; its outline and metrics are never altered by this study.
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
    mark=contours(source(donor),ord('こ'),[0]);b=bounds([mark])
    mark=transform(mark,(length/(b[2]-b[0]),0,0,.72,0,0))
    mark=transform(mark,(1,float(np.tan(angle)-mark_slope(mark)),0,1,0,0))
    b=bounds([mark]);mark=transform(mark,(1,0,0,1,left-b[0],0))
    x=left+length/2
    mark=transform(mark,(1,0,0,1,0,edge_y(we[:10],x)+gap-section(mark,x)[0]))
    return [body,mark]


def hwa_vowel(weight):
    # Retain native わ's bowl, upright and rising diagonal. Its second
    # contour also carries the unwanted crossbar: retain only the lower
    # diagonal, closing it inside the upright so no cut terminal is visible.
    donor=source(800 if weight==400 else 900)
    bowl,diagonal,upright=O.rings(contours(donor,ord('わ')))
    assert [len(bowl),len(diagonal),len(upright)]==[21,28,25]
    diagonal=diagonal[15:26]+[line(diagonal[26][0],diagonal[15][0])]
    sx=.43 if weight==400 else .40
    sy=.43
    dx=588 if weight==400 else 608
    vowel=[transform(O.draw([bowl]),(sx,0,0,sy,dx,10)),
           transform(O.draw([diagonal,upright]),(sx,0,0,.43,dx,10))]
    # Add weight around the accepted outline; keep its contour proportions.
    expansion=8 if weight==400 else 32
    if expansion:
        original=pathops.Path()
        for part in vowel:
            p=pathops.Path();part.replay(p.getPen())
            original=pathops.op(original,p,pathops.PathOp.UNION)
        border=pathops.Path(original)
        border.stroke(expansion,pathops.LineCap.ROUND_CAP,pathops.LineJoin.ROUND_JOIN,4)
        border.convertConicsToQuads(.05)
        expanded=pathops.op(original,border,pathops.PathOp.UNION)
        pen=RecordingPen();expanded.draw(pen);vowel=[pen]
    return vowel


def drawings(weight):
    f=source(weight); optical=source(min(900,weight+100))
    reduced=source(weight+200)
    # Main kana stem widths; Bold is a separate native master, not an offset.
    w=76 if weight==400 else 116
    topology={'く':[30],'て':[37],'と':[31,8],'つ':[28],'を':[31,14,31],
              'え':[10,63],'や':[8,19,30],'は':[10,42,31],'ゐ':[76]}
    def rings(ch, font=f):
        result=O.rings(contours(font,ord(ch)))
        assert [len(r) for r in result]==topology[ch],ch
        return result
    def native(ch, ids=None, sx=1,sy=1,dx=0,dy=0,font=f):
        return transform(contours(font,ord(ch),ids),(sx,0,0,sy,dx,dy))
    def s(path,width=w):return stroke(path,width)
    out={}
    # Cut perpendicular to the descending stroke, so both joining edges
    # follow its native direction without a horizontal shoulder.
    direction=np.array([.775,-.631]);direction/=np.linalg.norm(direction)
    matrix=np.array([direction,[-direction[1],direction[0]]])
    original=rings('く')[0];rotated=O.transform(original,matrix,(0,0))
    cuts=[c for c in O.crossings(rotated,0,np.dot(direction,(320,310))) if 7<=c[0]<=11 or 19<=c[0]<=22]
    assert len(cuts)==2,cuts
    ku=max((O.arc(original,*cuts),O.arc(original,*reversed(cuts))),key=lambda r:max(p[1] for seg in r for p in seg))
    kw=w*1.12
    out[0xF456]=[attach(ku,'M 375 260 C 419 224 456 228 465 165 C 474 102 480 28 555 28 C 615 28 639 103 661 168',w,(375,260)),
                 s('M 735 260 C 813 210 844 98 849 20')]
    out[0xF458]=[attach(ku,'M 375 260 C 419 224 465 210 500 195 L 208 -18',kw,(375,260)),
        s('M 330 71 C 415 133 520 210 553 109 C 579 19 563 -8 670 -8 L 851 -8',kw)]
    # One uninterrupted diagonal/bowl stroke, with a separate upright.
    out[0xF454]=[attach(ku,'M 375 260 C 419 224 517 245 500 198 C 494 155 488 50 500 -20',kw,(375,260)),
        s('M 205 18 C 302 110 392 217 506 307 C 630 399 790 429 842 316 C 907 172 793 51 633 7')]
    te=cut_keep(rings('て')[0],1,420,'high')
    out[0xF452]=[attach(te,'M 398 260 C 386 180 398 117 456 49 C 519 -27 623 85 659 199',w,(398,260)),
                 s('M 790 270 C 867 215 907 109 915 20')]
    # Keep full stroke width through the return and lower bowl. Compressing
    # the source outline vertically made its horizontal sections too light.
    bowl_width=76 if weight==400 else 116
    tu_tail=10 if weight==400 else 15
    wu_tail=-1 if weight==400 else 9
    out[0xF450]=[native('と',[1],sx=.91,sy=.78,dx=-100,dy=190,font=source(450 if weight==400 else 700)),
        s(f'M 620 685 C 529 630 415 559 310 491 C 224 435 163 400 163 340 '
          f'C 163 245 245 240 329 243 C 458 247.6 587 301 699 280 '
          f'C 839 254 864 184 799 120 C 717 41 530 {tu_tail} 329 {tu_tail}',bowl_width)]
    # Fit the native を arch and upright to the space above the return.
    wo=O.rings(contours(source(450) if weight==400 else optical,ord('を'),[0]))[0]
    # The arch loses vertical weight when compressed. Restore that section
    # alone, tapering the correction to zero at the native joins.
    arch_gain=(15 if weight==400 else 26)/2/.69
    peak=wo[20][0][0]
    for start,end,sign in ((4,9,1),(18,22,-1)):
        lo,hi=sorted((wo[start][0][0],wo[end-1][3][0]))
        def arch_point(q):
            x,y=q
            t=max(0,min(1,(x-lo)/(peak-lo) if x<=peak else (hi-x)/(hi-peak)))
            dt=1/(peak-lo) if x<=peak else -1/(hi-peak)
            slope=sign*arch_gain*6*t*(1-t)*dt
            return np.array([x,y+sign*arch_gain*t*t*(3-2*t)]),slope
        # Transform endpoint tangents with the warp, keeping the native joins.
        for i in range(start,end):
            p0,p1,p2,p3=wo[i]
            q0,d0=arch_point(p0);q3,d3=arch_point(p3)
            q1=q0+(p1-p0)+np.array([0,d0*(p1[0]-p0[0])])
            q2=q3+(p2-p3)+np.array([0,d3*(p2[0]-p3[0])])
            wo[i]=(q0,q1,q2,q3)
    # Extend only the upright below the crossing, preserving its width.
    extension=25 if weight==400 else 35
    for i in range(10,18):
        wo[i]=tuple(np.array([x,y-extension/.69*max(0,min(1,(310-y)/180))**2]) for x,y in wo[i])
    out[0xF465]=[O.draw([move(wo,sx=.9,sy=.69,dx=20,dy=272)]),
        native('を',[1],sx=.83,sy=1,dx=25,dy=60 if weight==400 else 80),
        s(f'M 815 612.5 C 715 562.5 609 510 529 470 C 449 430 240 430 240 320 '
          f'C 240 210 365 216 547 221 C 709 225.45 819 204 839 143 '
          f'C 867 46 656 {wu_tail} 340 {wu_tail}',70 if weight==400 else w)]
    # TSI carries the bowl into the left stroke of い.
    ts=rings('つ',reduced)[0]
    ts=move(ts[:14]+[line(ts[14][0],ts[15][0])]+ts[15:],sx=.91,sy=.7,dx=0,dy=245)
    # Open the terminal rather than intersecting two closed outlines.
    ts=ts[15:]+ts[:14]
    out[0xF469]=[attach(ts,'M 301 285 C 260 190 275 75 337 30 C 388 -10 459 94 479 153',w,(301,285)),
                 s('M 613 191 C 682 153 709 76 715 4')]
    # Keep both fu components at their native size and native weight. Position
    # changes make space for the vowel without changing their stroke contrast.
    fu=[native('ふ',[0],dx=-100),native('ふ',[1],dx=-100)]
    left_dot=native('ふ',[3],sx=.85,sy=.85,dx=20,dy=10 if weight==400 else 70)
    out[0xF45A]=fu+[left_dot]+hwa_vowel(weight)
    # Selected softened え corner, with separate Regular and Bold skeletons.
    vowels={
        0xF45B:('M 665 340 C 651 185 657 80 704 30 C 745 0 776 104 789 160',
                 'M 853 324 C 913 257 949 132 953 20'),
        0xF45C:(('M635 307 C687 315 758 331 798 321 C816 316 805 298 791 274 L645 0',
                   'M704 100 C742 169 789 190 819 140 C846 94 844 51 873 24 C893 4 940 0 975 5')
                  if weight==400 else
                  ('M657 282 C725 290 814 308 852 295 C873 287 854 263 832 235 L645 0',
                   'M710 100 C749 167 806 180 834 131 C857 87 863 47 892 24 C914 6 959 0 990 5')),
    }
    for cp,paths in vowels.items():
        dx=20 if weight==700 and cp!=0xF45C else 0
        # Balance the compact vowels independently of the full-size kana
        # stem width, preserving their accepted skeletons.
        vowel_width=((66 if weight==400 else 98) if cp==0xF45C
                     else (72 if weight==400 else 110))
        strokes=[transform(s(path,vowel_width),(1,0,0,1,dx,0)) for path in paths]
        if cp==0xF45C and weight==700:
            # The branch's butt cap crosses the diagonal's outer edge. Clip
            # that spur to the exact left offset of (645,0) -> (832,235).
            slope=187/235
            intercept=645-vowel_width/2*np.hypot(1,slope)
            clip=pathops.Path();pen=clip.getPen()
            pen.moveTo((intercept-500*slope,-500));pen.lineTo((2000,-500))
            pen.lineTo((2000,1000));pen.lineTo((intercept+1000*slope,1000));pen.closePath()
            branch=pathops.Path();strokes[1].replay(branch.getPen())
            trimmed=pathops.op(branch,clip,pathops.PathOp.INTERSECTION)
            strokes[1]=RecordingPen();trimmed.draw(strokes[1])
        out[cp]=fu+[left_dot]+strokes
    # Glottal YA joins native は's left stroke to native や's arm.
    arm=move(cut_keep(rings('や')[2],0,180,'high'),dx=120)
    neck=move(cut_keep(rings('は')[2],1,550,'high'),dx=-20 if weight==400 else -60)
    out[0xF45D]=[native('や',[0,1],dx=120),O.draw([rounded_join(neck,arm)])]
    # A lighter donor preserves the native shape; retain the accepted height.
    yu_mark=contours(source(450 if weight==400 else 700),ord('は'),[2])
    mb=BoundsPen(None);yu_mark.replay(mb)
    rb=BoundsPen(None);contours(optical,ord('は'),[2]).replay(rb)
    height=(rb.bounds[3]-rb.bounds[1])/(mb.bounds[3]-mb.bounds[1])
    yu_mark=transform(yu_mark,(1,0,0,height,0,rb.bounds[1]-height*mb.bounds[1]))
    yu_mark=transform(yu_mark,(.78,0,0,.74,8 if weight==400 else -30,130))
    yu_mark=transform(yu_mark,(1,0,-.044 if weight==400 else -.045,1,0,0))
    yu_body=native('ゆ',sx=.94,dx=150)
    # Match the adjacent left stroke's top, retaining the parallel slopes.
    yu_top=max(q[1] for seg in O.rings(yu_body)[0][-3:] for q in seg)
    mb=BoundsPen(None);yu_mark.replay(mb)
    yu_mark=transform(yu_mark,(1,0,0,1,0,yu_top-mb.bounds[3]))
    out[0xF45E]=[yu_mark,yu_body]
    # Optical donors restore weight in the shortened glottal mark while
    # retaining the native curve and terminal.
    yo_source=native('は',[2],sx=.78,sy=.74,font=source(475 if weight==400 else 900))
    yo_source=transform(yo_source,(1,0,-.044 if weight==400 else -.045,1,0,0))
    mb=BoundsPen(None);yo_source.replay(mb)
    scale=(480 if weight==400 else 500)/(mb.bounds[3]-mb.bounds[1])
    top=770 if weight==400 else 786
    yo_mark=transform(yo_source,(1,0,0,scale,(263 if weight==400 else 250)-(mb.bounds[0]+mb.bounds[2])/2,top-scale*mb.bounds[3]))
    out[0xF45F]=[yo_mark,native('よ',sx=.96,dx=150)]
    wi=rings('ゐ',optical)[0]
    wa=wi[:33]+[line(wi[33][0],wi[49][0])]+wi[49:]
    body_sy=.82
    for cp,ch in ((0xF460,None),(0xF461,'ゐ'),(0xF462,'ゑ')):
        body=O.draw([move(wa,sx=.82,sy=body_sy,dx=20)]) if ch is None else native(ch,sx=.82,sy=body_sy,dx=20,font=optical)
        mark=native('こ',[0],sx=.55,sy=.72,font=optical)
        bb=BoundsPen(None);body.replay(bb)
        mb=BoundsPen(None);mark.replay(mb)
        mx=(mb.bounds[0]+mb.bounds[2])/2
        out[cp]=[body,transform(mark,(1,0,0,1,365-mx,bb.bounds[3]+50-mb.bounds[1]))]
    out[0xF462]=fit_we_mark(out[0xF462][0],out[0xF461],475 if weight==400 else 725)
    # Native small-i has its own terminal and curvature. Uniform reduction
    # preserves that shape, using an optical donor to keep the mark legible.
    dot=native('ぃ',[1],sx=.65,sy=.65,font=reduced)
    db=BoundsPen(None);dot.replay(db);x0,y0,x1,y1=db.bounds
    out[0xF463]=[native('ん'),transform(dot,(1,0,0,1,870-x1,(650 if weight==400 else 675)-y1))]
    si_dot=native('ぃ',[1],sx=.8,sy=1,font=optical)
    sb=BoundsPen(None);si_dot.replay(sb)
    out[0xF467]=[native('す',sx=.86,dx=15,font=optical),transform(si_dot,(1,0,0,1,905-sb.bounds[2],10-sb.bounds[1]))]
    # Optical centering applies to base forms; voiced pairs retain native spacing.
    for cp,parts in out.items():
        b=BoundsPen(None)
        for p in parts:p.replay(b)
        dx=500-(b.bounds[0]+b.bounds[2])/2
        out[cp]=[transform(p,(1,0,0,1,dx,0)) for p in parts]
    return out

def voiced_parts(font, cp, parts, contours, transform):
    from okinawan import DAKUTEN
    ch,_,dx,dy=DAKUTEN[cp]
    if cp==0xF469:dy+=43
    if cp==0xF454:dx,dy=40,80
    if cp==0xF467:dy=50
    pair=[]
    for r in O.rings(contours(font,ord(ch))):
        p=O.draw([r]); b=BoundsPen(None);p.replay(b)
        x0,y0,x1,y1=b.bounds
        if x0>500 and y0>300 and x1-x0<210 and y1-y0<210:pair.append(p)
    assert len(pair)==2,(ch,len(pair))
    return parts+[transform(p,(1,0,0,1,dx,dy)) for p in pair]


def raised_parts(weight, char):
    # Approved optical weight for half-size Regular; Bold retains its native master.
    font=source(450 if weight==400 else 700)
    return [transform(contours(font,ord(char)),(.48,0,0,.48,10,410))]
