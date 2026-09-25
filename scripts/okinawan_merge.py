"""Okinawan letters made by merging an added stroke into a Noto kana's outline.

The kana keeps Noto Serif JP's outline. The added stroke is the top of a Noto
stroke, and the two become one contour: the kana's stroke is cut where the
added stroke meets it, the added stroke is cut above the meeting, and two new
curves join their edges, each leaving and arriving along the edges' own
directions. Only those two curves are new drawing.
"""
import numpy as np
import okinawan_outline as O

# Parameters of the glottal YA merge, with their defaults.
YA_DEFAULTS = dict(
    shift=75,        # や moves right to make room for the mark
    arm_cut=289,     # x (before the shift) where や's arm loses its head
    mark_cut=480,    # y where the mark (は's left stroke) is cut
    mark_x=0,        # horizontal offset of the mark
    mark_dy=0,       # vertical offset of the mark
    mark_len=1.0,    # length of the mark above the cut, along the stroke
    outer_full=1.0,  # fullness of the outer turn, relative to the fairest curve
    inner_full=1.0,  # fullness of the inner corner, relative to the fairest curve
    neck_w=1.0,      # width of the mark where it enters the turn
    head_w=1.0,      # width of the mark from its widest point up through the head
    mark_angle=0.0,  # degrees the mark turns about where it enters the turn; positive leans it left
)

# The form GenZui ships, chosen in the arena (research/okinawan-arena/glottal-ya):
# rounds 1-2 culled and compared samples, rounds 3-5 moved one factor at a time
# from the round-2 leader (position, cut, widths, turn, angle).
YA = dict(YA_DEFAULTS, shift=32, arm_cut=299, mark_cut=452, mark_x=-75, mark_dy=-2, mark_len=0.974,
          outer_full=1.102, inner_full=0.829, neck_w=1.0, head_w=0.9, mark_angle=-4.0)

HEAD_Y = 620         # height where は's left stroke is widest, below its head


def _reverse(segs):
    return [(s[3], s[2], s[1], s[0]) for s in reversed(segs)]


def _moved(segs, dx=0, dy=0):
    return O.transform(segs, np.eye(2), (dx, dy))


def _widened(segs, cut, neck, head, head_y=HEAD_Y):
    """The mark with its width scaled about its centre line: `neck` at the cut,
    `head` from head_y up, varying linearly in between."""
    c0, c1 = centre_at(segs, cut), centre_at(segs, head_y)
    def move(q):
        u = min(1, max(0, (q[1] - cut) / (head_y - cut)))
        cx, k = c0 + (c1 - c0) * u, neck + (head - neck) * u
        return np.array([cx + (q[0] - cx) * k, q[1]])
    return [tuple(move(np.asarray(q, float)) for q in seg) for seg in segs]


def _turned(segs, cut, degrees):
    """The mark turned about the middle of its cut."""
    xs = sorted(O.point(segs[i], t)[0] for i, t in O.crossings(segs, 1, cut))
    pivot = np.array([(xs[0] + xs[1]) / 2, cut])
    a = np.radians(degrees)
    m = np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]])
    return O.transform(segs, m, pivot - m @ pivot)


