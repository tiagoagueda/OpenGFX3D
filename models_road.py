"""Road vehicles of all climates: buses of Toyland and lorries for every cargo.

Road vehicle ids count from 0 in the order of src/table/engines.h (0 is the MPS Regal Bus).
The lorries share a few cabs (an early bonneted one, a flat-fronted one, a rounded mid-era one and a
playful Toyland one) and get a body for their cargo; loads use materials named "load...".
"""

import math

from gfx3d import MATERIALS, Model

MATERIALS.update({
    "road_white": (0.94, 0.94, 0.92),
    "road_armour": (0.46, 0.49, 0.47),
    "road_water": (0.62, 0.78, 0.90),
    "road_chrome": (0.82, 0.84, 0.86),
    "road_red": (0.80, 0.18, 0.16),
    "road_toy_pink": (0.96, 0.58, 0.74),
    "road_toy_yellow": (0.99, 0.84, 0.24),
    "road_toy_red": (0.90, 0.24, 0.22),
    "road_toy_green": (0.36, 0.76, 0.36),
    "road_toy_blue": (0.32, 0.58, 0.92),
    "road_toy_purple": (0.62, 0.42, 0.86),
    "road_cola": (0.30, 0.14, 0.08),
    "load_road_grain": (0.88, 0.74, 0.36),
    "load_road_copper": (0.42, 0.52, 0.40),
    "load_road_wood": (0.48, 0.33, 0.20),
    "load_road_wood_end": (0.82, 0.66, 0.44),
    "load_road_steel": (0.60, 0.62, 0.66),
    "load_road_steel_dark": (0.40, 0.42, 0.46),
    "load_road_paper": (0.95, 0.94, 0.89),
    "load_road_crate": (0.66, 0.50, 0.30),
    "load_road_fruit": (0.94, 0.56, 0.14),
    "load_road_fruit_red": (0.82, 0.16, 0.14),
    "load_road_cow": (0.52, 0.34, 0.22),
    "load_road_cow_white": (0.92, 0.90, 0.86),
    "load_road_drum": (0.34, 0.22, 0.18),
    "load_road_drum_top": (0.55, 0.42, 0.30),
    "load_road_sugar": (0.98, 0.98, 0.97),
    "load_road_candyfloss": (0.99, 0.70, 0.84),
    "load_road_candyfloss_blue": (0.70, 0.84, 0.99),
    "load_road_toffee": (0.64, 0.40, 0.16),
    "load_road_toffee_light": (0.86, 0.66, 0.36),
    "load_road_battery": (0.16, 0.16, 0.18),
    "load_road_battery_top": (0.86, 0.60, 0.26),
    "load_road_bottle": (0.30, 0.66, 0.36),
    "load_road_bottle_cap": (0.90, 0.24, 0.22),
    "load_road_fizzy_crate": (0.98, 0.84, 0.30),
    "load_road_bubble": (0.78, 0.90, 1.00),
    "load_road_bubble_pink": (0.98, 0.82, 0.94),
})

L, W = 9.0, 3.1
X0, X1 = -L / 2, L / 2
Y0, Y1 = -W / 2, W / 2


# Shapes the toolkit does not have. They orient their faces outwards from a point inside, so they
# only work for convex pieces.

def tri_out(m, mat, a, b, c, centre):
    u = [b[i] - a[i] for i in range(3)]
    v = [c[i] - a[i] for i in range(3)]
    n = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]]
    mid = [(a[i] + b[i] + c[i]) / 3 - centre[i] for i in range(3)]
    if sum(n[i] * mid[i] for i in range(3)) < 0:
        b, c = c, b
    m.triangle(mat, a, b, c)


def hexa(m, mat, corners):
    """Eight corners: the bottom four in order around, then the top four in the same order."""
    centre = [sum(p[i] for p in corners) / 8 for i in range(3)]
    b, t = corners[:4], corners[4:]
    faces = [b, t] + [[b[i], b[(i + 1) % 4], t[(i + 1) % 4], t[i]] for i in range(4)]
    for f in faces:
        tri_out(m, mat, f[0], f[1], f[2], centre)
        tri_out(m, mat, f[0], f[2], f[3], centre)


def cyl(m, mat, axis, c, r, a0, a1, sides=12, cap=None, rz=None):
    """A closed cylinder along axis 'x', 'y' or 'z'; c is the centre in the other two axes."""
    cap = cap or mat
    rz = rz or r

    def point(a, u, v):
        if axis == "x":
            return (a, u, v)
        if axis == "y":
            return (u, a, v)
        return (u, v, a)

    am = (a0 + a1) / 2
    centre = point(am, c[0], c[1])
    ring = [(c[0] + r * math.cos(2 * math.pi * i / sides), c[1] + rz * math.sin(2 * math.pi * i / sides)) for i in range(sides)]
    for i in range(sides):
        (pu, pv), (qu, qv) = ring[i], ring[(i + 1) % sides]
        p0, p1, q0, q1 = point(a0, pu, pv), point(a1, pu, pv), point(a0, qu, qv), point(a1, qu, qv)
        tri_out(m, mat, p0, p1, q1, centre)
        tri_out(m, mat, p0, q1, q0, centre)
        tri_out(m, cap, point(a1, *c), p1, q1, centre)
        tri_out(m, cap, point(a0, *c), p0, q0, centre)


def sphere(m, mat, cx, cy, cz, r, rings=4, segs=8, squash=1.0):
    centre = (cx, cy, cz)

    def p(i, j):
        t = math.pi * i / rings
        f = 2 * math.pi * j / segs
        return (cx + r * math.sin(t) * math.cos(f), cy + r * math.sin(t) * math.sin(f), cz + r * squash * math.cos(t))

    for i in range(rings):
        for j in range(segs):
            a, b, c, d = p(i, j), p(i + 1, j), p(i + 1, j + 1), p(i, j + 1)
            if i > 0:
                tri_out(m, mat, a, b, d, centre)
            if i < rings - 1:
                tri_out(m, mat, b, c, d, centre)


def arch(m, mat, x0, x1, y0, y1, z0, h, sides=8, ends=None):
    """A rounded roof along x: half an elliptic cylinder standing on z0."""
    ends = ends or mat
    yc, w = (y0 + y1) / 2, (y1 - y0) / 2
    centre = ((x0 + x1) / 2, yc, z0 + 0.01)
    pts = [(yc + w * math.cos(math.pi * i / sides), z0 + h * math.sin(math.pi * i / sides)) for i in range(sides + 1)]
    for i in range(sides):
        (ay, az), (by, bz) = pts[i], pts[i + 1]
        tri_out(m, mat, (x0, ay, az), (x1, ay, az), (x1, by, bz), centre)
        tri_out(m, mat, (x0, ay, az), (x1, by, bz), (x0, by, bz), centre)
        tri_out(m, ends, (x1, yc, z0), (x1, ay, az), (x1, by, bz), centre)
        tri_out(m, ends, (x0, yc, z0), (x0, ay, az), (x0, by, bz), centre)


# Running gear and cabs.

def chassis(m, x0=X0 + 0.1, x1=X1 - 0.1, z0=0.55, z1=1.0):
    m.box("dark", x0, x1, -1.2, 1.2, z0, z1)


