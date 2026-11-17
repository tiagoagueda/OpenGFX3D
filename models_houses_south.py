#!/usr/bin/env python3
"""Houses of the base game's sub-tropical and toyland towns (house types 78 to 109).

Houses that also appear in the temperate or sub-arctic climates are made elsewhere.
Frame: x to the front (south-west), y to the left (south-east), z up; a tile is 16 by 16.
The walls in "company" take the colour the game picked for the house.
"""

import math

from gfx3d import MATERIALS, Model

P = "houses_south_"

_COLOURS = {
    "white": (0.94, 0.93, 0.89),
    "redroof": (0.70, 0.30, 0.20),
    "stucco": (0.82, 0.64, 0.42),
    "stucco_dark": (0.62, 0.46, 0.28),
    "bluetile": (0.24, 0.40, 0.82),
    "bluedark": (0.14, 0.22, 0.55),
    "pink": (0.94, 0.56, 0.64),
    "pinkbrick": (0.84, 0.52, 0.44),
    "orangebrick": (0.90, 0.56, 0.36),
    "green": (0.44, 0.64, 0.34),
    "leaf": (0.24, 0.50, 0.20),
    "cream": (0.96, 0.91, 0.74),
    "snow": (0.95, 0.97, 1.00),
    "ice": (0.68, 0.85, 0.95),
    "canvas": (0.80, 0.72, 0.58),
    "red": (0.82, 0.14, 0.12),
    "yellow": (0.96, 0.80, 0.24),
    "teapot": (0.16, 0.32, 0.78),
    "dirt": (0.46, 0.37, 0.27),
    "leather": (0.44, 0.27, 0.14),
    "sole": (0.26, 0.16, 0.10),
    "skin": (0.96, 0.80, 0.68),
    "corrugated": (0.58, 0.58, 0.55),
    "brownroof": (0.52, 0.34, 0.20),
    "paving": (0.64, 0.62, 0.58),
    "glass_blue": (0.30, 0.42, 0.66),
    "roofblue": (0.20, 0.45, 0.85),
    "sandroof": (0.72, 0.62, 0.46),
    "logs": (0.62, 0.42, 0.20),
}
for _name, _colour in _COLOURS.items():
    MATERIALS[P + _name] = _colour


def c(name):
    return P + name


# ---------------------------------------------------------------- helpers

def box8(m, mat, b, t):
    """A box with any eight corners: b and t are the bottom and top corners (x0y0, x1y0, x1y1, x0y1)."""
    m.quad(mat, b[1], b[2], t[2], t[1])
    m.quad(mat, b[3], b[0], t[0], t[3])
    m.quad(mat, b[2], b[3], t[3], t[2])
    m.quad(mat, b[0], b[1], t[1], t[0])
    m.quad(mat, t[0], t[1], t[2], t[3])
    m.quad(mat, b[3], b[2], b[1], b[0])


def walls(m, mat, x0, x1, y0, y1, z0, z1):
    """The four walls of a box, without top and bottom (for a building under a roof)."""
    m.quad(mat, (x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1))
    m.quad(mat, (x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1))
    m.quad(mat, (x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1))
    m.quad(mat, (x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1))


def lean_to(m, mat, x0, x1, y0, y1, z_low, z_high, low_side="+x", thick=0.25):
    """A roof sloping down towards one side."""
    def z(x, y):
        if low_side == "+x":
            return z_high + (z_low - z_high) * (x - x0) / (x1 - x0)
        if low_side == "-x":
            return z_low + (z_high - z_low) * (x - x0) / (x1 - x0)
        if low_side == "+y":
            return z_high + (z_low - z_high) * (y - y0) / (y1 - y0)
        return z_low + (z_high - z_low) * (y - y0) / (y1 - y0)
    corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    b = [(x, y, z(x, y)) for x, y in corners]
    t = [(x, y, z(x, y) + thick) for x, y in corners]
    box8(m, mat, b, t)


def hip_roof(m, mat, x0, x1, y0, y1, z0, z1):
    """A hipped roof; the ridge runs along the longer side (a pyramid on a square)."""
    a, b, cc, d = (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z0)
    xm, ym = (x0 + x1) / 2, (y0 + y1) / 2
    if x1 - x0 >= y1 - y0:
        i = (y1 - y0) / 2
        r1, r0 = (x1 - i, ym, z1), (x0 + i, ym, z1)
        m.triangle(mat, a, b, r1)
        m.quad(mat, b, cc, r0, r1)
        m.triangle(mat, cc, d, r0)
        m.quad(mat, d, a, r1, r0)
    else:
        i = (x1 - x0) / 2
        rl, rr = (xm, y1 - i, z1), (xm, y0 + i, z1)
        m.quad(mat, a, b, rl, rr)
        m.triangle(mat, b, cc, rl)
        m.quad(mat, cc, d, rr, rl)
        m.triangle(mat, d, a, rr)


def roof_y(m, mat, gable, x0, x1, y0, y1, z0, z1):
    """A pitched roof with its ridge along y."""
    xm = (x0 + x1) / 2
    m.quad(mat, (x1, y0, z0), (x1, y1, z0), (xm, y1, z1), (xm, y0, z1))
    m.quad(mat, (x0, y1, z0), (x0, y0, z0), (xm, y0, z1), (xm, y1, z1))
    m.triangle(gable, (x1, y1, z0), (x0, y1, z0), (xm, y1, z1))
    m.triangle(gable, (x0, y0, z0), (x1, y0, z0), (xm, y0, z1))


def lathe(m, mat, cx, cy, profile, sides=16, cap=None, phase=0.0, sx=1.0, sy=1.0):
    """A solid of revolution around an upright axis; profile is (radius, z) from bottom to top."""
    angles = [phase + 2 * math.pi * i / sides for i in range(sides + 1)]

    def p(r, z, a):
        return (cx + sx * r * math.cos(a), cy + sy * r * math.sin(a), z)

    for (r0, z0), (r1, z1) in zip(profile, profile[1:]):
        for a0, a1 in zip(angles, angles[1:]):
            if r0 > 0:
                m.triangle(mat, p(r0, z0, a0), p(r0, z0, a1), p(r1, z1, a1))
            if r1 > 0:
                m.triangle(mat, p(r0, z0, a0), p(r1, z1, a1), p(r1, z1, a0))
    r, z = profile[-1]
    if r > 0 and cap:
        for a0, a1 in zip(angles, angles[1:]):
            m.triangle(cap, (cx, cy, z), p(r, z, a0), p(r, z, a1))


def dome(m, mat, cx, cy, z0, radius, height=None, sides=16, rings=6, sx=1.0, sy=1.0):
    height = radius if height is None else height
    prof = [(radius * math.cos(math.pi / 2 * k / rings), z0 + height * math.sin(math.pi / 2 * k / rings)) for k in range(rings + 1)]
    lathe(m, mat, cx, cy, prof, sides, sx=sx, sy=sy)


def sphere(m, mat, cx, cy, zc, radius, sides=14, rings=8, height=None):
    height = radius if height is None else height
    prof = [(radius * math.sin(math.pi * k / rings), zc - height * math.cos(math.pi * k / rings)) for k in range(rings + 1)]
    lathe(m, mat, cx, cy, prof, sides)


def column(m, mat, x, y, z0, z1, r, sides=10, cap=None):
    lathe(m, mat, x, y, [(r, z0), (r, z1)], sides, cap=cap or mat)


def tube(m, mat, p0, p1, r, sides=8):
    """A closed cylinder between two points."""
    d = [p1[i] - p0[i] for i in range(3)]
    ln = math.sqrt(sum(v * v for v in d))
    d = [v / ln for v in d]
    helper = (0, 0, 1) if abs(d[2]) < 0.9 else (1, 0, 0)
    u = [d[1] * helper[2] - d[2] * helper[1], d[2] * helper[0] - d[0] * helper[2], d[0] * helper[1] - d[1] * helper[0]]
    lu = math.sqrt(sum(v * v for v in u))
    u = [v / lu for v in u]
    v = [d[1] * u[2] - d[2] * u[1], d[2] * u[0] - d[0] * u[2], d[0] * u[1] - d[1] * u[0]]  # u x v = d
    def ring(p):
        return [tuple(p[k] + r * (math.cos(2 * math.pi * i / sides) * u[k] + math.sin(2 * math.pi * i / sides) * v[k]) for k in range(3)) for i in range(sides)]
    r0, r1 = ring(p0), ring(p1)
    for i in range(sides):
        j = (i + 1) % sides
        m.quad(mat, r0[i], r0[j], r1[j], r1[i])
        m.triangle(mat, tuple(p1), r1[i], r1[j])
        m.triangle(mat, tuple(p0), r0[j], r0[i])


