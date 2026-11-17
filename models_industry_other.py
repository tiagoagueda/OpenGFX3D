"""Industry tiles of the base-game industries that exist only in the sub-arctic, sub-tropical or toyland climates.

Each industry tile (gfx id) gets a model of one tile, 16 by 16. The tiles of an industry are drawn as parts of one
site: a building that spans several tiles is cut at the tile edges, so the tiles fit together as the layouts in
src/table/build_industry.h put them. In those layouts the first number is the offset along x (towards the front,
south-west) and the second along y (to the left of the model, south-east), so tile (0, 0) is the back corner.
"""

import math
import random

from gfx3d import MATERIALS, Model

GROUP = "industry_other"

NEW_MATERIALS = {
    "io_redearth": (0.66, 0.40, 0.26),
    "io_dirt": (0.50, 0.42, 0.32),
    "io_spoil": (0.54, 0.52, 0.49),
    "io_copper_ore": (0.62, 0.38, 0.24),
    "io_copper": (0.78, 0.46, 0.24),
    "io_verdigris": (0.36, 0.62, 0.52),
    "io_gold": (0.92, 0.76, 0.24),
    "io_water": (0.26, 0.46, 0.66),
    "io_leaf": (0.26, 0.50, 0.18),
    "io_leaf_dark": (0.13, 0.32, 0.13),
    "io_orange": (0.98, 0.56, 0.10),
    "io_trunk": (0.40, 0.28, 0.18),
    "io_bark": (0.58, 0.55, 0.48),
    "io_logs": (0.56, 0.40, 0.24),
    "io_logend": (0.82, 0.68, 0.46),
    "io_planks": (0.84, 0.70, 0.48),
    "io_paper": (0.95, 0.95, 0.91),
    "io_white": (0.96, 0.96, 0.96),
    "io_red": (0.90, 0.16, 0.18),
    "io_pink": (0.99, 0.66, 0.82),
    "io_pink_dark": (0.90, 0.46, 0.66),
    "io_yellow": (0.99, 0.84, 0.18),
    "io_blue": (0.22, 0.46, 0.92),
    "io_green": (0.30, 0.76, 0.30),
    "io_purple": (0.62, 0.32, 0.78),
    "io_cola": (0.28, 0.13, 0.06),
    "io_toffee": (0.72, 0.46, 0.18),
    "io_toffee_dark": (0.50, 0.30, 0.12),
    "io_battery": (0.16, 0.16, 0.18),
    "io_battery_band": (0.92, 0.66, 0.16),
    "io_sugar": (0.98, 0.98, 0.96),
    "io_bubble": (0.72, 0.88, 0.99),
    "io_soil": (0.46, 0.34, 0.24),
    "io_tan": (0.76, 0.60, 0.42),
    "io_lightblue": (0.56, 0.74, 0.90),
}
for _name, _colour in NEW_MATERIALS.items():
    MATERIALS.setdefault(_name, _colour)


class Shifted(Model):
    """Draws into another model, moved by (ox, oy); used to put the tiles of an industry together for previews."""

    def __init__(self, base, ox, oy):
        super().__init__()
        self.base, self.ox, self.oy = base, ox, oy

    def triangle(self, material, a, b, c):
        s = lambda p: (p[0] + self.ox, p[1] + self.oy, p[2])
        self.base.triangle(material, s(a), s(b), s(c))


# ---------------------------------------------------------------------------------------------------------------
# Shapes


def ext(ix, iy, nx, ny, margin=1.0):
    """The part of tile (ix, iy) covered by a building over nx by ny tiles, set back by margin at its outer walls."""
    return (-8 + (margin if ix == 0 else 0), 8 - (margin if ix == nx - 1 else 0),
            -8 + (margin if iy == 0 else 0), 8 - (margin if iy == ny - 1 else 0))


def outer(ix, iy, nx, ny):
    """The outer walls of tile (ix, iy) of a building over nx by ny tiles: x/X back/front, y/Y right/left."""
    return ("x" if ix == 0 else "") + ("X" if ix == nx - 1 else "") + ("y" if iy == 0 else "") + ("Y" if iy == ny - 1 else "")


def wins(m, x0, x1, y0, y1, z0, z1, rows, per_side, sides="xXyY", size=(1.4, 1.5), material="glass", depth=0.08):
    """Windows on some walls of a box: x is the back wall, X the front, y the right and Y the left."""
    w, h = size
    for row in range(rows):
        zc = z0 + (row + 0.5) * (z1 - z0) / rows
        for i in range(per_side):
            xc = x0 + (i + 0.5) * (x1 - x0) / per_side
            yc = y0 + (i + 0.5) * (y1 - y0) / per_side
            if "y" in sides:
                m.box(material, xc - w / 2, xc + w / 2, y0 - depth, y0, zc - h / 2, zc + h / 2)
            if "Y" in sides:
                m.box(material, xc - w / 2, xc + w / 2, y1, y1 + depth, zc - h / 2, zc + h / 2)
            if "x" in sides:
                m.box(material, x0 - depth, x0, yc - w / 2, yc + w / 2, zc - h / 2, zc + h / 2)
            if "X" in sides:
                m.box(material, x1, x1 + depth, yc - w / 2, yc + w / 2, zc - h / 2, zc + h / 2)


def roof_y(m, material, gable, x0, x1, y0, y1, z0, z1):
    """A pitched roof with its ridge along y."""
    xm = (x0 + x1) / 2
    m.quad(material, (x1, y0, z0), (x1, y1, z0), (xm, y1, z1), (xm, y0, z1))
    m.quad(material, (x0, y1, z0), (x0, y0, z0), (xm, y0, z1), (xm, y1, z1))
    m.triangle(gable, (x1, y1, z0), (x0, y1, z0), (xm, y1, z1))
    m.triangle(gable, (x0, y0, z0), (x1, y0, z0), (xm, y0, z1))


def sawtooth(m, roof, glass, wall, x0, x1, y0, y1, z0, h, teeth):
    """A sawtooth roof with its teeth along y, the glass facing -y."""
    step = (y1 - y0) / teeth
    for i in range(teeth):
        a = y0 + i * step
        m.quad(roof, (x0, a, z0 + h), (x1, a, z0 + h), (x1, a + step, z0), (x0, a + step, z0))
        m.quad(glass, (x1, a, z0), (x0, a, z0), (x0, a, z0 + h), (x1, a, z0 + h))
        m.triangle(wall, (x1, a, z0), (x1, a + step, z0), (x1, a, z0 + h))
        m.triangle(wall, (x0, a + step, z0), (x0, a, z0), (x0, a, z0 + h))


def tank(m, material, x, y, z0, z1, r, sides=12, top=None, bottom=False):
    """An upright closed cylinder."""
    top = top or material
    ring = [(x + r * math.cos(2 * math.pi * i / sides), y + r * math.sin(2 * math.pi * i / sides)) for i in range(sides)]
    for i in range(sides):
        (ax, ay), (bx, by) = ring[i], ring[(i + 1) % sides]
        m.quad(material, (ax, ay, z0), (bx, by, z0), (bx, by, z1), (ax, ay, z1))
        m.triangle(top, (x, y, z1), (ax, ay, z1), (bx, by, z1))
        if bottom:
            m.triangle(material, (x, y, z0), (bx, by, z0), (ax, ay, z0))


def cone(m, material, x, y, z0, z1, r0, r1=0.0, sides=12, top=None):
    """An upright cone, or a frustum when r1 > 0."""
    top = top or material
    for i in range(sides):
        a0, a1 = 2 * math.pi * i / sides, 2 * math.pi * (i + 1) / sides
        p = (x + r0 * math.cos(a0), y + r0 * math.sin(a0), z0)
        q = (x + r0 * math.cos(a1), y + r0 * math.sin(a1), z0)
        if r1 > 0:
            pt = (x + r1 * math.cos(a0), y + r1 * math.sin(a0), z1)
            qt = (x + r1 * math.cos(a1), y + r1 * math.sin(a1), z1)
            m.quad(material, p, q, qt, pt)
            m.triangle(top, (x, y, z1), pt, qt)
        else:
            m.triangle(material, p, q, (x, y, z1))


def sphere(m, material, x, y, z, r, rz=None, seg=10, rings=6, upper=False):
    """A sphere (or an ellipsoid with height rz); with upper, only the half above z."""
    rz = rz if rz is not None else r
    lo = 0 if upper else -rings // 2
    hi = rings // 2 if rings % 2 == 0 else rings // 2 + 1
    if upper:
        hi = rings

    def point(i, j):
        lat = (j / rings) * (math.pi / 2) if upper else (j / (rings / 2)) * (math.pi / 2)
        lat = max(-math.pi / 2, min(math.pi / 2, lat))
        lon = 2 * math.pi * i / seg
        return (x + r * math.cos(lat) * math.cos(lon), y + r * math.cos(lat) * math.sin(lon), z + rz * math.sin(lat))

    for j in range(lo, hi):
        for i in range(seg):
            a, b, c, d = point(i, j), point(i + 1, j), point(i + 1, j + 1), point(i, j + 1)
            if abs(a[0] - d[0]) < 1e-9 and abs(a[1] - d[1]) < 1e-9 and j + 1 == hi:
                m.triangle(material, a, b, c)
            elif abs(a[0] - b[0]) < 1e-9 and abs(a[1] - b[1]) < 1e-9 and abs(a[2] - b[2]) < 1e-9:
                m.triangle(material, a, c, d)
            else:
                m.quad(material, a, b, c, d)


def mound(m, material, x, y, rx, ry, h, seg=10, rings=3):
    """A heap: the upper half of a flattened ellipsoid."""
    def point(i, j):
        lat = (j / rings) * (math.pi / 2)
        lon = 2 * math.pi * i / seg
        return (x + rx * math.cos(lat) * math.cos(lon), y + ry * math.cos(lat) * math.sin(lon), h * math.sin(lat))
    for j in range(rings):
        for i in range(seg):
            a, b, c, d = point(i, j), point(i + 1, j), point(i + 1, j + 1), point(i, j + 1)
            if j == rings - 1:
                m.triangle(material, a, b, c)
            else:
                m.quad(material, a, b, c, d)


