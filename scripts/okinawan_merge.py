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


def _widened(segs, cut, neck, head):
    """The mark with its width scaled about its centre line: `neck` at the cut,
    `head` from HEAD_Y up, varying linearly in between."""
    def centre(y):
        xs = sorted(O.point(segs[i], t)[0] for i, t in O.crossings(segs, 1, y))
        return (xs[0] + xs[1]) / 2
    c0, c1 = centre(cut), centre(HEAD_Y)
    def move(q):
        u = min(1, max(0, (q[1] - cut) / (HEAD_Y - cut)))
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
