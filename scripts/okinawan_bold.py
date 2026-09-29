"""Compose Okinawan Regular and Bold from native Noto Serif JP masters.

Approved outlines guide placement and connections. Optical source weights
compensate for reduced vowel parts without expanding stroke ends.
"""
from functools import lru_cache

import numpy as np
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.svgLib.path import parse_path

import okinawan_outline as O
from okinawan_ligatures import source


def cut_keep(ring, axis, at, keep):
    crossings = sorted(O.crossings(ring, axis, at),
                       key=lambda c: O.point(ring[c[0]], c[1])[1-axis])
    assert len(crossings) >= 2, (axis, at, len(crossings))
    mid = np.mean([p[1-axis] for seg in ring for p in seg])
    a, b = min(zip(crossings[::2], crossings[1::2]),
               key=lambda pair: abs(sum(O.point(ring[c[0]], c[1])[1-axis]
                                        for c in pair)/2-mid))
    reach = ((lambda arc: -min(p[axis] for s in arc for p in s)) if keep == 'low'
             else (lambda arc: max(p[axis] for s in arc for p in s)))
    return max((O.arc(ring, a, b), O.arc(ring, b, a)), key=reach)


@lru_cache(maxsize=1)
def reference():
    from serif import instance
    return instance('NotoSerifJP', 400, set(map(ord, 'ふいぃわくえぇてとつを')))


def bounds(rings):
    p = BoundsPen(None)
    O.draw(rings).replay(p)
    return np.array(p.bounds)


def move(r, sx=1, sy=1, dx=0, dy=0):
    return O.transform(r, np.diag([sx, sy]), (dx, dy))


def clean(r):
    return [s for s in r if np.linalg.norm(s[-1] - s[0]) > 1e-8]


def line(p, q):
    return (p, p + (q-p)/3, p + 2*(q-p)/3, q)


def bridge(a, b, fullness=.33):
    p, q = a[-1][3], b[0][0]
    length = np.linalg.norm(q-p) * fullness
    return (p, p + O.tangent(a[-1], 1)*length,
            q - O.tangent(b[0], 0)*length, q)


def join(a, b):
    a, b = clean(a), clean(b)
    return a + [bridge(a, b)] + b + [bridge(b, a)]


def selected_join(a,b,outer,inner):
    """Join open contours with independent handles for their two edges."""
    a,b=clean(a),clean(b)
    def edge(x,y,h):
        p,q=x[-1][3],y[0][0]
        return (p,p+O.tangent(x[-1],1)*h[0],q-O.tangent(y[0],0)*h[1],q)
    return a+[edge(a,b,outer)]+b+[edge(b,a,inner)]

def native_turn(donor,left,right):
    """Fit a native turn to both endpoints and their tangents."""
    p,q=left[-1][3],right[0][0]
    u,v=O.tangent(donor[0],0),O.tangent(donor[-1],1)
    uv=np.column_stack([u,v]);a,b=np.linalg.solve(uv,donor[-1][3]-donor[0][0])
    U,V=O.tangent(left[-1],1),O.tangent(right[0],0)
    alpha,beta=np.linalg.solve(np.column_stack([a*U,b*V]),q-p)
    assert alpha>0 and beta>0,(alpha,beta)
    mat=np.column_stack([alpha*U,beta*V])@np.linalg.inv(uv)
    return O.transform(donor,mat,p-mat@donor[0][0])

def guide_join(a, b, guide, compact=False, outer_end=23):
    """Carry over the approved outer and inner turns between native Bold edges."""
    outer = native_turn(guide[22:outer_end], a, b)
    inner = native_turn(guide[-1:], b, a)
    if compact:
        for path in (outer, inner):
            first = list(path[0])
            first[1] = first[0] + .78 * (first[1] - first[0])
            path[0] = tuple(first)
            last = list(path[-1])
            last[2] = last[3] + .78 * (last[2] - last[3])
            path[-1] = tuple(last)
    return a + outer + b + inner


def rounded_join(a,b,fullness=1.0):
    """Match curvature where the continuous sweeps meet."""
    a,b=clean(a),clean(b)
    def edge(x,y):
        return O.fair(x[-1][3],O.tangent(x[-1],1),O.curvature(x[-1],1),
                      y[0][0],O.tangent(y[0],0),O.curvature(y[0],0),fullness=fullness)
    return a+[edge(a,b)]+b+[edge(b,a)]


def curvature_join(a, b):
    """Join a continuing stroke with matching tangent and endpoint curvature."""
    from scipy.optimize import least_squares
    def edge(left, right):
        p,q=left[-1][3],right[0][0]
        u,v=O.tangent(left[-1],1),O.tangent(right[0],0)
        k0,k1=O.curvature(left[-1],1),O.curvature(right[0],0)
        span=np.linalg.norm(q-p)
        def segment(h):return (p,p+u*h[0],q-v*h[1],q)
        def residual(h):
            s=segment(h)
            return span*np.array([O.curvature(s,0)-k0,O.curvature(s,1)-k1])
        attempts=[least_squares(residual,np.array(start)*span,
                                bounds=([span*.02]*2,[span*2]*2),
                                ftol=1e-12,xtol=1e-12,gtol=1e-12)
                  for start in ((.30,.60),(.60,.30),(.75,.75))]
        solved=min(attempts,key=lambda result:np.linalg.norm(result.fun))
        assert np.max(np.abs(residual(solved.x)))<1e-5, ('No smooth positive-handle join',p,q,k0,k1,solved.x,residual(solved.x))
        return segment(solved.x)
    return a+[edge(a,b)]+b+[edge(b,a)]