def rod(m, material, p0, p1, r, sides=6, caps=True):
    """A straight bar of radius r from p0 to p1, in any direction."""
    d = [p1[i] - p0[i] for i in range(3)]
    ln = math.sqrt(sum(v * v for v in d)) or 1.0
    d = [v / ln for v in d]
    ref = (0, 0, 1) if abs(d[2]) < 0.9 else (1, 0, 0)
    u = [d[1] * ref[2] - d[2] * ref[1], d[2] * ref[0] - d[0] * ref[2], d[0] * ref[1] - d[1] * ref[0]]
    lu = math.sqrt(sum(v * v for v in u))
    u = [v / lu for v in u]
    v = [d[1] * u[2] - d[2] * u[1], d[2] * u[0] - d[0] * u[2], d[0] * u[1] - d[1] * u[0]]
    ring = []
    for i in range(sides):
        a = 2 * math.pi * (i + 0.5) / sides
        ring.append([r * (math.cos(a) * u[k] + math.sin(a) * v[k]) for k in range(3)])
    P = lambda base, o: tuple(base[k] + o[k] for k in range(3))
    for i in range(sides):
        a, b = ring[i], ring[(i + 1) % sides]
        m.quad(material, P(p0, a), P(p1, a), P(p1, b), P(p0, b))
        if caps:
            m.triangle(material, tuple(p1), P(p1, b), P(p1, a))
            m.triangle(material, tuple(p0), P(p0, a), P(p0, b))


def lattice_tower(m, material, x, y, half, z0, z1, levels=4):
    """A tower of steel girders: four legs leaning in a little, with braces."""
    top = half * 0.6
    legs = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            legs.append(((x + sx * half, y + sy * half, z0), (x + sx * top, y + sy * top, z1)))
            rod(m, material, legs[-1][0], legs[-1][1], 0.22, 4)
    order = [0, 1, 3, 2]
    for lv in range(1, levels + 1):
        t = lv / levels
        pts = [tuple(a[k] + (b[k] - a[k]) * t for k in range(3)) for a, b in legs]
        for i in range(4):
            rod(m, material, pts[order[i]], pts[order[(i + 1) % 4]], 0.12, 4, caps=False)
        tp = [tuple(a[k] + (b[k] - a[k]) * (lv - 1) / levels for k in range(3)) for a, b in legs]
        for i in range(4):
            rod(m, material, tp[order[i]], pts[order[(i + 1) % 4]], 0.09, 4, caps=False)


def rails(m, x0, x1, y, z=0.0):
    """A short track along x."""
    for i in range(int((x1 - x0) / 1.2)):
        xs = x0 + 0.3 + i * 1.2
        m.box("wood", xs, xs + 0.5, y - 1.0, y + 1.0, z, z + 0.15)
    for dy in (-0.6, 0.6):
        m.box("metal", x0, x1, y + dy - 0.08, y + dy + 0.08, z + 0.15, z + 0.3)


def ore_cart(m, x, y, load, z=0.3):
    m.box("dark", x - 0.9, x + 0.9, y - 0.6, y + 0.6, z, z + 0.4)
    m.box("rust", x - 1.0, x + 1.0, y - 0.75, y + 0.75, z + 0.4, z + 1.4)
    m.box(load, x - 0.9, x + 0.9, y - 0.65, y + 0.65, z + 1.4, z + 1.65)


def crates(m, x, y, n, material="wood", seed=1, size=1.4):
    rnd = random.Random(seed)
    for i in range(n):
        cx = x + rnd.uniform(-1.5, 1.5)
        cy = y + rnd.uniform(-1.5, 1.5)
        hgt = size * rnd.choice((1, 1, 2))
        m.box(material, cx - size / 2, cx + size / 2, cy - size / 2, cy + size / 2, 0, hgt)


def pad(m, material="concrete", x0=-8, x1=8, y0=-8, y1=8, h=0.12):
    m.box(material, x0, x1, y0, y1, 0, h)


def tree(m, x, y, h, r, leaf="io_leaf", trunk="io_trunk", fruit=None, seed=0):
    rod(m, trunk, (x, y, 0), (x, y, h * 0.55), 0.25, 5)
    sphere(m, leaf, x, y, h * 0.62, r, rz=h * 0.38, seg=8, rings=4)
    if fruit:
        rnd = random.Random(seed)
        for i in range(5):
            a = rnd.uniform(0, 2 * math.pi)
            zz = h * 0.62 + rnd.uniform(-0.5, 0.5) * h * 0.3
            fx, fy = x + math.cos(a) * r * 0.98, y + math.sin(a) * r * 0.98
            m.box(fruit, fx - 0.25, fx + 0.25, fy - 0.25, fy + 0.25, zz - 0.25, zz + 0.25)


# ---------------------------------------------------------------------------------------------------------------
# Sub-arctic: printing works, paper mill, gold mine, food processing plant, bank


def fence(m, x0, x1, y0, y1, sides, material="metal", h=1.4):
    """A fence along some edges of a rectangle (sides as in wins)."""
    runs = []
    if "x" in sides:
        runs.append(((x0, y0), (x0, y1)))
    if "X" in sides:
        runs.append(((x1, y0), (x1, y1)))
    if "y" in sides:
        runs.append(((x0, y0), (x1, y0)))
    if "Y" in sides:
        runs.append(((x0, y1), (x1, y1)))
    for (ax, ay), (bx, by) in runs:
        n = max(1, int(max(abs(bx - ax), abs(by - ay)) / 3))
        for i in range(n + 1):
            px, py = ax + (bx - ax) * i / n, ay + (by - ay) * i / n
            m.box(material, px - 0.1, px + 0.1, py - 0.1, py + 0.1, 0, h)
        m.box(material, min(ax, bx) - 0.06, max(ax, bx) + 0.06, min(ay, by) - 0.06, max(ay, by) + 0.06, h - 0.3, h - 0.15)


def paper_rolls(m, x, y, nx, ny, layers=2, r=1.0):
    for k in range(layers):
        for i in range(nx):
            for j in range(ny):
                tank(m, "io_paper", x + i * 2.2 * r, y + j * 2.2 * r, k * 1.9 * r, (k + 1) * 1.9 * r - 0.05, r, sides=10, top="io_white")


def printing_works(m, ix, iy, gfx):
    """2x2 block of the printing works: brick buildings with roofs in the industry's colour; 43 with two chimneys,
    44 a building beside a yard, 45 a sawtooth hall, 46 a yard with rolls of paper."""
    if gfx == 43:
        m.box("brick", -7, 8, -7, 8, 0, 8)
        wins(m, -7, 8, -7, 8, 1, 7.5, 2, 4, "xy", size=(1.4, 1.8))
        roof_y(m, "slate", "brick", -7.2, 8, -7.2, 8, 8, 11)
        m.box("company", -7.3, 8, -7.3, -7.0, 7.6, 8.1)
        m.box("company", -7.3, -7.0, -7.3, 8, 7.6, 8.1)
        for (x, y, h) in ((-4, -4, 24), (2, -2, 20)):
            m.box("brick", x - 1.1, x + 1.1, y - 1.1, y + 1.1, 0, h)
            m.box("dark", x - 1.3, x + 1.3, y - 1.3, y + 1.3, h - 0.6, h + 0.2)
    elif gfx == 44:
        pad(m, "concrete", -7, 8, -8, 7)
        m.box("brick", -7, 1, -8, 2, 0, 9)
        wins(m, -7, 1, -8, 2, 1, 8.5, 2, 3, "xX", size=(1.4, 1.8))
        m.box("company", -7.2, 1.2, -8, 2.2, 9, 9.6)
        fence(m, 1, 8, -8, 7, "XY")
        fence(m, -7, 1, 2, 7, "Y")
        m.box("metal", 3, 3.2, -8, -7.8, 0, 6)
        rod(m, "metal", (1, -7.9, 6), (3.1, -7.9, 6), 0.1, 4)
    elif gfx == 45:
        m.box("brick", -8, 7, -7, 8, 0, 6.5)
        wins(m, -8, 7, -7, 8, 1, 6, 1, 4, "Xy", size=(1.8, 2.2))
        sawtooth(m, "company", "glass", "brick", -8, 7, -7, 8, 6.5, 2.4, 4)
        m.box("door", 7, 7.1, -1.6, 1.6, 0, 3.6)
    elif gfx == 46:
        pad(m, "concrete", -8, 7, -8, 7)
        fence(m, -8, 7, -8, 7, "XY", material="company")
        paper_rolls(m, -4, -4, 2, 2)
        paper_rolls(m, 2, 1, 2, 1, layers=1)
        tank(m, "io_paper", -3, 3.5, 0, 1.9, 1.0, sides=10, top="io_white")


