"""Houses of the temperate and sub-arctic climates that the first models do not cover yet.

Special buildings (hotel, theatre, cinema, stadiums, shopping centre, statue, fountain, parks, warehouse) and
the houses, shops, offices and church of sub-arctic towns. Sub-arctic houses come in two models, one for the
house below the snow line and one with snow on its roofs and ground for the house above it.
"""

import math

from gfx3d import MATERIALS, Model as BaseModel

P = "houses_north_"

MATERIALS.update({
    P + "snow": (0.93, 0.95, 0.98),
    P + "snow_ground": (0.86, 0.89, 0.93),
    P + "water": (0.24, 0.42, 0.62),
    P + "pitch": (0.32, 0.56, 0.24),
    P + "line": (0.95, 0.95, 0.95),
    P + "seats": (0.56, 0.52, 0.58),
    P + "crowd": (0.66, 0.46, 0.40),
    P + "foliage": (0.22, 0.42, 0.16),
    P + "foliage_light": (0.36, 0.56, 0.22),
    P + "conifer": (0.16, 0.32, 0.18),
    P + "trunk": (0.38, 0.27, 0.17),
    P + "flowers": (0.86, 0.36, 0.40),
    P + "path": (0.70, 0.66, 0.56),
    P + "paving": (0.62, 0.62, 0.60),
    P + "white": (0.93, 0.92, 0.88),
    P + "red_brick": (0.66, 0.28, 0.20),
    P + "yellow_brick": (0.84, 0.70, 0.46),
    P + "beige": (0.82, 0.72, 0.54),
    P + "orange_roof": (0.72, 0.40, 0.20),
    P + "red_roof": (0.56, 0.20, 0.18),
    P + "brown_roof": (0.46, 0.32, 0.20),
    P + "thatch": (0.66, 0.56, 0.32),
    P + "glass_blue": (0.18, 0.34, 0.66),
    P + "glass_dark": (0.10, 0.16, 0.36),
    P + "glass_roof": (0.52, 0.58, 0.70),
    P + "bronze": (0.50, 0.42, 0.30),
    P + "flag": (0.20, 0.36, 0.80),
})

SNOW = P + "snow"
STOREY = 3.3


class Model(BaseModel):
    """A Model that cuts big quads and triangles into pieces of about CELL units, so that pictures drawn without a depth
    buffer (preview.py) sort the faces right."""

    CELL = 4.0

    def triangle(self, material, a, b, c):
        def dist(p, q):
            return math.sqrt(sum((p[i] - q[i]) ** 2 for i in range(3)))
        if max(dist(a, b), dist(b, c), dist(c, a)) <= self.CELL * 1.5:
            BaseModel.triangle(self, material, a, b, c)
            return

        def mid(p, q):
            return tuple((p[i] + q[i]) / 2 for i in range(3))
        ab, bc, ca = mid(a, b), mid(b, c), mid(c, a)
        for t in ((a, ab, ca), (ab, b, bc), (ca, bc, c), (ab, bc, ca)):
            self.triangle(material, *t)

    def quad(self, material, a, b, c, d):
        def dist(p, q):
            return math.sqrt(sum((p[i] - q[i]) ** 2 for i in range(3)))
        nu = max(1, int(math.ceil(max(dist(a, b), dist(d, c)) / self.CELL - 0.01)))
        nv = max(1, int(math.ceil(max(dist(a, d), dist(b, c)) / self.CELL - 0.01)))
        if nu == 1 and nv == 1:
            BaseModel.quad(self, material, a, b, c, d)
            return

        def at(u, v):
            return tuple((1 - u) * (1 - v) * a[i] + u * (1 - v) * b[i] + u * v * c[i] + (1 - u) * v * d[i] for i in range(3))
        for i in range(nu):
            for j in range(nv):
                u0, u1, v0, v1 = i / nu, (i + 1) / nu, j / nv, (j + 1) / nv
                BaseModel.quad(self, material, at(u0, v0), at(u1, v0), at(u1, v1), at(u0, v1))


class Placed(Model):
    """Draws into another model, turned by quarter turns (counter-clockwise seen from above) and moved."""

    def __init__(self, target, turns=0, dx=0.0, dy=0.0, dz=0.0):
        self.target, self.turns, self.d = target, turns % 4, (dx, dy, dz)

    def _map(self, p):
        x, y, z = p
        for _ in range(self.turns):
            x, y = -y, x
        return (x + self.d[0], y + self.d[1], z + self.d[2])

    def triangle(self, material, a, b, c):
        self.target.triangle(material, self._map(a), self._map(b), self._map(c))

    def smoke_at(self, x, y, z, size=1.0):
        self.target.smoke_at(*self._map((x, y, z)), size)


# ---------------------------------------------------------------- helpers


def ground(m, material, x0=-8, x1=8, y0=-8, y1=8, z=0.05):
    m.box(material, x0, x1, y0, y1, 0, z)


def ground_around(m, material, outer, inner, z=0.05):
    """Ground over the area outer except for the area inner (x0, x1, y0, y1), which something else covers."""
    (X0, X1, Y0, Y1), (x0, x1, y0, y1) = outer, inner
    for a in ((X0, x0, Y0, Y1), (x1, X1, Y0, Y1), (x0, x1, Y0, y0), (x0, x1, y1, Y1)):
        if a[1] > a[0] and a[3] > a[2]:
            m.box(material, a[0], a[1], a[2], a[3], 0, z)


def plot(m, snow, x0=-8, x1=8, y0=-8, y1=8):
    ground(m, P + "snow_ground" if snow else "grass", x0, x1, y0, y1)


def roof_mat(snow, material):
    return SNOW if snow else material


def hip_roof(m, material, x0, x1, y0, y1, z0, z1):
    """A hipped roof; the ridge runs along the longer side."""
    if y1 - y0 > x1 - x0:
        # Turn a roof with its ridge along x by a quarter turn about the middle of the box.
        xm, ym = (x0 + x1) / 2, (y0 + y1) / 2
        hx, hy = (x1 - x0) / 2, (y1 - y0) / 2
        hip_roof(Placed(m, 1, xm, ym), material, -hy, hy, -hx, hx, z0, z1)
        return
    ym = (y0 + y1) / 2
    i = min((y1 - y0) / 2, (x1 - x0) / 2)
    m.quad(material, (x1, y1, z0), (x0, y1, z0), (x0 + i, ym, z1), (x1 - i, ym, z1))
    m.quad(material, (x0, y0, z0), (x1, y0, z0), (x1 - i, ym, z1), (x0 + i, ym, z1))
    m.triangle(material, (x1, y0, z0), (x1, y1, z0), (x1 - i, ym, z1))
    m.triangle(material, (x0, y1, z0), (x0, y0, z0), (x0 + i, ym, z1))


def gable_y(m, material, gable, x0, x1, y0, y1, z0, z1):
    """A pitched roof with its ridge along y."""
    xm, ym = (x0 + x1) / 2, (y0 + y1) / 2
    Placed(m, 1, xm, ym).prism_roof(material, gable, -(y1 - ym), y1 - ym, -(x1 - xm), x1 - xm, z0, z1)