def glottal_ya(font, contours, **params):
    """や with the glottal mark merged into the head of its arm."""
    p = {**YA_DEFAULTS, **params}
    ring = lambda ch, i: O.rings(contours(font, ord(ch), [i]))[0]
    arm = _moved(ring('や', 1), p['shift'])
    rest = _moved(ring('や', 0), p['shift'])
    mark = _widened(ring('は', 1), p['mark_cut'], p['neck_w'], p['head_w'])
    mark = _turned(mark, p['mark_cut'], p['mark_angle'])
    # lengthen or shorten the mark above its cut, along its length only
    m = np.array([[1, 0], [0, p['mark_len']]])
    mark = O.transform(mark, m, (p['mark_x'], p['mark_cut'] * (1 - p['mark_len']) + p['mark_dy']))
    cut_y = p['mark_cut'] + p['mark_dy']

    cx = O.crossings(arm, 0, p['arm_cut'] + p['shift'])
    body = max((O.arc(arm, cx[0], cx[1]), O.arc(arm, cx[1], cx[0])),
               key=lambda s: max(q[0] for seg in s for q in seg))   # the piece reaching furthest right
    cy = sorted(O.crossings(mark, 1, cut_y), key=lambda c: O.point(mark[c[0]], c[1])[0])[:2]
    top = max((O.arc(mark, cy[0], cy[1]), O.arc(mark, cy[1], cy[0])),
              key=lambda s: max(q[1] for seg in s for q in seg))    # the piece holding the head

    P, Q = body[0][0], body[-1][3]
    tP, tQ = -O.tangent(body[0], 0), O.tangent(body[-1], 1)
    kQ = O.curvature(body[-1], 1)
    upper_is_Q = Q[1] > P[1]
    R, L = top[0][0], top[-1][3]
    if (R[0] > L[0]) != upper_is_Q:
        top = _reverse(top)
        R, L = top[0][0], top[-1][3]
    tR, tL = -O.tangent(top[0], 0), O.tangent(top[-1], 1)
    kL = O.curvature(top[-1], 1)
    # inner corner and outer turn: fair curves that meet the Noto edges with
    # their direction and curvature, taken in the direction the outline runs
    inner = O.fair(Q, tQ, kQ, R, -tR, O.curvature(top[0], 0), p['inner_full'])
    outer = [O.fair(L, tL, kL, P, -tP, O.curvature(body[0], 0), p['outer_full'])]
    return O.draw([body + [inner] + top + outer, rest])


# Glottal YU, YO and N: in Funatsu's chart the mark stands free beside the
# kana. For YU and YO it is the same stroke as YA's mark, drawn whole down to
# its foot; the kana is Noto's own, narrowed only as far as the mark needs
# room, and the pair is centred in the em.
BESIDE_DEFAULTS = dict(
    mark_char='は',    # the Noto stroke used as the mark: character and contour
    mark_index=1,
    ramp_lo=YA['mark_cut'],  # heights between which the mark's width passes from neck_w to head_w
    ramp_hi=HEAD_Y,
    mark_lie=False,          # the stroke lies flat: widths, bow and slant work across it
    kana_anchor='right',     # the kana is scaled toward this side, away from the mark,
                             # or for 'bottom' toward the middle of its foot
    mark_len=0.9,      # height of the mark relative to は's left stroke, from its foot
    mark_scale=0.85,   # size of the whole mark, about its foot
    gap=60,            # closest distance between the mark and the kana
    mark_dy=60,        # vertical offset of the mark
    mark_angle=1.5,    # degrees the mark turns; positive leans it left
    mark_bend=0,       # units the middle of the mark bows sideways; positive to the right
    mark_slant=0,      # units the top of the mark moves sideways over the foot
    head_angle=0,      # degrees the mark's head turns on its own; positive counterclockwise
    tail_angle=0,      # the same for its tail
    neck_w=YA['neck_w'],
    head_w=YA['head_w'],
    kana_sx=0.88,      # horizontal scale of the kana, about its right edge
    kana_sy=0.97,      # vertical scale of the kana, about the middle of the body
    kana_bold=0,       # units of width added sideways to the kana's strokes, before it is scaled
    kana_dx=0,         # the kana moved after scaling; the letter is still centred as a whole
    kana_dy=0,
)


# The form GenZui ships, chosen in the arena (research/okinawan-arena/glottal-yu):
# two culls, then one factor at a time around the form the second cull kept.
YU = dict(BESIDE_DEFAULTS, mark_len=0.838, mark_scale=0.864, gap=38, mark_dy=148, mark_angle=4.875,
          neck_w=1.0, head_w=0.9, kana_sx=0.812, kana_sy=0.981, kana_bold=9.852)