def paper_mill(m, gfx):
    """The paper mill, 4 tiles along x and 3 along y, in tan stone: the mill (64), an open shed (65), gabled halls
    (66), a store of paper rolls (67), the boiler yard with two chimneys (68, 69), a shed (70), a log store (71)."""
    if gfx == 64:
        m.box("io_tan", -8, 7, -7, 8, 0, 6)
        roof_y(m, "slate", "io_tan", -8, 7.2, -7.2, 8, 6, 9.5)
        m.box("io_tan", -7, 1, -5, 4, 6, 11)
        m.box("brick", -7.2, 1.2, -5.2, 4.2, 11, 11.4)
        m.box("slate", -6.8, 0.8, -4.8, 3.8, 11.4, 11.6)
        wins(m, -8, 7, -7, 8, 1, 5.5, 1, 4, "Xy", size=(1.4, 1.8))
        wins(m, -7, 1, -5, 4, 7, 10.5, 1, 3, "Xy", size=(1.2, 1.6))
    elif gfx == 65:  # open shed on posts
        pad(m, "io_dirt")
        for x in (-6, 0, 6):
            for y in (-6, 6):
                m.box("metal", x - 0.2, x + 0.2, y - 0.2, y + 0.2, 0, 5)
        roof_y(m, "slate", "metal", -7, 7, -7, 7, 5, 7)
        m.cylinder("io_logs", -5, 5, -3, 0.8, 0.8, sides=8, caps="io_logend")
        m.cylinder("io_logs", -5, 5, -1.3, 0.8, 0.8, sides=8, caps="io_logend")
    elif gfx == 66:  # two gabled halls
        for (x0, x1, y0, y1, h) in ((-7, 1, -7, 3, 9), (1, 7, -3, 7, 6)):
            m.box("io_tan", x0, x1, y0, y1, 0, h)
            m.prism_roof("slate", "io_tan", x0 - 0.2, x1 + 0.2, y0 - 0.2, y1 + 0.2, h, h + 3)
            wins(m, x0, x1, y0, y1, 1, h - 0.5, 2 if h > 7 else 1, 3, "XY", size=(1.2, 1.8))
    elif gfx == 67:  # store with stacks of paper rolls
        pad(m, "concrete")
        m.box("io_tan", -7, -1, -7, 7, 0, 7)
        roof_y(m, "slate", "io_tan", -7.2, -0.8, -7.2, 7.2, 7, 9.5)
        wins(m, -7, -1, -7, 7, 1, 6.5, 1, 3, "X", size=(1.4, 2.0))
        paper_rolls(m, 1.5, -5.5, 3, 2)
        paper_rolls(m, 1.5, 2.5, 2, 2, layers=1)
    elif gfx in (68, 69):  # walled yard with two chimneys
        m.box("io_dirt", -8, 8, -8, 8, 0, 0.1)
        for (x0, x1, y0, y1) in ((-8, 8, -8, -7.3), (-8, 8, 7.3, 8), (-8, -7.3, -8, 8), (7.3, 8, -8, 8)):
            m.box("io_tan", x0, x1, y0, y1, 0, 1.6)
        m.box("io_tan", -7, -2.5, -7, -2.5, 0, 26)
        m.box("brick", -7.3, -2.2, -7.3, -2.2, 24, 25)
        m.box("dark", -6.4, -3.1, -6.4, -3.1, 25.9, 26.05)
        m.box("io_tan", -6.5, -3, -1, 2.5, 0, 16)
        m.box("brick", -6.8, -2.7, -1.3, 2.8, 14, 15)
        m.box("dark", -6, -3.5, -0.5, 2, 15.9, 16.05)
        if gfx == 69:
            paper_rolls(m, 1, 0, 3, 3, layers=1, r=1.1)
    elif gfx == 70:  # small shed on a dark yard
        m.box("dark", -8, 8, -8, 8, 0, 0.1)
        m.box("io_tan", -6, 0, -6, 0, 0, 4)
        roof_y(m, "slate", "io_tan", -6.2, 0.2, -6.2, 0.2, 4, 6)
        m.box("door", 0, 0.1, -3.8, -2.2, 0, 2.6)
    elif gfx == 71:  # shed and a pile of logs
        m.box("dark", -8, 8, -8, 8, 0, 0.1)
        m.box("io_tan", -6, -1, -6, -1, 0, 4)
        roof_y(m, "slate", "io_tan", -6.2, -0.8, -6.2, -0.8, 4, 6)
        rnd = random.Random(71)
        for layer in range(3):
            n = 5 - layer
            for i in range(n):
                y = 2.5 + (i - (n - 1) / 2) * 1.5
                m.cylinder("io_logs", -6 + rnd.uniform(-0.4, 0.4), 7 + rnd.uniform(-0.4, 0.4), y, 0.75 + layer * 1.25, 0.75, sides=8, caps="io_logend")


def spoil_heap(m, seed, material="io_spoil", big=1.0):
    rnd = random.Random(seed)
    for i in range(3):
        x, y = rnd.uniform(-3, 3), rnd.uniform(-3, 3)
        mound(m, material, x, y, rnd.uniform(3.5, 5.5) * big, rnd.uniform(3.5, 5.5) * big, rnd.uniform(2.5, 4.5) * big)


def gold_mine(m, gfx):
    """4x4 gold mine: buildings along the back, the shaft tower, rails, ore carts and spoil heaps."""
    if gfx == 72:  # ore mill
        m.box("stone", -7, 7, -7, 8, 0, 8)
        m.prism_roof("slate", "stone", -7.3, 7.3, -7.3, 8, 8, 11.5)
        wins(m, -7, 7, -7, 8, 1, 7.5, 2, 4, "xXy", size=(1.4, 1.8))
        m.box("wood", 2, 6, 8 - 0.01, 8, 0, 0.01)
    elif gfx == 73:  # yard with track and carts
        pad(m, "io_dirt")
        rails(m, -8, 8, 0)
        ore_cart(m, -3.5, 0, "io_gold")
        ore_cart(m, 0, 0, "io_spoil")
        crates(m, 4, -5, 3, seed=73)
    elif gfx == 74:  # mill with chimney
        m.box("stone", -8, 7, -8, 8, 0, 7)
        m.prism_roof("slate", "stone", -8, 7.3, -8, 8, 7, 10)
        wins(m, -8, 7, -8, 8, 1, 6.5, 2, 4, "X", size=(1.4, 1.8))
        m.box("brick", 1.5, 4, -5, -2.5, 0, 17)
        m.box("dark", 1.3, 4.2, -5.2, -2.3, 16.5, 17.3)
    elif gfx == 75:  # winding house beside the shaft tower
        m.box("wall", -7, 6, -7, 7, 0, 6)
        m.prism_roof("slate", "wall", -7.3, 6.3, -7.3, 7.3, 6, 9)
        wins(m, -7, 6, -7, 7, 1, 5.5, 1, 3, "xXY", size=(1.4, 1.8))
        m.box("door", 6, 6.1, -1, 1, 0, 3)
        m.box("brick", -4, -2.5, 3, 4.5, 6, 11)
        rod(m, "dark", (4, 0, 7.5), (14, 0, 17.5), 0.08, 4)  # cable to the tower
    elif gfx in (79, 88):  # shaft with headframe
        m.box("stone", -5, 5, -5, 5, 0, 1.2)
        m.box("dark", -2, 2, -2, 2, 1.2, 1.25)
        lattice_tower(m, "rust", 0, 0, 4, 1.2, 17, levels=5)
        m.cylinder("rust", -0.25, 0.25, 0, 17.2, 2.2, sides=12, caps="dark")
        m.box("rust", -2.6, 2.6, -2.6, 2.6, 17, 17.4)
        rod(m, "rust", (-4, 0, 1.2), (-1.2, 0, 15.5), 0.3, 4)  # back strut towards the winding house
        rod(m, "dark", (0, 2.2, 17.2), (0, 2.2, 1.2), 0.05, 4)
        m.box("wood", 3.0, 7.5, -1.4, 1.4, 0, 0.6)
        ore_cart(m, 6, 0, "io_gold", z=0.6)
    elif gfx in (76, 82, 85):  # spoil heaps
        spoil_heap(m, gfx, big={76: 0.9, 82: 1.1, 85: 0.8}[gfx])
    elif gfx in (77, 81):  # tracks with carts
        pad(m, "io_dirt")
        rails(m, -8, 8, -3)
        rails(m, -8, 8, 3)
        ore_cart(m, -2 if gfx == 77 else 3, -3, "io_spoil")
        ore_cart(m, 4 if gfx == 77 else -4, 3, "io_gold")
    elif gfx in (78, 80, 87):  # sheds
        pad(m, "io_dirt")
        m.box("wood", -5, 1, -4, 4, 0, 4)
        roof_y(m, "slate", "wood", -5.3, 1.3, -4.3, 4.3, 4, 6)
        m.box("door", 1, 1.1, -1, 1, 0, 2.6)
        if gfx == 78:
            rails(m, 2, 8, 0)
        else:
            mound(m, "io_spoil", 5, 4 if gfx == 80 else -4, 2.6, 2.6, 2.2)
            crates(m, 4.5, -4 if gfx == 80 else 4, 2, seed=gfx)
    elif gfx in (83, 84, 86):  # settling pond, fences and small heaps
        pad(m, "io_dirt")
        m.box("concrete", -6, 6, -6, 6, 0, 0.8)
        m.box("io_water", -5.4, 5.4, -5.4, 5.4, 0.8, 0.85)
        if gfx == 84:
            mound(m, "io_spoil", -2, 0, 3, 3, 2)
        for x in (-7.5, 7.3):
            for i in range(5):
                m.box("wood", x, x + 0.2, -7 + i * 3.5, -6.8 + i * 3.5, 0, 1.4)
            m.box("wood", x, x + 0.2, -7, 7, 1.0, 1.2)


def bank2(m, gfx):
    """The bank of the sub-arctic and sub-tropical climates: two tiles along x, 90 in front with white columns."""
    if gfx == 89:
        x0, x1 = -6.5, 8
    else:
        x0, x1 = -8, 4
    y0, y1 = -6.5, 6.5
    m.box("brick", x0, x1, y0, y1, 0, 8)
    m.box("io_white", x0 - 0.2, x1, y0 - 0.2, y1 + 0.2, 8, 8.6)
    m.box("io_white", x0 - 0.2, x1, y0 - 0.2, y1 + 0.2, 0, 0.6)
    m.box("io_white", x0 - 0.1, x1, y0 - 0.1, y1 + 0.1, 3.9, 4.3)
    wins(m, x0, x1, y0, y1, 0.8, 8, 2, 3, "yY" + ("x" if gfx == 89 else ""), size=(1.2, 2.2))
    m.box("slate", x0 + 0.5, x1 if gfx == 89 else x1 - 0.5, y0 + 0.5, y1 - 0.5, 8.6, 9.6)
    if gfx == 90:
        m.box("io_white", 4, 7.6, y0, y1, 0, 0.5)  # steps
        m.box("io_white", 4, 6.8, y0, y1, 0, 0.9)
        for i in range(5):
            y = y0 + 0.8 + i * (y1 - y0 - 1.6) / 4
            tank(m, "io_white", 6, y, 0.9, 7.6, 0.45, sides=8)
        m.box("io_white", 4, 7, y0, y1, 7.6, 8.4)
        m.triangle("io_white", (7, y0, 8.4), (7, y1, 8.4), (7, 0, 10.2))
        m.quad("slate", (7, y0, 8.4), (4, y0, 8.4), (4, 0, 10.2), (7, 0, 10.2))
        m.quad("slate", (4, y1, 8.4), (7, y1, 8.4), (7, 0, 10.2), (4, 0, 10.2))
        m.box("door", 4, 4.1, -1.2, 1.2, 0.9, 4.5)