def face_windows(m, mat, side, a0, a1, wall, zs, n, size=(1.2, 1.4), depth=0.08, skip=()):
    """A row of windows on one wall: side is +x, -x, +y or -y, the wall at coordinate wall, spread from a0 to a1."""
    w, h = size
    for z in zs:
        for i in range(n):
            if i in skip:
                continue
            a = a0 + (i + 0.5) * (a1 - a0) / n
            if side == "+x":
                m.box(mat, wall, wall + depth, a - w / 2, a + w / 2, z - h / 2, z + h / 2)
            elif side == "-x":
                m.box(mat, wall - depth, wall, a - w / 2, a + w / 2, z - h / 2, z + h / 2)
            elif side == "+y":
                m.box(mat, a - w / 2, a + w / 2, wall, wall + depth, z - h / 2, z + h / 2)
            else:
                m.box(mat, a - w / 2, a + w / 2, wall - depth, wall, z - h / 2, z + h / 2)


def arch(m, mat, side, wall, a, z0, w, h, segs=6):
    """A dark round-topped opening drawn flat on a wall facing +x or +y."""
    r = w / 2
    zs = z0 + h - r
    pts = [(a - r, z0), (a + r, z0), (a + r, zs)]
    for k in range(1, segs):
        t = math.pi * k / segs
        pts.append((a + r * math.cos(t), zs + r * math.sin(t)))
    pts.append((a - r, zs))
    if side == "+x":
        P3 = [(wall + 0.05, y, z) for y, z in pts]
    elif side == "+y":
        P3 = [(2 * a - u, wall + 0.05, z) for u, z in pts]
    elif side == "-x":
        P3 = [(wall - 0.05, y, z) for y, z in reversed(pts)]
    else:
        P3 = [(x, wall - 0.05, z) for x, z in pts]
    for k in range(1, len(P3) - 1):
        m.triangle(mat, P3[0], P3[k], P3[k + 1])


def garden_wall(m, mat, x0, x1, y0, y1, h=0.9, t=0.3, gate=None):
    """A low wall around a plot; gate is (side, centre, width) for an opening."""
    segs = [("+x", x1 - t, x1, y0, y1), ("-x", x0, x0 + t, y0, y1), ("+y", x0, x1, y1 - t, y1), ("-y", x0, x1, y0, y0 + t)]
    for side, a0, a1, b0, b1 in segs:
        if gate and gate[0] == side:
            g, gw = gate[1], gate[2]
            if side in ("+x", "-x"):
                m.box(mat, a0, a1, b0, g - gw / 2, 0, h)
                m.box(mat, a0, a1, g + gw / 2, b1, 0, h)
            else:
                m.box(mat, a0, g - gw / 2, b0, b1, 0, h)
                m.box(mat, g + gw / 2, a1, b0, b1, 0, h)
        else:
            m.box(mat, a0, a1, b0, b1, 0, h)


def ground(m, mat, x0=-7.8, x1=7.8, y0=-7.8, y1=7.8, z=0.05):
    m.box(mat, x0, x1, y0, y1, 0, z)


def tree(m, x, y, h=4.0, r=1.4):
    column(m, "wood", x, y, 0, h * 0.5, 0.25, sides=6)
    sphere(m, c("leaf"), x, y, h * 0.65, r, sides=8, rings=5)