def wheels(m, xs, radius=0.62, width=0.45, toy=False):
    for x in xs:
        for y in (Y0 + 0.2, Y1 - 0.2):
            m.wheel(x, y, radius, width)
            if toy:
                s = 1 if y > 0 else -1
                cyl(m, "road_toy_yellow", "y", (x, radius), radius * 0.38, y + s * width / 2, y + s * (width / 2 + 0.06), sides=8)


def lights(m, xf, z0=1.2, z1=1.5):
    m.box("dark", xf, xf + 0.15, Y0 + 0.05, Y1 - 0.05, 0.65, 0.95)  # bumper
    for y in (Y0 + 0.2, Y1 - 0.7):
        m.box("light", xf - 0.04, xf + 0.06, y, y + 0.5, z0, z1)


def cab_bonnet(m, xf=X1, body="company"):
    """An early cab: a long bonnet with the engine, wings over the front wheels, a small cabin."""
    m.box(body, xf - 1.55, xf - 0.12, -0.95, 0.95, 1.0, 1.95)  # bonnet
    m.prism_roof(body, body, xf - 1.55, xf - 0.12, -0.95, 0.95, 1.95, 2.1)
    m.box("road_chrome", xf - 0.14, xf - 0.02, -0.85, 0.85, 1.0, 2.0)  # radiator
    m.box("dark", xf - 0.03, xf, -0.7, 0.7, 1.1, 1.85)
    for s in (-1, 1):
        ya, yb = sorted((s * 0.95, s * 1.55))
        hexa(m, "company_dark", [(xf - 1.9, ya, 1.0), (xf - 0.25, ya, 1.0), (xf - 0.25, yb, 1.0), (xf - 1.9, yb, 1.0),
                                 (xf - 1.75, ya, 1.45), (xf - 0.5, ya, 1.45), (xf - 0.5, yb, 1.45), (xf - 1.75, yb, 1.45)])
        cyl(m, "light", "x", (s * 1.2, 1.62), 0.17, xf - 0.55, xf - 0.35, sides=8)
    m.box("dark", xf - 0.05, xf + 0.1, Y0 + 0.1, Y1 - 0.1, 0.65, 0.9)  # bumper
    cx0, cx1 = xf - 3.1, xf - 1.55
    m.box(body, cx0, cx1, Y0, Y1, 0.85, 1.95)
    m.box("glass", cx0 + 0.08, cx1 - 0.06, Y0 + 0.06, Y1 - 0.06, 1.95, 2.65)
    for x in (cx0, cx1 - 0.14):
        for y in (Y0, Y1 - 0.14):
            m.box(body, x, x + 0.14, y, y + 0.14, 1.95, 2.65)
    m.box(body, cx0, cx0 + 0.14, Y0, Y1, 1.95, 2.65)  # back wall
    m.box(body, cx0 - 0.06, cx1 + 0.1, Y0 - 0.05, Y1 + 0.05, 2.65, 2.85)  # roof
    return cx0


def cab_flat(m, xf=X1, body="company"):
    """A modern cab-over: flat front, big windscreen, a sun visor."""
    cx0 = xf - 2.1
    m.box(body, cx0, xf, Y0, Y1, 0.8, 1.9)
    m.box("glass", cx0 + 0.1, xf - 0.05, Y0 + 0.05, Y1 - 0.05, 1.9, 2.8)
    m.box(body, cx0, cx0 + 0.3, Y0, Y1, 1.9, 2.8)
    for y in (Y0, Y1 - 0.14):
        m.box(body, xf - 0.14, xf, y, y + 0.14, 1.9, 2.8)
        m.box(body, xf - 1.1, xf - 0.95, y, y + 0.14, 1.9, 2.8)  # door pillar
    m.box(body, cx0, xf, Y0, Y1, 2.8, 3.1)
    m.box("company_dark", xf - 0.2, xf + 0.06, Y0 + 0.1, Y1 - 0.1, 3.1, 3.3)  # roof spoiler
    m.box("dark", xf, xf + 0.04, -1.0, 1.0, 1.0, 1.55)  # grille
    lights(m, xf, 1.0, 1.3)
    return cx0


def cab_round(m, xf=X1, body="company"):
    """A mid-era cab with a short nose and a raked windscreen."""
    cx0 = xf - 2.6
    m.box(body, xf - 0.9, xf, -1.35, 1.35, 0.85, 1.75)  # nose
    m.box("dark", xf, xf + 0.04, -0.9, 0.9, 1.05, 1.6)  # grille
    lights(m, xf, 1.15, 1.45)
    m.box(body, cx0, xf - 0.9, Y0, Y1, 0.85, 1.9)
    hexa(m, "glass", [(cx0 + 0.1, Y0 + 0.05, 1.75), (xf - 0.82, Y0 + 0.05, 1.75), (xf - 0.82, Y1 - 0.05, 1.75), (cx0 + 0.1, Y1 - 0.05, 1.75),
                      (cx0 + 0.1, Y0 + 0.05, 2.75), (xf - 1.35, Y0 + 0.05, 2.75), (xf - 1.35, Y1 - 0.05, 2.75), (cx0 + 0.1, Y1 - 0.05, 2.75)])
    for y in (Y0, Y1 - 0.12):
        hexa(m, body, [(xf - 0.95, y, 1.85), (xf - 0.78, y, 1.85), (xf - 0.78, y + 0.12, 1.85), (xf - 0.95, y + 0.12, 1.85),
                       (xf - 1.45, y, 2.75), (xf - 1.28, y, 2.75), (xf - 1.28, y + 0.12, 2.75), (xf - 1.45, y + 0.12, 2.75)])
    m.box(body, cx0, cx0 + 0.25, Y0, Y1, 1.9, 2.75)
    m.box(body, cx0, xf - 1.25, Y0, Y1, 2.75, 2.95)
    m.box("company_dark", cx0, xf - 0.9, Y0 - 0.02, Y1 + 0.02, 1.2, 1.35)  # stripe
    return cx0


def cab_toy(m, xf=X1, body="company", accent="road_toy_yellow"):
    """A chubby Toyland cab with a round roof and big round eyes for headlights."""
    cx0 = xf - 2.3
    m.box(body, cx0, xf, Y0, Y1, 0.95, 1.95)
    m.box("glass", cx0 + 0.1, xf - 0.05, Y0 + 0.05, Y1 - 0.05, 1.95, 2.55)
    for y in (Y0, Y1 - 0.18):
        m.box(body, xf - 0.18, xf, y, y + 0.18, 1.95, 2.55)
    m.box(body, cx0, cx0 + 0.3, Y0, Y1, 1.95, 2.55)
    arch(m, accent, cx0 - 0.05, xf + 0.05, Y0 - 0.05, Y1 + 0.05, 2.55, 0.55)
    for y in (-0.85, 0.85):
        cyl(m, "road_white", "x", (y, 1.45), 0.34, xf, xf + 0.1, sides=10)
        cyl(m, "dark", "x", (y, 1.45), 0.15, xf + 0.1, xf + 0.14, sides=8)
    cyl(m, accent, "y", (xf + 0.05, 0.85), 0.25, Y0 + 0.05, Y1 - 0.05, sides=8)  # round bumper
    cyl(m, "road_toy_red", "z", (cx0 + 1.0, 0.0), 0.12, 3.05, 3.35, sides=8)  # a little horn on the roof
    sphere(m, "road_toy_red", cx0 + 1.0, 0.0, 3.4, 0.18, rings=3, segs=6)
    return cx0