def food_plant(m, gfx):
    """Food processing plant: brick halls with roofs in the industry's colour (60), a boiler house (61),
    striped silos (62) and a fenced grain store (63)."""
    if gfx == 60:
        m.box("brick", -8, 8, -8, 8, 0, 6)
        m.box("concrete", -8, 8, -8, 8, 0, 0.5)
        wins(m, -8, 8, -8, 8, 1, 5.5, 1, 4, size=(1.6, 1.8))
        m.prism_roof("company", "brick", -8, 8, -8.1, 8.1, 6, 9.5)
        m.box("dark", 8, 8.1, -2, 2, 0, 3.5)
    elif gfx == 61:
        pad(m)
        m.box("brick", -7, 2, -7, 3, 0, 6)
        m.box("company", -7.2, 2.2, -7.2, 3.2, 6, 6.5)
        wins(m, -7, 2, -7, 3, 1, 5.5, 1, 3, size=(1.6, 1.8))
        m.box("brick", -5, 0, 3, 7, 0, 3.5)
        m.box("company", -5.2, 0.2, 3, 7.2, 3.5, 3.9)
        m.box("brick", -3, -1, -5, -3, 0, 15)
        m.box("dark", -3.2, -0.8, -5.2, -2.8, 14.5, 15.2)
    elif gfx == 62:
        pad(m)
        for (x, y, r) in ((-2, -2, 4.0), (4.5, 4.5, 2.4)):
            for k in range(5):
                tank(m, "company" if k % 2 == 0 else "concrete", x, y, k * 3, (k + 1) * 3, r, sides=16)
            cone(m, "metal", x, y, 15, 16.5, r, 0.6, sides=16)
        rod(m, "metal", (-2, -2, 16.2), (4.5, 4.5, 16.2), 0.25, 4)
    elif gfx == 63:
        pad(m)
        m.box("brick", -6, 6, -6, 6, 0, 1.2)
        m.box("io_dirt", -5.4, 5.4, -5.4, 5.4, 0, 1.0)
        mound(m, "io_yellow", 0, 0, 4.2, 4.2, 2.6)
        fence(m, -7.5, 7.5, -7.5, 7.5, "xXyY")


# ---------------------------------------------------------------------------------------------------------------
# Sub-tropic: copper ore mine, diamond mine, plantations, water supply and tower, factory, lumber mill


def copper_mine(m, gfx):
    if gfx in (47, 48):  # headframe over the shaft, on a brick engine house
        m.box("brick", -5, 3, -5, 3, 0, 5)
        m.box("dark", -5.2, 3.2, -5.2, 3.2, 5, 5.3)
        lattice_tower(m, "boiler", -1, -1, 3.2, 5.3, 17, levels=4)
        m.cylinder("boiler", -1.25, -0.75, -1, 17.2, 2.2, sides=12, caps="dark")
        m.box("boiler", -3.2, 1.2, -3.2, 1.2, 17, 17.4)
        rod(m, "boiler", (6.5, -1, 0), (-0.5, -1, 16), 0.3, 4)
        rod(m, "boiler", (6.5, 1, 0), (-0.5, 1, 16), 0.3, 4)
        m.box("door", 3, 3.1, -1.5, 0.5, 0, 2.5)
    elif gfx == 49:  # smelter with three chimneys
        m.box("brick", -5, 5, -6, 4, 0, 6)
        roof_y(m, "slate", "brick", -5.2, 5.2, -6.2, 4.2, 6, 8)
        wins(m, -5, 5, -6, 4, 1, 5.5, 1, 3, "XY", size=(1.4, 1.8))
        for y in (-4.5, -2, 0.5):
            m.box("brick", -3, -1.5, y - 0.7, y + 0.7, 6, 14)
            m.box("dark", -3.15, -1.35, y - 0.85, y + 0.85, 13.6, 14.1)
    elif gfx == 50:  # small shed
        m.box("brick", -3.5, 3.5, -4, 4, 0, 4)
        roof_y(m, "slate", "brick", -3.7, 3.7, -4.2, 4.2, 4, 6)
        m.box("door", 3.5, 3.6, -1, 1, 0, 2.6)
    elif gfx == 51:  # two long low sheds with ore
        for (x0, x1, y0, y1) in ((-6, 0, -6, 6), (1.5, 6, -3, 7)):
            m.box("brick", x0, x1, y0, y1, 0, 2.5)
            roof_y(m, "slate", "brick", x0 - 0.2, x1 + 0.2, y0 - 0.2, y1 + 0.2, 2.5, 4.2)
        mound(m, "io_copper_ore", 3.5, -5.5, 2.3, 1.8, 1.4)


def pit_terrace(m, cx, cy, material="io_redearth", floor="io_dirt"):
    """A quarter of an open pit around (cx, cy) in tile coordinates: rings of terraces stepping down to the floor."""
    def height(r):
        if r < 5:
            return 0.0
        if r < 8:
            return 0.6
        if r < 11:
            return 1.3
        if r < 14:
            return 2.0
        if r < 16:
            return 2.8
        if r < 18:
            return 1.4
        return 0.0
    cell = 2.0
    for i in range(8):
        for j in range(8):
            x0, y0 = -8 + i * cell, -8 + j * cell
            r = math.hypot(x0 + cell / 2 - cx, y0 + cell / 2 - cy)
            h = height(r)
            if h > 0:
                m.box(material, x0, x0 + cell, y0, y0 + cell, 0, h)
            elif r < 5:
                m.box(floor, x0, x0 + cell, y0, y0 + cell, 0, 0.05)


def dump_truck(m, x, y, load="io_redearth"):
    m.box("io_yellow", x - 1.6, x + 1.6, y - 1.1, y + 1.1, 0.7, 1.9)
    m.box(load, x - 1.5, x + 0.8, y - 1.0, y + 1.0, 1.9, 2.3)
    m.box("io_yellow", x + 1.0, x + 2.2, y - 0.9, y + 0.9, 0.7, 2.6)
    m.box("glass", x + 2.2, x + 2.25, y - 0.7, y + 0.7, 1.8, 2.4)
    for wx in (x - 1.0, x + 1.5):
        for wy in (y - 1.0, y + 1.0):
            m.wheel(wx, wy, 0.55, 0.4)


def diamond_mine(m, gfx):
    """3x3 diamond mine: buildings on the back row and the right column, an open pit on the four front tiles."""
    if gfx == 91:  # treatment plant
        m.box("concrete", -7, 6, -7, 6, 0, 9)
        wins(m, -7, 6, -7, 6, 1, 8.5, 2, 3, "XY", size=(1.6, 1.8))
        m.box("metal", -7.2, 6.2, -7.2, 6.2, 9, 9.4)
        m.box("metal", -3, 2, -3, 2, 9.4, 12)
        tank(m, "metal", 3, 3, 9.4, 13, 1.2, top="dark")
    elif gfx == 92:  # sorting house, conveyor to the plant
        m.box("wall", -6, 6, -5, 6, 0, 6)
        roof_y(m, "tiles", "wall", -6.3, 6.3, -5.3, 6.3, 6, 8.5)
        wins(m, -6, 6, -5, 6, 1, 5.5, 1, 3, "XY", size=(1.4, 1.8))
        rod(m, "metal", (0, -5, 5), (0, -10, 8), 0.5, 4)
    elif gfx == 93:  # offices with a guarded fence
        m.box("io_white", -5, 4, -5, 5, 0, 6.6)
        m.box("concrete", -5.2, 4.2, -5.2, 5.2, 6.6, 7)
        wins(m, -5, 4, -5, 5, 0.6, 6.4, 2, 3, size=(1.3, 1.4))
        m.box("door", 4, 4.1, -0.7, 0.7, 0, 2.3)
        for y in (7.5,):
            m.box("metal", -8, 8, y, y + 0.15, 1.6, 1.8)
            for i in range(6):
                m.box("metal", -7.8 + i * 3.1, -7.6 + i * 3.1, y, y + 0.15, 0, 1.8)
    elif gfx == 94:  # crusher with conveyor down into the pit
        m.box("metal", -6, 2, -7, 1, 0, 10)
        m.box("rust", -6.2, 2.2, -7.2, 1.2, 10, 10.6)
        cone(m, "metal", -2, -3, 10.6, 13, 3, 1.2, sides=8)
        rod(m, "metal", (0, 0, 8), (6, 8, 2.8), 0.5, 4)
        for (x, y) in ((3, 4), (5, 6.7)):
            m.box("metal", x - 0.15, x + 0.15, y - 0.15, y + 0.15, 0, 5.5 - x * 0.5)
        mound(m, "io_redearth", 4, -4, 3, 3, 2.5)
    elif gfx == 97:  # workshop and spoil heap at the front right
        m.box("metal", -6, 1, -6, 2, 0, 5)
        roof_y(m, "slate", "metal", -6.2, 1.2, -6.2, 2.2, 5, 6.5)
        m.box("dark", 1, 1.1, -4.5, 0.5, 0, 4)
        mound(m, "io_redearth", 3, 4, 4.5, 3.5, 3.6)
        dump_truck(m, 4, -4.5)
    elif gfx == 95:
        pit_terrace(m, 8, 8)
    elif gfx == 96:
        pit_terrace(m, 8, -8)
        dump_truck(m, -1.5, -4)
    elif gfx == 98:
        pit_terrace(m, -8, 8)
    elif gfx == 99:
        pit_terrace(m, -8, -8)


def plantation(m, rubber):
    if rubber:
        for i, (x, y) in enumerate(((-4, -4), (-4, 4), (4, -4), (4, 4))):
            rod(m, "io_bark", (x, y, 0), (x, y, 6), 0.35, 6)
            sphere(m, "io_leaf_dark", x, y, 8.5, 3.2, rz=3.3, seg=9, rings=4)
            m.box("io_white", x + 0.35, x + 0.55, y - 0.25, y + 0.25, 1.2, 1.7)  # latex cup
    else:
        k = 0
        for x in (-5, 0, 5):
            for y in (-5, 0, 5):
                tree(m, x, y, 5.2, 2.0, fruit="io_orange", seed=k)
                k += 1


def frame_top(m, a, z):
    for (x0, x1, y0, y1) in ((-a, a, -a, -a + 0.4), (-a, a, a - 0.4, a), (-a, -a + 0.4, -a, a), (a - 0.4, a, -a, a), (-a, a, -0.2, 0.2)):
        m.box("metal", x0, x1, y0, y1, z, z + 0.4)