def wins(m, material, x0, x1, y0, y1, z0, z1, rows, nx, ny, w=1.2, h=1.4, sides="xXyY", d=0.06):
    """Windows as flat panes just in front of the walls of a box: nx along the x walls' faces (on the y sides), ny on the x sides."""
    for r in range(rows):
        zc = z0 + (r + 0.5) * (z1 - z0) / rows
        za, zb = zc - h / 2, zc + h / 2
        for i in range(ny):
            yc = y0 + (i + 0.5) * (y1 - y0) / ny
            ya, yb = yc - w / 2, yc + w / 2
            if "X" in sides:
                x = x1 + d
                m.quad(material, (x, ya, za), (x, yb, za), (x, yb, zb), (x, ya, zb))
            if "x" in sides:
                x = x0 - d
                m.quad(material, (x, yb, za), (x, ya, za), (x, ya, zb), (x, yb, zb))
        for i in range(nx):
            xc = x0 + (i + 0.5) * (x1 - x0) / nx
            xa, xb = xc - w / 2, xc + w / 2
            if "Y" in sides:
                y = y1 + d
                m.quad(material, (xb, y, za), (xa, y, za), (xa, y, zb), (xb, y, zb))
            if "y" in sides:
                y = y0 - d
                m.quad(material, (xa, y, za), (xb, y, za), (xb, y, zb), (xa, y, zb))


def ucyl(m, material, x, y, z0, z1, r, sides=12, top=None, bottom=False):
    """An upright closed cylinder."""
    top = top or material
    ring = [(x + r * math.cos(2 * math.pi * i / sides), y + r * math.sin(2 * math.pi * i / sides)) for i in range(sides)]
    for i in range(sides):
        (ax, ay), (bx, by) = ring[i], ring[(i + 1) % sides]
        m.quad(material, (ax, ay, z0), (bx, by, z0), (bx, by, z1), (ax, ay, z1))
        m.triangle(top, (x, y, z1), (ax, ay, z1), (bx, by, z1))
        if bottom:
            m.triangle(material, (x, y, z0), (bx, by, z0), (ax, ay, z0))


def blob(m, material, x, y, z, r, h=None, sides=7):
    """A rounded lump (a tree crown or bush): two rings between a bottom and a top point."""
    h = h or r
    rings = [(z - 0.45 * h, 0.75), (z + 0.35 * h, 0.85)]
    pts = [[(x + r * f * math.cos(2 * math.pi * (i + k * 0.5) / sides), y + r * f * math.sin(2 * math.pi * (i + k * 0.5) / sides), zz) for i in range(sides)] for k, (zz, f) in enumerate(rings)]
    bottom, top = (x, y, z - h), (x, y, z + h)
    lo, hi = pts
    for i in range(sides):
        j = (i + 1) % sides
        m.triangle(material, bottom, lo[j], lo[i])
        m.triangle(material, lo[i], lo[j], hi[i])
        m.triangle(material, lo[j], hi[j], hi[i])
        m.triangle(material, hi[i], hi[j], top)


def tree(m, x, y, h=7.0, r=2.2, kind="leaf"):
    m.box(P + "trunk", x - 0.25, x + 0.25, y - 0.25, y + 0.25, 0, h * 0.5)
    if kind == "leaf":
        blob(m, P + "foliage", x, y, h - r * 0.9, r, r * 0.95)
    else:
        m.pyramid(P + "conifer", x - r, x + r, y - r, y + r, h * 0.25, h * 0.75)
        m.pyramid(P + "conifer", x - r * 0.7, x + r * 0.7, y - r * 0.7, y + r * 0.7, h * 0.55, h)


def snow_tree(m, x, y, h=7.0, r=2.0):
    m.box(P + "trunk", x - 0.25, x + 0.25, y - 0.25, y + 0.25, 0, h * 0.3)
    m.pyramid(P + "conifer", x - r, x + r, y - r, y + r, h * 0.25, h * 0.75)
    m.pyramid(SNOW, x - r * 0.7, x + r * 0.7, y - r * 0.7, y + r * 0.7, h * 0.55, h)


def fence(m, material, x0, x1, y0, y1, h=0.9, t=0.15, sides="xXyY"):
    if "X" in sides:
        m.box(material, x1 - t, x1, y0, y1, 0, h)
    if "x" in sides:
        m.box(material, x0, x0 + t, y0, y1, 0, h)
    if "Y" in sides:
        m.box(material, x0, x1, y1 - t, y1, 0, h)
    if "y" in sides:
        m.box(material, x0, x1, y0, y0 + t, 0, h)


def flat_roof(m, x0, x1, y0, y1, z, snow, material="concrete", rim=0.3, t=0.5):
    """A flat roof with a raised edge; snow lies on it above the snow line."""
    m.box(material, x0 - rim, x1 + rim, y0 - rim, y1 + rim, z, z + t)
    if snow:
        m.box(SNOW, x0, x1, y0, y1, z + t, z + t + 0.15)


def door(m, x, y, w=1.2, h=2.2, material="door"):
    """A door on a wall facing +x at x."""
    m.box(material, x, x + 0.1, y - w / 2, y + w / 2, 0.2, h)


# ---------------------------------------------------------------- temperate special buildings


def hotel():
    """Hotel (1 x 2 tiles along y): a red brick block of four storeys with white bands, a wing round a courtyard
    with a pool, a penthouse and flags at the entrance."""
    m = Model()
    ground(m, P + "paving", -8, 8, -16, 16)
    H = 4 * STOREY
    # Main block on the northern tile, wing along the back and the far side of the southern tile.
    blocks = [(-6.5, 6.5, -14.5, 1.5), (-6.5, -1.0, 1.5, 14.5), (-1.0, 6.5, 8.5, 14.5)]
    for x0, x1, y0, y1 in blocks:
        m.box(P + "red_brick", x0, x1, y0, y1, 0, H)
        for k in range(1, 4):
            m.box(P + "white", x0 - 0.08, x1 + 0.08, y0 - 0.08, y1 + 0.08, k * STOREY - 0.2, k * STOREY + 0.1)
        m.box(P + "white", x0 - 0.25, x1 + 0.25, y0 - 0.25, y1 + 0.25, H, H + 0.5)
    wins(m, "glass", -6.5, 6.5, -14.5, 1.5, 0.3, H, 4, 4, 6, w=1.3, h=1.5, sides="xXy")
    wins(m, "glass", -6.5, 6.5, -14.5, 1.5, STOREY, H, 3, 4, 6, w=1.3, h=1.5, sides="Y")
    wins(m, "glass", -6.5, -1.0, 1.5, 14.5, 0.3, H, 4, 2, 5, w=1.3, h=1.5, sides="xX")
    wins(m, "glass", -1.0, 6.5, 8.5, 14.5, 0.3, H, 4, 3, 2, w=1.3, h=1.5, sides="XyY")
    wins(m, "glass", -6.5, -1.0, 1.5, 14.5, 0.3, H, 4, 2, 2, w=1.3, h=1.5, sides="Y")
    # Penthouse and roof housing.
    m.box(P + "red_brick", -4, 2, -11, -4, H + 0.5, H + 3.3)
    m.box(P + "white", -4.2, 2.2, -11.2, -3.8, H + 3.3, H + 3.7)
    wins(m, "glass", -4, 2, -11, -4, H + 0.5, H + 3.3, 1, 3, 3, w=1.1, h=1.3, sides="XY")
    m.box("metal", -5, -2, 3, 7, H + 0.5, H + 1.8)
    # Courtyard with a pool.
    m.box(P + "white", 0.0, 6.0, 2.5, 7.5, 0, 0.25)
    m.box(P + "water", 0.6, 5.4, 3.1, 6.9, 0.25, 0.3)
    # Entrance with a canopy and flags.
    m.box("glass", 6.5, 6.6, -8.5, -5.5, 0.2, 2.6)
    m.box(P + "white", 6.5, 9.0, -9.5, -4.5, 2.7, 3.0)
    for y in (-13.5, -12, -2.5, -1):
        m.box("metal", 7.4, 7.6, y - 0.1, y + 0.1, 0, 7.5)
        m.box(P + "flag", 7.45, 7.55, y + 0.1, y + 1.3, 6.2, 7.3)
    m.save(P + "hotel.glb")