# YO, placed by hand in the arena (research/okinawan-arena/glottal-yo): the
# mark sits high over よ's loop, as in Funatsu's chart.
YO = dict(BESIDE_DEFAULTS, mark_x=-51, mark_dy=300, mark_scale=0.884, mark_len=0.698, mark_angle=4.875,
          neck_w=1.2, head_w=1.1, kana_sx=0.92, kana_sy=0.98, kana_bold=8.696)

# N: い's falling stroke at the upper right of ん, where the earlier drawing
# put it.
N_DEFAULTS = dict(BESIDE_DEFAULTS, mark_char='い', mark_index=1, ramp_lo=300, ramp_hi=500, kana_anchor='left',
                  mark_scale=0.658, mark_len=1.0, mark_angle=0.0, neck_w=1.0, head_w=1.0,
                  kana_sx=1.0, kana_sy=1.0, kana_bold=0, mark_x=-21, mark_dy=214)

# N as placed by hand in the arena (research/okinawan-arena/glottal-n).
N = dict(N_DEFAULTS, mark_x=-11, mark_dy=144, mark_scale=0.658, mark_len=1.04, neck_w=1.3, head_w=1.25,
         mark_angle=-4.0, mark_bend=-20)

# WI and WE: こ's upper stroke as a dot above ゐ and ゑ, shrunk evenly under it,
# where the earlier drawing put them.
W_DEFAULTS = dict(BESIDE_DEFAULTS, mark_char='こ', mark_index=1, mark_lie=True, ramp_lo=-650, ramp_hi=-350,
                  kana_anchor='bottom', kana_sx=0.88, kana_sy=0.88, kana_bold=0, mark_scale=0.64, mark_len=1.0,
                  mark_angle=0.0, neck_w=1.0, head_w=1.0, mark_x=-24, mark_dy=252)

# WI as placed by hand in the arena (research/okinawan-arena/glottal-wi); WE
# and WA start from the same dot.
WI = dict(W_DEFAULTS, mark_x=-44, mark_dy=242, mark_scale=0.66, mark_len=0.84, mark_angle=-8.0, mark_bend=20,
          neck_w=1.45, head_w=1.45, kana_sx=0.88, kana_sy=0.88, kana_bold=9.091)

# WE as placed by hand (research/okinawan-arena/glottal-we): WI's dot, lower,
# over a shorter ゑ.
WE = dict(WI, mark_x=-34, mark_dy=172, kana_sy=0.8)

# WA as placed by hand (research/okinawan-arena/glottal-wa): WI's dot over a
# shorter, heavier body.
WA = dict(WI, kana_sy=0.86, kana_bold=14)

# SI: ぃ's second stroke, lengthened, standing to the right of す, where the
# earlier drawing put it.
SI_DEFAULTS = dict(BESIDE_DEFAULTS, mark_char='ぃ', mark_index=1, ramp_lo=200, ramp_hi=350, kana_anchor='left',
                   mark_scale=1.0, mark_len=1.627, mark_angle=0.0, neck_w=1.0, head_w=1.0,
                   kana_sx=0.9, kana_sy=1.0, kana_bold=0, mark_x=200, mark_dy=-109)

# SI as placed by hand in the arena (research/okinawan-arena/si).
SI = dict(SI_DEFAULTS, mark_x=80, mark_dy=-119, mark_scale=0.88, mark_len=1.607, mark_angle=-10.0, mark_bend=10)