# Bodies. They run from bx0 at the back to bx1 just behind the cab, on a floor at z = 1.0.

BX0 = X0 + 0.05


def heap(m, mat, x0, x1, y0, y1, z0, z1, peak):
    """A load filling a box, with a heaped top."""
    m.box(mat, x0, x1, y0, y1, z0, z1)
    m.prism_roof(mat, mat, x0, x1, y0, y1, z1, peak)


def walls(m, mat, x0, x1, z0, z1, t=0.12, front_extra=0.0):
    m.box(mat, x0, x1, Y0, Y0 + t, z0, z1)
    m.box(mat, x0, x1, Y1 - t, Y1, z0, z1)
    m.box(mat, x0, x0 + t, Y0 + t, Y1 - t, z0, z1)
    m.box(mat, x1 - t, x1, Y0 + t, Y1 - t, z0, z1 + front_extra)


def tipper(m, bx1, side, load, top=2.75, ribs="dark", canopy=False):
    x0 = BX0
    m.box("dark", x0 + 0.3, bx1, -1.1, 1.1, 1.0, 1.2)  # subframe
    m.box(side, x0, bx1, Y0, Y1, 1.2, 1.4)  # floor
    walls(m, side, x0, bx1, 1.4, top, front_extra=0.3)
    for x in [x0 + 0.6 + i * (bx1 - x0 - 1.0) / 3 for i in range(4)]:
        m.box(ribs, x - 0.07, x + 0.07, Y0 - 0.05, Y1 + 0.05, 1.3, top)
    m.box(ribs, x0 - 0.05, x0, Y0 + 0.2, Y1 - 0.2, 1.4, top - 0.1)  # tailgate
    if canopy:
        m.box(side, bx1, bx1 + 1.6, Y0 + 0.1, Y1 - 0.1, top + 0.3, top + 0.42)  # guard over the cab
    m.box("metal", bx1 - 0.6, bx1 - 0.3, -0.2, 0.2, 0.6, 1.2)  # tipping ram
    heap(m, load, x0 + 0.12, bx1 - 0.12, Y0 + 0.12, Y1 - 0.12, 1.4, top - 0.05, top + 0.5)


def box_body(m, bx1, mat, top=3.3, roof="roof", doors="company_dark", stripe=None):
    x0 = BX0
    m.box("dark", x0 + 0.3, bx1, -1.1, 1.1, 1.0, 1.15)
    m.box(mat, x0, bx1, Y0, Y1, 1.15, top - 0.1)
    m.box(roof, x0 - 0.03, bx1 + 0.03, Y0 - 0.03, Y1 + 0.03, top - 0.1, top)
    m.box(doors, x0 - 0.05, x0, Y0 + 0.12, -0.03, 1.3, top - 0.25)
    m.box(doors, x0 - 0.05, x0, 0.03, Y1 - 0.12, 1.3, top - 0.25)
    m.box("dark", x0 - 0.08, x0, -0.4, -0.3, 1.6, 2.4)  # handles
    m.box("dark", x0 - 0.08, x0, 0.3, 0.4, 1.6, 2.4)
    if stripe:
        m.box(stripe, x0 + 0.05, bx1 - 0.05, Y0 - 0.03, Y1 + 0.03, 1.5, 1.75)
    m.box("light", x0 - 0.06, x0, Y0 + 0.1, Y0 + 0.35, 1.2, 1.35)  # tail lights
    m.box("light", x0 - 0.06, x0, Y1 - 0.35, Y1 - 0.1, 1.2, 1.35)


def tank(m, bx1, mat, band="company", r=1.2, zc=2.15, ends=None, hatches=2):
    x0 = BX0
    m.box("dark", x0 + 0.3, bx1, -1.1, 1.1, 1.0, 1.2)
    for x in (x0 + 0.6, bx1 - 0.6):
        m.box("dark", x - 0.15, x + 0.15, -1.0, 1.0, 1.0, 1.4)  # cradles
    cyl(m, mat, "x", (0, zc), r * 0.92, x0 + 0.15, bx1 - 0.15, sides=16, cap=ends or mat, rz=r * 0.85)
    cyl(m, band, "x", (0, zc), r * 0.94, (x0 + bx1) / 2 - 0.15, (x0 + bx1) / 2 + 0.15, sides=16, rz=r * 0.87)
    top = zc + r * 0.85
    m.box("metal", x0 + 0.4, bx1 - 0.4, -0.35, 0.35, top - 0.05, top + 0.06)  # walkway
    for i in range(hatches):
        x = x0 + 0.4 + (i + 0.5) * (bx1 - x0 - 0.8) / hatches
        cyl(m, "metal", "z", (x, 0), 0.28, top - 0.1, top + 0.25, sides=8)
    m.box("metal", x0 + 0.05, x0 + 0.12, -0.5, -0.4, 1.2, top)  # ladder
    m.box("metal", x0 + 0.05, x0 + 0.12, 0.4, 0.5, 1.2, top)
    for z in (1.6, 2.1, 2.6):
        m.box("metal", x0 + 0.05, x0 + 0.12, -0.4, 0.4, z, z + 0.06)
    cyl(m, "dark", "y", (x0 + 0.5, 0.95), 0.12, Y0 + 0.1, Y1 - 0.1, sides=6)  # pipe
    return top


def flatbed(m, bx1, mat="wood", sides=0.0, side_mat="company_dark", headboard="company_dark"):
    x0 = BX0
    m.box("dark", x0 + 0.3, bx1, -1.1, 1.1, 1.0, 1.15)
    m.box(mat, x0, bx1, Y0, Y1, 1.15, 1.35)
    m.box(headboard, bx1 - 0.15, bx1, Y0 + 0.05, Y1 - 0.05, 1.35, 2.9)
    if sides:
        walls(m, side_mat, x0, bx1 - 0.15, 1.35, 1.35 + sides)
    m.box("light", x0 - 0.06, x0, Y0 + 0.1, Y0 + 0.35, 1.15, 1.3)
    m.box("light", x0 - 0.06, x0, Y1 - 0.35, Y1 - 0.1, 1.15, 1.3)


def slats(m, mat, x0, x1, z0, z1, n, gap=0.18, posts="dark", ends=True):
    """Sides made of planks with gaps between them, and posts."""
    h = (z1 - z0 - (n - 1) * gap) / n
    for i in range(n):
        za = z0 + i * (h + gap)
        m.box(mat, x0, x1, Y0, Y0 + 0.08, za, za + h)
        m.box(mat, x0, x1, Y1 - 0.08, Y1, za, za + h)
        if ends:
            m.box(mat, x0, x0 + 0.08, Y0, Y1, za, za + h)
            m.box(mat, x1 - 0.08, x1, Y0, Y1, za, za + h)
    k = max(2, int((x1 - x0) / 1.4) + 1)
    for i in range(k):
        x = x0 + i * (x1 - x0 - 0.14) / (k - 1)
        for y in (Y0 - 0.04, Y1 - 0.08):
            m.box(posts, x, x + 0.14, y, y + 0.12, z0 - 0.1, z1)


REAR_AXLES = (-3.2, -1.95)


# The models.

def coal_truck():
    m = Model()
    chassis(m)
    tipper(m, cab_bonnet(m) - 0.15, "company", "load_coal")
    wheels(m, (X1 - 1.1,) + REAR_AXLES)
    return m


