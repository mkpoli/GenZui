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

    # Retain the native i bowl and shorten only the flick above its waist.
    def short_i(ref):
        r = ring('い', ref=ref)
        # The cut meets both native hook edges, leaving their curvature intact.
        r = cut_keep(r, 1, 420, 'low')
        return clean(r)
    i = fit(short_i(False), short_i(True), (605, 40, 768, 375))
    # A diagonal cut removes the long original flick without rounding its tip.
    # Clip its upper end in the right-hand hook zone, using exact subdivisions.
    def trim_hook(r):
        # i's hook lives right of x700; cap at y215, clear of the outer bowl.
        cuts = [c for c in O.crossings(r, 1, 215)
                if O.point(r[c[0]], c[1])[0] > 705]
        if len(cuts) == 2:
            a = max((O.arc(r, *cuts), O.arc(r, *cuts[::-1])),
                    key=lambda s: max((p[1] for seg in s for p in seg if p[0] < 705), default=-1000))
            return a + [line(a[-1][3], a[0][0])]
        return r
    # Trimming a closed stem is followed by reopening its attachment.
    i = trim_hook(i + [line(i[-1][3], i[0][0])])
    i = clean(cut_keep(i, 1, 365, 'low')) if np.linalg.norm(i[0][0]-i[-1][3]) < 1e-5 else i
    hwi = [fu, guide_join(rise, i, approved['HWI'][1], not fuller), native('い', 1, (765.48, 68, 924.52, 341.6))]

    # The actual wa contours keep their native bowl/terminal contrast.
    from scipy.interpolate import PchipInterpolator
    wa_x = PchipInterpolator([73, 290, 430, 700, 950], [600, 685, 775, 860, 980])
    def hwa_map(r):
        out = []
        for seg in r:
            pieces = [seg]
            for _ in range(3):
                pieces = [part for s in pieces for part in O.split(s, .5)]
            out.extend(tuple(np.array([float(wa_x(p[0])), .49*p[1]+25]) for p in s)
                       for s in pieces)
        return out
    wa_font = vowel_source((900 if fuller else 850) if bold else (600 if fuller else 550))
    wa_rings = [O.rings(contours(wa_font, ord('わ'), [n]))[0] for n in range(3)]
    wa_stem = hwa_map(cut_keep(wa_rings[2], 1, 570, 'low'))
    # Extend the stem to the approved shoulder height. All native wa seams
    # below it share one map, preserving the small counter and bowl connection.
    top = 370
    first, last = wa_stem[0][0], wa_stem[-1][3]
    tf, tl = O.tangent(wa_stem[0], 0), O.tangent(wa_stem[-1], 1)
    q = first + tf * ((top-first[1])/tf[1])
    p = last + tl * ((top-last[1])/tl[1])
    wa_stem = [line(q, first)] + wa_stem + [line(last, p)]
    hwa = [fu, guide_join(rise, wa_stem, approved['HWA'][1], not fuller),
           hwa_map(wa_rings[0]), hwa_map(wa_rings[1])]

    # e keeps a complete native arch and terminal. A shear straightens its
    # diagonal; a uniform vertical fit lowers the arch without local warping.
    def e_lower(ref):
        r = ring('え', ref=ref)
        cuts = sorted(O.crossings(r, 1, 380), key=lambda c: O.point(r[c[0]], c[1])[0])[-2:]
        return min((O.arc(r, *cuts), O.arc(r, *cuts[::-1])), key=lambda a: min(p[1] for seg in a for p in seg))
    e = fit(e_lower(False), e_lower(True), (598, 20, 930, 365))
    e = O.transform(e, np.array([[1, -.20], [0, 1]]), (4, 0))
    e = move(e, 1, 1, 32, 0)
    hwe = [fu, guide_join(rise, e, approved['HWE'][1], not fuller, outer_end=28)]

    # Native optical weights compensate for the compressed vowel components.
    body_weight, vowel_weight = ((850, 900) if fuller else (800, 850)) if bold else ((600, 650) if fuller else (550, 600))
    kwi_i = native('ぃ', 0, (475, -78, 620, 291), (1, 375, 'low'))
    kwi_i = move(kwi_i, 1, .90, -30, -9.4)
    upper = ku('KWI')
    upper = clean(cut_keep(upper + [line(upper[-1][3], upper[0][0])], 1, 335, 'high'))
    donor = [tuple(reversed(s)) for s in reversed(approved['KWI'][0][31:36])]
    kwi_join = upper + native_turn(donor, upper, kwi_i) + kwi_i + [bridge(kwi_i, upper, .27)]
    kwi = [kwi_join, native('ぃ', 1, bounds([approved['KWI'][-1]]))]
    body_weight, vowel_weight = ((700, 850) if fuller else (700, 800)) if bold else ((550, 600) if fuller else (500, 550))
    fx = PchipInterpolator([92, 360, 915], [229, 495, 872])
    fy = PchipInterpolator([-48, 536], [-64, 339])
    def wa_placement(r):
        out = []
        for seg in r:
            pieces = [seg]
            for _ in range(2):
                pieces = [part for s in pieces for part in O.split(s, .5)]
            out.extend(tuple(np.array([float(fx(p[0])), float(fy(p[1]))]) for p in s)
                       for s in pieces)
        return out
    kwa_stem = wa_placement(cut_keep(ring('わ', 2), 1, 400, 'low'))
    kwa = [selected_join(ku('KWA'), kwa_stem, (14,24) if fuller else (8,20), (23,26) if fuller else (20,24)), wa_placement(ring('わ', 1)),
           move(ring('わ', 0), .67, .67, 495-356*.67, 339-536*.67)]
    body_weight, vowel_weight = ((850, 900) if fuller else (800, 850)) if bold else ((600, 650) if fuller else (550, 600))
    kwe_lower = fit(e_lower(False), e_lower(True), (203, -64, 847, 286))
    upper = ku('KWE')
    target = (upper[0][0][0]+upper[-1][3][0])/2 + 35
    current = (kwe_lower[0][0][0]+kwe_lower[-1][3][0])/2
    shear = (target-current)/(286+64)
    kwe_lower = O.transform(kwe_lower, np.array([[1, shear], [0, 1]]), (64*shear, 0))
    kwe_lower = move(kwe_lower, 1, .925, 0, -4.8)
    kwe = [upper + [bridge(upper, kwe_lower)] + kwe_lower + [O.fair(kwe_lower[-1][3], O.tangent(kwe_lower[-1], 1), O.curvature(kwe_lower[-1], 1), upper[0][0], O.tangent(upper[0], 0), O.curvature(upper[0], 0))]]

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
    body_weight, vowel_weight = ((850, 900) if fuller else (800, 850)) if bold else ((550, 650) if fuller else (500, 600))
    def tsu_arc(ref):
        r = ring('つ', ref=ref)
        cuts = sorted(O.crossings(r, 0, 470 if fuller else 450), key=lambda c: O.point(r[c[0]], c[1])[1])[:2]
        return max((O.arc(r, *cuts), O.arc(r, *cuts[::-1])), key=lambda a: max(p[1] for seg in a for p in seg))
    tsu_top = fit(tsu_arc(False), tsu_arc(True), (118, 294, 882, 690))
    tsi_i = native('ぃ', 0, (380, 19, 555, 280), (1, 375, 'low'))
    tsi_i = move(tsi_i, 1, .94, -25, .48)
    # The approved turn is an affine guide; native Bold edges set its width.
    turn=ring('て', ref=True)[39:44]
    tsi_join=tsu_top+native_turn(turn,tsu_top,tsi_i)+tsi_i+native_turn(turn,tsi_i,tsu_top)
    tsi = [tsi_join, move(native('ぃ', 1, bounds([approved['TSI'][-1]])), 1, 1, 0, -25)]

    # Native to/wo entries feed native tsu bowls. Horizontal sweeps retain
    # the Bold master's thin edge instead of receiving a contour offset.
    body_weight, vowel_weight = ((850, 850) if fuller else (800, 800)) if bold else ((600, 600) if fuller else (550, 550))
    def flowing(ch, index, box):
        def recipe(ref):
            r = ring(ch, index, ref)
            if ch == 'と':
                head = move(O.arc(r, (1, .55), (32, 0)), 1, .6, -5, 300)
                tail = O.arc(ring('つ', ref=ref), (29, 0), (7, 0))
                fy = PchipInterpolator([35,150,390,640], [-12,62,155,347])
                tail = [tuple(np.array([.88*p[0]+5, float(fy(p[1]))]) for p in seg) for seg in tail]
                head = [tuple(np.array([p[0], p[1]-50*np.clip((p[1]-420)/200,0,1)]) for p in seg) for seg in head]
            else:
                fy = PchipInterpolator([-53, 100, 551], [190, 275, 570])
                head = [tuple(np.array([.87*p[0]+1, float(fy(p[1]))]) for p in seg)
                        for seg in O.arc(r, (1, .55), (33, 0))]
                tail = O.arc(ring('つ', ref=ref), (29, 0), (7, 0))
                fy = PchipInterpolator([35,135,390,640], [-27,30,105,253])
                tail = [tuple(np.array([.87*p[0]-2, float(fy(p[1]))]) for p in seg) for seg in tail]
            return rounded_join(clean(head), clean(tail), 1.02 if fuller else .98)
        return fit(recipe(False), recipe(True), box)
    tu = [native('と', 1, bounds([approved['TU'][0]])),
          flowing('と', 0, bounds([approved['TU'][1]]))]
    wu = [native('を', 1, bounds([approved['WU'][0]])),
          native('を', 2, bounds([approved['WU'][1]])),
          flowing('を', 0, bounds([approved['WU'][2]]))]
    result = dict(TU=tu, TI=ti, KWA=kwa, KWI=kwi, KWE=kwe,
                  HWA=hwa, HWI=hwi, HWE=hwe, WU=wu, TSI=tsi)
    if not bold:
        # Retain the accepted Regular forms outside the requested revisions.
        for label in ('TI', 'HWI', 'HWE'):
            result[label] = approved[label]
        # Use the approved fu body and shoulder with the new native wa map.
        result['HWA'][0] = approved['HWA'][0]
    # Match native entry heights without moving the baseline or the lower join.
    for label, donor, hinge in (('KWA','く',300), ('KWI','く',300), ('KWE','く',300),
                               ('TU','と',350), ('WU','を',350), ('TSI','つ',280)):
        target = round(bounds(O.rings(contours(body_source(700 if bold else 400), ord(donor))))[3])
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