def statue():
    """A statue on a stone plinth in a small paved square with hedges."""
    m = Model()
    ground(m, "grass")
    m.box(P + "paving", -5, 5, -5, 5, 0, 0.15)
    m.box("stone", -1.6, 1.6, -1.6, 1.6, 0.15, 0.9)
    m.box("stone", -1.1, 1.1, -1.1, 1.1, 0.9, 3.6)
    m.box("stone", -1.4, 1.4, -1.4, 1.4, 3.6, 4.0)
    b = P + "bronze"
    m.box(b, -0.35, 0.35, -0.55, -0.1, 4.0, 5.4)   # legs
    m.box(b, -0.35, 0.35, 0.1, 0.55, 4.0, 5.4)
    m.box(b, -0.45, 0.45, -0.7, 0.7, 5.4, 7.2)     # body
    m.box(b, -0.25, 0.25, 0.7, 1.0, 5.6, 7.1)      # arm
    m.box(b, 0.0, 0.3, -1.6, -0.7, 6.8, 7.1)       # raised arm
    m.box(b, -0.2, 0.0, -1.8, -1.5, 6.8, 8.6)
    m.box(b, -0.3, 0.3, -0.3, 0.3, 7.2, 8.0)       # head
    for x0, x1, y0, y1 in ((-7, -5.5, -7, 7), (5.5, 7, -7, -1.2), (5.5, 7, 1.2, 7), (-5.5, 5.5, -7, -5.5), (-5.5, 5.5, 5.5, 7)):
        m.box(P + "foliage", x0, x1, y0, y1, 0, 1.0)
    m.save(P + "statue.glb")


def fountain():
    """A round fountain with a basin, a middle bowl and a jet of water, on a paved square."""
    m = Model()
    ground(m, "grass")
    m.box(P + "paving", -6.5, 6.5, -6.5, 6.5, 0, 0.15)
    ucyl(m, "stone", 0, 0, 0.15, 1.0, 4.6, sides=16)
    ucyl(m, P + "water", 0, 0, 0.15, 0.85, 4.1, sides=16)
    ucyl(m, "stone", 0, 0, 0.85, 2.6, 0.5, sides=8)
    ucyl(m, "stone", 0, 0, 2.6, 3.0, 1.6, sides=12, top=P + "water")
    ucyl(m, P + "line", 0, 0, 3.0, 5.2, 0.25, sides=6)
    for i in range(4):
        a = math.pi / 4 + i * math.pi / 2
        x, y = 6.0 * math.cos(a), 6.0 * math.sin(a)
        blob(m, P + "foliage", x, y, 1.0, 1.0, 1.0, sides=6)
    m.save(P + "fountain.glb")


def park_pond():
    """A park with a pond, a path and trees."""
    m = Model()
    ground(m, P + "foliage_light", z=0.08)
    ucyl(m, P + "water", 2.0, 1.5, 0.0, 0.14, 4.0, sides=14)
    m.box(P + "path", -8, -4.5, -8, 8, 0, 0.12)
    m.box(P + "path", -4.5, 8, -7.5, -5.5, 0, 0.12)
    tree(m, -6.5, 4.5, 9, 2.4)
    tree(m, 2.0, -3.5, 10, 2.6, "conifer")
    tree(m, -2.5, 6.0, 8, 2.2)
    tree(m, 6.0, 6.0, 7, 1.8)
    blob(m, P + "foliage", -1.5, -1.5, 0.8, 1.2, 0.9, sides=6)
    m.box("wood", 6.0, 6.6, -3.5, -1.5, 0, 0.7)  # bench
    m.save(P + "park_pond.glb")


def park_trees():
    """A park with trees, bushes and a flower bed."""
    m = Model()
    ground(m, P + "foliage_light", z=0.08)
    m.box(P + "path", -1.0, 1.0, -8, 8, 0, 0.12)
    m.box(P + "path", -8, 8, -1.0, 1.0, 0, 0.12)
    ucyl(m, P + "flowers", 0, 0, 0, 0.5, 1.8, sides=10)
    tree(m, -5, -5, 10, 2.6)
    tree(m, 5, -5, 8, 2.2)
    tree(m, -5, 5, 11, 2.4, "conifer")
    tree(m, 5, 5, 9, 2.4)
    for x, y in ((-3, -6.5), (6.5, 2.5), (-6.5, 2.5), (3, 6.5)):
        blob(m, P + "foliage", x, y, 0.8, 1.1, 0.8, sides=6)
    m.save(P + "park_trees.glb")


def warehouse():
    """A brown brick warehouse with two pitched roofs and loading doors."""
    m = Model()
    ground(m, P + "paving")
    H = 6.0
    m.box("wood", -6.5, 6.5, -6.5, 6.5, 0, H)
    m.box("brick", -6.6, 6.6, -6.6, 6.6, 0, 0.6)
    for y0, y1 in ((-6.8, 0), (0, 6.8)):
        m.prism_roof("slate", "wood", -6.8, 6.8, y0, y1, H, H + 3.2)
    for y in (-3.4, 3.4):
        m.box("dark", 6.5, 6.6, y - 1.4, y + 1.4, 0.2, 3.6)
    wins(m, "glass", -6.5, 6.5, -6.5, 6.5, 3.8, 5.6, 1, 5, 4, w=1.2, h=1.0, sides="xXyY")
    wins(m, "dark", -6.5, 6.5, -6.5, 6.5, 0.4, 3.0, 1, 2, 1, w=2.6, h=2.4, sides="Yy")
    m.save(P + "warehouse.glb")


def theatre():
    """A red brick theatre with a stage house at the back, a curved white canopy and lit entrance."""
    m = Model()
    ground(m, P + "paving")
    rb = P + "red_brick"
    m.box(rb, -6.5, 4.5, -6.5, 6.5, 0, 8.0)
    m.box(rb, -6.5, -0.5, -5.5, 5.5, 8.0, 12.0)  # stage house
    m.box("concrete", -6.7, -0.3, -5.7, 5.7, 12.0, 12.4)
    m.box("concrete", -6.7, 4.7, -6.7, 6.7, 8.0, 8.4)
    # Front part, lower, with a curved canopy.
    m.box(rb, 4.5, 6.8, -5.5, 5.5, 0, 5.0)
    m.box("concrete", 4.5, 7.0, -5.7, 5.7, 5.0, 5.4)
    m.box("glass", 6.8, 6.9, -4.0, 4.0, 0.2, 2.6)
    sides = 8
    for i in range(sides):
        a0 = -math.pi / 2 + math.pi * i / sides
        a1 = -math.pi / 2 + math.pi * (i + 1) / sides
        p = [(6.8 + 1.8 * math.cos(a), 5.8 * math.sin(a)) for a in (a0, a1)]
        (ax, ay), (bx, by) = p
        m.quad(P + "white", (ax, ay, 2.8), (bx, by, 2.8), (bx, by, 3.6), (ax, ay, 3.6))
        m.triangle(P + "white", (6.8, 0, 3.6), (ax, ay, 3.6), (bx, by, 3.6))
        m.triangle(P + "white", (6.8, 0, 2.8), (bx, by, 2.8), (ax, ay, 2.8))
        m.quad("light", (ax, ay, 2.65), (bx, by, 2.65), (bx, by, 2.8), (ax, ay, 2.8))
    wins(m, "glass", -6.5, 4.5, -6.5, 6.5, 3.6, 7.6, 1, 4, 4, w=1.0, h=2.2, sides="xyY")
    wins(m, "glass", 4.5, 6.8, -5.5, 5.5, 3.6, 5.0, 1, 1, 4, w=1.2, h=0.9, sides="X")
    wins(m, "glass", -6.5, -0.5, -5.5, 5.5, 9.0, 11.4, 1, 2, 3, w=1.0, h=1.2, sides="X")
    m.save(P + "theatre.glb")


