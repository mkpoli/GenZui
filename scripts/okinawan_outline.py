"""Vector outline editing for the Okinawan letters: cubic contours, cutting a contour
where a line crosses it, taking the arc between two cuts, and joining edges with
curves that leave and arrive along the edges' own directions.
"""
import numpy as np
from fontTools.pens.recordingPen import RecordingPen


def rings(pen):
    """Contours of a pen as lists of cubic segments (quadratics raised exactly)."""
    out, cur, start, last = [], [], None, None
    for op, args in pen.value:
        if op == 'moveTo':
            cur, start, last = [], np.array(args[0], float), np.array(args[0], float)
        elif op == 'lineTo':
            p = np.array(args[0], float)
            cur.append((last, last + (p - last) / 3, last + 2 * (p - last) / 3, p)); last = p
        elif op == 'curveTo':
            c1, c2, p = (np.array(a, float) for a in args)
            cur.append((last, c1, c2, p)); last = p
        elif op == 'qCurveTo':
            pts = [np.array(a, float) for a in args]
            if args[-1] is None:
                pts = pts[:-1]
            offs, end = pts[:-1], pts[-1]
            for i, q in enumerate(offs):
                nxt = end if i == len(offs) - 1 else (q + offs[i + 1]) / 2
                cur.append((last, last + 2 * (q - last) / 3, nxt + 2 * (q - nxt) / 3, nxt)); last = nxt
        elif op in ('closePath', 'endPath'):
            if np.linalg.norm(last - start) > 1e-6:
                cur.append((last, last + (start - last) / 3, last + 2 * (start - last) / 3, start))
            out.append(cur)
    return out


def point(seg, t):
    p0, c1, c2, p3 = seg; mt = 1 - t
    return mt**3 * p0 + 3 * mt**2 * t * c1 + 3 * mt * t**2 * c2 + t**3 * p3


def tangent(seg, t):
    p0, c1, c2, p3 = seg; mt = 1 - t
    d = 3 * mt**2 * (c1 - p0) + 6 * mt * t * (c2 - c1) + 3 * t**2 * (p3 - c2)
    return d / (np.linalg.norm(d) + 1e-12)


def split(seg, t):
    p0, c1, c2, p3 = seg
    a = p0 + (c1 - p0) * t; b = c1 + (c2 - c1) * t; c = c2 + (p3 - c2) * t
    d = a + (b - a) * t; e = b + (c - b) * t; f = d + (e - d) * t
    return (p0, a, d, f), (f, e, c, p3)


def crossings(ring, axis, value):
    """(segment index, t) where the ring crosses the line coordinate[axis] == value."""
    out = []
    for i, seg in enumerate(ring):
        ts = np.linspace(0, 1, 201)
        v = np.array([point(seg, t)[axis] for t in ts]) - value
        for j in np.nonzero(np.sign(v[:-1]) != np.sign(v[1:]))[0]:
            lo, hi = ts[j], ts[j + 1]
            for _ in range(40):
                mid = (lo + hi) / 2
                if np.sign(point(seg, mid)[axis] - value) == np.sign(v[j]):
                    lo = mid
                else:
                    hi = mid
            out.append((i, (lo + hi) / 2))
    return out


def arc(ring, a, b):
    """The part of a ring from cut a to cut b, following the ring's direction."""
    (ia, ta), (ib, tb) = a, b
    n = len(ring)
    segs = []
    first = split(ring[ia], ta)[1]
    if ia == ib and tb > ta:
        return [split(first, (tb - ta) / (1 - ta))[0]]
    segs.append(first)
    i = (ia + 1) % n
    while i != ib:
        segs.append(ring[i]); i = (i + 1) % n
    segs.append(split(ring[ib], tb)[0])
    return segs


def hermite(p0, t0, p1, t1, k=0.4):
    """A cubic from p0 leaving along t0 to p1 arriving along t1."""
    d = np.linalg.norm(p1 - p0) * k
    return (p0, p0 + t0 * d, p1 - t1 * d, p1)


def transform(segs, m, off):
    m = np.array(m, float); off = np.array(off, float)
    return [tuple(m @ p + off for p in s) for s in segs]


def draw(segs_list):
    pen = RecordingPen()
    for segs in segs_list:
        pen.moveTo(tuple(segs[0][0]))
        for s in segs:
            pen.curveTo(tuple(s[1]), tuple(s[2]), tuple(s[3]))
        pen.closePath()
    return pen