def water_supply(m, gfx):
    """Water supply: pumps in blue tanks in a steel frame (118) and the pipework (119), in the industry's colour."""
    pad(m)
    if gfx == 118:
        for (x, y) in ((-3, -3), (-3, 3), (3, -3), (3, 3)):
            tank(m, "company", x, y, 0, 4, 1.6, sides=12, top="metal")
        for (x, y) in ((-5, -5), (-5, 5), (5, -5), (5, 5)):
            m.box("metal", x - 0.25, x + 0.25, y - 0.25, y + 0.25, 0, 13)
        frame_top(m, 5.25, 13)
        for x in (-3, 3):
            rod(m, "company", (x, 0, 4), (x, 0, 13), 0.6, 8)
            rod(m, "company", (x, -3, 3.5), (x, 3, 3.5), 0.5, 8)
    else:
        for (x, y) in ((-5, -5), (-5, 5), (5, -5), (5, 5)):
            m.box("metal", x - 0.2, x + 0.2, y - 0.2, y + 0.2, 0, 9)
        frame_top(m, 5.2, 9)
        for z in (3, 6):
            rod(m, "metal", (-8, -2, z), (8, -2, z), 0.5, 8, caps=False)
            rod(m, "metal", (-2, -8, z + 1), (-2, 8, z + 1), 0.5, 8, caps=False)
        tank(m, "company", 2.5, 2.5, 0, 5, 2.0, sides=12, top="metal")
        tank(m, "io_white", -4.5, 4.5, 0, 2.5, 1.2, sides=10)


def water_tower(m):
    """A big tank with bands in the industry's colour on short legs."""
    pad(m)
    for i in range(8):
        a = 2 * math.pi * (i + 0.5) / 8
        x, y = 5.6 * math.cos(a), 5.6 * math.sin(a)
        m.box("metal", x - 0.3, x + 0.3, y - 0.3, y + 0.3, 0, 4)
    tank(m, "metal", 0, 0, 3.8, 4.2, 6.6, sides=20, bottom=True)
    for k in range(4):
        tank(m, "company" if k % 2 == 0 else "concrete", 0, 0, 4.2 + k * 2.4, 6.6 + k * 2.4, 6.3, sides=20)
    sphere(m, "company", 0, 0, 13.8, 6.3, rz=2.0, seg=20, rings=3, upper=True)
    rod(m, "metal", (6.3, 0, 13.8), (6.3, 0, 0), 0.15, 4)


def factory2(m, gfx):
    """The sub-tropical factory, 2x2: brick halls with roofs in the industry's colour; 121 with three chimneys,
    122 a tall block, 123 the long hall, 124 a yard of tyres and pallets."""
    if gfx == 121:
        pad(m, "concrete")
        m.box("brick", -6, 6, -6, 6, 0, 6)
        wins(m, -6, 6, -6, 6, 1, 5.5, 1, 3, size=(1.6, 1.8))
        m.prism_roof("company", "brick", -6.3, 6.3, -6.3, 6.3, 6, 8.5)
        for (x, y, h) in ((-3, -3, 18), (0, 0, 15), (3, 3, 20)):
            tank(m, "brick", x, y, 6, h, 0.8, sides=10, top="dark")
    elif gfx == 122:
        m.box("brick", -7, 6, -8, 2, 0, 15)
        wins(m, -7, 6, -8, 2, 1, 14.5, 4, 3, "xXY", size=(1.4, 1.8))
        m.box("company", -7.2, 6.2, -8.2, 2.2, 15, 15.6)
        m.box("brick", -7, 6, 2, 7, 0, 7)
        m.prism_roof("company", "brick", -7.2, 6.2, 2, 7.2, 7, 9)
        for x in (-4, 0, 4):
            rod(m, "io_battery", (x, 6.8, 0.9), (x, 8.0, 0.9), 0.9, 10)
    elif gfx == 123:
        m.box("brick", -8, 7, -7, 8, 0, 8)
        wins(m, -8, 7, -7, 8, 1, 7.5, 2, 4, "Xy", size=(1.6, 1.8))
        m.prism_roof("company", "brick", -8, 7.3, -7.3, 8, 8, 11)
        m.box("dark", 7, 7.1, -2.5, 2.5, 0, 4.5)
    elif gfx == 124:
        pad(m, "concrete", -8, 7, -8, 7)
        for (x, y) in ((-4, -4), (-4, 2), (2, -4)):
            m.box("wood", x - 2, x + 2, y - 2, y + 2, 0, 0.5)
            m.box("metal", x - 1.8, x + 1.8, y - 1.8, y + 1.8, 0.5, 1.4)
        for k in range(3):
            for (x, y) in ((2.5, 2.5), (5, 2.5), (2.5, 5)):
                tank(m, "io_battery", x, y, k * 0.9, k * 0.9 + 0.85, 1.1, sides=10, top="dark")


def lumber_mill(m, gfx):
    """2x2 lumber mill: saw shed, logs, timber stacks and a crane."""
    if gfx == 125:  # open saw shed
        pad(m, "io_dirt")
        for x in (-6, 0, 6):
            for y in (-6, 6):
                m.box("wood", x - 0.3, x + 0.3, y - 0.3, y + 0.3, 0, 6)
        roof_y(m, "rust", "wood", -7, 7, -7, 7, 6, 9)
        m.box("metal", -4, 4, -1.5, 1.5, 0, 1.6)
        m.cylinder("metal", -0.1, 0.1, 0, 2.3, 1.4, sides=12)  # saw blade
        m.cylinder("io_logs", -6, 6, -4, 0.8, 0.8, sides=8, caps="io_logend")
    elif gfx == 126:  # log pile
        rnd = random.Random(126)
        for layer in range(4):
            n = 6 - layer
            for i in range(n):
                y = (i - (n - 1) / 2) * 1.7
                m.cylinder("io_logs", -6.5 + rnd.uniform(-0.4, 0.4), 6.5 + rnd.uniform(-0.4, 0.4), y, 0.85 + layer * 1.45, 0.85, sides=8, caps="io_logend")
    elif gfx == 127:  # mill building with conveyor
        m.box("wood", -7, 4, -7, 6, 0, 7)
        roof_y(m, "rust", "wood", -7.3, 4.3, -7.3, 6.3, 7, 10)
        wins(m, -7, 4, -7, 6, 1.5, 6, 1, 3, "Xy", size=(1.4, 1.6))
        tank(m, "metal", -4, -4, 10, 13, 0.6, sides=8, top="dark")
        rod(m, "metal", (4, 2, 5), (8, 6, 1.5), 0.45, 4)
    elif gfx == 128:  # stacks of sawn timber and a crane
        pad(m, "io_dirt")
        for (x, y) in ((-4, -4), (-4, 3), (3, -4)):
            for layer in range(4):
                if layer % 2 == 0:
                    m.box("io_planks", x - 2.5, x + 2.5, y - 2.5, y + 2.5, layer * 0.8, layer * 0.8 + 0.6)
                else:
                    for k in (-2.2, 0, 2.2):
                        m.box("wood", x - 2.5, x + 2.5, y + k - 0.2, y + k + 0.2, layer * 0.8 - 0.2, layer * 0.8)
        m.box("io_yellow", 3, 6, 3, 6, 0, 1.2)
        m.box("io_yellow", 3.6, 5.4, 3.6, 5.4, 1.2, 10)
        rod(m, "io_yellow", (4.5, 4.5, 9.5), (-5, -4, 10), 0.3, 4)
        rod(m, "dark", (-4, -3, 9.8), (-4, -3, 4), 0.05, 4)


# ---------------------------------------------------------------------------------------------------------------
# Toyland


def candyfloss(m, harvested):
    spots = ((-4, -4), (-4, 4), (4, -4), (4, 4), (0, 0))
    for i, (x, y) in enumerate(spots):
        if harvested:
            rod(m, "io_white", (x, y, 0), (x, y, 1.4), 0.25, 6)
            sphere(m, "io_pink", x, y, 1.8, 0.8, seg=6, rings=4)
        else:
            h = 7 if i < 4 else 9
            rod(m, "io_white", (x, y, 0), (x, y, h - 2), 0.25, 6)
            sphere(m, "io_pink" if i % 2 == 0 else "io_pink_dark", x, y, h, 2.6, rz=2.4, seg=10, rings=6)


def candy_cane(m, x, y, h, hook=True):
    n = 7
    for k in range(n):
        tank(m, "io_red" if k % 2 == 0 else "io_white", x, y, k * h / n, (k + 1) * h / n, 0.4, sides=8)
    if hook:
        for k in range(4):
            a0, a1 = math.pi * k / 4, math.pi * (k + 1) / 4
            rod(m, "io_red" if k % 2 == 0 else "io_white", (x, y - 1 + math.cos(a0), h + math.sin(a0)),
                (x, y - 1 + math.cos(a1), h + math.sin(a1)), 0.4, 8)


def sweet_factory(m, gfx):
    """2x2 sweet factory: 131 a yard with a giant sweet; the rest are round halls with swirly roofs in the
    industry's colour and white, and candy-cane posts."""
    if gfx == 131:
        pad(m, "io_white", -7, 8, -7, 8)
        sphere(m, "io_red", 0, 0, 3, 2.4, seg=10, rings=6)
        for s in (-1, 1):
            rod(m, "io_yellow", (0, s * 2.0, 3), (0, s * 4.5, 3), 1.0, 6)
        candy_cane(m, -4.5, 4.5, 7)
    else:
        cx, cy = {132: (0.5, -0.5), 133: (-0.5, 0.5), 134: (-0.5, -0.5)}[gfx]
        r = 7.0
        tank(m, "io_white", cx, cy, 0, 5, r, sides=20)
        for i in range(20):
            if i % 4 == 0:
                a = 2 * math.pi * i / 20
                m.box("company", cx + (r + 0.05) * math.cos(a) - 0.6, cx + (r + 0.05) * math.cos(a) + 0.6,
                      cy + (r + 0.05) * math.sin(a) - 0.6, cy + (r + 0.05) * math.sin(a) + 0.6, 1, 4)
        # Dome with swirls: alternating segments.
        seg, rings = 16, 4
        for j in range(rings):
            for i in range(seg):
                def pt(ii, jj):
                    lat = jj / rings * math.pi / 2
                    lon = 2 * math.pi * ii / seg + jj * 0.45
                    return (cx + r * math.cos(lat) * math.cos(lon), cy + r * math.cos(lat) * math.sin(lon), 5 + 5 * math.sin(lat))
                mat = "company" if i % 2 == 0 else "io_white"
                if j == rings - 1:
                    m.triangle(mat, pt(i, j), pt(i + 1, j), pt(i, j + 1))
                else:
                    m.quad(mat, pt(i, j), pt(i + 1, j), pt(i + 1, j + 1), pt(i, j + 1))
        for (x, y) in ((cx + 7.2, cy - 3), (cx + 7.2, cy + 3), (cx - 3, cy + 7.2)):
            if -8 < x < 8 and -8 < y < 8:
                candy_cane(m, x, y, 7, hook=False)
        if gfx == 134:
            m.box("company", cx + r - 0.5, cx + r + 0.1, cy - 1.5, cy + 1.5, 0, 3.2)