def cinema():
    """A white art deco cinema with stepped walls, a marquee and a tall sign."""
    m = Model()
    ground(m, P + "paving")
    w = P + "white"
    m.box(w, -6.5, 5.0, -6.5, 6.5, 0, 6.5)
    m.box(w, -6.5, 3.5, -5.0, 5.0, 6.5, 9.0)
    m.box("concrete", -6.7, 5.2, -6.7, 6.7, 6.5, 6.8)
    m.box("concrete", -6.7, 3.7, -5.2, 5.2, 9.0, 9.4)
    m.box(w, 5.0, 6.6, -4.0, 4.0, 0, 5.4)  # entrance block
    m.box("glass", 6.6, 6.7, -2.8, 2.8, 0.2, 2.6)
    m.box("company", 6.6, 8.2, -4.5, 4.5, 2.8, 3.8)  # marquee in the house's colour
    m.box("light", 8.2, 8.3, -4.3, 4.3, 3.0, 3.6)
    m.box("dark", 6.6, 7.2, -0.5, 0.5, 4.0, 8.5)  # tall sign
    m.box("light", 7.2, 7.3, -0.35, 0.35, 4.2, 8.3)
    for y in (-5.8, -2.6, 2.6, 5.8):  # vertical ribs
        m.box("concrete", 5.0, 5.3, y - 0.3, y + 0.3, 0, 6.6)
    wins(m, "glass", -6.5, 5.0, -6.5, 6.5, 3.5, 6.0, 1, 4, 3, w=0.9, h=1.8, sides="yY")
    m.save(P + "cinema.glb")


def stand(m, x0, x1, y0, y1, h, roof=True):
    """A seated stand along y facing the pitch at +x: rows of seats rising towards the back wall at x0,
    sloping side walls and a roof over the upper rows."""
    rows = 4
    depth = x1 - x0
    for r in range(rows):
        b = x1 - depth * r / rows
        m.box(P + "crowd" if r % 2 else P + "seats", x0, b, y0, y1, 0, 0.4 + (r + 1) * h / rows)
    rb = P + "red_brick"
    m.box(rb, x0 - 0.5, x0, y0 - 0.5, y1 + 0.5, 0, h + 3.0)
    ya, yb = y0 - 0.5, y1 + 0.5
    m.quad(rb, (x0, ya, 0), (x1, ya, 0), (x1, ya, 0.6), (x0, ya, h + 3.0))
    m.quad(rb, (x1, y0, 0), (x0, y0, 0), (x0, y0, h + 3.0), (x1, y0, 0.6))
    m.quad(rb, (x1, yb, 0), (x0, yb, 0), (x0, yb, h + 3.0), (x1, yb, 0.6))
    m.quad(rb, (x0, y1, 0), (x1, y1, 0), (x1, y1, 0.6), (x0, y1, h + 3.0))
    if roof:
        m.box(P + "white", x0 - 0.5, x0 + depth * 0.6, ya, yb, h + 2.6, h + 3.0)


def pitch_lines(m, x0, x1, y0, y1, along="y", n=0, z=0.2):
    t = 0.15
    m.box(P + "line", x0, x1, y0, y0 + t, 0.15, z)
    m.box(P + "line", x0, x1, y1 - t, y1, 0.15, z)
    m.box(P + "line", x0, x0 + t, y0, y1, 0.15, z)
    m.box(P + "line", x1 - t, x1, y0, y1, 0.15, z)
    for i in range(1, n + 1):
        if along == "y":
            y = y0 + (y1 - y0) * i / (n + 1)
            m.box(P + "line", x0, x1, y - t / 2, y + t / 2, 0.15, z)
        else:
            x = x0 + (x1 - x0) * i / (n + 1)
            m.box(P + "line", x - t / 2, x + t / 2, y0, y1, 0.15, z)


def stadium_football():
    """Stadium (2 x 2 tiles): a football pitch with covered seated stands along the two far sides and low
    brick terraces with entrances along the near sides."""
    m = Model()
    ground_around(m, P + "paving", (-16, 16, -16, 16), (-8.5, 11.5, -8.5, 11.5))
    m.box(P + "pitch", -8.5, 11.5, -8.5, 11.5, 0, 0.15)
    pitch_lines(m, -7.5, 10.5, -7.5, 10.5, "y", 1)
    # Goals at both ends of the pitch (along y).
    for y in (-7.4, 10.4):
        m.box(P + "line", -0.5, -0.3, y - 0.1, y + 0.1, 0, 1.6)
        m.box(P + "line", 3.3, 3.5, y - 0.1, y + 0.1, 0, 1.6)
        m.box(P + "line", -0.5, 3.5, y - 0.1, y + 0.1, 1.4, 1.6)
    # Seated stands on the far (back, -x) and far right (-y) sides.
    stand(m, -15.5, -9.0, -9.0, 12.0, 4.5, roof=True)
    sm = Placed(m, 1)  # local x -> world y: a stand facing local +x faces world +y
    stand(sm, -15.5, -9.0, -12.0, 9.0, 4.5, roof=True)
    # Low brick terraces on the near sides.
    rb = P + "red_brick"
    for (x0, x1, y0, y1) in ((12.0, 15.5, -15.5, 15.5), (-15.5, 12.0, 12.0, 15.5)):
        m.box(rb, x0, x1, y0, y1, 0, 2.2)
        m.box("concrete", x0 - 0.1, x1 + 0.1, y0 - 0.1, y1 + 0.1, 2.2, 2.5)
    for y in (-9.0, 0.0, 9.0):
        m.box("dark", 15.5, 15.6, y - 1.0, y + 1.0, 0.1, 1.7)
    for x in (-9.0, 0.0, 9.0):
        m.box("dark", x - 1.0, x + 1.0, 15.5, 15.6, 0.1, 1.7)
    for (x, y) in ((-15, -15), (14.5, -15), (-15, 14.5)):
        m.box("metal", x, x + 0.5, y, y + 0.5, 0, 9.0)
        m.box("light", x - 0.5, x + 1.0, y - 0.5, y + 1.0, 9.0, 9.8)
    m.save(P + "stadium_football.glb")