def _widen_strokes(rings, d):
    """Each stroke made wider by d, sideways only: the outline swept along a
    horizontal segment, which restores what narrowing took from upright strokes
    and leaves level strokes as they are."""
    import pathops
    if d <= 0:
        return rings
    # Noto draws some kana as one self-crossing contour; resolve it first so
    # the counters stay open when the copies are united
    base = pathops.Path()
    O.draw(rings).replay(base.getPen())
    base.simplify(fix_winding=True, keep_starting_points=False)
    # Skia can fail, or worse, return a wrong outline without complaint, so
    # every result is checked: it must cover the kana, and grow it by no more
    # than the sweep can (d times the outline's height, both sides counted).
    def area(path):
        from fontTools.pens.areaPen import AreaPen
        pen = AreaPen(); path.draw(pen)
        return abs(pen.value)
    ys = [q[1] for r in rings for seg in r for q in seg]
    limit = area(base) + d * 2 * sum(abs(seg[3][1] - seg[0][1]) for r in rings for seg in r) / 2 + 1
    def sound(shape):
        try:
            missing = area(pathops.op(base, shape, pathops.PathOp.DIFFERENCE))
        except pathops.PathOpsError:
            return False
        return missing < 1 and area(base) <= area(shape) <= limit
    # Copies about 2 units apart (closer ones leave near-coincident edges Skia
    # cannot resolve); a count that fails is followed by its neighbours, and
    # each count is tried as one nonzero pass and as a chain of unions.
    def one_pass(count, jitter=0):
        shape = pathops.Path()
        for dx in np.linspace(-d / 2, d / 2, count) + jitter:
            base.transform(1, 0, 0, 1, dx, 0).draw(shape.getPen())
        shape.simplify(fix_winding=True, keep_starting_points=False)
        return shape
    def chained(count, jitter=0):
        shape = pathops.Path()
        for dx in np.linspace(-d / 2, d / 2, count) + jitter:
            shape = pathops.op(shape, base.transform(1, 0, 0, 1, dx, 0), pathops.PathOp.UNION, fix_winding=True)
        return shape
    # a last resort shifts every copy by a fraction of a unit, off the
    # coincidences that defeat Skia
    n = int(np.ceil(d / 2)) + 1
    for count, jitter in [*((c, 0) for c in [*range(n, n + 6), *range(n - 1, 1, -1)]),
                          *((c, j) for j in (0.13, 0.29, 0.47) for c in range(n, n + 3))]:
        for method in (one_pass, chained):
            try:
                shape = method(count, jitter)
            except pathops.PathOpsError:
                continue
            if sound(shape):
                break
        else:
            continue
        break
    else:
        raise ValueError(f'cannot widen the strokes by {d}')
    pen = O.RecordingPen(); shape.draw(pen)
    return O.rings(pen)


LIE = np.array([[0, 1], [-1, 0]])      # a lying stroke turned upright: (x, y) -> (y, -x)


def upright_mark(font, contours, p):
    """The mark's Noto stroke, stood upright if it lies."""
    mark = O.rings(contours(font, ord(p['mark_char']), [p['mark_index']]))[0]
    return O.transform(mark, LIE, (0, 0)) if p['mark_lie'] else mark


def centre_at(segs, y):
    """The middle of a stroke where a level line crosses it."""
    xs = sorted(O.point(segs[i], t)[0] for i, t in O.crossings(segs, 1, y))
    return (xs[0] + xs[1]) / 2


def wa_body(font, contours):
    """Glottal WA's body: in the chart it is WI without the small inner loop.
    Lowered by 42, わ's loop runs on top of ゐ's along the bottom arc from
    x = 720 to 800 with the same width, so they join at x = 740: ゐ loses its
    small loop and the rest of its bottom, and わ supplies the end of the loop.
    Both edges are redrawn across the join so the two run into each other."""
    import pathops
    box = pathops.Path(); pen = box.getPen()
    pen.moveTo((410, -100)); pen.lineTo((740, -100)); pen.lineTo((740, 245)); pen.lineTo((410, 245)); pen.closePath()
    def path(rings):
        out = pathops.Path(); O.draw(rings).replay(out.getPen())
        out.simplify(fix_winding=True, keep_starting_points=False)
        return out
    top = pathops.op(path(O.rings(contours(font, ord('ゐ')))), box, pathops.PathOp.DIFFERENCE)
    bottom = pathops.op(path([_moved(O.rings(contours(font, ord('わ'), [0]))[0], dy=-42)]), box, pathops.PathOp.INTERSECTION)
    pen = O.RecordingPen(); pathops.op(top, bottom, pathops.PathOp.UNION).draw(pen)
    # Bold's wider inner loop pokes past the cut at x = 410 and leaves a
    # sliver there; any such crumb is dropped
    from fontTools.pens.areaPen import AreaPen
    def area(ring):
        a = AreaPen(); O.draw([ring]).replay(a)
        return abs(a.value)
    return _smooth_seam([r for r in O.rings(pen) if area(r) > 1000], 740, 35, (-100, 245))