def battery_farm(m, reaped):
    m.box("io_soil", -7.5, 7.5, -7.5, 7.5, 0, 0.2)
    for x in (-5.5, -1.8, 1.8, 5.5):
        for y in (-5.5, -1.8, 1.8, 5.5):
            if reaped:
                m.box("io_battery", x - 0.4, x + 0.4, y - 0.4, y + 0.4, 0.2, 0.7)
            else:
                tank(m, "io_battery", x, y, 0.2, 3.0, 0.9, sides=8)
                tank(m, "io_battery_band", x, y, 3.0, 3.6, 0.92, sides=8)
                tank(m, "metal", x, y, 3.6, 4.0, 0.35, sides=6)


def cola_well(m):
    """A pool of cola with a yellow rim and a candy-cane arch over it."""
    m.box("io_yellow", -6, 6, -6, 6, 0, 0.9)
    m.box("io_yellow", -6.6, -1, -6.6, 2, 0, 1.0)
    m.box("io_cola", -5, 5, -5, 5, 0.9, 0.95)
    for k, (bx, by) in enumerate(((-1, -2), (2, 1), (-2, 3))):
        sphere(m, "io_cola", bx, by, 1.0, 0.4 + 0.15 * k, seg=6, rings=4, upper=True)
    n = 10
    for k in range(n):
        a0, a1 = math.pi * k / n, math.pi * (k + 1) / n
        rod(m, "io_red" if k % 2 == 0 else "io_white", (3.5 * math.cos(a0), 3.5 * math.cos(a0), 1 + 5.5 * math.sin(a0)),
            (3.5 * math.cos(a1), 3.5 * math.cos(a1), 1 + 5.5 * math.sin(a1)), 0.35, 8)


def toy_shop(m, gfx):
    """2x2 toy shop: a castle of building blocks in light blue, a tall tower of blocks with a flag on each building tile,
    and 138 a yard with toy blocks."""
    if gfx == 138:
        pad(m, "concrete", -7, 8, -7, 8)
        cols = ("io_red", "io_blue", "io_yellow", "io_green")
        k = 0
        for (x, y, n) in ((-3, -3, 3), (2, -3, 2), (-3, 2, 1), (3, 3, 2)):
            for j in range(n):
                m.box(cols[k % 4], x - 1.4, x + 1.4, y - 1.4, y + 1.4, j * 2.8, (j + 1) * 2.8)
                k += 1
        return
    x0, x1, y0, y1 = {139: (-7, 8, -8, 7), 140: (-8, 7, -7, 8), 141: (-8, 7, -8, 7)}[gfx]
    side = {139: "xY", 140: "Xy", 141: "XY"}[gfx]
    m.box("io_lightblue", x0, x1, y0, y1, 0, 7)
    wins(m, x0, x1, y0, y1, 1, 6.5, 1, 3, side, size=(1.6, 2.8), material="io_blue")
    for i in range(5):
        t = x0 + 0.2 + i * (x1 - x0 - 1.6) / 4
        for y in (y0, y1 - 1.2):
            m.box("io_lightblue", t, t + 1.2, y, y + 1.2, 7, 8.2)
        u = y0 + 0.2 + i * (y1 - y0 - 1.6) / 4
        for x in (x0, x1 - 1.2):
            m.box("io_lightblue", x, x + 1.2, u, u + 1.2, 7, 8.2)
    towers = {139: [(-1, 1, "io_blue", 20, "io_yellow")], 140: [(1, -1, "io_red", 19, "io_green")],
              141: [(-2, -2, "io_green", 26, "io_red"), (2, 2, "io_yellow", 18, "io_blue")]}[gfx]
    for (x, y, col, h, flag) in towers:
        m.box(col, x - 2.2, x + 2.2, y - 2.2, y + 2.2, 0, h)
        for k in range(int(h / 2.2)):
            m.box(col, x - 2.3, x + 2.3, y - 2.3, y + 2.3, k * 2.2 + 2.0, k * 2.2 + 2.2)
        for (sx, sy) in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
            m.box(col, x + sx * 1.3 - 0.7, x + sx * 1.3 + 0.7, y + sy * 1.3 - 0.7, y + sy * 1.3 + 0.7, h, h + 0.8)
        m.box("io_white", x - 0.1, x + 0.1, y - 0.1, y + 0.1, h, h + 5)
        m.box(flag, x - 0.05, x + 0.05, y, y + 2.4, h + 3.4, h + 5)
    if gfx != 139:
        m.box("door", x1, x1 + 0.1, -4.5 if gfx == 140 else 3, -2.5 if gfx == 140 else 5, 0, 3)


def toy_factory(m, gfx):
    """Toy factory: a long hall on 142-145, 146 the office at the front, 147 the yard beside the hall."""
    if gfx == 147:
        pad(m, "concrete")
        crates(m, 0, -2, 4, "io_yellow", seed=147, size=1.6)
        crates(m, 0, 4, 3, "io_blue", seed=148, size=1.6)
    elif gfx == 146:
        m.box("io_white", -6, 6, -6, 6, 0, 6)
        roof_y(m, "io_red", "io_white", -6.3, 6.3, -6.3, 6.3, 6, 9)
        wins(m, -6, 6, -6, 6, 0.6, 5.8, 2, 3, "XYy", size=(1.4, 1.4), material="io_blue")
        m.box("door", 6, 6.1, -0.8, 0.8, 0, 2.4)
    else:
        ix = {142: 0, 143: 1, 144: 2, 145: 3}[gfx]
        x0, x1, y0, y1 = ext(ix, 0, 4, 1, 1.0)
        m.box("brick", x0, x1, y0, y1, 0, 8)
        wins(m, x0, x1, y0, y1, 1, 7.5, 2, 3, outer(ix, 0, 4, 1).replace("y", ""), size=(1.8, 1.6), material="io_blue")
        m.box("io_yellow", x0, x1, y0, y1, 8, 8.5)
        m.quad("io_red", (x0, y0, 8.5), (x1, y0, 8.5), (x1, 0, 11), (x0, 0, 11))
        m.quad("io_red", (x1, y1, 8.5), (x0, y1, 8.5), (x0, 0, 11), (x1, 0, 11))
        if ix == 0:
            m.triangle("io_yellow", (x0, y1, 8.5), (x0, y0, 8.5), (x0, 0, 11))
        if ix == 3:
            m.triangle("io_yellow", (x1, y0, 8.5), (x1, y1, 8.5), (x1, 0, 11))
            m.box("dark", x1, x1 + 0.1, -2.5, 2.5, 0, 5)
        if gfx == 143:  # the press: a tower with a big stamp
            m.box("metal", -2.5, 2.5, -2.5, 2.5, 0, 15)
            m.box("io_purple", -3, 3, -3, 3, 15, 16)
            m.box("io_red", -1.5, 1.5, -1.5, 1.5, 11, 15)
        if gfx == 144:
            tank(m, "io_yellow", 0, 4, 8, 13, 1.0, sides=10, top="dark")
        if gfx == 142:
            m.box("io_blue", -2, 2, y1, y1 + 2, 0, 3)


def plastic_fountain(m):
    m.box("io_purple", -6, 6, -6, 6, 0, 1.0)
    m.box("io_blue", -5.3, 5.3, -5.3, 5.3, 1.0, 1.05)
    cols = ("io_red", "io_yellow", "io_green", "io_blue", "io_pink")
    tank(m, "io_white", 0, 0, 1.0, 3, 1.2, sides=10)
    z = 3
    for k in range(5):
        r = 0.9 - 0.12 * k
        tank(m, cols[k], 0, 0, z, z + 2.0, r, sides=10)
        z += 2.0
    sphere(m, "io_yellow", 0, 0, z + 0.6, 1.6, seg=10, rings=6)
    for k, (dx, dy) in enumerate(((1, 0), (0, 1), (-1, 0), (0, -1))):
        rod(m, cols[k], (dx * 1.5, dy * 1.5, z), (dx * 4.2, dy * 4.2, 1.1), 0.35, 6)


def fizzy_drinks(m, gfx):
    """2x2 fizzy drink factory: 156 a yard with crates of bottles, 157 a hall in the industry's colour, 158 a giant tap
    pouring into a glass, 159 a giant can in the industry's colour."""
    if gfx == 156:
        pad(m, "concrete", -7, 8, -7, 8)
        for (x, y) in ((-3, -3), (-3, 2), (2, -3)):
            m.box("io_red", x - 1.6, x + 1.6, y - 1.6, y + 1.6, 0, 1.3)
            for bx in (-0.8, 0.8):
                for by in (-0.8, 0.8):
                    tank(m, "io_green", x + bx, y + by, 1.3, 2.4, 0.3, sides=6)
        bottle(m, 3, 4, 0, 1.2, "io_green")
    elif gfx == 157:
        x0, x1, y0, y1 = -7, 8, -8, 6
        m.box("company", x0, x1, y0, y1, 0, 7)
        m.box("io_white", x0, x1, y0, y1, 7, 7.5)
        wins(m, x0, x1, y0, y1, 1, 6.5, 2, 3, "xY", size=(1.8, 1.6), material="io_blue")
        bottle(m, -1, -2, 7.5, 1.6, "io_green")
    elif gfx == 158:
        pad(m, "concrete", -8, 7, -7, 8)
        m.box("metal", -6, -3, -2, 2, 0, 1.0)
        tank(m, "metal", -4.5, 0, 1.0, 14, 1.0, sides=10)
        rod(m, "metal", (-4.5, 0, 12), (1.5, 0, 12), 0.9, 10)
        rod(m, "metal", (1.5, 0, 12.5), (1.5, 0, 9.5), 0.7, 10)
        m.box("metal", 0.9, 2.1, -1.8, 1.8, 13.2, 13.6)
        tank(m, "io_bubble", 1.5, 0, 0, 5.5, 2.4, sides=14, top="io_cola")
        tank(m, "io_cola", 1.5, 0, 5.5, 9.5, 0.4, sides=8)
    elif gfx == 159:
        pad(m, "concrete", -8, 7, -8, 7)
        tank(m, "company", -0.5, -0.5, 0.6, 12.5, 5.5, sides=20)
        cone(m, "metal", -0.5, -0.5, 0, 0.6, 5.0, 5.5, sides=20)
        cone(m, "metal", -0.5, -0.5, 12.5, 13.3, 5.5, 4.8, sides=20, top="metal")
        tank(m, "io_white", -0.5, -0.5, 5, 7, 5.55, sides=20)
        m.box("dark", 1.5, 3, -1.0, 0.0, 13.3, 13.4)