def iron_ore_truck():
    m = Model()
    chassis(m)
    tipper(m, cab_flat(m) - 0.15, "rust", "load_ore", top=2.65, ribs="company_dark", canopy=True)
    wheels(m, (X1 - 1.1,) + REAR_AXLES)
    return m


def copper_ore_truck():
    m = Model()
    chassis(m)
    bx1 = cab_round(m) - 0.15
    # A dump body with a sloping back.
    x0 = BX0
    m.box("dark", x0 + 0.3, bx1, -1.1, 1.1, 1.0, 1.2)
    for s in (-1, 1):
        ya, yb = sorted((s * 1.38, s * 1.55))
        hexa(m, "company_dark", [(x0 + 0.6, ya, 1.2), (bx1, ya, 1.2), (bx1, yb, 1.2), (x0 + 0.6, yb, 1.2),
                                 (x0, ya, 2.75), (bx1, ya, 2.75), (bx1, yb, 2.75), (x0, yb, 2.75)])
    hexa(m, "company_dark", [(x0 + 0.6, Y0, 1.2), (bx1, Y0, 1.2), (bx1, Y1, 1.2), (x0 + 0.6, Y1, 1.2),
                             (x0 + 0.6, Y0, 1.4), (bx1, Y0, 1.4), (bx1, Y1, 1.4), (x0 + 0.6, Y1, 1.4)])
    hexa(m, "company_dark", [(x0 + 0.6, Y0, 1.2), (x0 + 0.75, Y0, 1.2), (x0 + 0.75, Y1, 1.2), (x0 + 0.6, Y1, 1.2),
                             (x0, Y0, 2.75), (x0 + 0.15, Y0, 2.75), (x0 + 0.15, Y1, 2.75), (x0, Y1, 2.75)])
    m.box("company_dark", bx1 - 0.15, bx1, -1.38, 1.38, 1.4, 3.05)
    m.box("dark", x0 - 0.04, bx1, Y0 - 0.04, Y1 + 0.04, 2.6, 2.8)  # top rim
    hexa(m, "load_road_copper", [(x0 + 0.75, -1.38, 1.4), (bx1 - 0.15, -1.38, 1.4), (bx1 - 0.15, 1.38, 1.4), (x0 + 0.75, 1.38, 1.4),
                                 (x0 + 0.15, -1.38, 2.7), (bx1 - 0.15, -1.38, 2.7), (bx1 - 0.15, 1.38, 2.7), (x0 + 0.15, 1.38, 2.7)])
    m.pyramid("load_road_copper", x0 + 0.15, bx1 - 0.15, -1.38, 1.38, 2.7, 3.2)
    wheels(m, (X1 - 1.1,) + REAR_AXLES)
    return m


def grain_truck():
    m = Model()
    chassis(m)
    bx1 = cab_round(m) - 0.15
    x0 = BX0
    m.box("dark", x0 + 0.3, bx1, -1.1, 1.1, 1.0, 1.2)
    m.box("wood", x0, bx1, Y0, Y1, 1.2, 1.4)
    slats(m, "company_dark", x0, bx1, 1.4, 2.8, 3, gap=0.08)
    heap(m, "load_road_grain", x0 + 0.1, bx1 - 0.1, Y0 + 0.1, Y1 - 0.1, 1.4, 2.7, 3.15)
    wheels(m, (X1 - 1.1,) + REAR_AXLES)
    return m


def fruit_truck():
    m = Model()
    chassis(m)
    bx1 = cab_bonnet(m) - 0.15
    x0 = BX0
    m.box("dark", x0 + 0.3, bx1, -1.1, 1.1, 1.0, 1.2)
    m.box("wood", x0, bx1, Y0, Y1, 1.2, 1.4)
    slats(m, "wood", x0, bx1, 1.4, 2.2, 2, gap=0.15, posts="company_dark")
    # Crates of oranges and apples, two layers.
    n = 4
    dx = (bx1 - x0 - 0.2) / n
    for i in range(n):
        for j, y in enumerate((-0.72, 0.72)):
            xa = x0 + 0.1 + i * dx
            m.box("load_road_crate", xa + 0.05, xa + dx - 0.05, y - 0.66, y + 0.66, 1.4, 2.6)
            fruit = "load_road_fruit" if (i + j) % 2 == 0 else "load_road_fruit_red"
            m.box(fruit, xa + 0.12, xa + dx - 0.12, y - 0.58, y + 0.58, 2.6, 2.75)
            m.pyramid(fruit, xa + 0.12, xa + dx - 0.12, y - 0.58, y + 0.58, 2.75, 2.95)
    wheels(m, (X1 - 1.1,) + REAR_AXLES)
    return m


def livestock_truck():
    m = Model()
    chassis(m)
    bx1 = cab_round(m, body="company") - 0.15
    x0 = BX0
    m.box("dark", x0 + 0.3, bx1, -1.1, 1.1, 1.0, 1.2)
    m.box("wood", x0, bx1, Y0, Y1, 1.2, 1.4)
    slats(m, "wood", x0, bx1, 1.4, 3.1, 4, gap=0.22, posts="company_dark")
    m.box("roof", x0 - 0.05, bx1 + 0.05, Y0 - 0.05, Y1 + 0.05, 3.1, 3.25)
    m.box("wood", x0 - 0.12, x0 - 0.04, Y0 + 0.2, Y1 - 0.2, 1.3, 2.9)  # ramp door
    # Cattle inside, seen through the gaps.
    for i, x in enumerate((x0 + 0.9, x0 + 2.6, x0 + 4.2)):
        for k, y in enumerate((-0.68, 0.68)):
            hide = "load_road_cow" if (i + k) % 2 == 0 else "load_road_cow_white"
            m.box(hide, x - 0.75, x + 0.75, y - 0.45, y + 0.45, 1.4, 2.4)
            m.box(hide, x + 0.7, x + 1.1, y - 0.25, y + 0.25, 2.0, 2.65)
    wheels(m, (X1 - 1.1,) + REAR_AXLES)
    return m


def mail_truck():
    m = Model()
    chassis(m)
    bx1 = cab_flat(m, body="road_red") - 0.15
    box_body(m, bx1, "road_red", top=3.2, doors="road_red", stripe="company")
    # An envelope on each side.
    for y0, y1, s in ((Y0 - 0.06, Y0 - 0.02, -1), (Y1 + 0.02, Y1 + 0.06, 1)):
        m.box("road_white", -2.6, -0.6, y0, y1, 2.0, 2.9)
        ya = Y0 - 0.07 if s < 0 else Y1 + 0.07
        tri_out(m, "dark", (-2.6, ya, 2.9), (-0.6, ya, 2.9), (-1.6, ya, 2.4), (-1.6, ya * 0.5, 2.65))
    wheels(m, (X1 - 1.1, -2.6))
    return m


def goods_truck():
    m = Model()
    chassis(m)
    bx1 = cab_flat(m) - 0.15
    box_body(m, bx1, "company", top=3.45, doors="metal", stripe="road_white")
    # A roller door at the back: horizontal ribs.
    for z in (1.6, 2.0, 2.4, 2.8):
        m.box("dark", BX0 - 0.08, BX0, Y0 + 0.15, Y1 - 0.15, z, z + 0.04)
    for x in (-3.0, -1.5, 0.0):
        for y in (Y0 - 0.04, Y1):
            m.box("company_dark", x, x + 0.1, y, y + 0.04, 1.15, 3.35)
    wheels(m, (X1 - 1.1,) + REAR_AXLES)
    return m