def _smooth_seam(rings, x, half, ys):
    """Each edge crossing the splice at `x` (between heights `ys`) redrawn over
    x - half .. x + half as one fair curve meeting both sides with their own
    direction and curvature, so the two sources run into each other."""
    length = lambda segs: sum(np.linalg.norm(sg[3] - sg[0]) for sg in segs)
    y_of = lambda ring, c: O.point(ring[c[0]], c[1])[1]
    out = []
    for ring in rings:
        done = []                       # heights of the seams already redrawn
        while True:
            at = lambda v: [c for c in O.crossings(ring, 0, v) if ys[0] < y_of(ring, c) < ys[1]]
            pairs = [(a, b) for a in at(x - half) for b in at(x + half)
                     if abs(y_of(ring, a) - y_of(ring, b)) < 2 * half
                     and not any(abs(y_of(ring, a) - y) < 1 for y in done)]
            for a, b in sorted(pairs, key=lambda ab: abs(y_of(ring, ab[0]) - y_of(ring, ab[1]))):
                short, long = sorted((O.arc(ring, a, b), O.arc(ring, b, a)), key=length)
                if length(short) < 4 * half:    # the edge between the two cuts, not the rest of the letter
                    break
            else:
                break
            done.append(y_of(ring, a))
            end, start = long[-1], long[0]
            ring = long + [O.fair(end[3], O.tangent(end, 1), O.curvature(end, 1),
                                  start[0], O.tangent(start, 0), O.curvature(start, 0))]
        out.append(ring)
    return out


# bodies that are not one Noto kana, by the name the letters use for them
BODIES = {'ゐわ': wa_body}


def beside_pieces(font, contours, kana, p):
    """The mark at its widths, upright (a lying stroke is turned to stand, so
    its width runs across and its head is at the top), with the point it turns
    about; and the kana, sized and weighted, where it stays."""
    mark = _widened(upright_mark(font, contours, p), p['ramp_lo'], p['neck_w'], p['head_w'], p['ramp_hi'])
    xs = sorted(O.point(mark[i], t)[0] for i, t in O.crossings(mark, 1, p['ramp_lo']))
    pivot = ((xs[0] + xs[1]) / 2, p['ramp_lo'])
    body = BODIES[kana](font, contours) if kana in BODIES else O.rings(contours(font, ord(kana)))
    origin = kana_origin(body, p['kana_anchor'])
    # weight first, in the kana's own units, then the scaling: the sweep and
    # the scaling commute, so the weight is set in the kana's own units
    body = _widen_strokes(body, p['kana_bold'])
    sx, sy = p['kana_sx'], p['kana_sy']
    body = [O.transform(r, np.diag([sx, sy]), (origin[0] * (1 - sx) + p['kana_dx'], origin[1] * (1 - sy) + p['kana_dy']))
            for r in body]
    return mark, pivot, body


def kana_origin(body, anchor):
    """The point the kana is scaled about: the middle of the side away from
    the mark at mid-body height, or for 'bottom' the middle of its foot."""
    xs = [q[0] for r in body for seg in r for q in seg]
    ys = [q[1] for r in body for seg in r for q in seg]
    return {'right': (max(xs), 360), 'left': (min(xs), 360), 'bottom': ((min(xs) + max(xs)) / 2, min(ys))}[anchor]