def stadium_rugby():
    """Stadium (2 x 2 tiles): a rugby pitch running along y with H goal posts, a tall covered stand on the far
    side and a long low covered stand on the near side."""
    m = Model()
    ground_around(m, "grass", (-16, 16, -16, 16), (-6.0, 9.0, -15.0, 15.0))
    m.box(P + "pitch", -6.0, 9.0, -15.0, 15.0, 0, 0.15)
    pitch_lines(m, -5.5, 8.5, -14.5, 14.5, "y", 5)
    for y in (-13.5, 13.5):  # H posts
        for x in (0.5, 2.5):
            m.box(P + "line", x - 0.12, x + 0.12, y - 0.12, y + 0.12, 0, 6.5)
        m.box(P + "line", 0.5, 2.5, y - 0.12, y + 0.12, 2.0, 2.25)
    # Tall stand on the far side (-x).
    stand(m, -15.8, -6.5, -14.0, 14.0, 7.5, roof=True)
    # Long low stand on the near side (+x): a brick building with seats and a roof.
    rb = P + "red_brick"
    m.box(rb, 9.5, 15.8, -15.0, 15.0, 0, 2.2)
    for i in range(10):
        y = -13.5 + i * 3.0
        m.box("dark", 15.8, 15.9, y - 0.5, y + 0.5, 0.2, 1.6)
    m.box(P + "seats", 9.5, 12.5, -15.0, 15.0, 2.2, 3.0)
    m.box(P + "crowd", 12.5, 15.8, -15.0, 15.0, 2.2, 3.8)
    for y in (-14.8, -5, 5, 14.8):
        m.box("metal", 15.2, 15.6, y - 0.2, y + 0.2, 3.8, 6.0)
    m.quad(rb, (9.0, -15.3, 5.4), (9.0, 15.3, 5.4), (16.0, 15.3, 6.2), (16.0, -15.3, 6.2))
    m.quad(rb, (16.0, -15.3, 5.9), (16.0, 15.3, 5.9), (9.0, 15.3, 5.1), (9.0, -15.3, 5.1))
    m.save(P + "stadium_rugby.glb")


def vault(m, material, end, x0, x1, y0, y1, z0, rise, n=6):
    """A barrel vault running along x, from y0 to y1, rising by rise above z0; the ends take the material end."""
    ym, r = (y0 + y1) / 2, (y1 - y0) / 2
    pts = [(ym - r * math.cos(math.pi * i / n), z0 + rise * math.sin(math.pi * i / n)) for i in range(n + 1)]
    for i in range(n):
        (ya, za), (yb, zb) = pts[i], pts[i + 1]
        m.quad(material, (x0, ya, za), (x1, ya, za), (x1, yb, zb), (x0, yb, zb))
    for i in range(n):
        (ya, za), (yb, zb) = pts[i], pts[i + 1]
        m.triangle(end, (x1, ym, z0), (x1, ya, za), (x1, yb, zb))
        m.triangle(end, (x0, ym, z0), (x0, yb, zb), (x0, ya, za))


def shopping_centre():
    """Shopping centre (2 x 2 tiles): a brick ground floor of shops under glass barrel vaults, with a raised
    middle hall and car parking along the near side."""
    m = Model()
    ground(m, P + "paving", -16, 16, -16, 16)
    rb = P + "red_brick"
    H = 4.0
    m.box(rb, -15, 11, -15, 15, 0, H)
    m.box("concrete", -15.2, 11.2, -15.2, 15.2, H, H + 0.4)
    wins(m, "glass", -15, 11, -15, 15, 0.4, 3.0, 1, 8, 9, w=2.0, h=2.0, sides="XY")
    for y in (-10, 0, 10):
        m.box("company", 11.0, 12.8, y - 2.5, y + 2.5, 2.9, 3.2)  # awnings in the house's colour
    # Glass vaults along x, the middle one higher.
    for y0, y1, z, rise in ((-15, -5, H + 0.4, 3.5), (-5, 5, H + 0.4, 6.0), (5, 15, H + 0.4, 3.5)):
        vault(m, P + "glass_roof", "concrete", -15, 11, y0, y1, z, rise, n=6)
        for k in range(5):
            x = -15 + (k + 0.5) * 26 / 5
            vault(m, "metal", "metal", x - 0.15, x + 0.15, y0 - 0.05, y1 + 0.05, z, rise + 0.08, n=6)
    # Car park in front.
    for k in range(9):
        y = -14 + k * 3.5
        m.box(P + "line", 12.5, 15.5, y - 0.08, y + 0.08, 0, 0.1)
    m.save(P + "shopping_centre.glb")


# ---------------------------------------------------------------- sub-arctic houses


def office_snow():
    """Large office block above the snow line (the snowy twin of house 4, which uses office_tower.glb)."""
    m = Model()
    m.box("concrete", -5, 5, -5, 5, 0, 1.2)
    m.box("glass", -4.5, 4.5, -4.5, 4.5, 1.2, 26)
    for i in range(8):
        z = 1.2 + 3.1 * (i + 1)
        m.box("company", -4.7, 4.7, -4.7, 4.7, z - 0.5, z)
    for x in (-4.7, 4.1):
        for y in (-4.7, 4.1):
            m.box("company", x, x + 0.6, y, y + 0.6, 1.2, 26)
    m.box("concrete", -4.8, 4.8, -4.8, 4.8, 26, 26.6)
    m.box(SNOW, -4.6, 4.6, -4.6, 4.6, 26.6, 26.8)
    m.box("metal", -1.5, 1.5, -1.5, 1.5, 26.6, 28.5)
    m.box(SNOW, -1.6, 1.6, -1.6, 1.6, 28.5, 28.8)
    m.save(P + "office_tower_snow.glb")


def stone_house(snow):
    """A grey stone house with a red tiled roof, a lower annex and a garden (houses 37/38)."""
    m = Model()
    plot(m, snow)
    m.box(P + "path", 4.0, 8.0, 1.0, 3.0, 0, 0.1)
    m.box("stone", -4.5, 3.5, -5.5, 1.5, 0, 5.0)
    m.prism_roof(roof_mat(snow, P + "red_roof"), "stone", -4.9, 3.9, -6.0, 2.0, 5.0, 8.2)
    m.box("stone", -2.5, 3.0, 1.5, 5.5, 0, 3.0)
    gable_y(m, roof_mat(snow, P + "red_roof"), "stone", -2.8, 3.3, 1.5, 5.8, 3.0, 5.0)
    m.box("stone", -2.5, -1.3, -3.5, -2.3, 6.0, 9.0)
    m.smoke_at(-1.9, -2.9, 9.0, 0.5)
    wins(m, "glass", -4.5, 3.5, -5.5, 1.5, 0.4, 5.0, 2, 3, 3, w=1.0, h=1.2, sides="Xy")
    wins(m, "glass", -2.5, 3.0, 1.5, 5.5, 0.4, 3.0, 1, 2, 2, w=1.0, h=1.2, sides="XY")
    door(m, 3.5, -2.0)
    if snow:
        snow_tree(m, -6, 6, 6, 1.6)
    else:
        blob(m, P + "flowers", 6.0, -5.5, 0.6, 1.0, 0.6, sides=6)
        tree(m, -6, 6, 6, 1.6, "conifer")
    m.save(P + ("stone_house_snow.glb" if snow else "stone_house.glb"))


def thatched_flats(snow):
    """Two storeys of flats under a thatched (or snow covered) roof, with a stone ground floor (houses 44/45)."""
    m = Model()
    plot(m, snow)
    m.box("stone", -5.0, 4.5, -5.5, 5.0, 0, 3.0)
    m.box(P + "yellow_brick", -5.0, 4.5, -5.5, 5.0, 3.0, 5.6)
    hip_roof(m, roof_mat(snow, P + "thatch"), -5.6, 5.1, -6.1, 5.6, 5.6, 9.0)
    m.box("brick", -1.0, 0.0, 2.0, 3.0, 7.0, 9.8)
    m.smoke_at(-0.5, 2.5, 9.8, 0.5)
    wins(m, "glass", -5.0, 4.5, -5.5, 5.0, 0.4, 5.6, 2, 3, 3, w=1.0, h=1.2, sides="XYy")
    door(m, 4.5, -0.5)
    m.box(P + "path", 4.5, 8.0, -1.2, 0.2, 0, 0.1)
    m.save(P + ("thatched_flats_snow.glb" if snow else "thatched_flats.glb"))