def food_van():
    m = Model()
    chassis(m)
    bx1 = cab_round(m) - 0.15
    box_body(m, bx1, "road_white", top=3.35, doors="road_white", stripe="company")
    m.box("metal", bx1 - 0.05, bx1 + 0.3, -0.9, 0.9, 2.45, 3.25)  # refrigeration unit over the cab
    for z in (2.6, 2.8, 3.0):
        m.box("dark", bx1 + 0.3, bx1 + 0.34, -0.75, 0.75, z, z + 0.08)
    m.box("company_dark", BX0 + 0.05, bx1 - 0.05, Y0 - 0.03, Y1 + 0.03, 2.9, 3.0)  # top stripe
    wheels(m, (X1 - 1.1,) + REAR_AXLES)
    return m


def armoured_truck():
    m = Model()
    x0, x1 = X0 + 0.3, X1 - 0.1
    chassis(m, x0, x1 - 0.2)
    m.box("road_armour", x0, x1 - 0.6, Y0, Y1, 0.8, 3.1)
    hexa(m, "road_armour", [(x1 - 0.6, Y0, 0.8), (x1, Y0, 0.8), (x1, Y1, 0.8), (x1 - 0.6, Y1, 0.8),
                            (x1 - 0.6, Y0, 1.9), (x1, Y0, 1.9), (x1, Y1, 1.9), (x1 - 0.6, Y1, 1.9)])
    hexa(m, "road_armour", [(x1 - 0.6, Y0, 1.9), (x1 - 0.05, Y0, 1.9), (x1 - 0.05, Y1, 1.9), (x1 - 0.6, Y1, 1.9),
                            (x1 - 0.6, Y0, 3.1), (x1 - 0.6, Y0, 3.1), (x1 - 0.6, Y1, 3.1), (x1 - 0.6, Y1, 3.1)])
    # Narrow windscreen slit on the raked front, and small barred windows.
    hexa(m, "glass", [(x1 - 0.42, Y0 + 0.25, 2.1), (x1 - 0.09, Y0 + 0.25, 2.1), (x1 - 0.09, Y1 - 0.25, 2.1), (x1 - 0.42, Y1 - 0.25, 2.1),
                      (x1 - 0.55, Y0 + 0.25, 2.65), (x1 - 0.32, Y0 + 0.25, 2.65), (x1 - 0.32, Y1 - 0.25, 2.65), (x1 - 0.55, Y1 - 0.25, 2.65)])
    for y0, y1 in ((Y0 - 0.05, Y0), (Y1, Y1 + 0.05)):
        m.box("glass", x1 - 1.6, x1 - 0.8, y0, y1, 2.2, 2.75)
        for x in (x1 - 1.4, x1 - 1.2, x1 - 1.0):
            m.box("dark", x - 0.03, x + 0.03, min(y0, y1) - 0.02, max(y0, y1) + 0.02, 2.2, 2.75)
        m.box("company", x0 + 0.1, x1 - 0.7, y0, y1, 1.35, 1.75)  # company stripe
        m.box("dark", x1 - 2.1, x1 - 2.0, y0, y1, 0.9, 2.9)  # door seam
        for x in (x0 + 0.8, x0 + 2.0, x0 + 3.2):
            m.box("dark", x - 0.04, x + 0.04, y0, y1, 2.2, 2.6)  # gun ports
    m.box("company", x0 + 0.2, x1 - 0.8, -0.6, 0.6, 3.1, 3.2)  # roof hatch
    cyl(m, "light", "z", (x1 - 1.0, 0.0), 0.15, 3.1, 3.35, sides=8)  # beacon
    m.box("dark", x0 - 0.05, x0, Y0 + 0.15, Y1 - 0.15, 0.95, 2.95)  # rear doors
    m.box("metal", x0 - 0.1, x0 - 0.05, -0.05, 0.05, 1.0, 2.9)
    for z in (1.3, 2.5):
        for y in (Y0 + 0.2, Y1 - 0.35):
            m.box("metal", x0 - 0.1, x0, y, y + 0.15, z, z + 0.2)  # hinges
    m.box("dark", x1, x1 + 0.12, Y0 + 0.05, Y1 - 0.05, 0.6, 0.95)
    for y in (Y0 + 0.2, Y1 - 0.6):
        m.box("light", x1 - 0.02, x1 + 0.04, y, y + 0.4, 1.3, 1.55)
    wheels(m, (x1 - 1.2, x0 + 1.3), radius=0.66, width=0.5)
    return m


def tanker_truck(cab, mat, band="company", ends=None):
    m = Model()
    chassis(m)
    bx1 = cab(m) - 0.15
    tank(m, bx1, mat, band=band, ends=ends)
    wheels(m, (X1 - 1.1,) + REAR_AXLES)
    return m


def wood_truck():
    m = Model()
    chassis(m)
    bx1 = cab_flat(m, body="company") - 0.15
    x0 = BX0
    m.box("dark", x0 + 0.3, bx1, -1.1, 1.1, 1.0, 1.25)
    m.box("metal", bx1 - 0.15, bx1, Y0 + 0.05, Y1 - 0.05, 1.25, 3.0)  # headboard
    for x in (x0 + 0.5, (x0 + bx1) / 2, bx1 - 0.8):
        m.box("company_dark", x - 0.15, x + 0.15, Y0, Y1, 1.25, 1.45)  # bolsters
        for y in (Y0, Y1 - 0.12):
            m.box("company_dark", x - 0.06, x + 0.06, y, y + 0.12, 1.45, 3.0)  # stakes
    # A stack of logs: four, three, then two.
    r = 0.34
    z = 1.45 + r
    for row, n in enumerate((4, 3, 2)):
        for k in range(n):
            y = (k - (n - 1) / 2) * 2 * r
            cyl(m, "load_road_wood", "x", (y, z), r, x0 - 0.15 + 0.1 * (k % 2), bx1 - 0.2, sides=8, cap="load_road_wood_end")
        z += r * math.sqrt(3)
    wheels(m, (X1 - 1.1,) + REAR_AXLES)
    return m


def steel_truck():
    m = Model()
    chassis(m)
    bx1 = cab_round(m) - 0.15
    flatbed(m, bx1, mat="metal", sides=0.35)
    x0 = BX0
    # Steel coils lying across, on chocks, and a pile of girders.
    for x in (x0 + 0.85, x0 + 2.3):
        m.box("wood", x - 0.6, x + 0.6, -1.2, 1.2, 1.35, 1.5)
        cyl(m, "load_road_steel", "y", (x, 2.15), 0.65, -1.15, 1.15, sides=12, cap="load_road_steel_dark")
        cyl(m, "dark", "y", (x, 2.15), 0.25, -1.17, 1.17, sides=8)
    for k in range(3):
        z = 1.5 + k * 0.32
        for y in ((-0.9, -0.1), (0.1, 0.9)):
            m.box("load_road_steel_dark", x0 + 3.1, bx1 - 0.25, y[0], y[1], z, z + 0.08)
            m.box("load_road_steel_dark", x0 + 3.1, bx1 - 0.25, sum(y) / 2 - 0.05, sum(y) / 2 + 0.05, z + 0.08, z + 0.24)
            m.box("load_road_steel_dark", x0 + 3.1, bx1 - 0.25, y[0], y[1], z + 0.24, z + 0.32)
    wheels(m, (X1 - 1.1,) + REAR_AXLES)
    return m


