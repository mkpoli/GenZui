"""Okinawan letters made by merging an added stroke into a Noto kana's outline.

The kana keeps Noto Serif JP's outline. The added stroke is the top of a Noto
stroke, and the two become one contour: the kana's stroke is cut where the
added stroke meets it, the added stroke is cut above the meeting, and two new
curves join their edges, each leaving and arriving along the edges' own
directions. Only those two curves are new drawing.
"""
import numpy as np
import okinawan_outline as O

# Parameters of the glottal YA merge, with their defaults. The arena samples
# around these.
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
    kana_anchor='right',     # the kana narrows toward this side, away from the mark;
                             # 'bottom' shrinks it evenly toward the middle of its foot
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
    kana_bold=0,       # units of width given back to the kana's strokes after narrowing
)


# The form GenZui ships, chosen in the arena (research/okinawan-arena/glottal-yu):
# two culls, then one factor at a time around the form the second cull kept.
YU = dict(BESIDE_DEFAULTS, mark_len=0.838, mark_scale=0.864, gap=38, mark_dy=148, mark_angle=4.875,
          neck_w=1.0, head_w=0.9, kana_sx=0.812, kana_sy=0.981, kana_bold=8)

# YO, placed by hand in the arena (research/okinawan-arena/glottal-yo): the
# mark sits high over よ's loop, as in Funatsu's chart.
YO = dict(BESIDE_DEFAULTS, mark_x=-51, mark_dy=300, mark_scale=0.884, mark_len=0.698, mark_angle=4.875,
          neck_w=1.2, head_w=1.1, kana_sx=0.92, kana_sy=0.98, kana_bold=8)

# N: い's falling stroke at the upper right of ん, where the earlier drawing
# put it; the arena starts from that placement.
N_DEFAULTS = dict(BESIDE_DEFAULTS, mark_char='い', mark_index=1, ramp_lo=300, ramp_hi=500, kana_anchor='left',
                  mark_scale=0.658, mark_len=1.0, mark_angle=0.0, neck_w=1.0, head_w=1.0,
                  kana_sx=1.0, kana_sy=1.0, kana_bold=0, mark_x=-21, mark_dy=214)

# N as placed by hand in the arena (research/okinawan-arena/glottal-n).
N = dict(N_DEFAULTS, mark_x=-11, mark_dy=144, mark_scale=0.658, mark_len=1.04, neck_w=1.3, head_w=1.25,
         mark_angle=-4.0, mark_bend=-20)

# WI and WE: こ's upper stroke as a dot above ゐ and ゑ, shrunk evenly under it,
# where the earlier drawing put them; the arena starts from that placement.
W_DEFAULTS = dict(BESIDE_DEFAULTS, mark_char='こ', mark_index=1, mark_lie=True, ramp_lo=-650, ramp_hi=-350,
                  kana_anchor='bottom', kana_sx=0.88, kana_bold=0, mark_scale=0.64, mark_len=1.0,
                  mark_angle=0.0, neck_w=1.0, head_w=1.0, mark_x=-24, mark_dy=252)


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
    # each resolved copy winds 0 or 1 everywhere, so one nonzero pass unites them
    # copies about 2 units apart: closer ones leave near-coincident edges that
    # Skia cannot resolve, and the scallops between them stay far below a unit.
    # Some layouts still defeat it at one count and not at a neighbouring one,
    # so nearby counts are tried, denser first.
    n = int(np.ceil(d / 2)) + 1
    for count in [*range(n, n + 6), *range(n - 1, 1, -1)]:
        shape = pathops.Path()
        for dx in np.linspace(-d / 2, d / 2, count):
            base.transform(1, 0, 0, 1, dx, 0).draw(shape.getPen())
        try:
            shape.simplify(fix_winding=True, keep_starting_points=False)
            break
        except pathops.PathOpsError:
            continue
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


def beside_pieces(font, contours, kana, p):
    """The mark at its widths, upright (a lying stroke is turned to stand, so
    its width runs across and its head is at the top), with the point it turns
    about; and the kana, sized and weighted, where it stays."""
    mark = _widened(upright_mark(font, contours, p), p['ramp_lo'], p['neck_w'], p['head_w'], p['ramp_hi'])
    xs = sorted(O.point(mark[i], t)[0] for i, t in O.crossings(mark, 1, p['ramp_lo']))
    pivot = ((xs[0] + xs[1]) / 2, p['ramp_lo'])
    body = O.rings(contours(font, ord(kana)))
    xs = [q[0] for r in body for seg in r for q in seg]
    ys = [q[1] for r in body for seg in r for q in seg]
    sy = p['kana_sx'] if p['kana_anchor'] == 'bottom' else p['kana_sy']
    ox, oy = {'right': (max(xs), 360), 'left': (min(xs), 360),
              'bottom': ((min(xs) + max(xs)) / 2, min(ys))}[p['kana_anchor']]
    body = [O.transform(r, np.diag([p['kana_sx'], sy]), (ox * (1 - p['kana_sx']), oy * (1 - sy))) for r in body]
    return mark, pivot, _widen_strokes(body, p['kana_bold'])


def shaped(mark, pivot, p):
    """The mark turned about its pivot, bowed and slanted, laid back down if
    it lies, with the point it is sized about: its foot, level with its lowest
    point under its middle. The placement page repeats these steps point for
    point."""
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
