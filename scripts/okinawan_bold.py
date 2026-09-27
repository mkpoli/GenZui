"""Compose Bold ligatures from Noto Serif JP's actual weight-700 contours.

Affine placement is measured against the Regular donor. It is then applied to
Bold, so the weight master's thin terminals and heavy bowls remain intact.
Only connecting curves and the small HWI hook cut are newly drawn.
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


@lru_cache(maxsize=1)
def body_source():
    from serif import instance
    return instance('NotoSerifJP', 700, set(map(ord, 'ふくてとつを')))


@lru_cache(maxsize=2)
def vowel_source(weight):
    from serif import instance
    return instance('NotoSerifJP', weight, set(map(ord, 'いぃわえ')))


def drawings(font, contours, vowel_weight=750):
    regular = reference()
    approved = _approved()

    def ring(ch, index=0, ref=False):
        donor = regular if ref else vowel_source(vowel_weight) if ch in 'いぃわえ' else body_source()
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
    hwi = [fu, join(rise, i), native('い', 1, (765.48, 68, 924.52, 341.6))]

    # The actual wa contours keep their native bowl/terminal contrast.
    from scipy.interpolate import PchipInterpolator
    wa_x = PchipInterpolator([73, 360, 950], [620, 710, 980])
    def hwa_map(r):
        out = []
        for seg in r:
            pieces = [seg]
            for _ in range(3):
                pieces = [part for s in pieces for part in O.split(s, .5)]
            out.extend(tuple(np.array([float(wa_x(p[0])), .60*p[1]+28.8]) for p in s)
                       for s in pieces)
        return out
    wa_stem = hwa_map(cut_keep(ring('わ', 2), 1, 570, 'low'))
    hwa = [fu, join(rise, wa_stem), hwa_map(ring('わ', 1)), hwa_map(ring('わ', 0))]

    # e keeps a complete native arch and terminal. A shear straightens its
    # diagonal; a uniform vertical fit lowers the arch without local warping.
    def e_lower(ref):
        r = ring('え', ref=ref)
        cuts = sorted(O.crossings(r, 1, 380), key=lambda c: O.point(r[c[0]], c[1])[0])[-2:]
        return min((O.arc(r, *cuts), O.arc(r, *cuts[::-1])), key=lambda a: min(p[1] for seg in a for p in seg))
    e = fit(e_lower(False), e_lower(True), (598, 20, 930, 365))
    e = O.transform(e, np.array([[1, -.20], [0, 1]]), (4, 0))
    e = move(e, 1, 1, 32, 0)
    hwe = [fu, join(rise, e)]

    kwi_i = native('ぃ', 0, (475, -78, 620, 291), (1, 375, 'low'))
    kwi_i = move(kwi_i, 1, .90, -30, -9.4)
    kwi = [join(ku('KWI'), kwi_i), native('ぃ', 1, bounds([approved['KWI'][-1]]))]
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
    kwa = [join(ku('KWA'), kwa_stem), wa_placement(ring('わ', 1)),
           move(ring('わ', 0), .67, .67, 495-356*.67, 339-536*.67)]
    kwe_lower = fit(e_lower(False), e_lower(True), (203, -64, 847, 286))
    upper = ku('KWE')
    target = (upper[0][0][0]+upper[-1][3][0])/2 + 35
    current = (kwe_lower[0][0][0]+kwe_lower[-1][3][0])/2
    shear = (target-current)/(286+64)
    kwe_lower = O.transform(kwe_lower, np.array([[1, shear], [0, 1]]), (64*shear, 0))
    kwe_lower = move(kwe_lower, 1, .925, 0, -4.8)
    kwe = [join(upper, kwe_lower)]

    te = native('て', 0, (107, 225, 882, 718), (1, 250, 'high'))
    ti_i = native('ぃ', 0, (415, -10, 612, 195), (1, 375, 'low'))
    ti = [join(te, ti_i), native('ぃ', 1, bounds([approved['TI'][-1]]))]
    def tsu_arc(ref):
        r = ring('つ', ref=ref)
        cuts = sorted(O.crossings(r, 0, 410), key=lambda c: O.point(r[c[0]], c[1])[1])[:2]
        return max((O.arc(r, *cuts), O.arc(r, *cuts[::-1])), key=lambda a: max(p[1] for seg in a for p in seg))
    tsu_top = fit(tsu_arc(False), tsu_arc(True), (118, 294, 882, 690))
    tsi_i = native('ぃ', 0, (380, 19, 555, 280), (1, 375, 'low'))
    tsi_i = move(tsi_i, 1, .94, -25, .48)
    tsi = [join(tsu_top, tsi_i), move(native('ぃ', 1, bounds([approved['TSI'][-1]])), 1, 1, 0, -25)]

    # Native to/wo entries feed native tsu bowls. Horizontal sweeps retain
    # the Bold master's thin edge instead of receiving a contour offset.
    def flowing(ch, index, box):
        def recipe(ref):
            r = ring(ch, index, ref)
            if ch == 'と':
                head = move(O.arc(r, (1, 0), (32, 0)), 1, .6, -5, 300)
                tail = move(O.arc(ring('つ', ref=ref), (28, 0), (9, 0)), .88, .563, 5, -12.7)
            else:
                from scipy.interpolate import PchipInterpolator
                fy = PchipInterpolator([-53, 100, 551], [190, 275, 570])
                head = [tuple(np.array([.87*p[0]+1, float(fy(p[1]))]) for p in seg)
                        for seg in O.arc(r, (1, 0), (33, 0))]
                tail = move(O.arc(ring('つ', ref=ref), (28, 0), (9, 0)), .87, .463, -2, -43)
            return join(clean(head), clean(tail))
        return fit(recipe(False), recipe(True), box)
    tu = [native('と', 1, bounds([approved['TU'][0]])),
          flowing('と', 0, bounds([approved['TU'][1]]))]
    wu = [native('を', 1, bounds([approved['WU'][0]])),
          native('を', 2, bounds([approved['WU'][1]])),
          flowing('を', 0, bounds([approved['WU'][2]]))]
    result = dict(TU=tu, TI=ti, KWA=kwa, KWI=kwi, KWE=kwe,
                  HWA=hwa, HWI=hwi, HWE=hwe, WU=wu, TSI=tsi)
    return {int(g['codepoint'], 16): [O.draw([r]) for r in result[g['label']]]
            for g in source()['glyphs']}