def bottle(m, x, y, z, r, material):
    tank(m, material, x, y, z, z + 3.6 * r, r, sides=12)
    cone(m, material, x, y, z + 3.6 * r, z + 4.6 * r, r, 0.4 * r, sides=12)
    tank(m, material, x, y, z + 4.6 * r, z + 5.6 * r, 0.4 * r, sides=10)
    tank(m, "io_red", x, y, z + 5.6 * r, z + 5.9 * r, 0.45 * r, sides=10)
    tank(m, "io_white", x, y, z + 1.4 * r, z + 2.4 * r, r * 1.02, sides=12)


def bubble_generator(m, gfx):
    """Bubble generator: blue tubes with rings on top in a row along x (160 the tubes, 161 the brown funnel that
    blows the bubbles, 162 the catcher), 163 the pipe yard beside them."""
    pad(m, "concrete")
    if gfx == 163:
        for y in (-3, 1):
            rod(m, "company", (-8, y, 1.0), (8, y, 1.0), 0.6, 8, caps=False)
            for x in (-5, 0, 5):
                m.box("metal", x - 0.3, x + 0.3, y - 0.3, y + 0.3, 0, 0.6)
    elif gfx in (160, 162):
        spots = ((-3, -2, 12), (2, 2, 15)) if gfx == 160 else ((-3, 2, 14), (2, -2, 11), (3, 4, 9))
        for (x, y, h) in spots:
            for a in range(6):
                ang = 2 * math.pi * a / 6
                rod(m, "metal", (x + 1.9 * math.cos(ang), y + 1.9 * math.sin(ang), 0), (x + 1.4 * math.cos(ang), y + 1.4 * math.sin(ang), 2), 0.3, 4)
            tank(m, "company", x, y, 2, h, 1.4, sides=12, top="dark")
            tank(m, "io_white", x, y, h - 1, h - 0.6, 1.45, sides=12)
            rod(m, "metal", (x + 1.6, y, 0), (x + 1.6, y, h + 2), 0.12, 4)
            ring = [(x + 1.6 * math.cos(2 * math.pi * k / 10), y + 1.6 * math.sin(2 * math.pi * k / 10)) for k in range(10)]
            for k in range(10):
                (ax, ay), (bx, by) = ring[k], ring[(k + 1) % 10]
                rod(m, "metal", (ax, ay, h + 2), (bx, by, h + 2), 0.15, 4, caps=False)
    elif gfx == 161:
        for a in range(6):
            ang = 2 * math.pi * a / 6
            rod(m, "metal", (2.2 * math.cos(ang), 2.2 * math.sin(ang), 0), (1.6 * math.cos(ang), 1.6 * math.sin(ang), 2), 0.3, 4)
        tank(m, "io_bubble", 0, 0, 2, 9, 1.6, sides=14, top="metal")
        tank(m, "metal", 0, 0, 9, 10, 1.3, sides=12)
        cone(m, "io_cola", 0, 0, 10, 17, 0.8, 3.0, sides=14, top="dark")
        rnd = random.Random(161)
        for k in range(5):
            sphere(m, "io_bubble", rnd.uniform(-3, 3), rnd.uniform(-3, 3), 18.5 + k * 1.6, 0.6 + 0.2 * (k % 3), seg=8, rings=6)


def toffee_quarry(m, gfx):
    """Toffee quarry, three tiles along x: 164 slabs of toffee, 165 the digger in the pit, 166 the conveyor and shed."""
    if gfx == 164:
        m.box("io_toffee_dark", -8, 8, -8, 8, 0, 0.3)
        for (x, y, n) in ((-4, -4, 3), (2, -4, 2), (-4, 3, 2), (3, 3, 1)):
            for j in range(n):
                m.box("io_toffee", x - 2, x + 2, y - 2.5, y + 2.5, 0.3 + j * 1.3, 0.3 + j * 1.3 + 1.2)
                m.box("io_white", x - 2.05, x + 2.05, y - 0.3, y + 0.3, 0.3 + j * 1.3 + 0.2, 0.3 + j * 1.3 + 1.0)
    elif gfx == 165:
        for (r0, h) in ((8, 0.9), (6, 1.8)):
            pass
        m.box("io_toffee", -8, 8, -8, -5, 0, 2.6)
        m.box("io_toffee", -8, 8, 5, 8, 0, 2.6)
        m.box("io_toffee", -8, -5, -5, 5, 0, 2.6)
        m.box("io_toffee", -5, 8, -5, -3, 0, 1.3)
        m.box("io_toffee", -5, 8, 3, 5, 0, 1.3)
        m.box("io_toffee_dark", -5, 8, -3, 3, 0, 0.1)
        # Digger.
        m.box("io_yellow", 0, 4, -1.6, 1.6, 0.5, 2.5)
        m.box("io_battery", 0, 4, -1.8, 1.8, 0.1, 0.5)
        m.box("glass", 2.4, 4.05, -1.4, 0.2, 1.8, 2.4)
        rod(m, "io_yellow", (2, 0, 2.2), (-2, 0, 5.5), 0.3, 4)
        rod(m, "io_yellow", (-2, 0, 5.5), (-3.5, 0, 2.5), 0.25, 4)
        m.box("dark", -4.3, -3, -0.8, 0.8, 1.8, 2.8)
    elif gfx == 166:
        pad(m, "io_toffee_dark")
        m.box("io_pink", -2, 6, -6, 2, 0, 5)
        roof_y(m, "io_red", "io_pink", -2.2, 6.2, -6.2, 2.2, 5, 7)
        rod(m, "metal", (-8, 4, 1.5), (-2, 4, 4), 0.5, 4)
        m.box("metal", -2, 1, 2, 6, 0, 4)
        mound(m, "io_toffee", 4, 5.5, 2.5, 2.2, 2)


def sugar_mine(m, gfx):
    """Sugar mine, 4x2: heaps of sugar on the 2x2 at the back (167-170), a track yard (171), the hall (172), shaft (173) and sieve (174)."""
    corner = {167: (8, 8), 168: (8, -8), 169: (-8, 8), 170: (-8, -8)}
    if gfx in corner:
        cx, cy = corner[gfx]
        m.box("company", -8, 8, -8, 8, 0, 0.15)
        # A quarter of one big heap around the corner the four tiles share.
        mound(m, "io_sugar", cx, cy, 12, 12, 7, seg=24, rings=4)
        rnd = random.Random(gfx)
        mound(m, "io_sugar", rnd.uniform(-3, 0) * (cx / 8), rnd.uniform(-3, 0) * (cy / 8), 3, 3, 2.2)
    elif gfx == 171:
        pad(m, "concrete")
        rails(m, -8, 8, -3)
        rails(m, -8, 8, 3)
        ore_cart(m, -2, -3, "io_sugar")
        ore_cart(m, 3, 3, "io_sugar")
    elif gfx == 172:
        m.box("company", -7, 7, -6, 7, 0, 7)
        roof_y(m, "io_blue", "company_dark", -7.2, 7.2, -6.2, 7.2, 7, 10)
        wins(m, -7, 7, -6, 7, 1, 6.5, 1, 3, "xXY", size=(1.8, 2.0))
        m.box("door", 7, 7.1, -1.5, 1.5, 0, 4)
    elif gfx == 173:  # shaft tower
        m.box("concrete", -6, 6, -6, 6, 0, 1)
        lattice_tower(m, "io_red", 0, 0, 4, 1, 15, levels=4)
        m.cylinder("io_yellow", -0.25, 0.25, 0, 15.2, 2.0, sides=12, caps="dark")
        m.box("io_red", -2.6, 2.6, -2.6, 2.6, 15, 15.4)
    elif gfx == 174:  # sieve: a hopper on legs over a pile
        m.box("concrete", -6, 6, -6, 6, 0, 0.5)
        for (x, y) in ((-3.5, -3.5), (-3.5, 3.5), (3.5, -3.5), (3.5, 3.5)):
            m.box("metal", x - 0.3, x + 0.3, y - 0.3, y + 0.3, 0.5, 8)
        m.box("company", -4.5, 4.5, -4.5, 4.5, 8, 11)
        m.box("metal", -4.6, 4.6, -4.6, 4.6, 11, 11.3)
        mound(m, "io_sugar", 0, 0, 3, 3, 2.2)
        rod(m, "metal", (-4.5, 0, 10), (-8, 0, 3), 0.45, 4)


# ---------------------------------------------------------------------------------------------------------------
# The tiles, the layouts (for previews) and the index


def at(fn, *args):
    return lambda m: fn(m, *args)