def wa_sweep(rings):
    """Draw the diagonal and bowl as one stroke, removing their component caps."""
    bowl, diagonal = rings[:2]
    assert len(bowl) == 23 and len(diagonal) == 15, 'Native wa contour layout changed'
    inside = bowl[:9]
    foot = diagonal[10:] + diagonal[:6]
    outside = bowl[12:]
    return (inside + [bridge(inside, foot, .34)] + foot
            + [bridge(foot, outside, .36)] + outside)

def fit(r, ref, box):
    x0, y0, x1, y1 = bounds([ref])
    left, bottom, right, top = box
    sx, sy = (right-left)/(x1-x0), (top-bottom)/(y1-y0)
    return move(r, sx, sy, left-sx*x0, bottom-sy*y0)


def _approved():
    out = {}
    for g in source()['glyphs']:
        out[g['label']] = []
        for c in g['components']:
            p = RecordingPen()
            parse_path(c['path'], TransformPen(p, c['transform']))
            out[g['label']].extend(O.rings(p))
    return out


@lru_cache(maxsize=12)
def body_source(weight=700):
    from serif import instance
    return instance('NotoSerifJP', weight, set(map(ord, 'ふくてとつを')))


@lru_cache(maxsize=12)
def vowel_source(weight):
    from serif import instance
    return instance('NotoSerifJP', weight, set(map(ord, 'いぃわえ')))