def paper_truck():
    m = Model()
    chassis(m)
    bx1 = cab_bonnet(m) - 0.15
    flatbed(m, bx1, sides=0.5, side_mat="company")
    x0 = BX0
    n = 4
    dx = (bx1 - x0 - 0.35) / n
    for i in range(n):
        for y in (-0.7, 0.7):
            x = x0 + 0.15 + (i + 0.5) * dx
            cyl(m, "load_road_paper", "z", (x, y), min(dx / 2 - 0.04, 0.65), 1.35, 2.85, sides=10, cap="road_white")
    wheels(m, (X1 - 1.1,) + REAR_AXLES)
    return m


def rubber_truck():
    m = Model()
    chassis(m)
    bx1 = cab_flat(m) - 0.15
    flatbed(m, bx1, sides=0.45, side_mat="company_dark")
    x0 = BX0
    n = 5
    dx = (bx1 - x0 - 0.35) / n
    for i in range(n):
        for y in (-0.72, 0.0, 0.72):
            x = x0 + 0.15 + (i + 0.5) * dx
            cyl(m, "load_road_drum", "z", (x, y), 0.33, 1.35, 2.55, sides=8, cap="load_road_drum_top")
            cyl(m, "load_road_drum_top", "z", (x, y), 0.345, 1.9, 2.0, sides=8)
    wheels(m, (X1 - 1.1,) + REAR_AXLES)
    return m


# Toyland.

def toy_bus(double=False):
    m = Model()
    x0, x1 = X0, X1
    chassis(m, x0 + 0.3, x1 - 0.3, 0.6, 1.0)
    body, accent = "company", "road_toy_yellow"
    deck = [(0.95, 2.8)] if not double else [(0.95, 2.6), (2.6, 4.1)]
    top = deck[-1][1]
    m.box(body, x0, x1, Y0, Y1, 0.95, 1.9)
    for z0, z1 in deck:
        zg0 = max(z0, 1.9) + (0.15 if z0 > 1 else 0)
        m.box("glass", x0 + 0.06, x1 - 0.06, Y0 + 0.06, Y1 - 0.06, zg0, z1 - 0.15)
        m.box(body, x0, x1, Y0, Y1, z1 - 0.15, z1)
        for i in range(6):
            x = x0 + i * (L - 0.3) / 5
            for y in (Y0, Y1 - 0.12):
                m.box(body, x, x + 0.3, y, y + 0.12, zg0, z1 - 0.15)
        if z0 > 1:
            m.box(accent, x0, x1, Y0, Y1, z0, zg0)
    arch(m, accent, x0, x1, Y0, Y1, top, 0.5)
    m.box(accent, x0 - 0.02, x1 + 0.02, Y0 - 0.02, Y1 + 0.02, 1.25, 1.45)  # stripe
    for y in (-0.9, 0.9):
        cyl(m, "road_white", "x", (y, 1.45), 0.32, x1, x1 + 0.1, sides=10)
        cyl(m, "dark", "x", (y, 1.45), 0.14, x1 + 0.1, x1 + 0.14, sides=8)
    cyl(m, accent, "y", (x1 + 0.05, 0.85), 0.25, Y0 + 0.05, Y1 - 0.05, sides=8)
    cyl(m, accent, "y", (x0 - 0.05, 0.85), 0.25, Y0 + 0.05, Y1 - 0.05, sides=8)
    m.box("road_toy_red", x0 - 0.05, x0, Y0 + 0.2, Y0 + 0.5, 1.2, 1.5)
    m.box("road_toy_red", x0 - 0.05, x0, Y1 - 0.5, Y1 - 0.2, 1.2, 1.5)
    m.box("road_white", x1 - 0.02, x1 + 0.04, -0.8, 0.8, top - 0.15 - 0.45, top - 0.2)  # destination board
    wheels(m, (x1 - 1.6, x0 + 1.6), radius=0.78, width=0.55, toy=True)
    return m


def toy_mail():
    m = Model()
    chassis(m, z0=0.65)
    bx1 = cab_toy(m, body="road_toy_red", accent="road_toy_yellow") - 0.1
    x0 = BX0 + 0.2
    m.box("road_toy_red", x0, bx1, Y0, Y1, 0.95, 2.7)
    arch(m, "road_toy_red", x0, bx1, Y0, Y1, 2.7, 0.6)
    m.box("company", x0 - 0.02, bx1 + 0.02, Y0 - 0.02, Y1 + 0.02, 1.1, 1.35)
    for y, s in ((Y0 - 0.06, -1), (Y1 + 0.02, 1)):
        m.box("road_white", -2.9, -0.7, y, y + 0.04, 1.7, 2.75)
        ya = y + (0.0 if s < 0 else 0.04) + s * 0.01
        tri_out(m, "road_toy_red", (-2.9, ya, 2.75), (-0.7, ya, 2.75), (-1.8, ya, 2.2), (-1.8, ya * 0.5, 2.5))
        cyl(m, "road_toy_yellow", "y", (-1.8, 2.15), 0.18, ya, ya + s * 0.04, sides=8)  # seal
    m.box("road_toy_yellow", x0 - 0.05, x0, -0.6, 0.6, 1.2, 2.6)  # back door
    wheels(m, (X1 - 1.2, x0 + 1.2), radius=0.78, width=0.55, toy=True)
    return m


def toy_lorry(make_body, cab_colour="company", accent="road_toy_yellow"):
    m = Model()
    chassis(m, z0=0.65)
    bx1 = cab_toy(m, body=cab_colour, accent=accent) - 0.12
    make_body(m, bx1)
    wheels(m, (X1 - 1.2, BX0 + 1.3), radius=0.78, width=0.55, toy=True)
    return m


def toy_tub(m, bx1, mat, rim, top=2.5):
    x0 = BX0 + 0.1
    m.box("dark", x0 + 0.3, bx1, -1.1, 1.1, 1.0, 1.2)
    m.box(mat, x0, bx1, Y0, Y1, 1.2, 1.4)
    walls(m, mat, x0, bx1, 1.4, top, t=0.15)
    m.box(rim, x0 - 0.05, bx1 + 0.05, Y0 - 0.05, Y0 + 0.15, top, top + 0.15)
    m.box(rim, x0 - 0.05, bx1 + 0.05, Y1 - 0.15, Y1 + 0.05, top, top + 0.15)
    m.box(rim, x0 - 0.05, x0 + 0.15, Y0 + 0.15, Y1 - 0.15, top, top + 0.15)
    m.box(rim, bx1 - 0.15, bx1 + 0.05, Y0 + 0.15, Y1 - 0.15, top, top + 0.15)
    # Polka dots.
    for x in (x0 + 0.8, x0 + 2.2, x0 + 3.6):
        for y, s in ((Y0, -1), (Y1, 1)):
            cyl(m, "road_white", "y", (x, (1.4 + top) / 2), 0.25, y, y + s * 0.04, sides=8)
    return x0


def sugar_body(m, bx1):
    x0 = toy_tub(m, bx1, "road_toy_blue", "road_toy_yellow")
    heap(m, "load_road_sugar", x0 + 0.15, bx1 - 0.15, Y0 + 0.15, Y1 - 0.15, 1.4, 2.5, 2.8)
    for x, y, z in ((x0 + 0.8, -0.5, 2.75), (x0 + 1.8, 0.4, 2.85), (x0 + 2.8, -0.2, 2.85), (x0 + 3.6, 0.6, 2.7)):
        m.box("load_road_sugar", x - 0.25, x + 0.25, y - 0.25, y + 0.25, z - 0.25, z + 0.25)