def slate_house(snow):
    """An L-shaped red brick house with a grey slate roof (houses 46/47)."""
    m = Model()
    plot(m, snow)
    rm = roof_mat(snow, "slate")
    m.box(P + "red_brick", -5.0, 1.0, -5.0, 4.5, 0, 4.6)
    gable_y(m, rm, P + "red_brick", -5.4, 1.4, -5.4, 4.9, 4.6, 8.0)
    m.box(P + "red_brick", 1.0, 5.0, -5.0, 0.0, 0, 3.6)
    m.prism_roof(rm, P + "red_brick", 0.6, 5.4, -5.4, 0.4, 3.6, 6.0)
    m.box("brick", -3.0, -2.0, 2.5, 3.5, 6.0, 9.0)
    m.smoke_at(-2.5, 3.0, 9.0, 0.5)
    wins(m, "glass", -5.0, 1.0, -5.0, 4.5, 0.4, 4.6, 2, 2, 3, w=1.0, h=1.2, sides="XY")
    wins(m, "glass", 1.0, 5.0, -5.0, 0.0, 0.4, 3.4, 1, 2, 2, w=1.0, h=1.2, sides="X")
    door(m, 1.0, 2.5)
    m.box(P + "path", 1.0, 8.0, 1.8, 3.2, 0, 0.1)
    m.save(P + ("slate_house_snow.glb" if snow else "slate_house.glb"))


def villa(snow):
    """A sandstone house with a brown roof, a cross gable and a fenced garden (houses 48/49)."""
    m = Model()
    plot(m, snow)
    rm = roof_mat(snow, P + "brown_roof")
    yb = P + "yellow_brick"
    m.box(yb, -5.0, 2.0, -4.5, 4.5, 0, 4.6)
    gable_y(m, rm, yb, -5.4, 2.4, -4.9, 4.9, 4.6, 7.8)
    m.box(yb, 2.0, 4.5, -3.5, 0.5, 0, 4.6)
    m.prism_roof(rm, yb, 1.6, 5.0, -3.9, 0.9, 4.6, 7.2)
    m.house_chimney(P + "red_brick", -3.2, -2.5, 5.5, 8.8)
    wins(m, "glass", -5.0, 2.0, -4.5, 4.5, 0.4, 4.6, 2, 2, 3, w=1.0, h=1.2, sides="XY")
    wins(m, "glass", 2.0, 4.5, -3.5, 0.5, 0.4, 4.6, 2, 1, 1, w=1.2, h=1.3, sides="X")
    door(m, 2.0, 2.4)
    m.box(P + "path", 2.0, 8.0, 1.8, 3.0, 0, 0.1)
    for (x0, x1, y0, y1) in ((-7.6, 7.6, -7.6, -7.4), (-7.6, -7.4, -7.6, 7.6), (7.4, 7.6, -7.6, 1.6), (7.4, 7.6, 3.2, 7.6), (-7.6, 7.6, 7.4, 7.6)):
        m.box(P + "red_brick", x0, x1, y0, y1, 0, 0.8)
    m.save(P + ("villa_snow.glb" if snow else "villa.glb"))


def cottage(snow):
    """A small yellow house with an orange roof and a big chimney (houses 56/57)."""
    m = Model()
    plot(m, snow)
    rm = roof_mat(snow, P + "orange_roof")
    m.box(P + "beige", -3.5, 3.5, -2.0, 4.5, 0, 4.4)
    gable_y(m, rm, P + "beige", -3.9, 3.9, -2.4, 4.9, 4.4, 7.4)
    m.box(P + "red_brick", -1.0, 0.6, -3.2, -2.0, 0, 8.4)
    m.smoke_at(-0.2, -2.6, 8.4, 0.6)
    wins(m, "glass", -3.5, 3.5, -2.0, 4.5, 0.4, 4.4, 2, 2, 2, w=1.0, h=1.2, sides="XY")
    door(m, 3.5, 1.2)
    m.box(P + "path", 3.5, 8.0, 0.6, 1.8, 0, 0.1)
    if snow:
        snow_tree(m, -5.5, -5.5, 6, 1.7)
    else:
        m.box(P + "flowers", 4.5, 7.0, -6.5, -3.0, 0, 0.5)
        tree(m, -5.5, -5.5, 6, 1.7, "conifer")
    m.save(P + ("cottage_snow.glb" if snow else "cottage.glb"))


def brick_house(snow):
    """A red brick house with a hipped red roof inside a low fence (houses 62/63)."""
    m = Model()
    plot(m, snow)
    m.box(P + "red_brick", -4.5, 3.5, -4.5, 4.5, 0, 4.8)
    hip_roof(m, roof_mat(snow, P + "red_roof"), -5.0, 4.0, -5.0, 5.0, 4.8, 8.0)
    m.box(P + "red_brick", 3.5, 5.0, -1.2, 1.2, 0, 2.6)  # porch
    m.box(roof_mat(snow, P + "red_roof"), 3.4, 5.3, -1.5, 1.5, 2.6, 3.0)
    m.box("brick", 1.0, 2.0, 2.0, 3.0, 6.0, 9.0)
    m.smoke_at(1.5, 2.5, 9.0, 0.5)
    wins(m, "glass", -4.5, 3.5, -4.5, 4.5, 0.4, 4.8, 2, 3, 3, w=1.0, h=1.2, sides="XY")
    door(m, 5.0, 0.0)
    m.box(P + "path", 5.0, 8.0, -0.6, 0.6, 0, 0.1)
    for (x0, x1, y0, y1) in ((-7.6, 7.6, -7.6, -7.4), (-7.6, -7.4, -7.6, 7.6), (7.4, 7.6, -7.6, -0.8), (7.4, 7.6, 0.8, 7.6), (-7.6, 7.6, 7.4, 7.6)):
        m.box("wood", x0, x1, y0, y1, 0, 0.8)
    m.save(P + ("brick_house_snow.glb" if snow else "brick_house.glb"))


def gabled_shops(snow):
    """Shops and offices of three storeys in red brick under two steep gabled roofs (houses 58/59)."""
    m = Model()
    rb = P + "red_brick"
    H = 3 * STOREY
    m.box(rb, -6.5, 6.5, -6.5, 6.5, 0, H)
    for y0, y1 in ((-6.9, 0), (0, 6.9)):
        m.prism_roof(roof_mat(snow, P + "red_roof"), rb, -6.9, 6.9, y0, y1, H, H + 4.0)
    m.box("glass", 6.5, 6.6, -6.0, 6.0, 0.4, 2.6)
    m.box("glass", -6.0, 6.0, 6.5, 6.6, 0.4, 2.6)
    m.box("company", 6.6, 7.8, -6.3, 6.3, 2.7, 3.0)
    wins(m, "glass", -6.5, 6.5, -6.5, 6.5, STOREY, H, 2, 4, 4, w=1.1, h=1.5, sides="xXyY")
    m.save(P + ("gabled_shops_snow.glb" if snow else "gabled_shops.glb"))