# (name, gfx ids, drawing function)
TILES = [
    ("printing_works_back", [43], at(printing_works, 0, 0, 43)),
    ("printing_works_right", [44], at(printing_works, 0, 1, 44)),
    ("printing_works_entrance", [45], at(printing_works, 1, 0, 45)),
    ("printing_works_front", [46], at(printing_works, 1, 1, 46)),
    ("copper_mine_tower", [47, 48], at(copper_mine, 47)),
    ("copper_mine_smelter", [49], at(copper_mine, 49)),
    ("copper_mine_office", [50], at(copper_mine, 50)),
    ("copper_mine_ore", [51], at(copper_mine, 51)),
    ("food_plant_hall", [60], at(food_plant, 60)),
    ("food_plant_silos", [61], at(food_plant, 61)),
    ("food_plant_boiler", [62], at(food_plant, 62)),
    ("food_plant_loading", [63], at(food_plant, 63)),
    ("paper_mill_main", [64], at(paper_mill, 64)),
    ("paper_mill_hall", [65], at(paper_mill, 65)),
    ("paper_mill_tanks", [66], at(paper_mill, 66)),
    ("paper_mill_logs", [67], at(paper_mill, 67)),
    ("paper_mill_boiler", [68], at(paper_mill, 68)),
    ("paper_mill_conveyor", [69], at(paper_mill, 69)),
    ("paper_mill_office", [70], at(paper_mill, 70)),
    ("paper_mill_rolls", [71], at(paper_mill, 71)),
    ("gold_mine_mill", [72], at(gold_mine, 72)),
    ("gold_mine_track", [73], at(gold_mine, 73)),
    ("gold_mine_chimney", [74], at(gold_mine, 74)),
    ("gold_mine_winding", [75], at(gold_mine, 75)),
    ("gold_mine_heap_a", [76], at(gold_mine, 76)),
    ("gold_mine_carts_a", [77], at(gold_mine, 77)),
    ("gold_mine_shed_a", [78], at(gold_mine, 78)),
    ("gold_mine_tower", [79, 88], at(gold_mine, 79)),
    ("gold_mine_shed_b", [80], at(gold_mine, 80)),
    ("gold_mine_carts_b", [81], at(gold_mine, 81)),
    ("gold_mine_heap_b", [82], at(gold_mine, 82)),
    ("gold_mine_pond_a", [83, 86], at(gold_mine, 83)),
    ("gold_mine_pond_b", [84], at(gold_mine, 84)),
    ("gold_mine_heap_c", [85], at(gold_mine, 85)),
    ("gold_mine_shed_c", [87], at(gold_mine, 87)),
    ("bank_back", [89], at(bank2, 89)),
    ("bank_front", [90], at(bank2, 90)),
    ("diamond_mine_plant", [91], at(diamond_mine, 91)),
    ("diamond_mine_sorting", [92], at(diamond_mine, 92)),
    ("diamond_mine_office", [93], at(diamond_mine, 93)),
    ("diamond_mine_crusher", [94], at(diamond_mine, 94)),
    ("diamond_mine_pit_back", [95], at(diamond_mine, 95)),
    ("diamond_mine_pit_left", [96], at(diamond_mine, 96)),
    ("diamond_mine_workshop", [97], at(diamond_mine, 97)),
    ("diamond_mine_pit_right", [98], at(diamond_mine, 98)),
    ("diamond_mine_pit_front", [99], at(diamond_mine, 99)),
    ("fruit_plantation", [116], lambda m: plantation(m, False)),
    ("rubber_plantation", [117], lambda m: plantation(m, True)),
    ("water_supply_pumphouse", [118], at(water_supply, 118)),
    ("water_supply_tank", [119], at(water_supply, 119)),
    ("water_tower", [120], water_tower),
    ("factory_back", [121], at(factory2, 121)),
    ("factory_chimneys", [122], at(factory2, 122)),
    ("factory_doors", [123], at(factory2, 123)),
    ("factory_yard", [124], at(factory2, 124)),
    ("lumber_mill_saw", [125], at(lumber_mill, 125)),
    ("lumber_mill_logs", [126], at(lumber_mill, 126)),
    ("lumber_mill_building", [127], at(lumber_mill, 127)),
    ("lumber_mill_timber", [128], at(lumber_mill, 128)),
    ("candyfloss_forest", [129], lambda m: candyfloss(m, False)),
    ("candyfloss_forest_harvested", [130], lambda m: candyfloss(m, True)),
    ("sweet_factory_yard", [131], at(sweet_factory, 131)),
    ("sweet_factory_chimney", [132], at(sweet_factory, 132)),
    ("sweet_factory_dome", [133], at(sweet_factory, 133)),
    ("sweet_factory_front", [134], at(sweet_factory, 134)),
    ("battery_farm", [135], lambda m: battery_farm(m, False)),
    ("battery_farm_reaped", [136], lambda m: battery_farm(m, True)),
    ("cola_well", [137], cola_well),
    ("toy_shop_yard", [138], at(toy_shop, 138)),
    ("toy_shop_tower", [139], at(toy_shop, 139)),
    ("toy_shop_front", [140], at(toy_shop, 140)),
    ("toy_shop_corner", [141], at(toy_shop, 141)),
    ("toy_factory_hall_back", [142], at(toy_factory, 142)),
    ("toy_factory_press", [143], at(toy_factory, 143)),
    ("toy_factory_hall", [144], at(toy_factory, 144)),
    ("toy_factory_hall_front", [145], at(toy_factory, 145)),
    ("toy_factory_office", [146], at(toy_factory, 146)),
    ("toy_factory_yard", [147], at(toy_factory, 147)),
    ("plastic_fountain", list(range(148, 156)), plastic_fountain),
    ("fizzy_drinks_yard", [156], at(fizzy_drinks, 156)),
    ("fizzy_drinks_bottle", [157], at(fizzy_drinks, 157)),
    ("fizzy_drinks_bottle_red", [158], at(fizzy_drinks, 158)),
    ("fizzy_drinks_front", [159], at(fizzy_drinks, 159)),
    ("bubble_generator_tank", [160], at(bubble_generator, 160)),
    ("bubble_generator_blower", [161], at(bubble_generator, 161)),
    ("bubble_generator_catcher", [162], at(bubble_generator, 162)),
    ("bubble_generator_pipes", [163], at(bubble_generator, 163)),
    ("toffee_quarry_slabs", [164], at(toffee_quarry, 164)),
    ("toffee_quarry_pit", [165], at(toffee_quarry, 165)),
    ("toffee_quarry_shed", [166], at(toffee_quarry, 166)),
    ("sugar_mine_heap_back", [167], at(sugar_mine, 167)),
    ("sugar_mine_heap_left", [168], at(sugar_mine, 168)),
    ("sugar_mine_heap_right", [169], at(sugar_mine, 169)),
    ("sugar_mine_heap_front", [170], at(sugar_mine, 170)),
    ("sugar_mine_track", [171], at(sugar_mine, 171)),
    ("sugar_mine_hall", [172], at(sugar_mine, 172)),
    ("sugar_mine_shaft", [173], at(sugar_mine, 173)),
    ("sugar_mine_sieve", [174], at(sugar_mine, 174)),
]

# One layout of each industry, (x, y, gfx), as in build_industry.h; only used to draw previews of whole industries.
LAYOUTS = {
    "printing_works": [(0, 0, 43), (0, 1, 44), (1, 0, 45), (1, 1, 46), (0, 2, 43), (0, 3, 44), (1, 2, 45), (1, 3, 46),
                       (2, 1, 43), (2, 2, 44), (3, 1, 45), (3, 2, 46)],
    "copper_mine": [(0, 0, 47), (0, 1, 49), (0, 2, 51), (1, 0, 47), (1, 1, 49), (1, 2, 50), (2, 0, 51), (2, 1, 51)],
    "food_plant": [(0, 0, 60), (1, 0, 60), (2, 0, 60), (0, 1, 60), (1, 1, 60), (2, 1, 60), (0, 2, 61), (1, 2, 61),
                   (2, 2, 63), (0, 3, 62), (1, 3, 62), (2, 3, 63)],
    "paper_mill": [(0, 0, 64), (1, 0, 65), (2, 0, 66), (3, 0, 67), (0, 1, 68), (1, 1, 69), (2, 1, 67), (3, 1, 67),
                   (0, 2, 66), (1, 2, 71), (2, 2, 71), (3, 2, 70)],
    "gold_mine": [(x, y, 72 + 4 * x + y) for x in range(4) for y in range(4)],
    "bank": [(0, 0, 89), (1, 0, 90)],
    "diamond_mine": [(x, y, 91 + 3 * x + y) for x in range(3) for y in range(3)],
    "plantations": [(0, 0, 116), (1, 0, 116), (0, 1, 116), (1, 1, 116), (0, 2, 117), (1, 2, 117), (0, 3, 117), (1, 3, 117)],
    "water": [(0, 0, 118), (0, 1, 119), (1, 0, 118), (1, 1, 119), (2, 3, 120)],
    "factory": [(0, 0, 121), (0, 1, 122), (1, 0, 123), (1, 1, 124), (0, 2, 121), (0, 3, 122), (1, 2, 123), (1, 3, 124)],
    "lumber_mill": [(0, 0, 125), (0, 1, 126), (1, 0, 127), (1, 1, 128)],
    "candyfloss_batteries_cola": [(0, 0, 129), (0, 1, 129), (1, 0, 130), (1, 1, 129), (2, 0, 135), (2, 1, 136),
                                  (3, 0, 135), (3, 1, 135), (0, 3, 137), (1, 3, 137), (2, 3, 137)],
    "sweet_factory": [(0, 0, 131), (0, 1, 132), (1, 0, 133), (1, 1, 134), (0, 2, 131), (0, 3, 132), (1, 2, 133), (1, 3, 134),
                      (2, 1, 131), (2, 2, 132), (3, 1, 133), (3, 2, 134)],
    "toy_shop": [(0, 0, 138), (0, 1, 139), (1, 0, 140), (1, 1, 141)],
    "toy_factory": [(0, 0, 147), (0, 1, 142), (1, 0, 147), (1, 1, 143), (2, 0, 147), (2, 1, 144), (3, 0, 146), (3, 1, 145)],
    "plastic_fountains": [(0, 0, 148), (1, 0, 151), (2, 0, 154)],
    "fizzy_drinks": [(0, 0, 156), (0, 1, 157), (1, 0, 158), (1, 1, 159)],
    "bubble_generator": [(0, 0, 163), (0, 1, 160), (1, 0, 163), (1, 1, 161), (2, 0, 163), (2, 1, 162),
                         (0, 2, 163), (0, 3, 160), (1, 2, 163), (1, 3, 161), (2, 2, 163), (2, 3, 162)],
    "toffee_quarry": [(0, 0, 164), (1, 0, 165), (2, 0, 166)],
    "sugar_mine": [(0, 0, 167), (0, 1, 168), (1, 0, 169), (1, 1, 170), (2, 0, 171), (2, 1, 172), (3, 0, 173), (3, 1, 174)],
}


def filename(name):
    return f"{GROUP}_{name}.glb"


def build():
    buildings = []
    for name, ids, fn in TILES:
        m = Model()
        fn(m)
        m.save(filename(name))
        buildings.append({"type": "industry_tile", "ids": ids, "model": filename(name)})
    return {"vehicles": [], "buildings": buildings}


def build_layouts(folder):
    """Writes one model per industry with all its tiles in place, to look at the industry as a whole."""
    by_gfx = {g: fn for _, ids, fn in TILES for g in ids}
    paths = []
    for name, layout in LAYOUTS.items():
        base = Model()
        nx = max(x for x, _, _ in layout) + 1
        ny = max(y for _, y, _ in layout) + 1
        for x, y, g in layout:
            by_gfx[g](Shifted(base, 16 * x - 8 * (nx - 1), 16 * y - 8 * (ny - 1)))
        path = f"{folder}/{GROUP}_layout_{name}.glb"
        base.save(path)
        paths.append(path)
    return paths