def candyfloss_body(m, bx1):
    x0 = toy_tub(m, bx1, "road_toy_purple", "road_toy_pink", top=2.2)
    m.box("load_road_candyfloss", x0 + 0.15, bx1 - 0.15, Y0 + 0.15, Y1 - 0.15, 1.4, 2.4)
    for i, x in enumerate((x0 + 0.65, x0 + 1.75, x0 + 2.85, x0 + 3.85)):
        for j, y in enumerate((-0.6, 0.6)):
            mat = "load_road_candyfloss" if (i + j) % 3 else "load_road_candyfloss_blue"
            sphere(m, mat, x, y, 2.55, 0.62, rings=4, segs=8, squash=0.8)
    for x in (x0 + 1.2, x0 + 3.3):
        cyl(m, "road_white", "z", (x, 0.0), 0.06, 2.4, 3.45, sides=6)  # sticks
        sphere(m, "load_road_candyfloss", x, 0.0, 3.25, 0.4, rings=3, segs=8)


def toffee_body(m, bx1):
    x0 = toy_tub(m, bx1, "road_toy_green", "road_toy_yellow")
    heap(m, "load_road_toffee", x0 + 0.15, bx1 - 0.15, Y0 + 0.15, Y1 - 0.15, 1.4, 2.5, 2.75)
    for k, (x, y) in enumerate(((x0 + 0.7, -0.6), (x0 + 1.5, 0.5), (x0 + 2.4, -0.3), (x0 + 3.3, 0.6), (x0 + 3.8, -0.6))):
        mat = "load_road_toffee_light" if k % 2 else "load_road_toffee"
        m.box(mat, x - 0.3, x + 0.3, y - 0.25, y + 0.25, 2.55, 2.95)
        # Twisted wrapper ends.
        hexa(m, mat, [(x + 0.3, y - 0.05, 2.7), (x + 0.6, y - 0.18, 2.6), (x + 0.6, y + 0.18, 2.6), (x + 0.3, y + 0.05, 2.7),
                      (x + 0.3, y - 0.05, 2.8), (x + 0.6, y - 0.18, 2.9), (x + 0.6, y + 0.18, 2.9), (x + 0.3, y + 0.05, 2.8)])
        hexa(m, mat, [(x - 0.3, y - 0.05, 2.7), (x - 0.6, y - 0.18, 2.6), (x - 0.6, y + 0.18, 2.6), (x - 0.3, y + 0.05, 2.7),
                      (x - 0.3, y - 0.05, 2.8), (x - 0.6, y - 0.18, 2.9), (x - 0.6, y + 0.18, 2.9), (x - 0.3, y + 0.05, 2.8)])


def bubble_body(m, bx1):
    x0 = toy_tub(m, bx1, "road_toy_blue", "road_white", top=2.0)
    m.box("load_road_bubble", x0 + 0.15, bx1 - 0.15, Y0 + 0.15, Y1 - 0.15, 1.4, 2.1)
    bubbles = ((0.8, -0.6, 2.4, 0.55), (1.9, 0.5, 2.45, 0.6), (3.2, -0.4, 2.4, 0.6), (3.9, 0.6, 2.35, 0.45),
               (1.3, 0.0, 3.0, 0.42), (2.7, 0.2, 3.1, 0.45), (2.0, -0.7, 3.2, 0.3))
    for k, (x, y, z, r) in enumerate(bubbles):
        sphere(m, "load_road_bubble_pink" if k % 3 == 1 else "load_road_bubble", x0 + x, y, z, r, rings=4, segs=8)


def battery_body(m, bx1):
    x0 = BX0 + 0.1
    m.box("dark", x0 + 0.3, bx1, -1.1, 1.1, 1.0, 1.2)
    m.box("road_toy_green", x0, bx1, Y0, Y1, 1.2, 1.45)
    m.box("road_toy_yellow", bx1 - 0.2, bx1, Y0 + 0.1, Y1 - 0.1, 1.45, 2.6)
    for k, x in enumerate((x0 + 0.5, x0 + 1.3, x0 + 2.1, x0 + 2.9, x0 + 3.7)):
        for y in (-0.72, 0.72):
            cyl(m, "load_road_battery", "z", (x, y), 0.38, 1.45, 2.75, sides=10)
            cyl(m, "load_road_battery_top", "z", (x, y), 0.39, 2.45, 2.75, sides=10)
            cyl(m, "load_road_battery_top", "z", (x, y), 0.13, 2.75, 2.95, sides=6)
    for y in (Y0, Y1 - 0.1):
        m.box("road_toy_red", x0, bx1 - 0.2, y, y + 0.1, 1.45, 1.75)  # low rails


def fizzy_body(m, bx1):
    x0 = BX0 + 0.1
    m.box("dark", x0 + 0.3, bx1, -1.1, 1.1, 1.0, 1.2)
    m.box("road_toy_pink", x0, bx1, Y0, Y1, 1.2, 1.45)
    m.box("road_toy_blue", bx1 - 0.2, bx1, Y0 + 0.1, Y1 - 0.1, 1.45, 2.8)
    n = 3
    dx = (bx1 - 0.2 - x0) / n
    for i in range(n):
        xa = x0 + i * dx
        for y in (-0.72, 0.72):
            m.box("load_road_fizzy_crate", xa + 0.05, xa + dx - 0.05, y - 0.68, y + 0.68, 1.45, 2.15)
            for bx in (xa + dx * 0.3, xa + dx * 0.7):
                for by in (y - 0.35, y + 0.35):
                    cyl(m, "load_road_bottle", "z", (bx, by), 0.17, 2.15, 2.65, sides=6)
                    cyl(m, "load_road_bottle", "z", (bx, by), 0.07, 2.65, 2.9, sides=6)
                    cyl(m, "load_road_bottle_cap", "z", (bx, by), 0.09, 2.9, 2.98, sides=6)
    for y in (Y0, Y1 - 0.1):
        m.box("road_toy_yellow", x0, bx1 - 0.2, y, y + 0.1, 1.45, 1.8)


def cola_body(m, bx1):
    # A big bottle of cola lying on its side.
    x0 = BX0 + 0.1
    m.box("dark", x0 + 0.3, bx1, -1.1, 1.1, 1.0, 1.25)
    for x in (x0 + 1.2, bx1 - 0.5):
        m.box("road_toy_red", x - 0.15, x + 0.15, -1.1, 1.1, 1.0, 1.6)
    cyl(m, "road_cola", "x", (0, 2.2), 1.05, x0 + 1.1, bx1 - 0.1, sides=14)
    cyl(m, "road_toy_red", "x", (0, 2.2), 1.08, x0 + 1.9, x0 + 3.1, sides=14)  # label
    cyl(m, "road_white", "x", (0, 2.2), 1.1, x0 + 2.3, x0 + 2.7, sides=14)
    hexa(m, "road_cola", [(x0 + 1.1, -0.95, 1.3), (x0 + 1.1, 0.95, 1.3), (x0 + 1.1, 0.95, 3.1), (x0 + 1.1, -0.95, 3.1),
                          (x0 + 0.5, -0.35, 1.85), (x0 + 0.5, 0.35, 1.85), (x0 + 0.5, 0.35, 2.55), (x0 + 0.5, -0.35, 2.55)])
    cyl(m, "road_cola", "x", (0, 2.2), 0.32, x0 + 0.15, x0 + 0.55, sides=10)  # neck
    cyl(m, "road_toy_red", "x", (0, 2.2), 0.38, x0 - 0.1, x0 + 0.2, sides=10)  # cap