def shaped(mark, pivot, p):
    """The mark turned about its pivot, bowed and slanted, laid back down if
    it lies, with the point it is sized about: its foot, level with its lowest
    point under its middle."""
    a = np.radians(p['mark_angle'])
    m = np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]])
    mark = O.transform(mark, m, np.array(pivot) - m @ np.array(pivot))
    ys = [q[1] for seg in mark for q in seg]
    y0, y1 = min(ys), max(ys)
    def bend(q):
        u = (q[1] - y0) / (y1 - y0)
        # bow: the middle moves sideways, the ends stay; slant: the top moves, the foot stays
        return np.array([q[0] + p['mark_bend'] * 4 * u * (1 - u) + p['mark_slant'] * u, q[1]])
    mark = [tuple(bend(np.asarray(q, float)) for q in seg) for seg in mark]
    # the head (top third) and tail (bottom third) turn on their own, fading in
    # from where they meet the middle, so each end can point a new way. Each
    # turns about the middle of the stroke's control points near that meeting.
    if p['head_angle'] or p['tail_angle']:
        pts = np.array([q for seg in mark for q in seg], float)
        h = (y1 - y0) / 3
        def centre(y):
            band = pts[np.abs(pts[:, 1] - y) <= h / 2]
            return np.array([(band[:, 0].min() + band[:, 0].max()) / 2 if len(band) else pts[:, 0].mean(), y])
        turns = [(np.radians(p['head_angle']), centre(y1 - h), lambda q: (q[1] - (y1 - h)) / h),
                 (np.radians(p['tail_angle']), centre(y0 + h), lambda q: ((y0 + h) - q[1]) / h)]
        def ends(q):
            for a, c, weight in turns:
                w = min(1, max(0, weight(q)))
                if a and w:
                    d = q - c
                    q = c + np.array([np.cos(a * w) * d[0] - np.sin(a * w) * d[1], np.sin(a * w) * d[0] + np.cos(a * w) * d[1]])
            return q
        mark = [tuple(ends(np.asarray(q, float)) for q in seg) for seg in mark]
    if p['mark_lie']:
        mark = O.transform(mark, LIE.T, (0, 0))
    foot = min(q[1] for seg in mark for q in seg)
    fx = sum(q[0] for seg in mark for q in seg) / (4 * len(mark))
    return mark, (fx, foot)


def sized(mark, origin, p):
    """The mark at its size and length, both about its foot, raised by mark_dy."""
    fx, foot = origin
    mark = O.transform(mark, np.eye(2) * p['mark_scale'], np.array([fx, foot]) * (1 - p['mark_scale']))
    return O.transform(mark, np.array([[1, 0], [0, p['mark_len']]]),
                       (0, foot * (1 - p['mark_len']) + p['mark_dy']))


def gap_shift(mark, body, gap):
    """How far to slide the mark sideways so its nearest point is `gap` from the kana."""
    ts = np.linspace(0, 1, 12)
    pts = lambda rs: np.array([O.point(seg, t) for r in rs for seg in r for t in ts])
    ms, ks = pts([mark]), pts(body)
    near = lambda dx: np.min(np.linalg.norm((ms + [dx, 0])[:, None] - ks[None], axis=2))
    lo, hi = -400.0, 200.0          # well clear of the kana .. inside it
    for _ in range(30):
        dx = (lo + hi) / 2
        lo, hi = (dx, hi) if near(dx) >= gap else (lo, dx)
    return lo


def glottal_beside(font, contours, kana, **params):
    """The glottal mark standing beside a Noto kana. The mark is placed by
    `mark_x` when given, otherwise by its gap to the kana."""
    p = {**BESIDE_DEFAULTS, **params}
    mark, pivot, body = beside_pieces(font, contours, kana, p)
    mark = sized(*shaped(mark, pivot, p), p)
    mark = _moved(mark, p['mark_x'] if p.get('mark_x') is not None else gap_shift(mark, body, p['gap']))
    # centre the letter in the em
    xs = [q[0] for r in [mark, *body] for seg in r for q in seg]
    dx = 500 - (min(xs) + max(xs)) / 2
    # two parts, each a whole shape, so the kana's counters stay open
    return [O.draw([_moved(mark, dx)]), O.draw([_moved(r, dx) for r in body])]