def count(m):
    return sum(len(p) // 3 for p, _ in m.parts.values())


# ---------------------------------------------------------------- sub-tropical

def st_villa():
    """78: a white two-storey house with a red hipped roof in a walled garden."""
    m = Model()
    ground(m, "grass")
    m.box(c("paving"), 2, 7.8, -2.6, -0.6, 0.05, 0.1)
    garden_wall(m, c("white"), -7.8, 7.8, -7.8, 7.8, gate=("+x", -1.6, 2.2))
    walls(m, "company", -5, 2.5, -5.5, 4.5, 0, 6.6)
    m.box("concrete", -5.1, 2.6, -5.6, 4.6, 0, 0.35)
    hip_roof(m, c("redroof"), -5.6, 3.1, -6.1, 5.1, 6.6, 9.4)
    face_windows(m, "glass", "+x", -5.5, 4.5, 2.5, (1.7, 5.0), 4, skip=())
    face_windows(m, "glass", "+y", -5, 2.5, 4.5, (1.7, 5.0), 3)
    face_windows(m, "glass", "-x", -5.5, 4.5, -5, (1.7, 5.0), 3)
    face_windows(m, "glass", "-y", -5, 2.5, -5.5, (1.7, 5.0), 3)
    m.box("door", 2.5, 2.6, -2.2, -1.0, 0.1, 2.4)
    m.box("brick", -2.5, -1.6, 2, 2.9, 8, 10)
    m.save("houses_south_villa.glb")
    return m


def st_villa_l():
    """79: an L-shaped white house with red roofs and a walled garden."""
    m = Model()
    ground(m, "grass")
    m.box(c("paving"), 3.5, 7.8, 1.8, 4.2, 0.05, 0.1)
    garden_wall(m, c("white"), -7.8, 7.8, -7.8, 7.8, gate=("+x", 3, 2.4))
    # main wing along y at the back, side wing to the front on the right
    walls(m, "company", -6, -0.5, -6, 5.5, 0, 6.4)
    roof_y(m, c("redroof"), "company", -6.5, 0, -6.4, 5.9, 6.4, 9.2)
    walls(m, "company", -0.5, 4.5, -6, -1, 0, 4.4)
    m.prism_roof(c("redroof"), "company", -1, 5, -6.4, -0.6, 4.4, 6.8)
    face_windows(m, "glass", "+x", -1, 5.5, -0.5, (1.6, 4.8), 3)
    face_windows(m, "glass", "+x", -6, -1, 4.5, (2.0,), 2)
    face_windows(m, "glass", "+y", -6, -0.5, 5.5, (1.6, 4.8), 2)
    face_windows(m, "glass", "+y", -0.5, 4.5, -1, (2.0,), 2)
    face_windows(m, "glass", "-x", -6, 5.5, -6, (1.6, 4.8), 3)
    face_windows(m, "glass", "-y", -6, 4.5, -6, (1.6,), 4)
    m.box("door", -0.5, -0.4, 2.4, 3.6, 0.1, 2.4)
    m.save("houses_south_villa_l.glb")
    return m


def st_cottage():
    """80: a small white single-storey house with a red roof and a hedge."""
    m = Model()
    ground(m, "grass")
    for (x0, x1, y0, y1) in ((7.2, 7.8, -7.8, 7.8), (-7.8, -7.2, -7.8, 7.8), (-7.8, 7.8, 7.2, 7.8), (-7.8, 7.8, -7.8, -7.2)):
        m.box(c("leaf"), x0, x1, y0, y1, 0, 0.8)
    walls(m, "company", -3.5, 3.5, -4.5, 4.0, 0, 3.8)
    roof_y(m, c("redroof"), "company", -4.0, 4.0, -5.0, 4.5, 3.8, 6.8)
    face_windows(m, "glass", "+x", -4.5, 4.0, 3.5, (2.0,), 3, skip=(1,))
    face_windows(m, "glass", "+y", -3.5, 3.5, 4.0, (2.0, 4.8), 2)
    face_windows(m, "glass", "-x", -4.5, 4.0, -3.5, (2.0,), 3)
    m.box("door", 3.5, 3.6, -0.8, 0.4, 0.05, 2.3)
    m.box(c("paving"), 3.6, 7.2, -0.9, 0.5, 0.05, 0.1)
    m.save("houses_south_cottage.glb")
    return m


def st_shacks():
    """81: huts with lean-to roofs on bare ground at the edge of town."""
    m = Model()
    ground(m, c("dirt"))
    # a hut of mud brick with a corrugated roof
    m.box(c("stucco"), -5, 1, -1, 5, 0, 2.8)
    lean_to(m, c("corrugated"), -5.4, 1.4, -1.4, 5.4, 2.6, 3.8, low_side="+x")
    m.box("door", 1.0, 1.1, 1.2, 2.4, 0, 2.0)
    m.box("glass", -2.5, -1.5, 5.0, 5.08, 1.1, 1.9)
    # a smaller shed with a dark roof
    m.box(c("stucco_dark"), 2, 5.5, -6, -2, 0, 2.0)
    lean_to(m, "slate", 1.7, 5.8, -6.3, -1.7, 1.9, 2.9, low_side="-y")
    m.box("door", 5.5, 5.6, -4.6, -3.4, 0, 1.7)
    # a lean-to shelter on posts
    for x, y in ((-6.5, -6.5), (-6.5, -3), (-2.5, -6.5), (-2.5, -3)):
        m.box("wood", x - 0.15, x + 0.15, y - 0.15, y + 0.15, 0, 2.2)
    lean_to(m, c("corrugated"), -7, -2, -7, -2.5, 1.9, 2.5, low_side="+x", thick=0.15)
    # crates and a woodpile
    m.box("wood", 3, 4, 2.5, 3.5, 0, 1)
    m.box(c("yellow"), 4.2, 5, 3, 3.8, 0, 0.8)
    for i in range(3):
        m.cylinder(c("logs"), -6, -3.5, -5.7 + i * 0.55, 0.3, 0.27, sides=6)
    m.save("houses_south_shacks.glb")
    return m


def st_tower_flats():
    """82: a tall block of flats, brick at the back, white with many windows at the front."""
    m = Model()
    ground(m, c("paving"))
    x0, x1, y0, y1, h = -4.5, 4.5, -4.5, 4.5, 26
    m.box("brick", x0, x0 + 2, y0, y1, 0, h)
    m.box("brick", x0 + 2, x1, y0, y0 + 2, 0, h)
    m.box("company", x0 + 2, x1 + 0.1, y0 + 2, y1 + 0.1, 0, h)
    m.box("company", x0 - 0.1, x1 + 0.2, y0 - 0.1, y1 + 0.2, h, h + 0.6)
    m.box("concrete", x0 + 1, x0 + 3.5, y0 + 1, y0 + 3.5, h + 0.6, h + 2.2)
    zs = [1.8 + 2.9 * i for i in range(9)]
    face_windows(m, "glass", "+x", y0 + 2, y1, x1 + 0.1, zs, 3, size=(1.6, 1.6))
    face_windows(m, "glass", "+y", x0 + 2, x1, y1 + 0.1, zs, 3, size=(1.6, 1.6))
    face_windows(m, "glass", "-x", y0, y1, x0, zs, 3, size=(1.2, 1.4))
    face_windows(m, "glass", "-y", x0, x1, y0, zs, 3, size=(1.2, 1.4))
    m.box("door", x1 + 0.1, x1 + 0.2, -0.8, 0.8, 0, 2.4)
    m.box("concrete", x1 + 0.1, x1 + 1.8, -1.6, 1.6, 2.6, 2.9)
    m.save("houses_south_tower_flats.glb")
    return m


def st_mission_church():
    """83: a church in the colonial mission style: arcade, curved gable and a bell tower with a dome."""
    m = Model()
    ground(m, c("paving"))
    st, sd = c("stucco"), c("stucco_dark")
    m.box(st, -6.5, 3.5, -6, 5, 0, 7.5)
    m.box(sd, -6.6, 3.6, -6.1, 5.1, 7.5, 7.9)  # cornice
    m.box(c("sandroof"), -6.2, 3.2, -5.7, 4.7, 7.9, 8.0)
    # arcade in front
    m.box(st, 3.5, 6.5, -6, 5, 3.4, 4.0)
    m.box(c("sandroof"), 3.5, 6.5, -6, 5, 4.0, 4.1)
    for y in (-5.8, -3.0, -0.2, 2.6, 4.8):
        m.box(st, 5.9, 6.5, y - 0.3, y + 0.3, 0, 3.4)
    for y in (-4.4, -1.6, 1.2, 3.7):
        arch(m, "dark", "+x", 3.5, y, 0, 1.8, 2.8)
    # curved (stepped) gable over the door
    prof = [(-3.2, 7.9), (-2.4, 9.0), (-1.2, 9.6), (0, 10.4), (1.2, 9.6), (2.4, 9.0), (3.2, 7.9)]
    for (ya, za), (yb, zb) in zip(prof, prof[1:]):
        lo = 7.5
        b = [(3.0, ya - 0.5, lo), (3.6, ya - 0.5, lo), (3.6, yb - 0.5, lo), (3.0, yb - 0.5, lo)]
        t = [(3.0, ya - 0.5, za), (3.6, ya - 0.5, za), (3.6, yb - 0.5, zb), (3.0, yb - 0.5, zb)]
        box8(m, st, b, t)
    arch(m, "dark", "+x", 3.6, -0.5, 7.9, 1.0, 1.6)
    m.box("brass", 3.62, 3.7, -0.8, -0.2, 8.0, 8.6)
    # upper windows
    for y in (-4.4, -1.6, 1.2, 3.7):
        arch(m, "glass", "+x", 3.5, y, 5.0, 1.0, 1.8)
    for x in (-5, -2.5, 0, 2.5):
        arch(m, "glass", "+y", 5, x, 1.6, 1.0, 2.0)
        arch(m, "glass", "+y", 5, x, 4.9, 1.0, 1.8)
    # bell tower with a small dome at the left front corner
    tx, ty = 1.2, 3.0
    m.box(st, tx - 1.6, tx + 1.6, ty - 1.6, ty + 1.6, 7.9, 11.5)
    arch(m, "dark", "+x", tx + 1.6, ty, 9.3, 1.2, 1.8)
    arch(m, "dark", "+y", ty + 1.6, tx, 9.3, 1.2, 1.8)
    m.box(sd, tx - 1.8, tx + 1.8, ty - 1.8, ty + 1.8, 11.5, 11.9)
    dome(m, st, tx, ty, 11.9, 1.5, 1.6, sides=12, rings=4)
    m.box(sd, tx - 0.08, tx + 0.08, ty - 0.08, ty + 0.08, 13.4, 14.6)
    m.box(sd, tx - 0.08, tx + 0.08, ty - 0.45, ty + 0.45, 14.0, 14.2)
    m.save("houses_south_mission_church.glb")
    return m


def st_house_garden():
    """84: a white two-storey house with a red roof, a balcony and a walled yard."""
    m = Model()
    ground(m, "grass", -7.8, 7.8, 0, 7.8)
    ground(m, c("paving"), -7.8, 7.8, -7.8, 0)
    garden_wall(m, c("white"), -7.8, 7.8, -7.8, 7.8, gate=("+x", -4, 2.6))
    walls(m, "company", -6, 1.5, -6.5, 4, 0, 6.6)
    m.prism_roof(c("redroof"), "company", -6.5, 2.0, -7.0, 4.5, 6.6, 9.6)
    m.box("brick", -4, -3.1, 1.5, 2.4, 8.5, 10.4)
    # balcony on the front
    m.box("concrete", 1.5, 3.0, -5.5, -0.5, 3.1, 3.4)
    m.box("company", 2.85, 3.0, -5.5, -0.5, 3.4, 4.3)
    face_windows(m, "glass", "+x", -6.5, 4.0, 1.5, (1.7,), 3)
    face_windows(m, "glass", "+x", -6.5, 4.0, 1.5, (5.0,), 3, skip=(0,))
    m.box("glass", 1.5, 1.58, -4.5, -3.2, 3.4, 5.6)
    face_windows(m, "glass", "+y", -6, 1.5, 4, (1.7, 5.0), 3)
    face_windows(m, "glass", "-x", -6.5, 4.0, -6, (1.7, 5.0), 3)
    m.box("door", 1.5, 1.6, 1.0, 2.2, 0.05, 2.4)
    tree(m, -6.3, 6.0, 4.5, 1.3)
    m.save("houses_south_house_garden.glb")
    return m


def st_balcony_flats():
    """85: white flats with coloured balconies on every floor and a stair house on the roof."""
    m = Model()
    ground(m, c("paving"))
    x0, x1, y0, y1, h = -5.5, 5, -5.5, 5, 20
    m.box(c("white"), x0, x1, y0, y1, 0, h)
    m.box("concrete", x0 - 0.1, x1 + 0.1, y0 - 0.1, y1 + 0.1, h, h + 0.5)
    m.box(c("white"), x0 + 1, x0 + 5, y0 + 1, y0 + 4.5, h + 0.5, h + 3)
    m.box("glass", x0 + 3, x0 + 4, y0 + 4.5, y0 + 4.58, h + 1, h + 2.2)
    zs = [3.3 * (i + 1) for i in range(5)]
    for z in zs:
        for a in (-3.0, 2.5):
            m.box("company", x1, x1 + 1.3, a - 1.3, a + 1.3, z - 0.15, z + 0.15)
            m.box("company", x1 + 1.15, x1 + 1.3, a - 1.3, a + 1.3, z + 0.15, z + 1.1)
            m.box("company", a - 1.3, a + 1.3, y1, y1 + 1.3, z - 0.15, z + 0.15)
            m.box("company", a - 1.3, a + 1.3, y1 + 1.15, y1 + 1.3, z + 0.15, z + 1.1)
    face_windows(m, "glass", "+x", y0, y1, x1, [z + 1.4 for z in [0] + zs], 2, size=(1.4, 2.0), skip=())
    face_windows(m, "glass", "+y", x0, x1, y1, [z + 1.4 for z in [0] + zs], 2, size=(1.4, 2.0))
    face_windows(m, "glass", "-x", y0, y1, x0, [z + 1.6 for z in [0] + zs], 3, size=(1.2, 1.4))
    face_windows(m, "glass", "-y", x0, x1, y0, [z + 1.6 for z in [0] + zs], 3, size=(1.2, 1.4))
    m.box("door", x1, x1 + 0.1, -0.6, 0.6, 0, 2.3)
    m.save("houses_south_balcony_flats.glb")
    return m


def st_band_flats():
    """86: low concrete flats with coloured bands along each floor."""
    m = Model()
    ground(m, c("paving"))
    x0, x1, y0, y1, h = -6, 6, -6, 6, 10
    m.box("concrete", x0, x1, y0, y1, 0, h)
    m.box(c("white"), x0 - 0.1, x1 + 0.1, y0 - 0.1, y1 + 0.1, h, h + 0.6)
    m.box("slate", x0 + 0.5, x1 - 0.5, y0 + 0.5, y1 - 0.5, h + 0.6, h + 0.65)
    for z in (3.3, 6.6):
        m.box("company", x0 - 0.4, x1 + 0.4, y0 - 0.4, y1 + 0.4, z - 0.3, z + 0.2)
    m.windows("glass", x0, x1, y0, y1, 0.3, h, 3, 4, size=(1.8, 1.4))
    m.box("glass", x1, x1 + 0.1, -3, 3, 0.2, 2.6)
    m.save("houses_south_band_flats.glb")
    return m


def glass_block(m, x0, x1, y0, y1, z0, z1, floor=3.0, roof=c("roofblue"), nx=3, ny=3):
    """A glass block with dark mullions and floor lines."""
    m.box(c("glass_blue"), x0, x1, y0, y1, z0, z1)
    m.box(roof, x0 + 0.2, x1 - 0.2, y0 + 0.2, y1 - 0.2, z1, z1 + 0.15)
    m.box("dark", x0 - 0.1, x1 + 0.1, y0 - 0.1, y1 + 0.1, z1 - 0.3, z1)
    z = z0 + floor
    while z < z1 - 0.5:
        m.box("dark", x0 - 0.05, x1 + 0.05, y0 - 0.05, y1 + 0.05, z - 0.12, z + 0.12)
        z += floor
    for i in range(nx + 1):
        x = x0 + (x1 - x0) * i / nx
        for y in (y0, y1):
            m.box("dark", x - 0.15, x + 0.15, y - 0.15, y + 0.15, z0, z1)
    for i in range(1, ny):
        y = y0 + (y1 - y0) * i / ny
        for x in (x0, x1):
            m.box("dark", x - 0.15, x + 0.15, y - 0.15, y + 0.15, z0, z1)


def st_office_pair():
    """87 + 88: a 2 by 1 office complex of glass towers (32 along x)."""
    m = Model()
    ground(m, c("paving"), -15.8, 15.8, -7.8, 7.8)
    # back tile: a slim tower and a low wing
    glass_block(m, -15, -1.5, -7, 1, 0, 6, roof=c("roofblue"), nx=4, ny=2)
    glass_block(m, -12, -6, -2, 4, 0, 40, nx=2, ny=2)
    m.box("concrete", -10, -8, 0, 2, 40.15, 41.5)
    tube(m, c("red"), (-9, 1, 41.5), (-9, 1, 43.5), 0.15, 6)
    tube(m, c("white"), (-9, 1, 43.5), (-9, 1, 45.5), 0.15, 6)
    tube(m, c("red"), (-9, 1, 45.5), (-9, 1, 47), 0.15, 6)
    # front tile: a big tower at the back and a lower block in front
    glass_block(m, 2, 9, -1, 7, 0, 34, nx=2, ny=3)
    glass_block(m, 4, 14, -7, 3, 0, 18, nx=3, ny=3)
    m.box(c("red"), 13.6, 14.15, -6, -1, 15.5, 17.2)  # a sign
    tube(m, c("red"), (5.5, 3, 34.15), (5.5, 3, 37), 0.15, 6)
    tube(m, c("white"), (5.5, 3, 37), (5.5, 3, 39), 0.15, 6)
    m.box("glass", 14, 14.15, -1, 1, 0, 2.6)
    # flower beds
    m.box(c("leaf"), 1, 3.5, 4, 7, 0.05, 0.6)
    m.box(c("leaf"), -1, 1, -7, -4, 0.05, 0.6)
    m.save("houses_south_office_pair.glb")
    return m


def st_flats_tank():
    """89: white flats with a flat roof and a water tank on the roof."""
    m = Model()
    ground(m, c("paving"))
    x0, x1, y0, y1, h = -6, 6, -6, 6, 10
    m.box("company", x0, x1, y0, y1, 0, h)
    m.box(c("white"), x0 - 0.1, x1 + 0.1, y0 - 0.1, y1 + 0.1, h, h + 0.7)
    m.box(c("sandroof"), x0 + 0.3, x1 - 0.3, y0 + 0.3, y1 - 0.3, h + 0.7, h + 0.75)
    m.windows("glass", x0, x1, y0, y1, 0.3, h, 3, 4, size=(1.4, 1.5))
    m.box("door", x1, x1 + 0.12, 2.6, 3.8, 0, 2.3)
    # water tank on four legs
    for dx in (-1.4, 1.4):
        for dy in (-1.4, 1.4):
            m.box("metal", -2 + dx - 0.15, -2 + dx + 0.15, 1 + dy - 0.15, 1 + dy + 0.15, h + 0.75, h + 2.8)
    lathe(m, c("white"), -2, 1, [(2.2, h + 2.8), (2.2, h + 5.2), (1.6, h + 5.9), (0, h + 6.2)], sides=14, cap=None)
    m.box("concrete", 2, 4.5, -4.5, -2, h + 0.75, h + 2.4)  # stair house
    m.save("houses_south_flats_tank.glb")
    return m


def st_tower_atrium():
    """90: a tall white tower with an antenna over a glass base with a roof terrace."""
    m = Model()
    m.box(c("glass_blue"), -7.5, 7.5, -7.5, 7.5, 0, 6)
    for z in (3, 6):
        m.box("dark", -7.6, 7.6, -7.6, 7.6, z - 0.2, z + 0.1)
    for a in (-7.5, -3.75, 0, 3.75, 7.5):
        for b in (-7.5, 7.5):
            m.box("dark", a - 0.15, a + 0.15, b - 0.15, b + 0.15, 0, 6)
            m.box("dark", b - 0.15, b + 0.15, a - 0.15, a + 0.15, 0, 6)
    m.box(c("dirt"), -7.3, 7.3, -7.3, 7.3, 6, 6.15)
    # tower at the back left
    tx0, tx1, ty0, ty1, h = -6.5, 0.5, -0.5, 6.5, 34
    m.box(c("white"), tx0, tx1, ty0, ty1, 6, h)
    face_windows(m, "glass", "+x", ty0, ty1, tx1, [7.6 + 2.6 * i for i in range(10)], 4, size=(1.1, 1.6))
    face_windows(m, "glass", "-y", tx0, tx1, ty0, [7.6 + 2.6 * i for i in range(10)], 4, size=(1.1, 1.6))
    face_windows(m, "glass", "+y", tx0, tx1, ty1, [7.6 + 2.6 * i for i in range(10)], 4, size=(1.1, 1.6))
    face_windows(m, "glass", "-x", ty0, ty1, tx0, [7.6 + 2.6 * i for i in range(10)], 4, size=(1.1, 1.6))
    # stepped top
    m.box("company", tx0 - 0.1, tx1 + 0.1, ty0 - 0.1, ty1 + 0.1, h - 0.6, h)
    m.box(c("white"), tx0 + 1, tx1 - 1, ty0 + 1, ty1 - 1, h, h + 2.5)
    m.box("concrete", tx0 + 2, tx1 - 2, ty0 + 2, ty1 - 2, h + 2.5, h + 3.5)
    tube(m, c("white"), (-3, 3, h + 3.5), (-3, 3, h + 11), 0.2, 6)
    # roof terrace: a tree and parasols
    column(m, "wood", 4.5, -4.5, 6.15, 7.8, 0.25, sides=6)
    sphere(m, c("leaf"), 4.5, -4.5, 9.2, 1.6, sides=8, rings=5)
    for (x, y) in ((4.5, 3.5), (1.5, -5.0)):
        column(m, "metal", x, y, 6.15, 8.3, 0.08, sides=4)
        lathe(m, c("white"), x, y, [(1.4, 8.0), (0, 8.6)], sides=8)
        lathe(m, c("white"), x, y, [(0, 8.0), (1.4, 8.0)], sides=8)
    m.box("glass", 7.5, 7.6, -2, 2, 0, 2.8)
    m.save("houses_south_tower_atrium.glb")
    return m


# ---------------------------------------------------------------- toyland

def toy_church():
    """91: a cream tower house with a tall red pointed spire."""
    m = Model()
    walls(m, "company", -4.5, 4.5, -4.5, 4.5, 0, 11)
    m.box(c("green"), -4.8, 4.8, -4.8, 4.8, 3.4, 3.8)
    m.box(c("green"), -4.8, 4.8, -4.8, 4.8, 7.4, 7.8)
    m.box(c("green"), -5.2, 5.2, -5.2, 5.2, 11, 11.6)
    for z in (1.0, 4.6, 8.4):
        for a in (-2.2, 2.2):
            arch(m, "glass", "+x", 4.5, a, z, 1.3, 2.3)
            arch(m, "glass", "+y", 4.5, a, z, 1.3, 2.3)
            arch(m, "glass", "-x", -4.5, a, z, 1.3, 2.3)
            arch(m, "glass", "-y", -4.5, a, z, 1.3, 2.3)
    m.box(c("brownroof"), 4.5, 4.62, -0.7, 0.7, 0, 2.6)
    lathe(m, c("red"), 0, 0, [(6.2, 11.6), (3.5, 14.0), (0, 23)], sides=8, phase=math.pi / 8, sx=1.0, sy=1.0)
    lathe(m, c("red"), 0, 0, [(0, 11.6), (6.2, 11.6)], sides=8, phase=math.pi / 8)
    # dormers on the spire
    for a in (0, 90):
        if a == 0:
            m.box(c("cream"), 3.0, 5.4, -0.8, 0.8, 11.6, 13.4)
            m.prism_roof(c("green"), c("cream"), 2.8, 5.6, -1.0, 1.0, 13.4, 14.4)
            m.box("glass", 5.4, 5.48, -0.45, 0.45, 12.0, 13.1)
        else:
            m.box(c("cream"), -0.8, 0.8, 3.0, 5.4, 11.6, 13.4)
            roof_y(m, c("green"), c("cream"), -1.0, 1.0, 2.8, 5.6, 13.4, 14.4)
            m.box("glass", -0.45, 0.45, 5.4, 5.48, 12.0, 13.1)
    m.box("metal", -0.1, 0.1, -0.1, 0.1, 22.5, 25)
    m.save("houses_south_toy_church.glb")
    return m


def pavilion(m, roof, top_floor, base=None, lantern=False):
    """An open tower: floors on four white columns under a big sloping roof."""
    for x in (-5.5, 5.5):
        for y in (-5.5, 5.5):
            column(m, c("white"), x, y, 0, 12, 0.8, sides=10)
    if base:
        m.box(base, -4.5, 4.5, -4.5, 4.5, 0, 3)
        face_windows(m, "glass", "+x", -4.5, 4.5, 4.5, (1.6,), 3)
        face_windows(m, "glass", "+y", -4.5, 4.5, 4.5, (1.6,), 3)
    for z in ((3, 7) if not base else (3.0, 7.0)):
        m.box(top_floor, -5.6, 5.6, -5.6, 5.6, z, z + 0.4)
        # lattice railing
        m.box(top_floor, -5.0, 5.0, -5.0, 5.0, z + 0.4, z + 2.4)
        face_windows(m, c("bluetile") if not base else "glass", "+x", -5, 5, 5.0, (z + 1.4,), 4, size=(1.4, 1.2))
        face_windows(m, c("bluetile") if not base else "glass", "+y", -5, 5, 5.0, (z + 1.4,), 4, size=(1.4, 1.2))
        face_windows(m, c("bluetile") if not base else "glass", "-x", -5, 5, -5.0, (z + 1.4,), 4, size=(1.4, 1.2))
        face_windows(m, c("bluetile") if not base else "glass", "-y", -5, 5, -5.0, (z + 1.4,), 4, size=(1.4, 1.2))
    m.box(c("white"), -6.6, 6.6, -6.6, 6.6, 12, 12.8)
    box8(m, roof, [(-6.8, -6.8, 12.8), (6.8, -6.8, 12.8), (6.8, 6.8, 12.8), (-6.8, 6.8, 12.8)],
         [(-4.0, -4.0, 17), (4.0, -4.0, 17), (4.0, 4.0, 17), (-4.0, 4.0, 17)])


def toy_pink_pavilion():
    """92: a tower of open floors on white columns under a pink roof."""
    m = Model()
    pavilion(m, c("pink"), c("white"))
    m.box(c("white"), -4.0, 4.0, -4.0, 4.0, 17, 17.4)
    m.box(c("pink"), -2.5, 2.5, -2.5, 2.5, 17.4, 17.6)
    m.box(c("red"), -0.8, 0.8, -0.8, 0.8, 17.6, 17.8)
    m.save("houses_south_toy_pink_pavilion.glb")
    return m


def toy_green_pavilion():
    """94: an open tower on white columns with a green roof, dormers and a little lantern."""
    m = Model()
    pavilion(m, c("green"), c("cream"), base=c("pinkbrick"))
    m.box(c("cream"), -4.0, 4.0, -4.0, 4.0, 17, 17.4)
    m.box(c("cream"), -1.6, 1.6, -1.6, 1.6, 17.4, 19.4)
    face_windows(m, "glass", "+x", -1.6, 1.6, 1.6, (18.4,), 1, size=(1.4, 1.2))
    face_windows(m, "glass", "+y", -1.6, 1.6, 1.6, (18.4,), 1, size=(1.4, 1.2))
    m.pyramid(c("green"), -2.2, 2.2, -2.2, 2.2, 19.4, 22)
    # dormers on the big roof
    m.box(c("cream"), 4.4, 5.6, -1.1, 1.1, 13.2, 15.0)
    m.box("glass", 5.6, 5.68, -0.6, 0.6, 13.6, 14.6)
    m.prism_roof(c("green"), c("cream"), 4.2, 5.9, -1.3, 1.3, 15.0, 15.9)
    m.box(c("cream"), -1.1, 1.1, 4.4, 5.6, 13.2, 15.0)
    m.box("glass", -0.6, 0.6, 5.6, 5.68, 13.6, 14.6)
    roof_y(m, c("green"), c("cream"), -1.3, 1.3, 4.2, 5.9, 15.0, 15.9)
    m.save("houses_south_toy_green_pavilion.glb")
    return m


def toy_log_cabin():
    """93: a little log cabin with a striped green roof and a chimney."""
    m = Model()
    walls(m, c("logs"), -4, 3, -5, 4, 0, 3)
    for z in (0.5, 1.1, 1.7, 2.3, 2.9):
        m.cylinder("wood", -4.3, 3.3, -5.1, z, 0.25, sides=6)
        m.cylinder("wood", -4.3, 3.3, 4.1, z, 0.25, sides=6)
    m.prism_roof(c("green"), c("logs"), -4.8, 3.8, -5.8, 4.8, 3, 6)
    # stripes on the roof
    for x in (-3.0, -0.5, 2.0):
        m.quad(c("yellow"), (x, -5.8, 3.05), (x + 0.6, -5.8, 3.05), (x + 0.6, -0.5, 6.05), (x, -0.5, 6.05))
        m.quad(c("yellow"), (x + 0.6, 4.8, 3.05), (x, 4.8, 3.05), (x, -0.5, 6.05), (x + 0.6, -0.5, 6.05))
    m.box("stone", -2.5, -1.3, 1.5, 2.7, 4, 7)
    sphere(m, c("leaf"), -1.9, 2.1, 7.4, 0.6, sides=8, rings=4)
    m.box("door", 3, 3.1, -1, 0.4, 0, 2.2)
    m.box("glass", 3, 3.08, 1.4, 2.6, 1.0, 2.1)
    m.box("glass", -2, -0.6, 4, 4.08, 1.0, 2.1)
    m.save("houses_south_toy_log_cabin.glb")
    return m


def toy_striped_house():
    """95: a two-storey house painted in stripes with a blue roof and a TV aerial."""
    m = Model()
    x0, x1, y0, y1 = -5, 4.5, -5.5, 5
    for i in range(6):
        mat = "company" if i % 2 == 0 else c("yellow")
        walls(m, mat, x0, x1, y0, y1, i * 1.1, (i + 1) * 1.1)
    m.box(c("bluedark"), x0 - 0.1, x1 + 0.1, y0 - 0.1, y1 + 0.1, 6.6, 6.9)
    hip_roof(m, c("bluetile"), x0 - 0.5, x1 + 0.5, y0 - 0.5, y1 + 0.5, 6.9, 10.0)
    face_windows(m, "glass", "+x", y0, y1, x1, (1.8, 5.0), 3, size=(1.3, 1.4), skip=())
    face_windows(m, "glass", "+y", x0, x1, y1, (1.8, 5.0), 3, size=(1.3, 1.4))
    face_windows(m, "glass", "-x", y0, y1, x0, (1.8, 5.0), 3, size=(1.3, 1.4))
    face_windows(m, "glass", "-y", x0, x1, y0, (1.8, 5.0), 3, size=(1.3, 1.4))
    m.box("door", x1, x1 + 0.1, -2.6, -1.4, 0, 2.4)
    m.box(c("bluedark"), -3.5, -2.3, -4, -2.8, 8, 11)
    tube(m, "metal", (0, 1.5, 9.5), (0, 1.5, 12.5), 0.08, 4)
    tube(m, "metal", (0, 0.3, 12), (0, 2.7, 12), 0.06, 4)
    tube(m, "metal", (0, 0.6, 11.3), (0, 2.4, 11.3), 0.06, 4)
    m.save("houses_south_toy_striped_house.glb")
    return m


def toy_brick_house():
    """96: a pink brick house of three storeys with a blue-tiled edge on its flat roof and a bent pipe."""
    m = Model()
    x0, x1, y0, y1, h = -5, 5, -5, 5, 10.5
    m.box(c("pinkbrick"), x0, x1, y0, y1, 0, h)
    m.box("company", x0 - 0.1, x1 + 0.1, y0 - 0.1, y1 + 0.1, h - 0.1, h + 0.2)
    # blue tiled parapet sloping inwards
    box8(m, c("bluetile"), [(x0 - 0.4, y0 - 0.4, h + 0.2), (x1 + 0.4, y0 - 0.4, h + 0.2), (x1 + 0.4, y1 + 0.4, h + 0.2), (x0 - 0.4, y1 + 0.4, h + 0.2)],
         [(x0 + 1.2, y0 + 1.2, h + 1.6), (x1 - 1.2, y0 + 1.2, h + 1.6), (x1 - 1.2, y1 - 1.2, h + 1.6), (x0 + 1.2, y1 - 1.2, h + 1.6)])
    m.box(c("dirt"), x0 + 1.2, x1 - 1.2, y0 + 1.2, y1 - 1.2, h + 1.6, h + 1.62)
    face_windows(m, c("green"), "+x", y0, y1, x1, (1.8, 5.3, 8.8), 3, size=(1.3, 1.6))
    face_windows(m, c("green"), "+y", x0, x1, y1, (1.8, 5.3, 8.8), 3, size=(1.3, 1.6))
    face_windows(m, c("green"), "-x", y0, y1, x0, (1.8, 5.3, 8.8), 3, size=(1.3, 1.6))
    face_windows(m, c("green"), "-y", x0, x1, y0, (1.8, 5.3, 8.8), 3, size=(1.3, 1.6))
    m.box("door", x1, x1 + 0.12, 1.0, 2.2, 0, 2.4)
    # a bent pipe chimney up the front-right corner
    tube(m, c("yellow"), (x1 + 0.4, y0 - 0.4, 6), (x1 + 0.4, y0 - 0.4, h + 4), 0.3, 8)
    tube(m, c("yellow"), (x1 + 0.4, y0 - 0.4, h + 4), (x1 - 1.2, y0 - 0.4, h + 4), 0.3, 8)
    tube(m, c("yellow"), (x1 + 0.4, y0 - 0.4, 6), (x1 - 0.2, y0 - 0.4, 6), 0.3, 8)
    m.save("houses_south_toy_brick_house.glb")
    return m


def toy_blue_house():
    """97: a pale house with a blue roof, window boxes and two little chimneys."""
    m = Model()
    x0, x1, y0, y1 = -5, 4.5, -5.5, 5.5
    walls(m, "company", x0, x1, y0, y1, 0, 6.4)
    m.box(c("ice"), x0 - 0.05, x1 + 0.05, y0 - 0.05, y1 + 0.05, 0, 0.6)
    m.prism_roof(c("bluetile"), "company", x0 - 0.5, x1 + 0.5, y0 - 0.6, y1 + 0.6, 6.4, 9.6)
    face_windows(m, "glass", "+x", y0, y1, x1, (1.8, 4.9), 3, size=(1.3, 1.5), skip=())
    face_windows(m, c("leaf"), "+x", y0, y1, x1, (0.85, 3.95), 3, size=(1.5, 0.4), depth=0.4)
    face_windows(m, "glass", "+y", x0, x1, y1, (1.8, 4.9), 2, size=(1.3, 1.5))
    face_windows(m, c("leaf"), "+y", x0, x1, y1, (0.85, 3.95), 2, size=(1.5, 0.4), depth=0.4)
    face_windows(m, "glass", "-x", y0, y1, x0, (1.8, 4.9), 3, size=(1.3, 1.5))
    face_windows(m, "glass", "-y", x0, x1, y0, (1.8, 4.9), 2, size=(1.3, 1.5))
    for y in (-3, 2.5):
        m.box(c("green"), -0.6, 0.4, y - 0.5, y + 0.5, 8.5, 10.6)
        m.pyramid(c("green"), -0.9, 0.7, y - 0.8, y + 0.8, 10.6, 11.6)
    m.box("door", x1, x1 + 0.1, -0.6, 0.6, 0, 2.3)
    m.save("houses_south_toy_blue_house.glb")
    return m


def toy_office():
    """98: a white office block with a brown roof edge and a box on the roof."""
    m = Model()
    x0, x1, y0, y1, h = -6, 6, -6, 6, 20
    m.box("company", x0, x1, y0, y1, 0, h)
    m.box(c("brownroof"), x0 - 0.3, x1 + 0.3, y0 - 0.3, y1 + 0.3, h, h + 1.2)
    m.box(c("yellow"), x0 - 0.35, x1 + 0.35, y0 - 0.35, y1 + 0.35, h + 0.4, h + 0.7)
    m.box(c("sandroof"), x0, x1, y0, y1, h + 1.2, h + 1.25)
    m.box(c("white"), -3, 0.5, -1, 2.5, h + 1.25, h + 3.2)
    m.box(c("bluetile"), -2.7, 0.2, -0.7, 2.2, h + 3.2, h + 3.3)
    zs = [2.0 + 3.0 * i for i in range(6)]
    face_windows(m, "glass", "+x", y0, y1, x1, zs, 4, size=(1.7, 2.0))
    face_windows(m, "glass", "+y", x0, x1, y1, zs, 4, size=(1.7, 2.0))
    face_windows(m, "glass", "-x", y0, y1, x0, zs, 4, size=(1.7, 2.0))
    face_windows(m, "glass", "-y", x0, x1, y0, zs, 4, size=(1.7, 2.0))
    m.box("dark", x1, x1 + 0.12, 2, 4, 0, 2.4)
    m.save("houses_south_toy_office.glb")
    return m


def toy_shoe():
    """99 + 100: the old woman's shoe, a house in a boot, on a 1 by 2 plot (32 along y)."""
    m = Model()
    lt, sole = c("leather"), c("sole")
    # sole and foot: an elongated half-capsule running along y, toe at +y
    m.box(sole, -5.2, 5.2, -12.5, 9.0, 0, 0.8)
    dome(m, sole, 0, 9.0, 0, 5.2, 0.8, sides=16, rings=1, sx=1.0, sy=1.3)
    m.box(lt, -4.8, 4.8, -12.0, 9.0, 0.8, 5.0)
    dome(m, lt, 0, 9.0, 0.8, 4.8, 4.2, sides=16, rings=5, sx=1.0, sy=1.35)
    lathe(m, lt, 0, -12.0, [(4.8, 0.8), (4.8, 5.0)], sides=16, sx=1.0, sy=0.6)
    # the leg of the boot rising at the back
    m.box(lt, -4.6, 4.6, -13.5, -3.5, 0.8, 16)
    m.box(sole, -4.8, 4.8, -13.7, -3.3, 0, 2.5)  # heel
    m.box(c("brownroof"), -4.8, 4.8, -13.7, -3.3, 16, 16.4)
    # laces up the front of the leg
    for z in (6.5, 8.5, 10.5, 12.5, 14.5):
        box8(m, c("yellow"), [(4.6, -6.8, z), (4.75, -6.8, z), (4.75, -3.6, z + 0.7), (4.6, -3.6, z + 0.7)],
             [(4.6, -6.8, z + 0.35), (4.75, -6.8, z + 0.35), (4.75, -3.6, z + 1.05), (4.6, -3.6, z + 1.05)])
        box8(m, c("yellow"), [(4.6, -10.2, z + 0.7), (4.75, -10.2, z + 0.7), (4.75, -6.8, z), (4.6, -6.8, z)],
             [(4.6, -10.2, z + 1.05), (4.75, -10.2, z + 1.05), (4.75, -6.8, z + 0.35), (4.6, -6.8, z + 0.35)])
    # a green roof with a chimney on the leg
    m.prism_roof(c("leaf"), lt, -5.4, 5.4, -14.3, -2.7, 16.4, 19.5)
    m.box("brick", -2.5, -1.2, -10.5, -9.2, 17.5, 21)
    # windows and a door
    for y in (-11, -6):
        m.box("glass", 4.6, 4.68, y - 0.8, y + 0.8, 2.8, 4.6)
        m.box("frame", 4.68, 4.72, y - 0.06, y + 0.06, 2.8, 4.6)
    for (x, z) in ((-2.4, 9), (2.4, 9), (-2.4, 13), (2.4, 13)):
        m.box("glass", x - 0.8, x + 0.8, -3.5, -3.42, z - 0.9, z + 0.9)
    for y in (-0.5, 4.5):
        m.box("glass", 4.75, 4.83, y - 0.8, y + 0.8, 1.9, 3.6)
    m.box("door", 4.75, 4.85, 1.4, 2.6, 0.8, 3.2)
    m.save("houses_south_toy_shoe.glb")
    return m


def toy_brick_tower():
    """101: a tall orange brick block of flats with green windows and a roof garden."""
    m = Model()
    x0, x1, y0, y1, h = -5.5, 5.5, -5.5, 5.5, 26
    m.box(c("orangebrick"), x0, x1, y0, y1, 0, h)
    for z in range(3, 26, 3):
        m.box("company", x0 - 0.1, x1 + 0.1, y0 - 0.1, y1 + 0.1, z - 0.15, z + 0.1)
    m.box("company", x0 - 0.2, x1 + 0.2, y0 - 0.2, y1 + 0.2, h, h + 0.6)
    m.box(c("green"), x0 + 0.4, x1 - 0.4, y0 + 0.4, y1 - 0.4, h + 0.6, h + 0.7)
    m.box(c("orangebrick"), -1.5, 1.5, -1.5, 1.5, h + 0.6, h + 2.2)
    zs = [1.5 + 3 * i for i in range(9)]
    face_windows(m, c("green"), "+x", y0, y1, x1, zs, 4, size=(1.2, 1.7))
    face_windows(m, c("green"), "+y", x0, x1, y1, zs, 4, size=(1.2, 1.7))
    face_windows(m, c("green"), "-x", y0, y1, x0, zs, 4, size=(1.2, 1.7))
    face_windows(m, c("green"), "-y", x0, x1, y0, zs, 4, size=(1.2, 1.7))
    m.box("door", x1, x1 + 0.15, -0.7, 0.7, 0, 2.4)
    m.save("houses_south_toy_brick_tower.glb")
    return m


def toy_igloo():
    """102: an igloo of snow blocks with an entrance tunnel, on a patch of ice."""
    m = Model()
    m.box(c("ice"), -7.5, 7.5, -7.5, 7.5, 0, 0.1)
    dome(m, c("snow"), -1, 0, 0.1, 5.2, 4.6, sides=16, rings=6)
    # block joints
    for z in (1.4, 2.7, 3.8):
        r = 5.2 * math.cos(math.asin(min(1, (z - 0.1) / 4.6)))
        lathe(m, "concrete", -1, 0, [(r + 0.06, z - 0.06), (r + 0.06, z + 0.06)], sides=16)
    # tunnel to the front
    m.box(c("snow"), 2.5, 6, -1.7, 1.7, 0.1, 1.2)
    m.cylinder(c("snow"), 2.5, 6, 0, 1.2, 1.7, sides=12)
    arch(m, "dark", "+x", 6.0, 0, 0.1, 2.0, 2.2)
    # fishing hole
    lathe(m, c("bluedark"), 4, 5, [(0, 0.12), (0.9, 0.12)], sides=10)
    m.save("houses_south_toy_igloo.glb")
    return m


def toy_tepees():
    """103: two tepees with poles sticking out of their tops."""
    m = Model()
    for (x, y, r, h) in ((1.5, -3.0, 3.4, 9.0), (-2.5, 3.5, 3.0, 8.0)):
        lathe(m, c("canvas"), x, y, [(r, 0), (0.4, h * 0.85), (0, h * 0.88)], sides=12)
        for k in range(5):
            a = 2 * math.pi * k / 5 + 0.3
            tube(m, "wood", (x + 0.3 * math.cos(a), y + 0.3 * math.sin(a), h * 0.8),
                 (x + 0.9 * math.cos(a), y + 0.9 * math.sin(a), h * 1.08), 0.08, 4)
        # door flap and a coloured band
        lathe(m, c("red"), x, y, [(r * 0.78 + 0.05, h * 0.2), (r * 0.72 + 0.05, h * 0.26)], sides=12)
        zt = 2.8
        rt = r + (0.4 - r) * zt / (h * 0.85) + 0.1
        m.triangle("dark", (x + r + 0.05, y - 1.0, 0.02), (x + r + 0.05, y + 1.0, 0.02), (x + rt, y, zt))
    m.save("houses_south_toy_tepees.glb")
    return m


def toy_candy_shop():
    """104: a white sweet shop with a red chequered roof, a chimney and a shop sign."""
    m = Model()
    x0, x1, y0, y1, h = -5, 5, -5, 5, 13
    m.box(c("white"), x0, x1, y0, y1, 0, h)
    m.box("glass", x1, x1 + 0.1, y0 + 0.6, y1 - 0.6, 0.4, 2.8)
    m.box("glass", x0 + 0.6, x1 - 0.6, y1, y1 + 0.1, 0.4, 2.8)
    m.box("company", x1, x1 + 1.4, y0, y1, 3.0, 3.3)  # awning
    m.box("company", x0, x1, y1, y1 + 1.4, 3.0, 3.3)
    m.box(c("red"), x1 + 0.1, x1 + 0.3, y0 + 0.5, y1 - 0.5, 3.5, 4.6)  # sign
    m.box(c("yellow"), x1 + 0.3, x1 + 0.35, y0 + 1.0, y1 - 1.0, 3.8, 4.3)
    zs = [6.0, 9.0, 12.0]
    face_windows(m, "glass", "+x", y0, y1, x1, zs, 3, size=(1.3, 1.8))
    face_windows(m, "glass", "+y", x0, x1, y1, zs, 3, size=(1.3, 1.8))
    face_windows(m, "glass", "-x", y0, y1, x0, zs, 3, size=(1.3, 1.8))
    face_windows(m, "glass", "-y", x0, x1, y0, zs, 3, size=(1.3, 1.8))
    m.box(c("red"), x0 - 0.3, x1 + 0.3, y0 - 0.3, y1 + 0.3, h, h + 0.4)
    # chequered pyramid roof in two colours
    zt = h + 4.5
    corners = [(x1 + 0.3, y0 - 0.3), (x1 + 0.3, y1 + 0.3), (x0 - 0.3, y1 + 0.3), (x0 - 0.3, y0 - 0.3)]
    for k in range(4):
        (ax, ay), (bx, by) = corners[k], corners[(k + 1) % 4]
        # split each face into 4 triangles in alternating colours
        mid = ((ax + bx) / 2, (ay + by) / 2, h + 0.4)
        top = (0, 0, zt)
        ua = ((ax + 0) / 2, (ay + 0) / 2, (h + 0.4 + zt) / 2)
        ub = ((bx + 0) / 2, (by + 0) / 2, (h + 0.4 + zt) / 2)
        um = ((mid[0] + 0) / 2, (mid[1] + 0) / 2, (h + 0.4 + zt) / 2)
        a, b = (ax, ay, h + 0.4), (bx, by, h + 0.4)
        m.quad(c("red"), a, mid, um, ua)
        m.quad(c("pink"), mid, b, ub, um)
        m.triangle(c("pink"), ua, um, top)
        m.triangle(c("red"), um, ub, top)
    m.box(c("white"), -2.5, -1.3, 1.5, 2.7, h + 1.5, h + 6)
    m.box(c("red"), -2.7, -1.1, 1.3, 2.9, h + 6, h + 6.4)
    m.save("houses_south_toy_candy_shop.glb")
    return m


def toy_bar():
    """105: a white building with brown roofs and a bar with a sign in front."""
    m = Model()
    walls(m, c("white"), -6, 2, -5.5, 3.5, 0, 10)
    m.prism_roof(c("brownroof"), c("white"), -6.6, 2.6, -6.2, 4.2, 10, 13)
    m.box(c("white"), -2, -0.8, -3, -1.8, 11, 14.5)
    m.box(c("brownroof"), -2.2, -0.6, -3.2, -1.6, 14.5, 14.9)
    face_windows(m, "glass", "+x", -5.5, 3.5, 2, (4.6, 7.6), 3, size=(1.2, 1.7))
    face_windows(m, "glass", "+y", -6, 2, 3.5, (1.8, 4.6, 7.6), 3, size=(1.2, 1.7))
    face_windows(m, "glass", "-x", -5.5, 3.5, -6, (1.8, 4.6, 7.6), 3, size=(1.2, 1.7))
    face_windows(m, "glass", "-y", -6, 2, -5.5, (1.8, 4.6, 7.6), 3, size=(1.2, 1.7))
    # the bar in front
    m.box(c("white"), 2, 6.5, -5.5, 6.5, 0, 3.2)
    lean_to(m, c("brownroof"), 1.8, 7.0, -5.8, 6.8, 3.0, 4.6, low_side="+x")
    m.box("glass", 6.5, 6.6, -4.5, 1.5, 0.6, 2.4)
    m.box("door", 6.5, 6.6, 3.0, 4.4, 0, 2.4)
    m.box("glass", 2.5, 6, 6.5, 6.6, 0.6, 2.4)
    # sign on a frame over the bar roof, three letter blocks
    m.box("dark", 4.6, 4.8, -3.5, 3.5, 4.2, 6.2)
    for y in (-2.2, 0, 2.2):
        m.box(c("yellow"), 4.8, 4.9, y - 0.7, y + 0.7, 4.5, 5.9)
    m.save("houses_south_toy_bar.glb")
    return m


def toy_pink_tower():
    """106: a tall pink block of flats with a grey hipped roof."""
    m = Model()
    x0, x1, y0, y1, h = -5, 5, -5.5, 5.5, 26
    m.box(c("pinkbrick"), x0 - 0.2, x1 + 0.2, y0 - 0.2, y1 + 0.2, 0, 3.2)
    m.box(c("pink"), x0, x1, y0, y1, 3.2, h)
    m.box(c("white"), x0 - 0.2, x1 + 0.2, y0 - 0.2, y1 + 0.2, h, h + 0.4)
    hip_roof(m, "slate", x0 - 0.4, x1 + 0.4, y0 - 0.4, y1 + 0.4, h + 0.4, h + 4.0)
    zs = [4.8 + 2.8 * i for i in range(8)]
    face_windows(m, "glass", "+x", y0, y1, x1, zs, 4, size=(1.1, 1.6))
    face_windows(m, "glass", "+y", x0, x1, y1, zs, 4, size=(1.1, 1.6))
    face_windows(m, "glass", "-x", y0, y1, x0, zs, 4, size=(1.1, 1.6))
    face_windows(m, "glass", "-y", x0, x1, y0, zs, 4, size=(1.1, 1.6))
    m.box("glass", x1 + 0.2, x1 + 0.3, y0 + 1, y1 - 1, 0.5, 2.6)
    m.box("door", x0 + 1.5, x0 + 3, y1 + 0.2, y1 + 0.3, 0, 2.4)
    m.save("houses_south_toy_pink_tower.glb")
    return m


def toy_statue():
    """107: a big toy clown figure on a red plinth."""
    m = Model()
    m.box(c("paving"), -6, 6, -6, 6, 0, 0.3)
    m.box(c("red"), -3.2, 3.2, -3.2, 3.2, 0.3, 4.5)
    m.box(c("yellow"), 3.2, 3.3, -2, 2, 1.5, 3.3)
    m.box("company", -3.5, 3.5, -3.5, 3.5, 4.5, 5.0)
    # body
    lathe(m, c("red"), 0, 0, [(2.6, 5.0), (2.4, 7.0), (1.6, 9.5), (0.0, 10.0)], sides=14)
    lathe(m, c("white"), 0, 0, [(2.65, 6.4), (2.5, 7.2)], sides=14)
    # arms
    tube(m, c("red"), (0, 1.4, 9), (1.2, 2.6, 7.2), 0.6, 8)
    tube(m, c("red"), (0, -1.4, 9), (1.2, -2.6, 7.2), 0.6, 8)
    sphere(m, c("white"), 1.3, 2.7, 7.0, 0.65, sides=8, rings=4)
    sphere(m, c("white"), 1.3, -2.7, 7.0, 0.65, sides=8, rings=4)
    # ruff collar and head
    lathe(m, c("white"), 0, 0, [(0, 9.6), (2.0, 9.9), (0, 10.3)], sides=14)
    sphere(m, c("skin"), 0, 0, 11.8, 1.7, sides=14, rings=8)
    sphere(m, c("red"), 1.65, 0, 11.6, 0.4, sides=8, rings=4)  # nose
    m.box("dark", 1.4, 1.6, 0.45, 0.75, 12.3, 12.6)
    m.box("dark", 1.4, 1.6, -0.75, -0.45, 12.3, 12.6)
    lathe(m, c("yellow"), 0, 0, [(1.4, 13.0), (0, 15.6)], sides=12)
    sphere(m, c("red"), 0, 0, 15.7, 0.4, sides=8, rings=4)
    m.save("houses_south_toy_statue.glb")
    return m


def toy_teapot():
    """108: a blue teapot house with a green lid, a spout and a handle."""
    m = Model()
    tp = c("teapot")
    prof = [(0, 0), (3.8, 0), (4.9, 1.6), (5.3, 3.4), (5.0, 5.2), (4.0, 6.6), (2.6, 7.3)]
    lathe(m, tp, 0, 0, prof, sides=18)
    lathe(m, c("green"), 0, 0, [(2.8, 7.2), (2.8, 7.5), (2.0, 8.4), (0, 8.7)], sides=18)
    sphere(m, c("green"), 0, 0, 9.1, 0.55, sides=10, rings=5)

    def radius(z):
        for (r0, z0), (r1, z1) in zip(prof, prof[1:]):
            if z0 <= z <= z1 and z1 > z0:
                return r0 + (r1 - r0) * (z - z0) / (z1 - z0)
        return prof[-1][0]

    def on_body(angle, out=0.0):
        a = math.radians(angle)
        return lambda r, z: (r * math.cos(a), r * math.sin(a), z)

    # the spout points to the front right corner, the handle to the back left corner
    sp = on_body(-45)
    tube(m, tp, sp(4.6, 2.4), sp(7.2, 5.0), 0.85, 10)
    tube(m, tp, sp(7.2, 5.0), sp(8.6, 7.0), 0.6, 10)
    tube(m, tp, sp(8.6, 7.0), sp(9.2, 7.4), 0.45, 8)
    hd = on_body(135)
    pts = []
    for k in range(9):
        t = math.pi * k / 8
        pts.append(hd(4.4 + 3.0 * math.sin(t), 5.8 - 3.8 * k / 8))
    for a, b in zip(pts, pts[1:]):
        tube(m, tp, a, b, 0.5, 8)

    def panel(mat, angle, z0, z1, half):
        """A flat door or window on the body, facing out at an angle."""
        a = math.radians(angle)
        nx, ny = math.cos(a), math.sin(a)
        ux, uy = -ny, nx
        r0, r1 = radius(z0) + 0.15, radius(z1) + 0.15
        m.quad(mat, (r0 * nx - half * ux, r0 * ny - half * uy, z0), (r0 * nx + half * ux, r0 * ny + half * uy, z0),
               (r1 * nx + half * ux, r1 * ny + half * uy, z1), (r1 * nx - half * ux, r1 * ny - half * uy, z1))

    panel("door", 20, 0.4, 2.8, 0.7)
    for angle in (-15, 60, 100):
        panel(c("yellow"), angle, 3.6, 5.0, 0.6)
    m.save("houses_south_toy_teapot.glb")
    return m


def toy_piggy_bank():
    """109: a red money box with a coin slot on top and a combination dial on the front."""
    m = Model()
    r = 0.8
    # a rounded box: the body plus rounded edges along z
    m.box(c("red"), -5 + r, 5 - r, -5, 5, 0, 9)
    m.box(c("red"), -5, 5, -5 + r, 5 - r, 0, 9)
    for x in (-5 + r, 5 - r):
        for y in (-5 + r, 5 - r):
            column(m, c("red"), x, y, 0, 9, r, sides=8)
    m.box(c("red"), -4.6, 4.6, -4.6, 4.6, 9, 9.4)
    m.box("dark", -0.4, 0.4, -2.2, 2.2, 9.4, 9.45)  # coin slot
    m.box(c("yellow"), -0.1, 0.1, -1.0, 1.0, 9.4, 10.6)  # a coin dropping in
    # dial and handle on the front
    m.cylinder("metal", 5, 5.35, 0, 5.2, 1.6, sides=14, caps="hub")
    m.cylinder("dark", 5.35, 5.6, 0, 5.2, 0.5, sides=10)
    m.box("hub", 5.0, 5.4, -2.8, -2.3, 3, 7.4)
    # a little door and windows so people can live in it
    m.box("door", 5.0, 5.12, 1.6, 3.0, 0, 2.6)
    m.box("glass", -2.5, -1.0, 5.0, 5.08, 3.5, 5.0)
    m.box("glass", 1.0, 2.5, 5.0, 5.08, 3.5, 5.0)
    m.save("houses_south_toy_piggy_bank.glb")
    return m


MODELS = [
    (st_villa, [78]),
    (st_villa_l, [79]),
    (st_cottage, [80]),
    (st_shacks, [81]),
    (st_tower_flats, [82]),
    (st_mission_church, [83]),
    (st_house_garden, [84]),
    (st_balcony_flats, [85]),
    (st_band_flats, [86]),
    (st_office_pair, [87, 88]),
    (st_flats_tank, [89]),
    (st_tower_atrium, [90]),
    (toy_church, [91]),
    (toy_pink_pavilion, [92]),
    (toy_log_cabin, [93]),
    (toy_green_pavilion, [94]),
    (toy_striped_house, [95]),
    (toy_brick_house, [96]),
    (toy_blue_house, [97]),
    (toy_office, [98]),
    (toy_shoe, [99, 100]),
    (toy_brick_tower, [101]),
    (toy_igloo, [102]),
    (toy_tepees, [103]),
    (toy_candy_shop, [104]),
    (toy_bar, [105]),
    (toy_pink_tower, [106]),
    (toy_statue, [107]),
    (toy_teapot, [108]),
    (toy_piggy_bank, [109]),
]


def build():
    buildings = []
    for func, ids in MODELS:
        func()
        name = "houses_south_" + func.__name__.removeprefix("st_") + ".glb"
        buildings.append({"type": "house", "ids": ids, "model": name})
    return {"vehicles": [], "buildings": buildings}


if __name__ == "__main__":
    print(build())
