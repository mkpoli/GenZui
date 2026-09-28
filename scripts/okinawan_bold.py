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
    """Control the outer and inner KWA turn independently."""
    a,b=clean(a),clean(b)
    def edge(x,y,h):
        p,q=x[-1][3],y[0][0]
        return (p,p+O.tangent(x[-1],1)*h[0],q-O.tangent(y[0],0)*h[1],q)
    return a+[edge(a,b,outer)]+b+[edge(b,a,inner)]

def native_turn(donor,left,right):
    """Fit the approved native turn to both Bold edges and their tangents."""
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


def drawings(font, contours, option="B", style="Bold"):
    assert option in ("A", "B")
    fuller = option == "B"
    bold = style == "Bold"
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
        factor = .40 if fuller else .46
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

    # KWE keeps the native arch; its terminal has an independent donor weight.
    def e_lower(ref, foot_weight=None, foot_scale=None):
        r = ring('え', ref=ref)
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
        cuts = sorted(O.crossings(r, 1, 380), key=lambda c: O.point(r[c[0]], c[1])[0])[-2:]
        return min((O.arc(r, *cuts), O.arc(r, *cuts[::-1])), key=lambda a: min(p[1] for seg in a for p in seg))
    vowel_weight = (850 if fuller else 800) if bold else (650 if fuller else 600)
    # Retain e's own entry corner, diagonal, arch and terminal. Cut on the
    # nearly straight entry run, so the join never has to invent its corner.
    er = ring('え')
    assert len(er)==75
    # Remove the isolated pen-start swelling from the now-continuous entry.
    er = er[:43]+[bridge(er[:43],er[50:],.40)]+er[50:]
    cuts = sorted(O.crossings(er, 0, 420),
                  key=lambda c: O.point(er[c[0]],c[1])[1])[-2:]
    e = max((O.arc(er,*cuts),O.arc(er,*cuts[::-1])),
            key=lambda a: max(p[0] for seg in a for p in seg))
    e = clean(e)
    left,bottom,_,_ = bounds([e])
    sx,sy = (.50,.68) if fuller else (.47,.64)
    e = move(e,sx,sy,600-sx*left,vowel_target_bottom-sy*bottom)
    # Stop fu's rising run before its old shoulder. This gives the native
    # e entry room to continue upward without a dip between two high points.
    erise = clean(cut_keep(hwa_rise+[line(hwa_rise[-1][3],hwa_rise[0][0])],0,400,'low'))
    hwe = [fu, selected_join(erise,e,(35,45),(45,35))]

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

    # Keep the rising native tsu crown and scale the whole bowl uniformly.
    # Separate tangent handles leave an open inner radius at the left turn.
    body_weight, vowel_weight = ((850, 850) if fuller else (800, 800)) if bold else ((600, 600) if fuller else (550, 550))
    def flowing_sweep(ch):
        # The tsu entry rises into its full native crown. Neither the crown
        # nor the bowl is flattened into a horizontal connecting belt.
        head = clean(cut_keep(ring(ch),1,(190 if fuller else 210) if ch=='と' else (150 if fuller else 170),'high'))
        head = move(head,.90 if ch=='と' else .86,.75,
                    5 if ch=='と' else 25,230 if ch=='と' else 130)
        r = ring('つ')
        cuts = sorted(O.crossings(r,0,385 if fuller else 425),
                      key=lambda c: O.point(r[c[0]],c[1])[1])[-2:]
        tail = max((O.arc(r,*cuts),O.arc(r,*cuts[::-1])),
                   key=lambda a: max(p[0] for seg in a for p in seg))
        scale = (.52 if fuller else .50) if ch=='を' else (.72 if fuller else .68)
        tail = move(clean(tail),scale,scale,250 if ch=='を' else 130,-25 if ch=='を' else -38)
        return selected_join(head,tail,(100,80) if ch=='と' else (70,60),
                             (100,100) if ch=='と' else (70,80))
    tu = [native('と', 1, (250, 380, 450, 774)), flowing_sweep('と')]
    wu = [native('を', 1, (214, 220, 530, 797)),
          native('を', 2, bounds([approved['WU'][1]])), flowing_sweep('を')]
    # Shorten the two straight sides above wo's native terminal. The arch,
    # entry and rounded cap retain their native outlines.
    stem=wu[0]
    assert len(stem)==49, 'Native wo stem contour layout changed'
    body=stem[5:44]
    cap=move(stem[47:]+stem[:2],dy=115)
    wu[0]=selected_join(body,cap,(20,20),(8,8))
    result = dict(TU=tu, TI=ti, KWA=kwa, KWI=kwi, KWE=kwe,
                  HWA=hwa, HWI=hwi, HWE=hwe, WU=wu, TSI=tsi)
    if not bold:
        # Retain the accepted Regular forms outside the requested revisions.
        for label in ('TI', 'HWI'):
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
        hwi_body = approved['HWI'][1][23:-1]
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
