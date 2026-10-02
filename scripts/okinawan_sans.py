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
    # Restore the downward continuation after the crossing without scaling
    # its width or changing the upper arch. Blend only the upright's ends.
    wo=O.rings(contours(source(450) if weight==400 else optical,ord('を'),[0]))[0]
    extension=25 if weight==400 else 35
    for i in range(10,18):
        wo[i]=tuple(np.array([x,y-extension/.69*max(0,min(1,(310-y)/180))**2]) for x,y in wo[i])
    out[0xF465]=[O.draw([move(wo,sx=.9,sy=.69,dx=20,dy=272)]),
        native('を',[1],sx=.83,sy=1,dx=25,dy=60),
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
    vowels={
        0xF45A:('M 672 337 L 646 -2',
                 'M 647 35 C 691 136 711 259 788 285 C 844 316 917 270 923 192 C 935 85 852 24 786 0'),
        0xF45B:('M 665 340 C 651 185 657 80 704 30 C 745 0 776 104 789 160',
                 'M 853 324 C 913 257 949 132 953 20'),
        0xF45C:('M 620 430 C 686 464 780 491 794 426 C 806 370 747 312 714 237 L 610 0',
                 f'M 687 158 C 747 288 809 288 841 158 C 857 93 848 6 913 3 L {963 if weight==700 else 975} 5'),
    }
    for cp,paths in vowels.items():
        dx=(32 if cp==0xF45C else 20) if weight==700 else 0
        out[cp]=fu+[left_dot]+[transform(s(path),(1,0,0,1,dx,0)) for path in paths]
    # Glottal YA joins native は's left stroke to native や's arm.
    arm=move(cut_keep(rings('や')[2],0,180,'high'),dx=120)
    neck=move(cut_keep(rings('は')[2],1,550,'high'),dx=-20 if weight==400 else -60)
    out[0xF45D]=[native('や',[0,1],dx=120),O.draw([rounded_join(neck,arm)])]
    yu_mark=native('は',[2],sx=.78,sy=.66,dx=-20 if weight==400 else -52,dy=160,font=optical)
    yu_mark=transform(yu_mark,(1,0,.06,1,-12,0))
    out[0xF45E]=[yu_mark,
                  native('ゆ',sx=.94,dx=150)]
    out[0xF45F]=[native('は',[2],sx=.90 if weight==400 else .85,sy=.75,dx=15 if weight==400 else -20,dy=135,font=optical),
                  native('よ',sx=.96,dx=150)]
    wi=rings('ゐ',optical)[0]
    wa=wi[:33]+[line(wi[33][0],wi[49][0])]+wi[49:]
    body_sy=.82
    for cp,ch in ((0xF460,None),(0xF461,'ゐ'),(0xF462,'ゑ')):
        body=O.draw([move(wa,sx=.82,sy=body_sy,dx=20)]) if ch is None else native(ch,sx=.82,sy=body_sy,dx=20,font=f if ch=='ゑ' else optical)
        mark=native('こ',[0],sx=.55,sy=.72,font=optical)
        if cp==0xF462:
            mark=native('こ',[0],sx=.42,sy=.58)
            mark=transform(mark,(.985,-.174,.174,.985,0,0))
        bb=BoundsPen(None);body.replay(bb)
        mb=BoundsPen(None);mark.replay(mb)
        mx=(mb.bounds[0]+mb.bounds[2])/2
        out[cp]=[body,transform(mark,(1,0,0,1,(460 if cp==0xF462 else 365)-mx,bb.bounds[3]+50-mb.bounds[1]))]
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