def chapel(snow):
    """A small brick church with a steep roof, a cross gable with a white cross, and a bell turret (houses 60/61)."""
    m = Model()
    plot(m, snow)
    rb = P + "red_brick"
    rm = roof_mat(snow, "slate")
    m.box(rb, -6.0, 5.0, -3.0, 3.0, 0, 4.5)
    m.prism_roof(rm, rb, -6.4, 5.4, -3.6, 3.6, 4.5, 10.0)
    m.box(rb, -2.0, 3.0, -5.0, 5.5, 0, 4.5)
    gable_y(m, rm, rb, -2.4, 3.4, -5.4, 5.9, 4.5, 9.0)
    for (x0, x1, y0, y1, z0, z1) in ((0.35, 0.65, 5.9, 6.0, 4.6, 7.6), (-0.4, 1.4, 5.9, 6.0, 6.4, 6.8)):
        m.box(P + "white", x0, x1, y0, y1, z0, z1)
    for x in (-5.0, -3.2, 3.7):
        for y in (-3.06, 3.0):
            m.box("glass", x - 0.35, x + 0.35, y, y + 0.06, 1.0, 3.8)
    m.box("glass", 0.0, 1.0, 5.5, 5.56, 1.0, 3.8)
    m.box("door", 5.0, 5.1, -0.7, 0.7, 0, 2.6)
    m.box("glass", 5.0, 5.06, -0.4, 0.4, 5.2, 7.0)
    m.box("wood", 3.6, 4.6, -0.5, 0.5, 9.0, 10.8)  # bell turret on the ridge
    m.pyramid(rm, 3.4, 4.8, -0.7, 0.7, 10.8, 12.5)
    m.box(P + "path", 5.0, 8.0, -0.7, 0.7, 0, 0.1)
    m.save(P + ("chapel_snow.glb" if snow else "chapel.glb"))


def tall_gabled(snow):
    """Shops and offices of four storeys in red brick with a steep red gabled roof and a flat roofed back (houses 64/65)."""
    m = Model()
    rb = P + "red_brick"
    H = 4 * STOREY
    m.box(rb, -6.5, 6.5, -6.5, 6.5, 0, H)
    m.prism_roof(roof_mat(snow, P + "red_roof"), rb, -1.0, 6.9, -6.9, 6.9, H, H + 5.0)
    flat_roof(m, -6.5, -1.0, -6.5, 6.5, H, snow, "concrete", 0.2, 0.4)
    m.box("glass", 6.5, 6.6, -6.0, 6.0, 0.4, 2.6)
    m.box("company", 6.6, 7.8, -6.3, 6.3, 2.7, 3.0)
    wins(m, "glass", -6.5, 6.5, -6.5, 6.5, STOREY, H, 3, 5, 5, w=1.0, h=1.5, sides="xXyY")
    wins(m, "glass", -6.5, 6.5, -6.5, 6.5, 0.4, STOREY, 1, 5, 5, w=1.0, h=1.5, sides="xyY")
    m.save(P + ("tall_gabled_snow.glb" if snow else "tall_gabled.glb"))


def stone_offices(snow):
    """Shops and offices: a grey stone front block of four storeys with a red brick block behind (houses 70/71)."""
    m = Model()
    rb = P + "red_brick"
    m.box(rb, -6.5, 0.0, -6.5, 6.5, 0, 5 * STOREY)
    flat_roof(m, -6.5, 0.0, -6.5, 6.5, 5 * STOREY, snow, "concrete", 0.2, 0.5)
    wins(m, "glass", -6.5, 0.0, -6.5, 6.5, 0.4, 5 * STOREY, 5, 2, 4, w=0.9, h=1.4, sides="xyY")
    H = 4 * STOREY
    m.box("stone", 0.0, 6.5, -6.5, 6.5, 0, H)
    flat_roof(m, 0.0, 6.5, -6.5, 6.5, H, snow, P + "red_brick", 0.2, 0.6)
    m.box("glass", 6.5, 6.6, -5.0, 5.0, 0.4, 2.6)
    m.box("company", 6.6, 7.6, -5.3, 5.3, 2.7, 3.0)
    wins(m, "glass", 0.0, 6.5, -6.5, 6.5, STOREY, H, 3, 3, 5, w=1.0, h=1.6, sides="XyY")
    m.save(P + ("stone_offices_snow.glb" if snow else "stone_offices.glb"))


def terrace(snow):
    """Hotel above the arctic towns (1 x 2 tiles along y): a long terrace of brick houses with gables to the
    front and dark roofs (houses 66-69)."""
    m = Model()
    plot(m, snow, -8, 8, -16, 16)
    rb = P + "red_brick"
    rm = roof_mat(snow, "slate")
    H = 2 * STOREY
    m.box(P + "yellow_brick", -5.5, 3.5, -14.5, 14.5, 0, H)
    gable_y(m, rm, P + "yellow_brick", -6.0, 4.0, -15.0, 15.0, H, H + 3.6)
    for k in range(5):
        yc = -12 + k * 6.0
        m.box(rb, 3.5, 6.0, yc - 2.0, yc + 2.0, 0, H)
        m.prism_roof(rm, rb, -1.0, 6.4, yc - 2.4, yc + 2.4, H, H + 3.0)
        m.box("glass", 6.0, 6.06, yc - 1.4, yc - 0.2, 0.6, 2.4)
        m.box("glass", 6.0, 6.06, yc - 0.8, yc + 0.8, 3.9, 5.6)
        m.box("door", 6.0, 6.1, yc + 0.4, yc + 1.4, 0.1, 2.3)
        m.box("brick", -3.0, -2.0, yc + 2.4, yc + 3.4, H + 1.5, H + 4.6)
        m.smoke_at(-2.5, yc + 2.9, H + 4.6, 0.5)
        m.box(P + "path", 6.0, 8.0, yc + 0.3, yc + 1.5, 0, 0.1)
    wins(m, "glass", -5.5, 3.5, -14.5, 14.5, 0.4, H, 2, 2, 10, w=1.0, h=1.2, sides="xyY")
    m.save(P + ("terrace_snow.glb" if snow else "terrace.glb"))


def grid_tower(snow):
    """A tall pale office tower with a wider podium and a coloured roof (houses 50/51)."""
    m = Model()
    m.box("concrete", -7, 7, -7, 7, 0, 0.3)
    m.box(P + "white", -6.5, 6.5, -6.5, 6.5, 0.3, 11)
    m.box("concrete", -6.7, 6.7, -6.7, 6.7, 11, 11.6)
    m.box(P + "white", -5.8, 5.8, -5.8, 5.8, 11.6, 36)
    wins(m, "glass", -6.5, 6.5, -6.5, 6.5, 0.3, 11, 3, 5, 5, w=1.6, h=2.0)
    wins(m, "glass", -5.8, 5.8, -5.8, 5.8, 11.6, 36, 7, 5, 5, w=1.4, h=2.2)
    m.box("company", -6.0, 6.0, -6.0, 6.0, 36, 36.6)
    m.box(SNOW if snow else "company_dark", -5.8, 5.8, -5.8, 5.8, 36.6, 36.8)
    m.box("metal", -2, 1.5, -1.5, 1.5, 36.8, 38.2)
    if snow:
        m.box(SNOW, -2.1, 1.6, -1.6, 1.6, 38.2, 38.4)
    m.save(P + ("grid_tower_snow.glb" if snow else "grid_tower.glb"))


