import collections
import math

# source: https://www.redblobgames.com/grids/hexagons/

Point = collections.namedtuple("Point", ["x", "y"])

Hex = collections.namedtuple("Hex", ["q", "r", "s"])


def set_hex(q, r, s):
    assert not (round(q + r + s) != 0), "q + r + s must be 0"
    return Hex(q, r, s)

def set_hex_from_coords(coords: list) -> Hex:
    assert len(coords) == 3, "must take 3 coords"
    return set_hex(coords[0], coords[1], coords[2])

def set_hex_from_2_coords(coords: list) -> Hex:
    assert len(coords) == 2, "must take 2 coords"
    return set_hex(coords[0], coords[1], -coords[0]-coords[1])


def hex_to_coords(Hex: Hex) -> list:
    return [Hex.q, Hex.r, Hex.s]


def hex_add(a, b):
    return set_hex(a.q + b.q, a.r + b.r, a.s + b.s)
def hex_subtract(a, b):
    return set_hex(a.q - b.q, a.r - b.r, a.s - b.s)

def hex_scale(a, k):
    return set_hex(a.q * k, a.r * k, a.s * k)

def hex_rotate_left(a):
    return set_hex(-a.s, -a.q, -a.r)
def hex_rotate_right(a):
    return set_hex(-a.r, -a.s, -a.q)

hex_directions = [set_hex(1, 0, -1), set_hex(1, -1, 0), set_hex(0, -1, 1), set_hex(-1, 0, 1), set_hex(-1, 1, 0), set_hex(0, 1, -1)]
def hex_direction(direction):
    return hex_directions[direction]

def hex_neighbor(hex, direction):
    return hex_add(hex, hex_direction(direction))

hex_diagonals = [set_hex(2, -1, -1), set_hex(1, -2, 1), set_hex(-1, -1, 2), set_hex(-2, 1, 1), set_hex(-1, 2, -1), set_hex(1, 1, -2)]
def hex_diagonal_neighbor(hex, direction):
    return hex_add(hex, hex_diagonals[direction])

def hex_length(hex)->int:
    return int((abs(hex.q) + abs(hex.r) + abs(hex.s)) / 2)

def hex_distance(hex_a, hex_b)->int:
    return hex_length(hex_subtract(hex_a, hex_b))

def hex_round(h):
    qi = int(round(h.q))
    ri = int(round(h.r))
    si = int(round(h.s))
    q_diff = abs(qi - h.q)
    r_diff = abs(ri - h.r)
    s_diff = abs(si - h.s)
    if q_diff > r_diff and q_diff > s_diff:
        qi = -ri - si
    else:
        if r_diff > s_diff:
            ri = -qi - si
        else:
            si = -qi - ri
    return set_hex(qi, ri, si)

def hex_lerp(a, b, t):
    return set_hex(a.q * (1.0 - t) + b.q * t, a.r * (1.0 - t) + b.r * t, a.s * (1.0 - t) + b.s * t)

def hex_linedraw(a, b):
    N = hex_distance(a, b)
    a_nudge = Hex(a.q + 1e-06, a.r + 1e-06, a.s - 2e-06)
    b_nudge = Hex(b.q + 1e-06, b.r + 1e-06, b.s - 2e-06)
    results = []
    step = 1.0 / max(N, 1)
    for i in range(0, N + 1):
        results.append(hex_round(hex_lerp(a_nudge, b_nudge, step * i)))
    return results

Orientation = collections.namedtuple("Orientation", ["f0", "f1", "f2", "f3", "b0", "b1", "b2", "b3", "start_angle"])
Layout = collections.namedtuple("Layout", ["orientation", "size", "origin"])
layout_pointy = Orientation(math.sqrt(3.0), math.sqrt(3.0) / 2.0, 0.0, 3.0 / 2.0, math.sqrt(3.0) / 3.0, -1.0 / 3.0, 0.0, 2.0 / 3.0, 0.5)
layout_flat = Orientation(3.0 / 2.0, 0.0, math.sqrt(3.0) / 2.0, math.sqrt(3.0), 2.0 / 3.0, 0.0, -1.0 / 3.0, math.sqrt(3.0) / 3.0, 0.0)

def hex_to_pixel(layout, h):
    M = layout.orientation
    size = layout.size
    origin = layout.origin
    x = (M.f0 * h.q + M.f1 * h.r) * size.x
    y = (M.f2 * h.q + M.f3 * h.r) * size.y
    return Point(x + origin.x, y + origin.y)

def pixel_to_hex(layout, p):
    M = layout.orientation
    size = layout.size
    origin = layout.origin
    pt = Point((p.x - origin.x) / size.x, (p.y - origin.y) / size.y)
    # pt = Point((p.x) / size.x, (p.y) / size.y)
    q = M.b0 * pt.x + M.b1 * pt.y
    r = M.b2 * pt.x + M.b3 * pt.y
    return set_hex(q, r, -q - r)

def hex_corner_offset(layout, corner) -> Point:
    M = layout.orientation
    size = layout.size
    angle = 2.0 * math.pi * (M.start_angle - corner) / 6.0
    return Point(size.x * math.cos(angle), size.y * math.sin(angle))

def hex_corners_list(layout, h) -> list:
    corners = []
    center = hex_to_pixel(layout, h)
    for i in range(0, 6):
        offset = hex_corner_offset(layout, i)
        corners.append(Point(center.x + offset.x, center.y + offset.y))
    return corners

def hex_corners_set(layout, h) -> set:
    corners = set()
    center = hex_to_pixel(layout, h)
    for i in range(0, 6):
        offset = hex_corner_offset(layout, i)
        corners.add((round(center.x + offset.x), round(center.y + offset.y)))
    return corners


OffsetCoord = collections.namedtuple("OffsetCoord", ["col", "row"])

EVEN = 1
ODD = -1
def qoffset_from_cube(offset, h):
    col = h.q
    row = h.r + (h.q + offset * (h.q & 1)) // 2
    if offset != EVEN and offset != ODD:
        raise ValueError("offset must be EVEN (+1) or ODD (-1)")
    return OffsetCoord(col, row)

def qoffset_to_cube(offset, h):
    q = h.col
    r = h.row - (h.col + offset * (h.col & 1)) // 2
    s = -q - r
    if offset != EVEN and offset != ODD:
        raise ValueError("offset must be EVEN (+1) or ODD (-1)")
    return set_hex(q, r, s)

def roffset_from_cube(offset, h):
    col = h.q + (h.r + offset * (h.r & 1)) // 2
    row = h.r
    if offset != EVEN and offset != ODD:
        raise ValueError("offset must be EVEN (+1) or ODD (-1)")
    return OffsetCoord(col, row)

def roffset_to_cube(offset, h):
    q = h.col - (h.row + offset * (h.row & 1)) // 2
    r = h.row
    s = -q - r
    if offset != EVEN and offset != ODD:
        raise ValueError("offset must be EVEN (+1) or ODD (-1)")
    return set_hex(q, r, s)




DoubledCoord = collections.namedtuple("DoubledCoord", ["col", "row"])

def qdoubled_from_cube(h):
    col = h.q
    row = 2 * h.r + h.q
    return DoubledCoord(col, row)

def qdoubled_to_cube(h):
    q = h.col
    r = (h.row - h.col) // 2
    s = -q - r
    return set_hex(q, r, s)

def rdoubled_from_cube(h):
    col = 2 * h.q + h.r
    row = h.r
    return DoubledCoord(col, row)

def rdoubled_to_cube(h):
    q = (h.col - h.row) // 2
    r = h.row
    s = -q - r
    return set_hex(q, r, s)