def drawings(font, contours, option="B", style="Bold", wu_variant=None):
    assert option in ("A", "B")
    wu_variant = option if wu_variant is None else wu_variant
    assert wu_variant in ("A", "B", "C", "D")
    fuller = option == "B"
    bold = style == "Bold"
    # Keep the chosen B weight and construction in every WU comparison.
    wu_body,wu_bowl,wu_crown=500,550,28
    body_weight, vowel_weight = (700, 750) if bold else (400, 500)
    regular = reference()
    approved = _approved()

    def ring(ch, index=0, ref=False):
        donor = regular if ref else vowel_source(vowel_weight) if ch in 'いぃわえ' else body_source(body_weight)
        return O.rings(contours(donor, ord(ch), [index]))[0]

    def native(ch, index, box, cut=None):
        r, q = ring(ch, index), ring(ch, index, True)
        if cut:
            r, q = (clean(cut_keep(x, *cut)) for x in (r, q))
        return fit(r, q, box)

    def ku(label):
        def shape(ref):
            r = cut_keep(ring('く', ref=ref), 1, 210, 'high')
            def mapping(p):
                x, y = p
                z = 360-y
                ramp = 0 if z <= -40 else z if z >= 40 else (z+40)**2/160
                return np.array([.94*x+20+.55*ramp,
                                 480+(y-360)*320/437-(130/150-320/437)*ramp])
            result = []
            for s in r:
                chunks = [s]
                for _ in range(3):
                    chunks = [c for seg in chunks for c in O.split(seg, .5)]
                result.extend(tuple(mapping(p) for p in seg) for seg in chunks)
            return clean(result)
        target = cut_keep(approved[label][0], 1, 300, 'high')
        return fit(shape(False), shape(True), bounds([target]))

    # One native fu body and rising stroke supply all three labials.
    def fu_main(ref):
        r = ring('ふ', ref=ref)
        cuts = [c for c in O.crossings(r, 0, 310)
                if O.point(r[c[0]], c[1])[1] < 180]
        assert len(cuts) == 2
        a = max((O.arc(r, *cuts), O.arc(r, *cuts[::-1])),
                key=lambda a: max(p[1] for s in a for p in s))
        return a + [line(a[-1][3], a[0][0])]
    fu = fit(fu_main(False), fu_main(True), bounds([approved['HWI'][0]]))
    def rising(ref):
        r = cut_keep(ring('ふ', 1, ref), 0, 580, 'low')
        angle = np.radians(12)
        rot = np.array([[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]])
        return O.transform(r, rot, (0, 0))
    rise_target = approved['HWI'][1][:22]
    rise = fit(rising(False), rising(True), bounds([rise_target]))

    # Keep the approved connection centre. The native master's terminal
    # otherwise lifts the whole shoulder while barely increasing its width.
    wanted = (rise_target[0][0] + rise_target[-1][3]) / 2
    actual = (rise[0][0] + rise[-1][3]) / 2
    delta = wanted - actual
    def anchor_rise(p):
        t = np.clip((p[0] - 350) / 190, 0, 1)
        return p + delta * (t*t*(3-2*t))
    rise = [tuple(anchor_rise(p) for p in seg) for seg in rise]

    # The earlier upright return aimed at the right stroke's start. Retain
    # that axis and a finite cap, narrowing only the upper part of the hook.
    if not bold:
        vowel_weight = 500 if fuller else 475
    def short_i(ref):
        return clean(cut_keep(ring('い', ref=ref), 1, 420, 'low'))
    i = fit(short_i(False), short_i(True), (605, 40, 768, 375))
    r = i + [line(i[-1][3], i[0][0])]
    cuts = [c for c in O.crossings(r, 1, 215)
            if O.point(r[c[0]], c[1])[0] > 705]
    assert len(cuts) == 2
    i = max((O.arc(r, *cuts), O.arc(r, *cuts[::-1])),
            key=lambda a: max((p[1] for seg in a for p in seg if p[0]<705), default=-1000))
    i += [line(i[-1][3], i[0][0])]
    def narrow(p):
        x,y = p
        t = np.clip((y-160)/55, 0, 1)
        side = np.clip((x-695)/15, 0, 1)
        blend = t*t*(3-2*t)*side*side*(3-2*side)
        axis = 733.4+.24*(y-215)
        factor = (.40 if fuller else .46) if bold else 0
        return np.array([x-factor*blend*(x-axis), y])
    shaped = []
    for seg in i:
        pieces = [seg]
        for _ in range(3):
            pieces = [part for curve in pieces for part in O.split(curve,.5)]
        shaped.extend(tuple(narrow(p) for p in part) for part in pieces)
    i = clean(cut_keep(shaped, 1, 365, 'low'))
    hwi = [fu, guide_join(rise, i, approved['HWI'][1], not fuller), native('い', 1, (765.48, 68, 924.52, 341.6))]

    # The actual wa contours keep their native bowl/terminal contrast.
    wa_y = 25
    wa_scale = .56
    wa_x = lambda x: (604 if bold else 584) + (x-73)*410/877
    def hwa_map(r):
        out = []
        for seg in r:
            pieces = [seg]
            for _ in range(3):
                pieces = [part for s in pieces for part in O.split(s, .5)]
            out.extend(tuple(np.array([float(wa_x(p[0])), wa_scale*p[1]+wa_y]) for p in s)
                       for s in pieces)
        return out
    wa_font = vowel_source(900 if bold else 850)
    wa_rings = [O.rings(contours(wa_font, ord('わ'), [n]))[0] for n in range(3)]
    if bold:
        # Enlarge the right stroke inward while retaining its native outside
        # and terminal. A smaller counter restores weight after the narrow fit.
        bowl = wa_rings[0]
        for j in range(9):
            def inner(p):
                x,y=p; t=np.clip((y+15)/170,0,1); t=t*t*(3-2*t)
                return np.array([x-.16*max(x-420,0)*t,y-12*t])
            bowl[j]=tuple(inner(p) for p in bowl[j])
    vowel_target_bottom = .49*bounds([wa_rings[2]])[1]+25
    if not bold:
        reference_wa = O.rings(contours(vowel_source(600), ord('わ'), [2]))
        vowel_target_bottom = .49*bounds(reference_wa)[1]+25
    wa_y = vowel_target_bottom-wa_scale*bounds([wa_rings[2]])[1]
    wa_stem = hwa_map(cut_keep(wa_rings[2], 1, 450, 'low'))
    # Extend the stem to the approved shoulder height. All native wa seams
    # below it share one map, preserving the small counter and bowl connection.
    top = 315 if fuller else 340
    first, last = wa_stem[0][0], wa_stem[-1][3]
    tf, tl = O.tangent(wa_stem[0], 0), O.tangent(wa_stem[-1], 1)
    q = first + tf * ((top-first[1])/tf[1])
    p = last + tl * ((top-last[1])/tl[1])
    wa_stem = [line(q, first)] + wa_stem + [line(last, p)]
    saved_weight = body_weight
    body_weight = 850 if bold else 600
    hwa_rise = fit(rising(False), rising(True), bounds([rise_target]))
    body_weight = saved_weight
    # Keep the established connector endpoints while taking the heavier master.
    delta = wanted - (hwa_rise[0][0]+hwa_rise[-1][3])/2
    hwa_rise = [tuple(anchor_rise(p) for p in seg) for seg in hwa_rise]
    assert len(hwa_rise) == len(rise)
    hwa_rise = [tuple(p + (q-p)*np.clip((p[0]-350)/180, 0, 1)
                      for p,q in zip(a,b)) for a,b in zip(rise,hwa_rise)]
    # One rising shoulder turns directly into the stem. Both candidates use
    # the accepted weight, differing only in shoulder height and curvature.
    shoulder = O.rings(contours(body_source(850 if bold else 600), ord('つ'), [0]))[0]
    hwa = [fu, hwa_rise + native_turn(shoulder[27:33], hwa_rise, wa_stem)
           + wa_stem + native_turn(shoulder[4:9], wa_stem, hwa_rise),
           hwa_map(wa_sweep(wa_rings))]

    # Select the native e body, with an optional independent terminal weight.
    def e_lower(ref, foot_weight=None, foot_scale=None, cut_height=380, smooth_left=False):
        r = ring('え', ref=ref)
        if smooth_left and not ref:
            from scipy.interpolate import CubicSpline
            cap=r[11:19]
            points=np.array([cap[0][0]]+[seg[3] for seg in cap])
            lengths=[sum(np.linalg.norm(O.point(seg,t)-O.point(seg,t-.05))
                         for t in np.linspace(.05,1,20)) for seg in cap]
            knots=np.r_[0,np.cumsum(lengths)]
            spline=CubicSpline(knots,points,axis=0,
                               bc_type=((1,O.tangent(cap[0],0)),(1,O.tangent(cap[-1],1))))
            r[11:19]=[(spline(a),spline(a)+spline(a,1)*(b-a)/3,
                       spline(b)-spline(b,1)*(b-a)/3,spline(b))
                      for a,b in zip(knots[:-1],knots[1:])]
        if foot_weight and not ref:
            light = O.rings(contours(vowel_source(foot_weight), ord('え'), [0]))[0]
            assert len(r) == len(light) == 75
            # Preserve the terminal's native aspect ratio after the vowel's
            # narrow fit. The diagonal and arch keep their original master.
            body = r[2:64]
            foot = light[66:] + light[:1]
            baseline = light[0][0][1]
            scale = foot_scale if foot_scale is not None else (.65 if fuller else .60)
            foot = move(foot, 1, scale, 0, baseline*(1-scale))
            if foot_scale is not None:
                foot = move(foot, 1, 1, 0, bounds([r[66:]+r[:1]])[1]-bounds([foot])[1])
            r = rounded_join(body, foot)
        cuts = sorted(O.crossings(r, 1, cut_height), key=lambda c: O.point(r[c[0]], c[1])[0])[-2:]
        return min((O.arc(r, *cuts), O.arc(r, *cuts[::-1])), key=lambda a: min(p[1] for seg in a for p in seg))
    vowel_weight = (800 if fuller else 750) if bold else (600 if fuller else 550)
    # Take the native lower stroke below its separate pen-start head.
    e=clean(e_lower(False,foot_weight=650 if bold else 450,foot_scale=.85,cut_height=460,smooth_left=True))
    left,bottom,_,_ = bounds([e])
    sx,sy = (.50,.74) if fuller else (.48,.70)
    e = move(e,sx,sy,580-sx*left,vowel_target_bottom-sy*bottom)
    # Keep the lower native arch and terminal. Above them, bring the long
    # diagonal upright so the shoulder can rise with HWA and HWI.
    def upright_e(p):
        x,y=p; z=y-175
        ramp=0 if z<=-30 else z if z>=30 else (z+30)**2/120
        return np.array([x-(.38 if fuller else .30)*ramp,y])
    shaped=[]
    for seg in e:
        pieces=[seg]
        for _ in range(3):pieces=[part for s in pieces for part in O.split(s,.5)]
        shaped.extend(tuple(upright_e(p) for p in s) for s in pieces)
    e=shaped
    # Use the same native rounded shoulder as HWA. The e diagonal takes
    # over below the turn, without retaining an isolated pen-start head.
    e=clean(cut_keep(e+[line(e[-1][3],e[0][0])],1,300 if fuller else 290,'low'))
    outside=native_turn(shoulder[27:33],hwa_rise,e)
    for _ in range(3):
        outside=[part for seg in outside for part in O.split(seg,.5)]
    # Relieve the outer shoulder locally, leaving both attachment tangents.
    span=sum(np.linalg.norm(seg[3]-seg[0]) for seg in outside)
    offset=0; shaped=[]
    for seg in outside:
        length=np.linalg.norm(seg[3]-seg[0]); a=offset/span; b=(offset+length)/span
        f=lambda t:np.sin(np.pi*t)**2
        df=lambda t:np.pi*np.sin(2*np.pi*t)
        relief=(f(a),f(a)+(b-a)*df(a)/3,f(b)-(b-a)*df(b)/3,f(b))
        shaped.append(tuple(p+np.array([-24.,-20.] if bold else [-18.,-16.])*v for p,v in zip(seg,relief)))
        offset+=length
    hwe=[fu,hwa_rise+shaped+e+native_turn(shoulder[4:9],e,hwa_rise)]

    # Native optical weights compensate for the compressed vowel components.
    body_weight, vowel_weight = ((850, 900) if fuller else (800, 850)) if bold else ((600, 650) if fuller else (550, 600))
    kwi_i = native('ぃ', 0, (475, -78, 620, 291), (1, 375, 'low'))
    kwi_i = move(kwi_i, 1, .90, -30, -9.4)
    upper = ku('KWI')
    upper = clean(cut_keep(upper + [line(upper[-1][3], upper[0][0])], 1, 335, 'high'))
    donor = [tuple(reversed(s)) for s in reversed(approved['KWI'][0][31:36])]
    kwi_join = upper + native_turn(donor, upper, kwi_i) + kwi_i + [bridge(kwi_i, upper, .27)]
    kwi = [kwi_join, native('ぃ', 1, bounds([approved['KWI'][-1]]))]
    body_weight, vowel_weight = (700,850) if bold else (500,550)
    # The entire native wa shares one master and one affine map. Its three
    # component caps are covered by the native stem, so no seam is exposed.
    wa_font = vowel_source((900 if fuller else 875) if bold else 700)
    kwa_rings = [O.rings(contours(wa_font, ord('わ'), [n]))[0] for n in range(3)]
    def wa_placement(r):
        sx = .82 if bold and fuller else .80
        return move(r, sx, .67, 470-356*sx, 339-536*.67)
    kwa_stem = wa_placement(cut_keep(kwa_rings[2], 1, 400, 'low'))
    kwa_fuller = bold and fuller
    kwa = [selected_join(ku('KWA'), kwa_stem, (14,24) if kwa_fuller else (8,20), (23,26) if kwa_fuller else (20,24)),
           wa_placement(wa_sweep(kwa_rings))]
    left,_,right,_=bounds(kwa)
    kwa=[move(r,1,1,500-(left+right)/2,0) for r in kwa]
    body_weight, vowel_weight = ((850, 900) if fuller else (800, 850)) if bold else ((600, 650) if fuller else (550, 600))
    if not bold:
        body_weight, vowel_weight = 550, 500
    kwe_foot = (600 if fuller else 550) if not bold else None
    kwe_lower = fit(e_lower(False, kwe_foot, 1 if not bold else None), e_lower(True), (203, -64 if bold else -12, 847, 286))
    upper = ku('KWE')
    target = (upper[0][0][0]+upper[-1][3][0])/2 + 35
    current = (kwe_lower[0][0][0]+kwe_lower[-1][3][0])/2
    shear = (target-current)/(286+64)
    kwe_lower = O.transform(kwe_lower, np.array([[1, shear], [0, 1]]), (64*shear, 0))
    if bold:
        kwe_lower = move(kwe_lower, 1, .925, 0, -4.8)
    # Back away from the original attachment so both tangent rays meet
    # ahead of the edges. This convex turn has no reverse-curvature notch.
    kwe_lower = kwe_lower[:-1]
    p, q = kwe_lower[-1][3], upper[0][0]
    u, v = O.tangent(kwe_lower[-1], 1), O.tangent(upper[0], 0)
    a, b = np.linalg.solve(np.column_stack([u, v]), q-p)
    assert a > 0 and b > 0, ('KWE inner turn', a, b)
    inner = (p, p+u*a*2/3, q-v*b*2/3, q)
    kwe = [upper + [bridge(upper, kwe_lower)] + kwe_lower + [inner]]

    body_weight, vowel_weight = (700, 750) if bold else (400, 500)
    te = native('て', 0, (107, 225, 882, 718), (1, 250, 'high'))
    te = clean(cut_keep(te + [line(te[-1][3], te[0][0])], 1, 300, 'high'))
    ti_i = native('ぃ', 0, (415, -10, 612, 195), (1, 375, 'low'))
    # Preserve the visible te-to-i elbow on the inner edge. The outer edge
    # turns into the i bowl while the inner contour retains its native corner.
    ti_i = move(ti_i, 1, 1, 64 if fuller else 52, 0)
    corner = ti_i[-1][3]
    inner = []
    p, q = corner, te[0][0]
    inner.append((p, p+np.array([-54., 14.]), q-O.tangent(te[0], 0)*48, q))
    ti = [te + [bridge(te, ti_i, .42)] + ti_i + inner,
          native('ぃ', 1, bounds([approved['TI'][-1]]))]
    tsi_fuller = fuller if bold else False
    body_weight, vowel_weight = ((850, 900) if tsi_fuller else (800, 850)) if bold else ((550, 650) if tsi_fuller else (500, 600))
    def tsu_arc(ref):
        r = ring('つ', ref=ref)
        cuts = sorted(O.crossings(r, 0, 470 if tsi_fuller else 450), key=lambda c: O.point(r[c[0]], c[1])[1])[:2]
        return max((O.arc(r, *cuts), O.arc(r, *cuts[::-1])), key=lambda a: max(p[1] for seg in a for p in seg))
    body_weight = (900 if tsi_fuller else 875) if bold else (700 if tsi_fuller else 650)
    tsu_top = fit(tsu_arc(False), tsu_arc(True), (118, 294, 882, 690))
    tsi_i = native('ぃ', 0, (380, 19, 555, 280), (1, 375, 'low'))
    tsi_i = move(tsi_i, 1, .94, -25, .48)
    # The approved turn is an affine guide; native Bold edges set its width.
    turn=ring('て', ref=True)[39:44]
    tsi_join=tsu_top+native_turn(turn,tsu_top,tsi_i)+tsi_i+native_turn(turn,tsi_i,tsu_top)
    tsi = [tsi_join, move(native('ぃ', 1, bounds([approved['TSI'][-1]])), 1, 1, 0, -25)]

    # Retain the native rounded turn into the rightward exit. The old cut
    # on the descending edge forced a cramped reversal before the tsu bowl.
    body_weight, vowel_weight = ((850, 850) if fuller else (800, 800)) if bold else ((600, 600) if fuller else (550, 550))
    def flowing_sweep(ch):
        r=ring(ch)
        if ch=='を':
            # The native lower return needs less optical compensation than
            # the reduced upper entry. Blend masters before placing the turn.
            weight=(700 if fuller else 650) if bold else (500 if fuller else 450)
            light=O.rings(contours(body_source(weight),ord('を'),[0]))[0]
            assert len(light)==len(r)
            def blend(p,q):
                t=np.clip((p[1]-100)/220,0,1); t=t*t*(3-2*t)
                return q+(p-q)*t
            r=[tuple(blend(p,q) for p,q in zip(a,b)) for a,b in zip(r,light)]
            # Separate the native inner edge only along the thin return.
            # Both fades finish before the upper crossing and lower join.
            strength=36 if bold else 28
            lower_fade=180 if bold else 145
            assert len(r)==45, 'Native wo return contour layout changed'
            widened=[]
            def open_return(p):
                x,y=p
                a=np.clip((y-60)/lower_fade,0,1); b=np.clip((350-y)/100,0,1)
                amount=strength*a*a*(3-2*a)*b*b*(3-2*b)
                direction=np.array([.35,-1.])
                if not bold:
                    turn=np.clip((240-y)/130,0,1);turn=turn*turn*(3-2*turn)
                    direction+=np.array([.65,.75])*turn
                return p+direction*amount
            for index,seg in enumerate(r):
                if not 25<=index<=33:
                    widened.append(seg)
                    continue
                pieces=[seg]
                for _ in range(3):pieces=[part for curve in pieces for part in O.split(curve,.5)]
                widened.extend(tuple(open_return(p) for p in part) for part in pieces)
            # Fit the diagonal's weighted inner edge as one cubic. Its
            # endpoint tangents and mean width guide the fit,
            # without retaining the short swell from the local offset.
            first,last=25,25+6*8
            arc=widened[first:last]
            samples=np.array([O.point(seg,t) for seg in arc for t in np.linspace(0,1,9)[:-1]]+[arc[-1][3]])
            distance=np.r_[0,np.cumsum(np.linalg.norm(np.diff(samples,axis=0),axis=1))]
            t=(distance/distance[-1])[:,None]
            p,q=arc[0][0],arc[-1][3]
            u,v=O.tangent(arc[0],0),O.tangent(arc[-1],1)
            base=(1-t)**2*(1+2*t)*p+t*t*(3-2*t)*q
            matrix=np.stack([3*t*(1-t)**2*u,-3*t*t*(1-t)*v],axis=-1).reshape(-1,2)
            h=np.linalg.lstsq(matrix,(samples-base).reshape(-1),rcond=None)[0]
            assert np.all(h>0), 'WU diagonal fit reversed a tangent'
            widened=widened[:first]+[(p,p+u*h[0],q-v*h[1],q)]+widened[last:]
            r=widened
        cuts=sorted(O.crossings(r,0,(400 if bold else 375) if ch=='を' else 325),key=lambda c: O.point(r[c[0]],c[1])[1])[:2]
        assert len(cuts)==2 and max(O.point(r[i],t)[1] for i,t in cuts)<130, 'Expected the native rightward exit'
        head=max((O.arc(r,*cuts),O.arc(r,*cuts[::-1])),
                 key=lambda a:max(p[1] for seg in a for p in seg))
        head=clean(head)
        if ch=='を':
            # Leave the native upper diagonal at its established height.
            # Extra room for the left return belongs below the central stem.
            def lower_turn(p):
                x,y=p
                t=np.clip(y/400,0,1); t=t*t*(3-2*t)
                return np.array([.86*x+25,.88*y+65+(120 if fuller else 100)*(1-t)])
            shaped=[]
            for seg in head:
                pieces=[seg]
                for _ in range(3):pieces=[part for s in pieces for part in O.split(s,.5)]
                shaped.extend(tuple(lower_turn(p) for p in s) for s in pieces)
            head=shaped
        else:
            head=move(head,.90,.74,5,175)
        tail_weight=(900 if fuller else 850) if bold else (650 if fuller else 600)
        if ch=='を' and not bold:
            tail_weight=wu_bowl
        r=O.rings(contours(body_source(tail_weight),ord('つ'),[0]))[0]
        # Compensate for the vertical reduction of the tsu hairline.
        # The native outer bowl and tapered terminal retain their contours.
        shaped=[]
        scale=.53 if ch=='と' else .45
        depth=((54 if fuller else 46) if bold else (34 if fuller else 28))/scale
        if ch=='を' and not bold:
            depth=wu_crown/scale
        if ch=='を':
            assert len(r)==41, 'Native tsu terminal contour layout changed'
        for index,seg in enumerate(r):
            if ch=='を' and index<3:
                if index==0:
                    # Give the reduced terminal a native slanted cut and a
                    # continuous taper into the untouched right-hand bowl.
                    bottom=r[-1][0]
                    height=((36 if fuller else 30) if bold else (28 if fuller else 22))/scale
                    tip=bottom+(r[0][0]-bottom)*height/(r[0][0][1]-bottom[1])
                    end=r[2][3]
                    span=np.linalg.norm(end-tip)
                    shaped.append((tip,tip+O.tangent(r[0],0)*span*.40,
                                   end-O.tangent(r[2],1)*span*.30,end))
                continue
            if ch=='を' and index==len(r)-1:
                shaped.append(line(seg[0],tip))
                continue
            if index>=12:
                shaped.append(seg)
                continue
            pieces=[seg]
            for _ in range(2):pieces=[part for curve in pieces for part in O.split(curve,.5)]
            def inner(p):
                x,y=p; t=np.clip((y-150)/400,0,1); t=t*t*(3-2*t)
                return np.array([x,y-depth*t])
            shaped.extend(tuple(inner(p) for p in part) for part in pieces)
        r=shaped
        if ch=='を':
            # Match the crown correction's final endpoint and tangent.
            tip,end=r[0][0],r[1][0]
            span=np.linalg.norm(end-tip)
            r[0]=(tip,tip+O.tangent(r[0],0)*span*.40,
                  end-O.tangent(r[1],0)*span*.30,end)
        cuts=sorted(O.crossings(r,0,600 if ch=='を' else 470),key=lambda c:O.point(r[c[0]],c[1])[1])[-2:]
        tail=max((O.arc(r,*cuts),O.arc(r,*cuts[::-1])),
                 key=lambda a:max(p[0] for seg in a for p in seg))
        tail=move(clean(tail),.78 if ch=='と' else .82,
                  .53 if ch=='と' else .45,
                  115 if ch=='と' else 80,-62 if ch=='と' else -63)
        if ch=='を' and wu_variant!='A':
            # Spread the reversal across a full-height arc. The native
            # diagonal flows into two round edges before the bowl shoulder.
            drop,outer_x,turn_y={
                'B':(14,265,250),
                'C':(8,275,245),
                'D':(20,250,255),
            }[wu_variant]
            lowered=[]
            _,floor,_,crown=bounds([tail])
            def lower_shoulder(p):
                t=np.clip((p[1]-floor)/(crown-floor),0,1)
                t=t*t*t*(10+t*(-15+6*t))
                return p+np.array([0.,-drop*t])
            for seg in tail:
                pieces=[seg]
                for _ in range(3):
                    pieces=[part for curve in pieces for part in O.split(curve,.5)]
                lowered.extend(tuple(lower_shoulder(p) for p in part) for part in pieces)
            tail=lowered
            head=clean(cut_keep(head+[line(head[-1][3],head[0][0])],1,360,'high'))
            inner_x=outer_x+(68 if bold else 42)
            left_inner=np.array([inner_x,float(turn_y)])
            left_outer=np.array([float(outer_x),float(turn_y)])
            p,q=head[-1][3],tail[0][0]
            inside=[(p,p+O.tangent(head[-1],1)*110,left_inner+np.array([0.,60.]),left_inner),
                    (left_inner,left_inner-np.array([0.,55.]),q-O.tangent(tail[0],0)*145,q)]
            p,q=tail[-1][3],head[0][0]
            outside=[(p,p+O.tangent(tail[-1],1)*205,left_outer-np.array([0.,80.]),left_outer),
                     (left_outer,left_outer+np.array([0.,70.]),q-O.tangent(head[0],0)*110,q)]
            # Match curvature at the vertical reversals. The outer radius
            # includes the local stroke width, keeping both edges round.
            def rounded_left(pair,radius):
                before,after=map(list,pair)
                point=before[3]
                for curve,index,remote in ((before,2,1),(after,1,2)):
                    handle=np.sqrt(2*abs(curve[remote][0]-point[0])*radius/3)
                    direction=(curve[index]-point)/np.linalg.norm(curve[index]-point)
                    curve[index]=point+direction*handle
                return [tuple(before),tuple(after)]
            inside=rounded_left(inside,50)
            outside=rounded_left(outside,50+(68 if bold else 42))
            return head+inside+tail+outside
        if ch=='を':
            # Start the return on the descending diagonal. Replacing both
            # edges here removes the low belly of the old native exit.
            head=clean(cut_keep(head+[line(head[-1][3],head[0][0])],1,330,'high'))
            joined=selected_join(head,tail,(220,160),(200,170))
            # Move both edges together around the reversal, preserving
            # B's thickness while opening the space below the stem.
            # The displacement fades before the upper crossing and bowl.
            dx,dy=-40,-36
            def open_turn(p):
                x,y=p
                a=np.clip((572-x)/(572-390),0,1)
                b=np.clip((430-y)/(430-300),0,1)
                smooth=lambda t:t*t*t*(10+t*(-15+6*t))
                return p+np.array([dx,dy])*smooth(a)*smooth(b)
            opened=[]
            for index,seg in enumerate(joined):
                # Native right bowl and terminal remain exact. Only the
                # head and its two joining curves receive displacement.
                points=np.array(seg)
                if (len(head)<index<len(head)+len(tail)+1 or
                    points[:,0].min()>=572 or points[:,1].min()>=430):
                    opened.append(seg)
                    continue
                if points[:,0].max()<=390 and points[:,1].max()<=300:
                    opened.append(tuple(p+np.array([dx,dy]) for p in seg))
                    continue
                pieces=[seg]
                depth=max(0,int(np.ceil(np.log2(max(np.ptp(points,axis=0))/16))))
                for _ in range(depth):
                    pieces=[part for curve in pieces for part in O.split(curve,.5)]
                opened.extend(tuple(open_turn(p) for p in part) for part in pieces)
            joined=opened
            return joined
        return curvature_join(head,tail)
    tu = [native('と', 1, (250, 380, 450, 774)), flowing_sweep('と')]
    # WU candidates share the accepted B placement and terminal.
    original_fuller=fuller
    fuller=True
    body_weight=850 if bold else wu_body
    # Restore horizontal room to wo's reduced upper arch. Its native
    # contour stays intact, with the entry height and lower sweep fixed.
    wu = [native('を', 1, (214, 220, 565, 797)),
          native('を', 2, bounds([approved['WU'][1]])), flowing_sweep('を')]
    # Scale around the native bar's centre so the explicit lift opens the
    # space below it without moving the arch, entry or lower sweep.
    left,bottom,right,top=bounds([wu[1]])
    cx,cy=(left+right)/2,(bottom+top)/2
    wu[1]=move(wu[1],.90,.90,cx*(1-.90),cy*(1-.90)+14)
    # Shorten the two straight sides above wo's native terminal. The arch,
    # entry and rounded cap retain their native outlines.
    stem=wu[0]
    assert len(stem)==49, 'Native wo stem contour layout changed'
    body=stem[5:44]
    cap=move(stem[47:]+stem[:2],dy=45)
    wu[0]=selected_join(body,cap,(20,20),(8,8))
    fuller=original_fuller
    result = dict(TU=tu, TI=ti, KWA=kwa, KWI=kwi, KWE=kwe,
                  HWA=hwa, HWI=hwi, HWE=hwe, WU=wu, TSI=tsi)
    if not bold:
        # Retain the accepted Regular forms outside the requested revisions.
        for label in ('TI',):
            result[label] = approved[label]
        # Use the approved fu body and shoulder with the new native wa map.
        result['HWA'][0] = approved['HWA'][0]
    # Set the reduced vowels on the same optical baseline as HWA's wa.
    vowel_baseline = bounds([hwa_map(wa_rings[2])])[1]
    if not bold:
        baseline_source = O.rings(contours(vowel_source(600), ord('わ'), [2]))
        vowel_baseline = bounds(baseline_source)[1]*.49+25
    if bold:
        hwi_body = i
        hwi_rise = rise
    else:
        result['HWI'][0] = approved['HWI'][0]
        # Add weight toward the counter while preserving the accepted outer
        # contour, terminal direction and finite tip. The right stroke uses
        # the native heavier master selected above.
        hwi_body=approved['HWI'][1][23:-1]
        offsets=np.array([(6,0),(6,0),(3,7),(0,7)]+[(0,0)]*8,float)
        offsets*=1 if fuller else .75
        hwi_body=[tuple(p+d for p,d in zip(seg,(offsets[j],offsets[j],offsets[j+1],offsets[j+1])))
                  for j,seg in enumerate(hwi_body)]
        hwi_rise = approved['HWI'][1][:22]
    def stand(r, anchor=365):
        bottom = bounds([r])[1]
        sy = (anchor-vowel_baseline)/(anchor-bottom)
        return move(r, 1, sy, 0, anchor*(1-sy)), sy
    hwi_body, i_scale = stand(hwi_body)
    result['HWI'][1] = guide_join(hwi_rise, hwi_body, approved['HWI'][1], not fuller if bold else False)
    result['HWI'][2] = move(result['HWI'][2], 1, i_scale, 0, 365*(1-i_scale))
    # Match native entry heights without moving the baseline or the lower join.
    for label, donor, hinge in (('KWA','く',300), ('KWI','く',300), ('KWE','く',300),
                               ('TU','と',450), ('WU','を',350), ('TSI','つ',280)):
        target = round(bounds(O.rings(contours(body_source(700 if bold else 400), ord(donor))))[3])
        if label == 'TSI':
            target += 25
        current = bounds(result[label])[3]
        def align(p):
            return np.array([p[0], p[1] if p[1] <= hinge else hinge+(p[1]-hinge)*(target-hinge)/(current-hinge)])
        result[label] = [ [tuple(align(p) for p in seg) for seg in r] for r in result[label] ]
    # End the to entry inside its receiving stroke. Its old exposed tip
    # otherwise projects below the lowered diagonal as a small diamond.
    entry, receiver = result['TU']
    centres = []
    for x in (340, 440):
        ys = sorted((O.point(receiver[i], t)[1] for i,t in O.crossings(receiver, 0, x)), reverse=True)
        centres.append((x, (ys[0]+ys[1])/2))
    slope = (centres[1][1]-centres[0][1])/100
    intercept = centres[0][1]-slope*340
    tilted = O.transform(entry, [[1,0],[-slope,1]], (0,0))
    trimmed = clean(cut_keep(tilted, 1, intercept, 'high'))
    trimmed.append(line(trimmed[-1][3], trimmed[0][0]))
    result['TU'][0] = O.transform(trimmed, [[1,0],[slope,1]], (0,0))
    return {int(g['codepoint'], 16): [O.draw([r]) for r in result[g['label']]]
            for g in source()['glyphs']}