def blue_tower(snow):
    """A dark blue glass tower with white ribs, a lower wing to the front and machinery on the roof (houses 52/53)."""
    m = Model()
    m.box("concrete", -7, 7, -7, 7, 0, 0.3)
    g = P + "glass_dark"
    m.box(g, -6.0, 3.0, -6.0, 6.0, 0.3, 36)
    m.box(g, 3.0, 6.5, -6.0, 1.0, 0.3, 22)
    m.box(g, 3.0, 6.5, 1.0, 6.5, 0.3, 14)
    for x in (-6.2, -3.0, 0.0, 2.8):
        for y in (-6.2, 5.8):
            m.box(P + "white", x, x + 0.4, y, y + 0.4, 0.3, 36)
    for y in (-3.0, 0.0, 3.0):
        m.box(P + "white", -6.2, -5.8, y, y + 0.4, 0.3, 36)
        m.box(P + "white", 2.8, 3.2, y, y + 0.4, 22, 36)
    for y in (-6.2, -3.0, 0.6):
        m.box(P + "white", 6.3, 6.7, y, y + 0.4, 0.3, 22)
    for y in (1.2, 3.8, 6.3):
        m.box(P + "white", 6.3, 6.7, y, y + 0.4, 0.3, 14)
    flat_roof(m, -6.0, 3.0, -6.0, 6.0, 36, snow, P + "white", 0.3, 0.6)
    flat_roof(m, 3.0, 6.5, -6.0, 1.0, 22, snow, P + "white", 0.2, 0.5)
    flat_roof(m, 3.0, 6.5, 1.0, 6.5, 14, snow, P + "white", 0.2, 0.5)
    m.box("metal", -4, 0, -3, 1, 36.6, 38.4)
    m.box("metal", -1, 2, 2, 4, 36.6, 37.6)
    if snow:
        m.box(SNOW, -4.1, 0.1, -3.1, 1.1, 38.4, 38.6)
    m.save(P + ("blue_tower_snow.glb" if snow else "blue_tower.glb"))


def stepped_tower(snow):
    """A bright blue glass tower that steps back twice towards its top, with an entrance canopy (houses 54/55)."""
    m = Model()
    m.box("concrete", -7.5, 7.5, -7.5, 7.5, 0, 0.3)
    g = P + "glass_blue"
    sections = [(6.0, 0.3, 28.0), (4.6, 29.0, 40.0), (3.0, 41.0, 46.0)]
    for i, (r, z0, z1) in enumerate(sections):
        m.box(g, -r, r, -r, r, z0, z1)
        rows = int((z1 - z0) / STOREY)
        for k in range(1, rows + 1):
            z = z0 + k * (z1 - z0) / rows
            m.box("metal", -r - 0.08, r + 0.08, -r - 0.08, r + 0.08, z - 0.35, z)
        rr = r + 0.6
        m.box("concrete", -rr, rr, -rr, rr, z1, z1 + 1.0 if i < 2 else z1 + 0.6)
        if snow:
            m.box(SNOW, -rr + 0.2, rr - 0.2, -rr + 0.2, rr - 0.2, z1 + (1.0 if i < 2 else 0.6), z1 + (1.15 if i < 2 else 0.75))
    m.box("metal", -1.2, 1.2, -1.2, 1.2, 46.6, 48.0)
    m.box(P + "white", 6.0, 8.0, -3.0, 3.0, 2.8, 3.2)  # canopy
    m.box("dark", 6.0, 6.1, -1.5, 1.5, 0.3, 2.6)
    m.save(P + ("stepped_tower_snow.glb" if snow else "stepped_tower.glb"))


def pilotis_tower(snow):
    """A grey office tower standing on columns over a recessed glass lobby (houses 72/73)."""
    m = Model()
    m.box("concrete", -7, 7, -7, 7, 0, 0.3)
    m.box("glass", -4.5, 4.5, -4.5, 4.5, 0.3, 4.0)
    for x in (-5.6, 4.8):
        for y in (-5.6, -0.4, 4.8):
            m.box("concrete", x, x + 0.8, y, y + 0.8, 0.3, 4.0)
            m.box("concrete", y, y + 0.8, x, x + 0.8, 0.3, 4.0)
    m.box("concrete", -5.6, 5.6, -5.6, 5.6, 4.0, 32)
    wins(m, "glass", -5.6, 5.6, -5.6, 5.6, 4.0, 32, 9, 5, 5, w=1.5, h=2.0)
    flat_roof(m, -5.6, 5.6, -5.6, 5.6, 32, snow, "metal", 0.2, 0.6)
    m.box("metal", -2, 2, -2, 2, 32.6, 34.0)
    if snow:
        m.box(SNOW, -2.1, 2.1, -2.1, 2.1, 34.0, 34.2)
    m.save(P + ("pilotis_tower_snow.glb" if snow else "pilotis_tower.glb"))


def slab_tower(snow):
    """A tall beige slab of offices over two tiles along x, with a dark stair tower and a lawn (houses 74-77)."""
    m = Model()
    ground_around(m, "concrete", (-16, 16, -8, 8), (6, 15, -7, 7))
    plot(m, snow, 6, 15, -7, 7)
    b = P + "beige"
    m.box(b, -14, 5, -5.5, 5.5, 0.05, 44)
    wins(m, "glass", -14, 5, -5.5, 5.5, 1.0, 44, 13, 9, 5, w=1.2, h=1.6)
    m.box(P + "brown_roof", -4.5, -2.5, 5.5, 6.4, 0.05, 45)  # stair tower on the near side
    m.box("glass", -4.0, -3.0, 6.4, 6.46, 1.0, 43)
    m.box("dark", 5.0, 5.1, -2.0, 2.0, 0.05, 2.6)
    flat_roof(m, -14, 5, -5.5, 5.5, 44, snow, P + "white", 0.3, 0.7)
    m.box("metal", -8, -2, -2.5, 2.5, 44.7, 46.4)
    if snow:
        m.box(SNOW, -8.1, -1.9, -2.6, 2.6, 46.4, 46.6)
    else:
        for x, y in ((8.5, -4.5), (12.5, 4.0)):
            blob(m, P + "foliage", x, y, 0.9, 1.0, 0.8, sides=6)
    m.save(P + ("slab_tower_snow.glb" if snow else "slab_tower.glb"))


# ---------------------------------------------------------------- index


def build():
    hotel()
    statue()
    fountain()
    park_pond()
    park_trees()
    warehouse()
    theatre()
    cinema()
    stadium_football()
    stadium_rugby()
    shopping_centre()
    office_snow()
    for snow in (False, True):
        stone_house(snow)
        thatched_flats(snow)
        slate_house(snow)
        villa(snow)
        cottage(snow)
        brick_house(snow)
        gabled_shops(snow)
        chapel(snow)
        tall_gabled(snow)
        stone_offices(snow)
        terrace(snow)
        grid_tower(snow)
        blue_tower(snow)
        stepped_tower(snow)
        pilotis_tower(snow)
        slab_tower(snow)

    def house(ids, name):
        return {"type": "house", "ids": ids, "model": P + name + ".glb"}

    buildings = [
        house([7, 8], "hotel"),
        house([9], "statue"),
        house([10], "fountain"),
        house([11], "park_pond"),
        house([12], "park_trees"),
        house([18], "warehouse"),
        house([20, 21, 22, 23], "stadium_football"),
        house([31], "theatre"),
        house([32, 33, 34, 35], "stadium_rugby"),
        house([39], "cinema"),
        house([40, 41, 42, 43], "shopping_centre"),
        house([5], "office_tower_snow"),
    ]
    # Sub-arctic houses: (below the snow line, above it), model.
    pairs = [
        ([37], [38], "stone_house"),
        ([44], [45], "thatched_flats"),
        ([46], [47], "slate_house"),
        ([48], [49], "villa"),
        ([50], [51], "grid_tower"),
        ([52], [53], "blue_tower"),
        ([54], [55], "stepped_tower"),
        ([56], [57], "cottage"),
        ([58], [59], "gabled_shops"),
        ([60], [61], "chapel"),
        ([62], [63], "brick_house"),
        ([64], [65], "tall_gabled"),
        ([66, 67], [68, 69], "terrace"),
        ([70], [71], "stone_offices"),
        ([72], [73], "pilotis_tower"),
        ([74, 75], [76, 77], "slab_tower"),
    ]
    for below, above, name in pairs:
        buildings.append(house(below, name))
        buildings.append(house(above, name + "_snow"))
    return {"vehicles": [], "buildings": buildings}
