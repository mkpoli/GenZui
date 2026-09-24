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
    shift=60,        # や moves right to make room for the mark
    arm_cut=280,     # x (before the shift) where や's arm loses its head
    mark_cut=480,    # y where the mark (は's left stroke) is cut
    mark_x=0,        # horizontal offset of the mark
    mark_dy=0,       # vertical offset of the mark
    mark_len=1.0,    # length of the mark above the cut, along the stroke
    outer_drop=40,   # how far the outside of the turn dips below the two edges
    outer_k=0.55,    # fullness of the outer turn
    inner_k=0.45,    # fullness of the inner corner
)


def _reverse(segs):
    return [(s[3], s[2], s[1], s[0]) for s in reversed(segs)]


def _moved(segs, dx=0, dy=0):
    return O.transform(segs, np.eye(2), (dx, dy))


def glottal_ya(font, contours, **params):
    """や with the glottal mark merged into the head of its arm."""
    p = {**YA_DEFAULTS, **params}
    ring = lambda ch, i: O.rings(contours(font, ord(ch), [i]))[0]
    arm = _moved(ring('や', 1), p['shift'])
    rest = _moved(ring('や', 0), p['shift'])
    mark = ring('は', 1)
    # lengthen or shorten the mark above its cut, along its length only
    m = np.array([[1, 0], [0, p['mark_len']]])
    mark = O.transform(mark, m, (p['mark_x'], p['mark_cut'] * (1 - p['mark_len']) + p['mark_dy']))
    cut_y = p['mark_cut'] + p['mark_dy']

    cx = O.crossings(arm, 0, p['arm_cut'] + p['shift'])
    body = max((O.arc(arm, cx[0], cx[1]), O.arc(arm, cx[1], cx[0])),
               key=lambda s: np.mean([q[0] for seg in s for q in seg]))
    cy = sorted(O.crossings(mark, 1, cut_y), key=lambda c: O.point(mark[c[0]], c[1])[0])[:2]
    top = max((O.arc(mark, cy[0], cy[1]), O.arc(mark, cy[1], cy[0])),
              key=lambda s: np.mean([q[1] for seg in s for q in seg]))

    P, Q = body[0][0], body[-1][3]
    tP, tQ = -O.tangent(body[0], 0), O.tangent(body[-1], 1)
    upper_is_Q = Q[1] > P[1]
    R, L = top[0][0], top[-1][3]
    if (R[0] > L[0]) != upper_is_Q:
        top = _reverse(top)
        R, L = top[0][0], top[-1][3]
    tR, tL = -O.tangent(top[0], 0), O.tangent(top[-1], 1)
    # inner corner: from the arm's upper edge into the mark's inner edge
    inner = O.hermite(Q, tQ, R, -tR, p['inner_k'])
    # outer turn: from the mark's outer edge down around into the arm's lower edge
    low = np.array([min(L[0], P[0]) + 25, min(L[1], P[1]) - p['outer_drop']])
    along = (P - L) / np.linalg.norm(P - L)
    outer = [O.hermite(L, tL, low, along, p['outer_k']), O.hermite(low, along, P, -tP, p['outer_k'])]
    return O.draw([body + [inner] + top + outer, rest])