def plastic_body(m, bx1):
    x0 = BX0 + 0.1
    m.box("dark", x0 + 0.3, bx1, -1.1, 1.1, 1.0, 1.25)
    for x in (x0 + 0.6, bx1 - 0.6):
        m.box("road_toy_blue", x - 0.15, x + 0.15, -1.0, 1.0, 1.0, 1.5)
    cyl(m, "company", "x", (0, 2.2), 1.1, x0 + 0.1, bx1 - 0.1, sides=16, cap="road_toy_yellow")
    for k, x in enumerate((x0 + 1.0, x0 + 2.0, x0 + 3.0, x0 + 4.0)):
        mat = ("road_toy_yellow", "road_toy_green", "road_toy_pink", "road_toy_blue")[k]
        if x < bx1 - 0.3:
            cyl(m, mat, "x", (0, 2.2), 1.13, x - 0.18, x + 0.18, sides=16)
    for x in (x0 + 1.5, x0 + 3.5):
        sphere(m, "road_toy_red", x, 0.0, 3.2, 0.32, rings=3, segs=8)  # round hatches


def toy_box_body(m, bx1, mat, roof, stripes=None):
    x0 = BX0 + 0.1
    m.box("dark", x0 + 0.3, bx1, -1.1, 1.1, 1.0, 1.2)
    if stripes:
        # The body in bands of two colours, side by side.
        x, k = x0, 0
        while x < bx1 - 0.01:
            xb = min(x + 0.45, bx1)
            m.box(stripes if k % 2 == 0 else mat, x, xb, Y0, Y1, 1.2, 3.0)
            x, k = xb, k + 1
    else:
        m.box(mat, x0, bx1, Y0, Y1, 1.2, 3.0)
    arch(m, roof, x0 - 0.05, bx1 + 0.05, Y0 - 0.05, Y1 + 0.05, 3.0, 0.4)
    m.box("dark", x0 - 0.04, x0, -0.03, 0.03, 1.3, 2.9)
    return x0


def toy_van_body(m, bx1):
    x0 = toy_box_body(m, bx1, "road_toy_yellow", "company")
    # Big toy blocks painted on the sides, and a ball on the roof.
    blocks = ("road_toy_red", "road_toy_blue", "road_toy_green")
    for k, x in enumerate((x0 + 0.5, x0 + 1.7, x0 + 2.9)):
        for y, s in ((Y0, -1), (Y1, 1)):
            ya, yb = sorted((y, y + s * 0.05))
            m.box(blocks[k], x, x + 1.0, ya, yb, 1.5, 2.6)
            yc, yd = sorted((y + s * 0.05, y + s * 0.08))
            m.box("road_white", x + 0.3, x + 0.7, yc, yd, 1.8, 2.3)
    sphere(m, "road_toy_red", x0 + 1.2, 0.0, 3.75, 0.45, rings=4, segs=8)
    m.box("road_toy_blue", x0 + 2.6, x0 + 3.4, -0.4, 0.4, 3.3, 4.0)  # a block on the roof


def sweet_van_body(m, bx1):
    x0 = toy_box_body(m, bx1, "road_white", "road_toy_pink", stripes="road_toy_pink")
    # A lollipop on the roof.
    cyl(m, "road_white", "z", (x0 + 2.0, 0.0), 0.07, 3.3, 3.8, sides=6)
    cyl(m, "road_toy_red", "y", (x0 + 2.0, 4.05), 0.38, -0.12, 0.12, sides=12)
    cyl(m, "road_white", "y", (x0 + 2.0, 4.05), 0.2, -0.14, 0.14, sides=12)


def build():
    models = [
        ("road_coal_truck.glb", coal_truck, [7, 8, 9]),
        ("road_mail_truck.glb", mail_truck, [10, 11, 12]),
        ("road_oil_tanker.glb", lambda: tanker_truck(cab_flat, "boiler"), [16, 17, 18]),
        ("road_livestock_van.glb", livestock_truck, [19, 20, 21]),
        ("road_goods_truck.glb", goods_truck, [22, 23, 24]),
        ("road_grain_truck.glb", grain_truck, [25, 26, 27]),
        ("road_wood_truck.glb", wood_truck, [28, 29, 30]),
        ("road_iron_ore_truck.glb", iron_ore_truck, [31, 32, 33]),
        ("road_steel_truck.glb", steel_truck, [34, 35, 36]),
        ("road_armoured_truck.glb", armoured_truck, [37, 38, 39]),
        ("road_food_van.glb", food_van, [40, 41, 42]),
        ("road_paper_truck.glb", paper_truck, [43, 44, 45]),
        ("road_copper_ore_truck.glb", copper_ore_truck, [46, 47, 48]),
        ("road_water_tanker.glb", lambda: tanker_truck(cab_round, "road_water", band="company", ends="road_white"), [49, 50, 51]),
        ("road_fruit_truck.glb", fruit_truck, [52, 53, 54]),
        ("road_rubber_truck.glb", rubber_truck, [55, 56, 57]),
        ("road_toy_bus.glb", toy_bus, [4, 5]),
        ("road_toy_bus_double.glb", lambda: toy_bus(double=True), [6]),
        ("road_toy_mail_truck.glb", toy_mail, [13, 14, 15]),
        ("road_toy_sugar_truck.glb", lambda: toy_lorry(sugar_body, "road_toy_red"), [58, 59, 60]),
        ("road_toy_cola_truck.glb", lambda: toy_lorry(cola_body, "company", "road_toy_red"), [61, 62, 63]),
        ("road_toy_candyfloss_truck.glb", lambda: toy_lorry(candyfloss_body, "road_toy_pink", "road_toy_purple"), [64, 65, 66]),
        ("road_toy_toffee_truck.glb", lambda: toy_lorry(toffee_body, "company", "road_toy_green"), [67, 68, 69]),
        ("road_toy_toy_van.glb", lambda: toy_lorry(toy_van_body, "company", "road_toy_red"), [70, 71, 72]),
        ("road_toy_sweet_truck.glb", lambda: toy_lorry(sweet_van_body, "road_toy_pink", "road_white"), [73, 74, 75]),
        ("road_toy_battery_truck.glb", lambda: toy_lorry(battery_body, "company", "road_toy_green"), [76, 77, 78]),
        ("road_toy_fizzy_drink_truck.glb", lambda: toy_lorry(fizzy_body, "road_toy_blue", "road_toy_pink"), [79, 80, 81]),
        ("road_toy_plastic_truck.glb", lambda: toy_lorry(plastic_body, "road_toy_green", "road_toy_blue"), [82, 83, 84]),
        ("road_toy_bubble_truck.glb", lambda: toy_lorry(bubble_body, "company", "road_white"), [85, 86, 87]),
    ]
    vehicles = []
    for filename, make, ids in models:
        make().save(filename)
        vehicles.append({"type": "road", "ids": ids, "model": filename})
    return {"vehicles": vehicles, "buildings": []}
