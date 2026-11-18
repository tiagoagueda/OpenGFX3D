"""Infrastructure models: airport tiles of all base-game airports, docks, buoy, depots and objects.

Airport tiles are one tile each, seen as in an unrotated airport: x (front) points south-west, y (left)
south-east, so the fence names of src/table/airporttile_ids.h map to the edges as
NE = -x, SW = +x, NW = -y, SE = +y. The runways of the base airports run along x.

Heights: the game draws one z unit of the 2D game as 0.408 world units, so a height level is about 3.27
and things the 2D game puts at a z offset (the heliport roof at 60) are at about 0.408 times that here.
"""

import math

from gfx3d import MATERIALS, Model

GROUP = "infra"

for _name, _colour in {
    "infra_tarmac": (0.40, 0.40, 0.42),
    "infra_runway": (0.27, 0.27, 0.29),
    "infra_white": (0.93, 0.93, 0.90),
    "infra_yellow": (0.92, 0.74, 0.18),
    "infra_red": (0.78, 0.16, 0.12),
    "infra_orange": (0.96, 0.50, 0.10),
    "infra_gravel": (0.62, 0.58, 0.50),
    "infra_water": (0.20, 0.34, 0.48),
}.items():
    MATERIALS.setdefault(_name, _colour)

SLAB = 0.1  # height of the ground slabs of airport tiles
MARK = SLAB + 0.02  # height of the markings on them
Z = 0.40824829  # world units per z unit of the 2D game


# ---------------------------------------------------------------------------------------------------
# Generic shape helpers.

def _sub(a, b):
    return [a[i] - b[i] for i in range(3)]


def _cross(u, v):
    return [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]]


def _norm(v):
    ln = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / ln for x in v]


def face(m, mat, pts, centre):
    """A flat polygon (as a fan), turned so that it faces away from the point centre."""
    n = _cross(_sub(pts[1], pts[0]), _sub(pts[2], pts[0]))
    mid = [sum(p[i] for p in pts) / len(pts) for i in range(3)]
    if sum(n[i] * (mid[i] - centre[i]) for i in range(3)) < 0:
        pts = list(reversed(pts))
    for i in range(1, len(pts) - 1):
        m.triangle(mat, tuple(pts[0]), tuple(pts[i]), tuple(pts[i + 1]))


class Ground:
    """A flat surface with markings, cut into pieces that do not overlap, so nothing fights for depth.

    The base covers the rectangle; each marking (a convex polygon, counter-clockwise seen from above)
    is cut out of what lies under it, so later markings lie on top of earlier ones."""

    def __init__(self, m, z, base, x0=-8, x1=8, y0=-8, y1=8):
        self.z = z
        self.pieces = [([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], base)]
        m.__dict__.setdefault("grounds", []).append(self)

    @staticmethod
    def _clip(poly, a, b):
        """Split a convex polygon by the line through a and b: (left part, right part)."""
        left, right = [], []
        n = len(poly)
        side = [(b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0]) for p in poly]
        for i in range(n):
            p, q = poly[i], poly[(i + 1) % n]
            sp, sq = side[i], side[(i + 1) % n]
            if sp >= 0:
                left.append(p)
            if sp <= 0:
                right.append(p)
            if (sp > 0 and sq < 0) or (sp < 0 and sq > 0):
                t = sp / (sp - sq)
                c = (p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1]))
                left.append(c)
                right.append(c)
        return left, right

    @staticmethod
    def _area(poly):
        return sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1] for i in range(len(poly))) / 2

    def poly(self, mat, pts):
        if self._area(pts) < 0:
            pts = list(reversed(pts))
        bx0, bx1 = min(p[0] for p in pts), max(p[0] for p in pts)
        by0, by1 = min(p[1] for p in pts), max(p[1] for p in pts)
        out = []
        for piece, pmat in self.pieces:
            if max(p[0] for p in piece) <= bx0 or min(p[0] for p in piece) >= bx1 or max(p[1] for p in piece) <= by0 or min(p[1] for p in piece) >= by1:
                out.append((piece, pmat))
                continue
            inside = piece
            for i in range(len(pts)):
                inside, outside = self._clip(inside, pts[i], pts[(i + 1) % len(pts)])
                if len(outside) >= 3 and self._area(outside) > 1e-6:
                    out.append((outside, pmat))
                if len(inside) < 3 or self._area(inside) <= 1e-6:
                    inside = None
                    break
            if inside:
                out.append((inside, mat))
        self.pieces = out

    def emit(self, m):
        for piece, mat in self.pieces:
            if mat is None:
                continue
            for i in range(1, len(piece) - 1):
                m.triangle(mat, (piece[0][0], piece[0][1], self.z), (piece[i][0], piece[i][1], self.z), (piece[i + 1][0], piece[i + 1][1], self.z))


def _ground_at(m, z):
    for g in m.__dict__.get("grounds", []):
        if g.z - 0.01 <= z <= g.z + 0.12:
            return g
    return None


def finish(m):
    """Draw the grounds of a model; call once when the model is complete."""
    for g in m.__dict__.pop("grounds", []):
        g.emit(m)


def up(m, mat, x0, x1, y0, y1, z=MARK):
    """A rectangle facing up, for markings; on a ground surface it becomes part of it."""
    g = _ground_at(m, z)
    if g:
        g.poly(mat, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
    else:
        m.quad(mat, (x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z))


def stripe(m, mat, a, b, w, z=MARK):
    """A line of width w from a to b on the ground, facing up."""
    d = _norm([b[0] - a[0], b[1] - a[1], 0])
    n = (-d[1] * w / 2, d[0] * w / 2)
    pts = [(a[0] - n[0], a[1] - n[1]), (b[0] - n[0], b[1] - n[1]), (b[0] + n[0], b[1] + n[1]), (a[0] + n[0], a[1] + n[1])]
    g = _ground_at(m, z)
    if g:
        g.poly(mat, pts)
    else:
        m.quad(mat, *[(p[0], p[1], z) for p in pts])


def beam(m, mat, p0, p1, w):
    """A square beam of width w from p0 to p1."""
    d = _norm(_sub(p1, p0))
    ref = [0, 0, 1] if abs(d[2]) < 0.9 else [1, 0, 0]
    u = [x * w / 2 for x in _norm(_cross(d, ref))]
    v = [x * w / 2 for x in _norm(_cross(d, u))]
    centre = [(p0[i] + p1[i]) / 2 for i in range(3)]
    corners = []
    for p in (p0, p1):
        corners.append([[p[i] + su * u[i] + sv * v[i] for i in range(3)] for su, sv in ((1, 1), (-1, 1), (-1, -1), (1, -1))])
    for k in range(4):
        face(m, mat, [corners[0][k], corners[0][(k + 1) % 4], corners[1][(k + 1) % 4], corners[1][k]], centre)
    face(m, mat, corners[0], centre)
    face(m, mat, corners[1], centre)


def frustum(m, mat, x, y, z0, z1, r0, r1, sides=12, top=None, bottom=False, rot=0.0):
    """An upright cone frustum (or prism when r0 == r1) with a top cap of material top."""
    centre = [x, y, (z0 + z1) / 2]
    ring0, ring1 = [], []
    for i in range(sides):
        a = rot + 2 * math.pi * i / sides
        ring0.append([x + r0 * math.cos(a), y + r0 * math.sin(a), z0])
        ring1.append([x + r1 * math.cos(a), y + r1 * math.sin(a), z1])
    for i in range(sides):
        j = (i + 1) % sides
        face(m, mat, [ring0[i], ring0[j], ring1[j], ring1[i]], centre)
    if top and r1 > 0:
        face(m, top, ring1, [x, y, z0 - 1])
    if bottom:
        face(m, mat, ring0, [x, y, z1 + 1])


def disc(m, mat, x, y, r, z=MARK, sides=16):
    g = _ground_at(m, z)
    if g:
        g.poly(mat, [(x + r * math.cos(2 * math.pi * i / sides), y + r * math.sin(2 * math.pi * i / sides)) for i in range(sides)])
        return
    for i in range(sides):
        a, b = 2 * math.pi * i / sides, 2 * math.pi * (i + 1) / sides
        m.triangle(mat, (x, y, z), (x + r * math.cos(a), y + r * math.sin(a), z), (x + r * math.cos(b), y + r * math.sin(b), z))


def ring(m, mat, x, y, r0, r1, z=MARK, sides=20):
    g = _ground_at(m, z)
    for i in range(sides):
        a, b = 2 * math.pi * i / sides, 2 * math.pi * (i + 1) / sides
        if g:
            g.poly(mat, [(x + r0 * math.cos(a), y + r0 * math.sin(a)), (x + r1 * math.cos(a), y + r1 * math.sin(a)),
                         (x + r1 * math.cos(b), y + r1 * math.sin(b)), (x + r0 * math.cos(b), y + r0 * math.sin(b))])
            continue
        m.quad(mat, (x + r0 * math.cos(a), y + r0 * math.sin(a), z), (x + r1 * math.cos(a), y + r1 * math.sin(a), z),
               (x + r1 * math.cos(b), y + r1 * math.sin(b), z), (x + r0 * math.cos(b), y + r0 * math.sin(b), z))


# ---------------------------------------------------------------------------------------------------
# Airport ground.

def sides(m, mat, x0, x1, y0, y1, z0, z1):
    """The four walls of a box, without top and bottom."""
    m.quad(mat, (x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1))
    m.quad(mat, (x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1))
    m.quad(mat, (x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1))
    m.quad(mat, (x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1))


def slab(m, mat="infra_tarmac"):
    """The ground slab of a tile; its top is a Ground that markings become part of."""
    sides(m, mat, -8, 8, -8, 8, 0, SLAB)
    return Ground(m, SLAB, mat)


def fence(m, edge):
    """A company-coloured airport fence on one edge of the tile: ne (-x), sw (+x), nw (-y) or se (+y)."""
    e = 7.75
    if edge in ("ne", "sw"):
        x = -e if edge == "ne" else e
        for i in range(7):
            y = -7.5 + i * 2.5
            m.box("metal", x - 0.1, x + 0.1, y - 0.1, y + 0.1, 0, 2.2)
        for z in (0.8, 1.5, 2.1):
            m.box("company", x - 0.06, x + 0.06, -8, 8, z - 0.06, z + 0.06)
    else:
        y = -e if edge == "nw" else e
        for i in range(7):
            x = -7.5 + i * 2.5
            m.box("metal", x - 0.1, x + 0.1, y - 0.1, y + 0.1, 0, 2.2)
        for z in (0.8, 1.5, 2.1):
            m.box("company", -8, 8, y - 0.06, y + 0.06, z - 0.06, z + 0.06)


def fences(m, edges):
    for e in edges:
        fence(m, e)


def apron_joints(m):
    """Faint concrete joints on the apron."""
    for v in (-8, 0):
        up(m, "infra_gravel", v - 0.04, v + 0.04, -8, 8)
        up(m, "infra_gravel", -8, 8, v - 0.04, v + 0.04)


def ground_apron(m):
    slab(m)
    apron_joints(m)


def ground_grass(m):
    slab(m, "grass")


def taxi_lines(m, lines):
    """Yellow taxi lines: ("x", off) runs along x at y = off, ("y", off) along y at x = off."""
    for axis, off in lines:
        if axis == "x":
            up(m, "infra_yellow", -8, 8, off - 0.18, off + 0.18)
        else:
            up(m, "infra_yellow", off - 0.18, off + 0.18, -8, 8, MARK + 0.005)


def stand_marking(m):
    """An aircraft stand: a lead-in line, a stop bar and a white box."""
    stripe(m, "infra_yellow", (-8, 0), (3.5, 0), 0.35)
    up(m, "infra_yellow", 3.5, 4.1, -2.2, 2.2)
    for a, b in (((-7, -7), (7, -7)), ((7, -7), (7, 7)), ((7, 7), (-7, 7)), ((-7, 7), (-7, -7))):
        stripe(m, "infra_white", a, b, 0.25, MARK + 0.005)


def runway(m, kind="plain"):
    """A runway tile along x: centre line, edge lines, and threshold or exit markings."""
    slab(m, "infra_runway")
    for y in (-6.9, 6.9):
        up(m, "infra_white", -8, 8, y - 0.2, y + 0.2)
    if kind == "end":
        # Threshold bars, the same at both ends of the runway.
        for i in range(4):
            y = 1.2 + i * 1.4
            for s in (-1, 1):
                up(m, "infra_white", -4.5, 4.5, s * y - 0.45, s * y + 0.45)
        up(m, "infra_white", -0.4, 0.4, -6.9, 6.9)
        for x in (-6, 6):
            up(m, "infra_white", x - 0.6, x + 0.6, -0.15, 0.15)
        # Runway end lights.
        for y in (-5, -2.5, 2.5, 5):
            for x in (-7.5, 7.5):
                m.box("light", x - 0.15, x + 0.15, y - 0.15, y + 0.15, SLAB, SLAB + 0.25)
        return
    for x0 in (-6.5, 1.5):
        up(m, "infra_white", x0, x0 + 3, -0.18, 0.18)
    exits = {"a": ((-4, 0), (4, -8)), "c": ((-4, -8), (4, 0)), "d": ((-8, -8), (0, 0))}
    if kind in exits:
        a, b = exits[kind]
        stripe(m, "infra_yellow", a, b, 0.35, MARK + 0.005)
        # A gap in the edge line where the exit leaves the runway.
        mx = (a[0] + b[0]) / 2 + (2 if kind == "a" else -2 if kind != "d" else -4)
        up(m, "infra_runway", mx - 1.2, mx + 1.2, -7.2, -6.6, MARK + 0.003)


def small_runway(m, end=None):
    """A grass airfield's runway: a paved strip on grass; end is 'near' (+x end) or 'far' (-x end)."""
    slab(m, "grass")
    up(m, "infra_runway", -8, 8, -5, 5)
    z = MARK
    for y in (-4.5, 4.5):
        up(m, "infra_white", -8, 8, y - 0.15, y + 0.15, z)
    if end is None:
        for x0 in (-6.5, 1.5):
            up(m, "infra_white", x0, x0 + 3, -0.15, 0.15, z)
        return
    s = 1 if end == "near" else -1
    for i in range(3):
        y = 0.8 + i * 1.2
        for t in (-1, 1):
            up(m, "infra_white", min(s * 3, s * 7), max(s * 3, s * 7), t * y - 0.35, t * y + 0.35, z)
    up(m, "infra_white", -6, 1, -0.15, 0.15, z) if s == 1 else up(m, "infra_white", -1, 6, -0.15, 0.15, z)


def half_apron(m, east):
    """Half grass, half apron, split along the diagonal from the north to the south corner."""
    slab(m, "grass")
    # The east corner is (-x, +y), the west corner (+x, -y).
    tri = [(-8, -8), (8, 8), (-8, 8)] if east else [(-8, -8), (8, -8), (8, 8)]
    _ground_at(m, SLAB).poly("infra_tarmac", tri)


# ---------------------------------------------------------------------------------------------------
# Airport buildings and furniture.

def banded(m, wall, x0, x1, y0, y1, z0, z1, bands, glass="glass", inset=0.12):
    """Walls of a block with glass bands (za, zb) set slightly into them, stacked so nothing overlaps."""
    z = z0
    for za, zb in sorted(bands):
        if za > z:
            sides(m, wall, x0, x1, y0, y1, z, za)
        sides(m, glass, x0 + inset, x1 - inset, y0 + inset, y1 - inset, za, zb)
        for zz, sgn in ((za, 1), (zb, -1)):  # the ledges above and below the glass
            for (a0, a1, b0, b1) in ((x0, x1, y0, y0 + inset), (x0, x1, y1 - inset, y1), (x0, x0 + inset, y0 + inset, y1 - inset), (x1 - inset, x1, y0 + inset, y1 - inset)):
                if sgn > 0:
                    m.quad(wall, (a0, b0, zz), (a1, b0, zz), (a1, b1, zz), (a0, b1, zz))
                else:
                    m.quad(wall, (a0, b1, zz), (a1, b1, zz), (a1, b0, zz), (a0, b0, zz))
        z = zb
    if z1 > z:
        sides(m, wall, x0, x1, y0, y1, z, z1)
    m.quad(wall, (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1))


def terminal_block(m, x0, x1, y0, y1, h, storeys=2):
    """An airport terminal block: concrete base, glass bands, company-coloured trim, flat roof."""
    sh = (h - 3) / max(1, storeys - 1)
    bands = [(SLAB + 0.6, SLAB + 2.6)] + [(3 + (k - 0.5) * sh - 0.9, 3 + (k - 0.5) * sh + 0.9) for k in range(1, storeys)]
    banded(m, "concrete", x0, x1, y0, y1, SLAB, h, bands)
    m.box("company", x0 - 0.2, x1 + 0.2, y0 - 0.2, y1 + 0.2, h, h + 0.6)
    m.box("roof", x0 + 0.3, x1 - 0.3, y0 + 0.3, y1 - 0.3, h + 0.6, h + 0.7)


def building_1(m):
    """APT_BUILDING_1: a long terminal block along x."""
    ground_apron(m)
    terminal_block(m, -8, 8, -5, 6, 9.5, 3)
    m.box("metal", -4, 0, -2, 2, 10.3, 11.6)
    m.box("metal", 3, 5, -1, 1.5, 10.3, 11.0)
    m.box("company", -6, 6, 6.2, 7.6, 3.0, 3.3)  # canopy over the apron side


def building_2(m):
    """APT_BUILDING_2: the main terminal block along y, a little taller, with a sign."""
    ground_apron(m)
    terminal_block(m, -6, 5, -8, 8, 11, 3)
    m.box("company", 5.1, 5.3, -4, 4, 8.0, 9.8)  # sign panel
    m.box("infra_white", 5.3, 5.35, -3.2, 3.2, 8.5, 9.3)
    m.box("company", 5.2, 7.2, -5, 5, 3.0, 3.3)  # canopy
    m.box("metal", -3, 1, -3, 3, 11.7, 13)


def building_3(m):
    """APT_BUILDING_3: a smaller terminal wing."""
    ground_apron(m)
    terminal_block(m, -5, 5, -5, 6, 8, 2)
    m.box("glass", -2, 2, -2, 2, 8.7, 10.5)
    m.box("company", -2.3, 2.3, -2.3, 2.3, 10.5, 11)


def round_terminal(m):
    """APT_ROUND_TERMINAL: a round concourse with jetways around it."""
    ground_apron(m)
    cx, cy = -1, 0
    frustum(m, "concrete", cx, cy, SLAB, 0.8, 7, 7, 20)
    frustum(m, "glass", cx, cy, 0.8, 6.8, 6.8, 6.8, 20)
    for z in (3.6, 6.8):
        frustum(m, "company", cx, cy, z, z + 0.5, 7.1, 7.1, 20, top="roof" if z > 5 else None)
    frustum(m, "roof", cx, cy, 7.3, 8.3, 6.0, 3.0, 20, top="company")


def pier(m):
    """APT_PIER: a corridor along x from the terminal to the concourse."""
    ground_apron(m)
    m.box("concrete", -8, 6.5, -0.2, 3.2, SLAB, 4.2)
    m.box("glass", -8, 6.5, -0.28, 3.28, 1.2, 3.4)
    m.box("company", -8, 6.5, -0.4, 3.4, 4.2, 4.6)


def jetway(m, a, b):
    """An airbridge on legs from a to b (ground points), with a cab at b."""
    h0, h1 = 3.6, 5.6
    beam(m, "concrete", (a[0], a[1], (h0 + h1) / 2), (b[0], b[1], (h0 + h1) / 2), 2.0)
    beam(m, "company", (a[0], a[1], h1 + 0.1), (b[0], b[1], h1 + 0.1), 2.1)
    beam(m, "glass", (a[0], a[1], h0 + 1.2), (b[0], b[1], h0 + 1.2), 2.08)
    m.box("dark", b[0] - 1.3, b[0] + 1.3, b[1] - 1.3, b[1] + 1.3, h0 - 0.2, h1 + 0.3)
    mx, my = (a[0] * 0.3 + b[0] * 0.7), (a[1] * 0.3 + b[1] * 0.7)
    for d in (-0.6, 0.6):
        m.box("metal", mx - 0.18 + d, mx + 0.18 + d, my - 0.18, my + 0.18, SLAB, h0)
    m.box("tyre", mx - 1.0, mx + 1.0, my - 0.4, my + 0.4, SLAB, 0.7)


def stand(m, jet=None, edges=()):
    ground_apron(m)
    stand_marking(m)
    if jet:
        jetway(m, *jet)
    fences(m, edges)


def tower(m, grass=False, edges=()):
    """A control tower with a glass cab on top."""
    if grass:
        ground_grass(m)
    else:
        ground_apron(m)
    m.box("concrete", -4, 4, -4, 4, SLAB, 3.5)
    m.windows("glass", -4, 4, -4, 4, SLAB, 3.5, 1, 2, size=(1.6, 1.4))
    m.box("company", -4.2, 4.2, -4.2, 4.2, 3.5, 3.9)
    frustum(m, "concrete", 0, 0, 3.9, 16, 1.8, 1.4, 8)
    frustum(m, "concrete", 0, 0, 16, 17, 2.0, 3.2, 8, rot=math.pi / 8)
    frustum(m, "glass", 0, 0, 17, 19.6, 3.2, 3.6, 8, rot=math.pi / 8)
    frustum(m, "company", 0, 0, 19.6, 20.4, 3.8, 3.8, 8, top="roof", rot=math.pi / 8)
    m.box("metal", -0.1, 0.1, -0.1, 0.1, 20.4, 23)
    m.box("infra_red", -0.2, 0.2, -0.2, 0.2, 23, 23.3)
    fences(m, edges)


def radar(m, edges=()):
    """A radar on a mast, on grass."""
    ground_grass(m)
    m.box("concrete", -2.5, 2.5, -2.5, 2.5, SLAB, 0.6)
    beam(m, "metal", (0, 0, 0.6), (0, 0, 5.2), 0.5)
    m.box("dark", -0.7, 0.7, -0.7, 0.7, 5.2, 6.0)
    # The radar antenna: a wide curved screen, seen facing south-west.
    pts = []
    for i in range(7):
        a = math.radians(-60 + 20 * i)
        pts.append((0.8 - 1.2 * (1 - math.cos(a)), 4.2 * math.sin(a)))
    for i in range(6):
        (xa, ya), (xb, yb) = pts[i], pts[i + 1]
        m.quad("infra_white", (xa, ya, 5.7), (xb, yb, 5.7), (xb - 0.5, yb, 8.0), (xa - 0.5, ya, 8.0))
        m.quad("metal", (xb, yb, 5.7), (xa, ya, 5.7), (xa - 0.5, ya, 8.0), (xb - 0.5, yb, 8.0))
    beam(m, "metal", (0, 0, 6.0), (0.4, 0, 6.8), 0.25)
    m.box("concrete", -6, -3, 3, 6, SLAB, 2.4)  # equipment hut
    m.box("company", -6.2, -2.8, 2.8, 6.2, 2.4, 2.7)
    fences(m, edges)


def radio_mast(m, height, base=2.6):
    """A tapered red and white lattice mast standing at the origin."""
    top = 0.35
    legs = [(1, 1), (-1, 1), (-1, -1), (1, -1)]
    levels = 8
    for k in range(levels):
        z0 = height * k / levels
        z1 = height * (k + 1) / levels
        r0 = base + (top - base) * k / levels
        r1 = base + (top - base) * (k + 1) / levels
        mat = "infra_red" if k % 2 == 0 else "infra_white"
        for (sx, sy) in legs:
            beam(m, mat, (sx * r0, sy * r0, z0), (sx * r1, sy * r1, z1), 0.28)
        for i in range(4):
            (ax, ay), (bx, by) = legs[i], legs[(i + 1) % 4]
            beam(m, "metal", (ax * r0, ay * r0, z0), (bx * r1, by * r1, z1), 0.12)
            beam(m, "metal", (ax * r1, ay * r1, z1), (bx * r1, by * r1, z1), 0.14)
    m.box("infra_red", -0.2, 0.2, -0.2, 0.2, height, height + 3)
    m.box("light", -0.25, 0.25, -0.25, 0.25, height + 3, height + 3.4)


def radio_tower(m):
    """APT_RADIO_TOWER_FENCE_NE: a radio mast on grass with a hut."""
    ground_grass(m)
    m.box("concrete", -3.2, 3.2, -3.2, 3.2, SLAB, 0.5)
    radio_mast(m, 20, 2.4)
    m.box("concrete", 3.5, 6.5, -6.5, -3.5, SLAB, 2.4)
    m.box("company", 3.3, 6.7, -6.7, -3.3, 2.4, 2.7)
    fence(m, "ne")


def hangar(m, w=8, h_wall=6.0, h_top=9.5, small=False):
    """A hangar with the door to +y (south-east), as the depots of the base airports."""
    if small:
        slab(m, "infra_gravel")
    else:
        ground_apron(m)
    wall = "metal" if small else "concrete"
    t = 1.2
    y0, y1 = -7.6, 7.6
    m.box(wall, -w, -w + t, y0, y1, SLAB, h_wall)
    m.box(wall, w - t, w, y0, y1, SLAB, h_wall)
    m.box(wall, -w, w, y0, y0 + 0.6, SLAB, h_wall)
    m.box("dark", -w + t, w - t, y0 + 0.6, y0 + 0.7, SLAB, h_wall)  # inside of the back wall
    # Arched roof across x, along the whole length.
    n = 10
    arch = []
    for i in range(n + 1):
        a = math.pi * i / n
        arch.append((-w * math.cos(a), h_wall + (h_top - h_wall) * math.sin(a)))
    roof = "company" if small else "roof"
    for i in range(n):
        (xa, za), (xb, zb) = arch[i], arch[i + 1]
        m.quad(roof, (xa, y1, za), (xa, y0, za), (xb, y0, zb), (xb, y1, zb))
        m.quad("dark", (xb, y1 - 0.01, zb - 0.1), (xb, y0, zb - 0.1), (xa, y0, za - 0.1), (xa, y1 - 0.01, za - 0.1))
    # Gable ends: closed at the back, a company-coloured header over the door at the front.
    for y, mat in ((y0, wall), (y1, "company")):
        pts = [(x, y, z) for x, z in arch]
        face(m, mat, [(w, y, h_wall)] + pts[1:-1] + [(-w, y, h_wall)], (0, -y * 2, h_wall))
    m.box("company", -w, w, y1 - 0.3, y1, h_wall - 1.0, h_wall)
    # Door leaves pushed to the sides.
    for s in (-1, 1):
        m.box("company_dark", s * (w - t) - (1.6 if s > 0 else 0), s * (w - t) + (0 if s > 0 else 1.6), y1 - 0.4, y1 - 0.1, SLAB, h_wall - 1.0)
    if not small:
        m.windows("glass", -w, w, y0, y1, 2.5, 5.0, 1, 4, size=(1.6, 1.2))
    for x in (-3, 3):
        up(m, "infra_yellow", x - 0.12, x + 0.12, 0, 8)


def helipad(m, raised=False, edges=()):
    """A helicopter landing pad with an H."""
    ground_apron(m)
    z = MARK
    if raised:
        _ground_at(m, SLAB).poly(None, [(-7, -7), (7, -7), (7, 7), (-7, 7)])
        sides(m, "concrete", -7, 7, -7, 7, SLAB, 0.75)
        sides(m, "infra_yellow", -7, 7, -7, 7, 0.75, 0.9)
        Ground(m, 0.9, "concrete", -7, 7, -7, 7)
        z = 0.92
        for x in (-7.2, 7.2):
            for y in (-7.2, 7.2):
                m.box("light", x - 0.2, x + 0.2, y - 0.2, y + 0.2, 0.9, 1.15)
    disc(m, "infra_runway", 0, 0, 6.2, z, 20)
    ring(m, "infra_white", 0, 0, 5.4, 6.0, z + 0.01)
    for y in (-1.5, 1.5):
        up(m, "infra_white", -2.6, 2.6, y - 0.4, y + 0.4, z + 0.02)
    up(m, "infra_white", -0.4, 0.4, -1.5, 1.5, z + 0.02)
    fences(m, edges)


def low_building(m, edges=()):
    """The helidepot office: a low office block with a company stripe."""
    ground_apron(m)
    m.box("wall", -5, 5, -5, 5, SLAB, 6.2)
    m.box("company", -5.1, 5.1, -5.1, 5.1, 3.0, 3.5)
    m.windows("glass", -5, 5, -5, 5, SLAB + 0.3, 6.0, 2, 3, size=(1.6, 1.3))
    m.box("door", 5.0, 5.1, -0.7, 0.7, SLAB, 2.4)
    m.box("concrete", -5.3, 5.3, -5.3, 5.3, 6.2, 6.6)
    m.box("metal", -2, 1, -2, 1, 6.6, 7.6)
    fences(m, edges)


def windsock(m, edges=()):
    """APT_GRASS_FENCE_NE_FLAG: grass with a windsock."""
    ground_grass(m)
    x, y = -3.5, 3.5
    m.box("metal", x - 0.12, x + 0.12, y - 0.12, y + 0.12, SLAB, 6.5)
    # The sock blows towards +x, tapering.
    for i, mat in enumerate(("infra_orange", "infra_white", "infra_orange", "infra_white", "infra_orange")):
        r0 = 0.8 - 0.1 * i
        r1 = r0 - 0.1
        x0 = x + 0.2 + 0.7 * i
        z0 = 6.1 - 0.12 * i
        beam(m, mat, (x0, y, z0), (x0 + 0.7, y, z0 - 0.12), (r0 + r1))
    fences(m, edges)


def small_building(m, which):
    """The country airfield's buildings: 1 the terminal with a lookout, 2 a waiting hall, 3 a fuel store."""
    slab(m, "infra_gravel")
    if which == 1:
        m.box("wall", -7, 6, -7, 5, SLAB, 6.4)
        m.windows("glass", -7, 6, -7, 5, SLAB + 0.3, 6.2, 2, 3, size=(1.5, 1.3))
        m.prism_roof("company", "wall", -7.4, 6.4, -7.4, 5.4, 6.4, 8.6)
        m.box("wall", -2, 2, -3.5, 0.5, 6.4, 10)
        m.box("glass", -2.1, 2.1, -3.6, 0.6, 10, 11.6)
        m.box("company", -2.4, 2.4, -3.9, 0.9, 11.6, 12.0)
        m.box("door", 6.0, 6.1, 1, 2.6, SLAB, 2.4)
    elif which == 2:
        m.box("wood", -5, 4, -6, 6, SLAB, 4.2)
        m.windows("glass", -5, 4, -6, 6, SLAB + 0.5, 3.6, 1, 3, size=(1.6, 1.2))
        m.prism_roof("slate", "wood", -5.4, 4.4, -6.4, 6.4, 4.2, 6.2)
        m.box("company", 4.0, 6.5, -5, 5, 2.9, 3.1)  # awning
        for y in (-4.8, 4.6):
            m.box("metal", 6.2, 6.4, y, y + 0.2, SLAB, 2.9)
        m.box("door", 4.0, 4.1, -0.7, 0.7, SLAB, 2.4)
    else:
        for y in (-4, 0.5):
            m.cylinder("infra_white", -5, 2, y, 1.9, 1.7, sides=12, caps="metal")
            for x in (-4, 1):
                m.box("dark", x - 0.2, x + 0.2, y - 1, y + 1, SLAB, 0.4)
        m.box("brick", 3, 7, -6, 6, SLAB, 3.2)
        m.box("company", 2.8, 7.2, -6.2, 6.2, 3.2, 3.5)
        m.box("door", 7.0, 7.1, -1, 1, SLAB, 2.2)
        m.box("company", 6, 6.6, 4.6, 5.2, SLAB, 1.6)  # fuel pump


def heliport(m):
    """APT_HELIPORT: a tall building with a landing pad on the roof, at 60 z units like the 2D game."""
    ground_grass(m)
    top = 61 * Z - 0.3
    m.box("concrete", -7, 7, -7, 7, SLAB, 1.0)
    storeys = 7
    bands = []
    for k in range(storeys):
        z = 1.0 + (k + 0.5) * (top - 1.4) / storeys
        bands.append((z - 1.0, z + 1.0))
    banded(m, "wall", -6.5, 6.5, -6.5, 6.5, 1.0, top - 0.4, bands)
    for x in (-6.7, 6.0):
        for y in (-6.7, 6.0):
            m.box("company", x, x + 0.7, y, y + 0.7, 1.0, top)
    m.box("door", 6.5, 6.6, -1.2, 1.2, 1.0, 3.4)
    sides(m, "company", -7.3, 7.3, -7.3, 7.3, top - 0.4, top + 0.05)
    m.quad("company", (-7.3, 7.3, top - 0.4), (7.3, 7.3, top - 0.4), (7.3, -7.3, top - 0.4), (-7.3, -7.3, top - 0.4))
    Ground(m, top + 0.05, "company", -7.3, 7.3, -7.3, 7.3)
    disc(m, "infra_runway", 0, 0, 6.0, top + 0.07, 20)
    ring(m, "infra_white", 0, 0, 5.2, 5.8, top + 0.08)
    for y in (-1.5, 1.5):
        up(m, "infra_white", -2.6, 2.6, y - 0.4, y + 0.4, top + 0.09)
    up(m, "infra_white", -0.4, 0.4, -1.5, 1.5, top + 0.09)
    for x in (-7.1, 6.9):
        for y in (-7.1, 6.9):
            m.box("light", x, x + 0.2, y, y + 0.2, top, top + 0.3)


# ---------------------------------------------------------------------------------------------------
# The airport tiles. Each entry: gfx id -> (model name, builder). Ids sharing a name share the model.

def _apron(*edges):
    def build(m):
        ground_apron(m)
        fences(m, edges)
    return build


def _taxi(lines, *edges):
    def build(m):
        ground_apron(m)
        taxi_lines(m, lines)
        fences(m, edges)
    return build


def _runway(kind, *edges):
    def build(m):
        runway(m, kind)
        fences(m, edges)
    return build


def _grass(*edges, pad=None):
    def build(m):
        ground_grass(m)
        if pad == "stand":
            up(m, "infra_gravel", -6.5, 6.5, -7, 7)
            stripe(m, "infra_white", (-8, 0), (4, 0), 0.3)
        elif pad == "taxi":
            up(m, "infra_gravel", -5, 5, -8, 8)
        fences(m, edges)
    return build


def _with(fn, *args, **kw):
    return lambda m: fn(m, *args, **kw)


AIRPORT_TILES = {
    0: ("apron", _apron()),
    1: ("apron_fence_nw", _apron("nw")),
    2: ("apron_fence_sw", _apron("sw")),
    3: ("stand", _with(stand)),
    4: ("taxi_w", _taxi([("y", 4)])),
    5: ("taxi_s", _taxi([("x", 4)])),
    6: ("taxi_xing_s", _taxi([("y", 0), ("x", 4)])),
    7: ("taxi_xing_w", _taxi([("x", 0), ("y", 4)])),
    8: ("taxi_ver", _taxi([("y", 0)])),
    9: ("taxi_xing_e", _taxi([("x", 0), ("y", -4)])),
    10: ("taxi_e", _taxi([("y", -4)])),
    11: ("taxi_n", _taxi([("x", -4)])),
    12: ("taxi_hor", _taxi([("x", 0)])),
    13: ("taxi_n_fence_sw", _taxi([("x", -4)], "sw")),
    14: ("runway_exit_a", _runway("a", "se")),
    15: ("runway_fence_se", _runway("plain", "se")),
    16: ("runway_exit_c", _runway("c", "se")),
    17: ("runway_exit_d", _runway("d", "se")),
    18: ("runway_end_fence_se", _runway("end", "se")),
    19: ("terminal_2", building_2),
    20: ("tower_fence_sw", _with(tower, grass=True, edges=("sw",))),
    21: ("round_terminal", round_terminal),
    22: ("terminal_3", building_3),
    23: ("terminal_1", building_1),
    24: ("hangar", _with(hangar)),
    25: ("stand_jetway_1", _with(stand, jet=((0.5, 8), (0.5, 2.5)), edges=("nw",))),
    26: ("stand_jetway_2", _with(stand, jet=((-8, 0.5), (-3.0, 0.5)))),
    27: ("apron_jetway_3", lambda m: (ground_apron(m), jetway(m, (-3.5, -8), (-3.5, -3.0)))),
    28: ("pier", pier),
    29: ("grass", _grass()),
    30: ("grass_fence_ne", _grass("ne")),
    31: ("radar_fence_sw", _with(radar, edges=("sw",))),
    32: ("radio_tower_fence_ne", radio_tower),
    33: ("small_building_3", _with(small_building, 3)),
    34: ("small_building_2", _with(small_building, 2)),
    35: ("small_building_1", _with(small_building, 1)),
    36: ("grass_taxi_fence_sw", _grass("sw", pad="taxi")),
    37: ("grass_stand", _grass(pad="stand")),
    38: ("grass_stand", _grass(pad="stand")),
    39: ("windsock_fence_ne", _with(windsock, edges=("ne",))),
    40: ("small_runway_near_end", lambda m: (small_runway(m, "near"), fence(m, "se"))),
    41: ("small_runway", lambda m: (small_runway(m), fence(m, "se"))),
    42: ("small_runway_far_end", lambda m: (small_runway(m, "far"), fence(m, "se"))),
    43: ("small_hangar", _with(hangar, w=7.4, h_wall=5.0, h_top=8.0, small=True)),
    44: ("heliport", heliport),
    45: ("runway_end", _runway("end")),
    46: ("runway", _runway("plain")),
    47: ("tower", _with(tower)),
    48: ("apron_fence_ne", _apron("ne")),
    49: ("runway_end_fence_nw", _runway("end", "nw")),
    50: ("runway_fence_nw", _runway("plain", "nw")),
    51: ("radar_fence_sw", _with(radar, edges=("sw",))),
    52: ("radar_fence_ne", _with(radar, edges=("ne",))),
    53: ("helipad_fence_sw", _with(helipad, edges=("sw",))),
    54: ("helipad_fence_nw", _with(helipad, edges=("nw",))),
    55: ("helipad", _with(helipad)),
    56: ("apron_fence_ne_sw", _apron("ne", "sw")),
    57: ("runway_end_fence_nw_sw", _runway("end", "nw", "sw")),
    58: ("runway_end_fence_se_sw", _runway("end", "se", "sw")),
    59: ("runway_end_fence_ne_nw", _runway("end", "ne", "nw")),
    60: ("runway_end_fence_ne_se", _runway("end", "ne", "se")),
    61: ("helipad_fence_ne_se", _with(helipad, edges=("ne", "se"))),
    62: ("apron_fence_se_sw", _apron("se", "sw")),
    63: ("low_building_fence_ne_nw", _with(low_building, edges=("ne", "nw"))),
    64: ("low_building_fence_nw", _with(low_building, edges=("nw",))),
    65: ("apron_fence_se", _apron("se")),
    66: ("helipad_raised_fence_se_sw", _with(helipad, raised=True, edges=("se", "sw"))),
    67: ("helipad_raised_fence_nw_sw", _with(helipad, raised=True, edges=("nw", "sw"))),
    68: ("helipad_raised_fence_nw", _with(helipad, raised=True, edges=("nw",))),
    69: ("low_building", _with(low_building)),
    70: ("apron_fence_ne_se", _apron("ne", "se")),
    71: ("apron_half_east", _with(half_apron, True)),
    72: ("apron_half_west", _with(half_apron, False)),
    73: ("windsock_fence_ne", _with(windsock, edges=("ne",))),
}


# ---------------------------------------------------------------------------------------------------
# Docks, buoy and depots.

def dock_shore():
    """Dock id 0: a concrete ramp down the sloped shore; land at -x (z = 0 at the top), water at +x."""
    m = Model()
    drop = 8 * Z  # the slope goes down one height level across the tile
    y0, y1 = -4, 4

    def ground(x):
        return -drop * (x + 8) / 16

    def deck(x):
        return 0.25 - (drop - 1.1) * (x + 8) / 16

    xs = [-8, 8]
    c = (0, 0, -drop / 2)
    for y, s in ((y0, -1), (y1, 1)):
        face(m, "concrete", [(xs[0], y, ground(xs[0]) - 0.3), (xs[1], y, ground(xs[1]) - 0.3), (xs[1], y, deck(xs[1])), (xs[0], y, deck(xs[0]))], (0, -s * 10, c[2]))
    face(m, "concrete", [(8, y0, ground(8) - 0.3), (8, y1, ground(8) - 0.3), (8, y1, deck(8)), (8, y0, deck(8))], (-10, 0, c[2]))
    face(m, "concrete", [(-8, y0, deck(-8)), (-8, y1, deck(-8)), (-8, y1, -0.3), (-8, y0, -0.3)], (10, 0, c[2]))
    # Deck surface in steps of planking, sloping down to the water.
    face(m, "infra_gravel", [(-8, y0, deck(-8)), (8, y0, deck(8)), (8, y1, deck(8)), (-8, y1, deck(-8))], (0, 0, -20))
    for i in range(1, 8):
        x = -8 + 2 * i
        stripe(m, "concrete", (x, y0 + 0.3), (x, y1 - 0.3), 0.18, deck(x) + 0.02)
    # Railings in company colour along both sides.
    for y in (y0 + 0.15, y1 - 0.15):
        for x in (-7, -3, 1, 5):
            m.box("metal", x - 0.1, x + 0.1, y - 0.1, y + 0.1, deck(x), deck(x) + 1.3)
        beam(m, "company", (-8, y, deck(-8) + 1.3), (8, y, deck(8) + 1.3), 0.14)
    # A small harbour office at the top of the ramp, next to it.
    m.box("wall", -8, -4.5, 4.4, 7.6, -1.0, 3.4)
    m.prism_roof("tiles", "wall", -8.2, -4.3, 4.2, 7.8, 3.4, 4.8)
    m.box("glass", -4.48, -4.4, 5.2, 6.8, 1.0, 2.6)
    m.box("company", -6.6, -5.9, 4.3, 4.4, 0.6, 2.7)
    m.save(f"{GROUP}_dock_shore.glb")
    return f"{GROUP}_dock_shore.glb"


def dock_water():
    """Dock id 1: a jetty on piles over the water; the shore is at -x, the open water at +x."""
    m = Model()
    y0, y1 = -4, 4
    zd = 1.35  # meets the lower end of the shore part's deck
    for x in (-6, -2, 2, 6):
        for y in (y0 + 0.5, y1 - 0.5):
            frustum(m, "wood", x, y, -1.5, zd - 0.3, 0.35, 0.35, 8)
    sides(m, "concrete", -8, 8, y0, y1, zd - 0.45, zd)
    m.quad("concrete", (-8, y1, zd - 0.45), (8, y1, zd - 0.45), (8, y0, zd - 0.45), (-8, y0, zd - 0.45))
    g = Ground(m, zd, "concrete", -8, 8, y0, y1)
    g.poly("infra_gravel", [(-8, y0 + 0.3), (8, y0 + 0.3), (8, y1 - 0.3), (-8, y1 - 0.3)])
    up(m, "infra_yellow", -8, 8, y0 + 0.3, y0 + 0.55, zd + 0.03)
    up(m, "infra_yellow", -8, 8, y1 - 0.55, y1 - 0.3, zd + 0.03)
    up(m, "infra_yellow", 7.45, 7.7, y0 + 0.3, y1 - 0.3, zd + 0.03)
    for x in (-5, 0, 5):
        for y in (y0 + 0.4, y1 - 0.4):
            frustum(m, "dark", x, y, zd, zd + 0.6, 0.25, 0.22, 8, top="dark")
    # Fenders on the piles.
    for y, s in ((y0 - 0.12, -1), (y1 + 0.12, 1)):
        for x in (-4, 2.5):
            m.box("tyre", x - 0.4, x + 0.4, y - 0.12, y + 0.12, zd - 1.4, zd - 0.3)
    # A small crane at the shore end.
    m.box("company", -7.4, -5.6, -1.2, 1.2, zd, zd + 1.2)
    beam(m, "company", (-6.5, 0, zd + 1.2), (-6.5, 0, zd + 5.5), 0.5)
    beam(m, "company", (-6.5, 0, zd + 5.3), (-1.0, -2.6, zd + 6.5), 0.35)
    beam(m, "metal", (-1.0, -2.6, zd + 6.4), (-1.0, -2.6, zd + 3.0), 0.06)
    m.box("dark", -1.25, -0.75, -2.85, -2.35, zd + 2.6, zd + 3.0)
    m.box("glass", -7.3, -6.6, -0.6, 0.6, zd + 1.2, zd + 2.2)
    finish(m)
    m.save(f"{GROUP}_dock_water.glb")
    return f"{GROUP}_dock_water.glb"


def buoy():
    m = Model()
    frustum(m, "infra_red", 0, 0, -0.4, 0.5, 1.0, 1.0, 12, bottom=True)
    frustum(m, "infra_white", 0, 0, 0.5, 1.0, 1.0, 0.8, 12)
    frustum(m, "infra_red", 0, 0, 1.0, 2.6, 0.8, 0.25, 12, top="infra_red")
    m.box("metal", -0.06, 0.06, -0.06, 0.06, 2.6, 3.2)
    m.box("light", -0.18, 0.18, -0.18, 0.18, 3.2, 3.55)
    m.save(f"{GROUP}_buoy.glb")
    return f"{GROUP}_buoy.glb"


def track(m, x0, x1, z=0.0):
    """A plain track along x: sleepers and two rails 2.4 apart."""
    x = x0 + 0.5
    while x < x1:
        m.box("wood", x - 0.3, x + 0.3, -1.7, 1.7, z, z + 0.12)
        x += 1.3
    for y in (-1.2, 1.2):
        m.box("metal", x0, x1, y - 0.08, y + 0.08, z + 0.12, z + 0.32)


def rail_depot():
    """A brick engine shed with the door to +x and the track running out of it."""
    m = Model()
    x0, x1, y0, y1, h = -7.5, 4.5, -6, 6, 6.0
    track(m, -7, 8)
    m.box("brick", x0, x1, y0, y0 + 0.7, 0, h)
    m.box("brick", x0, x1, y1 - 0.7, y1, 0, h)
    m.box("brick", x0, x0 + 0.7, y0, y1, 0, h)
    m.box("dark", x0 + 0.7, x0 + 0.8, y0 + 0.7, y1 - 0.7, 0, h)
    for y in (y0 + 0.7, y1 - 0.8):
        m.box("dark", x0 + 0.7, x1 - 0.2, y, y + 0.1, 0, h)
    m.box("dark", x0 + 0.7, x1, y0 + 0.7, y1 - 0.7, h - 0.1, h)
    m.box("brick", x1 - 0.7, x1, y0, y1, h - 1.3, h)  # lintel over the door
    for y in (y0, y1 - 1.6):
        m.box("brick", x1 - 0.7, x1, y, y + 1.6, 0, h)
    m.box("company", x1, x1 + 0.12, -3.6, 3.6, h - 1.3, h - 0.9)
    for ya, yb in ((-4.4, -3.2), (3.2, 4.4)):  # door leaves folded back
        m.box("company_dark", x1 + 0.1, x1 + 0.25, ya, yb, 0, h - 1.4)
    m.prism_roof("slate", "brick", x0 - 0.3, x1 + 0.3, y0 - 0.4, y1 + 0.4, h, h + 3.2)
    m.box("slate", -3, 1, -0.8, 0.8, h + 2.6, h + 3.8)  # smoke vent
    for x in (-5, -1.5, 2):
        for y in (y0 - 0.06, y1):
            m.box("glass", x - 0.7, x + 0.7, y, y + 0.06, 2.0, 4.2)
    m.save(f"{GROUP}_rail_depot.glb")
    return f"{GROUP}_rail_depot.glb"


def road_depot(kind="road"):
    """A garage for road vehicles, the door to +x. kind "trolley" is a trolleybus garage, with the wire pairs of both
    lanes running in through the door; "tram" is a tram shed, with a track in each lane and their contact wires."""
    m = Model()
    x0, x1, y0, y1, h = -7, 4, -6, 6, 5.2
    m.box("concrete", x1, 8, -4.2, 4.2, 0, 0.08)
    m.box("wall", x0, x1, y0, y0 + 0.6, 0, h)
    m.box("wall", x0, x1, y1 - 0.6, y1, 0, h)
    m.box("wall", x0, x0 + 0.6, y0, y1, 0, h)
    m.box("dark", x0 + 0.6, x0 + 0.7, y0 + 0.6, y1 - 0.6, 0, h)
    for y in (y0 + 0.6, y1 - 0.7):
        m.box("dark", x0 + 0.6, x1 - 0.2, y, y + 0.1, 0, h)
    m.box("dark", x0 + 0.6, x1, y0 + 0.6, y1 - 0.6, h - 0.1, h)
    for y in (y0, y1 - 1.8):
        m.box("wall", x1 - 0.6, x1, y, y + 1.8, 0, h)
    m.box("wall", x1 - 0.6, x1, y0, y1, 3.8, h)
    m.box("company_dark", x1 - 0.5, x1 - 0.1, -4.2, 4.2, 3.0, 3.8)  # rolled-up door
    m.box("company", x0 - 0.2, x1 + 0.2, y0 - 0.2, y1 + 0.2, h, h + 0.7)
    m.box("roof", x0, x1, y0, y1, h + 0.7, h + 0.8)
    m.windows("glass", x0, x1 - 1, y0, y1, 1.8, 3.6, 1, 3, size=(1.5, 1.2))
    name = "road_depot" if kind == "road" else f"{kind}_depot"
    if kind != "road":
        from models_track import CONTACT, LANE, PAIR
        # The door is raised for the poles and pantographs; the wires go in through it to the back wall.
        m.box("wall", x1 - 0.6, x1, y0, y1, 4.9, h)
        m.box("dark", x1 - 0.5, x1 - 0.1, -4.2, 4.2, 4.3, 4.9)
        m.box("company", x1, x1 + 0.3, -4.4, 4.4, CONTACT + 0.1, CONTACT + 0.3)  # bracket holding the wires
        for lane in (-LANE, LANE):
            wires_y = (lane - PAIR, lane + PAIR) if kind == "trolley" else (lane,)
            for y in wires_y:
                m.box("dark", x0 + 1.0, 8, y - 0.06, y + 0.06, CONTACT - 0.06, CONTACT + 0.06)
            if kind == "tram":
                for y in (lane - 0.75, lane + 0.75):
                    m.box("track_rail", x0 + 1.0, 8, y - 0.12, y + 0.12, 0.04, 0.12)
    m.save(f"{GROUP}_{name}.glb")
    return f"{GROUP}_{name}.glb"


def ship_depot():
    """A ship shed over the water, 32 long along x and 16 wide; ships enter along x."""
    m = Model()
    x0, x1 = -16, 16
    h = 7.5
    for s in (-1, 1):
        ya, yb = (4.6, 7.8) if s > 0 else (-7.8, -4.6)
        m.box("concrete", x0, x1, ya, yb, -1.0, 0.6)
        m.box("brick", x0 + 0.5, x1 - 0.5, ya, yb, 0.6, h)
        m.windows("glass", x0 + 0.5, x1 - 0.5, ya, yb, 2, h - 1, 1, 6, size=(1.8, 2.0))
        for x in (x0, x1 - 1.0):
            m.box("company", x, x + 1.0, ya - 0.1, yb + 0.1, 0.6, h + 0.2)
    m.box("dark", x0 + 0.5, x1 - 0.5, -4.6, 4.6, h - 0.1, h)  # ceiling over the water
    m.box("dark", x0 + 0.5, x1 - 0.5, -4.7, -4.6, 0.6, h)
    m.box("dark", x0 + 0.5, x1 - 0.5, 4.6, 4.7, 0.6, h)
    m.prism_roof("slate", "brick", x0 - 0.3, x1 + 0.3, -8.2, 8.2, h, h + 4.2)
    for x in (x0, x1 - 0.6):
        m.box("company", x, x + 0.6, -4.6, 4.6, h - 1.2, h)  # door lintels
    m.box("slate", -6, 6, -0.6, 0.6, h + 3.7, h + 4.6)  # roof vent
    m.save(f"{GROUP}_ship_depot.glb")
    return f"{GROUP}_ship_depot.glb"


# ---------------------------------------------------------------------------------------------------
# Objects.

def transmitter():
    m = Model()
    m.box("concrete", -3.6, 3.6, -3.6, 3.6, 0, 0.4)
    radio_mast(m, 30, 3.0)
    for (x, y) in ((1, 0), (0, 1), (-1, 0), (0, -1)):
        beam(m, "metal", (x * 7.5, y * 7.5, 0.2), (x * 0.6, y * 0.6, 22), 0.06)  # guy wires
        m.box("concrete", x * 7.5 - 0.4, x * 7.5 + 0.4, y * 7.5 - 0.4, y * 7.5 + 0.4, 0, 0.4)
    m.box("concrete", 3.8, 7, 3.8, 7, 0, 2.6)
    m.box("metal", 3.6, 7.2, 3.6, 7.2, 2.6, 2.9)
    m.box("door", 7.0, 7.1, 4.8, 6.0, 0, 2.0)
    m.save(f"{GROUP}_transmitter.glb")
    return f"{GROUP}_transmitter.glb"


def lighthouse():
    m = Model()
    m.box("stone", -4.2, 4.2, -4.2, 4.2, 0, 0.8)
    bands = 5
    h = 18
    for k in range(bands):
        z0, z1 = 0.8 + h * k / bands, 0.8 + h * (k + 1) / bands
        r0, r1 = 3.0 - 1.0 * k / bands, 3.0 - 1.0 * (k + 1) / bands
        frustum(m, "infra_white" if k % 2 == 0 else "infra_red", 0, 0, z0, z1, r0, r1, 14)
    zt = 0.8 + h
    frustum(m, "dark", 0, 0, zt, zt + 0.4, 2.8, 2.8, 14, top="dark")
    for i in range(10):
        a = 2 * math.pi * i / 10
        m.box("metal", 2.6 * math.cos(a) - 0.06, 2.6 * math.cos(a) + 0.06, 2.6 * math.sin(a) - 0.06, 2.6 * math.sin(a) + 0.06, zt + 0.4, zt + 1.4)
    frustum(m, "metal", 0, 0, zt + 1.3, zt + 1.45, 2.65, 2.65, 14)
    frustum(m, "light", 0, 0, zt + 0.4, zt + 2.8, 1.5, 1.5, 10)
    frustum(m, "infra_red", 0, 0, zt + 2.8, zt + 4.2, 1.8, 0.2, 10, top="infra_red")
    m.box("metal", -0.06, 0.06, -0.06, 0.06, zt + 4.2, zt + 5.2)
    for k in range(3):
        z = 4 + k * 5
        m.box("glass", 2.85 - 0.12 * k, 3.0 - 0.12 * k, -0.4, 0.4, z, z + 1.2)
    # The keeper's cottage.
    m.box("wall", -7.5, -3.6, -7.5, -2.5, 0, 3.2)
    m.prism_roof("slate", "wall", -7.8, -3.3, -7.8, -2.2, 3.2, 5.0)
    m.box("door", -3.6, -3.5, -5.6, -4.4, 0, 2.2)
    m.save(f"{GROUP}_lighthouse.glb")
    return f"{GROUP}_lighthouse.glb"


def statue():
    """The company statue: a figure in company colour on a stone plinth, on a paved square."""
    m = Model()
    m.box("concrete", -7.6, 7.6, -7.6, 7.6, 0, 0.15)
    m.box("stone", -4.5, 4.5, -4.5, 4.5, 0.15, 0.8)
    m.box("stone", -3.5, 3.5, -3.5, 3.5, 0.8, 1.6)
    m.box("stone", -2.4, 2.4, -2.4, 2.4, 1.6, 5.4)
    m.box("company_dark", 2.4, 2.48, -1.4, 1.4, 3.0, 4.2)  # plaque
    m.box("stone", -2.7, 2.7, -2.7, 2.7, 5.4, 5.8)
    zb = 5.8
    # Figure, facing +x, one arm raised.
    for y in (-0.55, 0.55):
        m.box("company", -0.45, 0.45, y - 0.35, y + 0.35, zb, zb + 2.8)
    m.box("company", -0.6, 0.6, -1.2, 1.2, zb + 2.8, zb + 5.4)
    m.box("company", -0.4, 0.4, -0.5, 0.5, zb + 5.4, zb + 5.8)
    frustum(m, "company", 0, 0, zb + 5.8, zb + 7.0, 0.55, 0.55, 10, top="company")
    beam(m, "company", (0, -1.4, zb + 5.0), (0.4, -1.8, zb + 3.0), 0.5)
    beam(m, "company", (0, 1.4, zb + 5.0), (0.6, 1.8, zb + 7.5), 0.5)
    for x in (-6.5, 6.5):
        for y in (-6.5, 6.5):
            m.box("grass", x - 0.8, x + 0.8, y - 0.8, y + 0.8, 0.15, 0.6)
    m.save(f"{GROUP}_statue.glb")
    return f"{GROUP}_statue.glb"


def company_hq():
    """The company headquarters on 2x2 tiles: an office tower with company-coloured bands and a flag."""
    m = Model()
    m.box("concrete", -15, 15, -15, 15, 0, 0.2)
    # Low wing along the back.
    m.box("wall", -13, -3, -13, 13, 0.2, 7)
    m.windows("glass", -13, -3, -13, 13, 0.4, 6.8, 2, 4, size=(1.8, 1.6))
    m.box("company", -13.3, -2.7, -13.3, 13.3, 7, 7.6)
    # The main tower.
    x0, x1, y0, y1, h = -6, 8, -7, 7, 20
    banded(m, "company", x0, x1, y0, y1, 0.2, h, [(0.2 + 3.25 * k, 3.25 * (k + 1) - 0.3) for k in range(6)], inset=0.25)
    for x in (x0 - 0.2, x1 - 0.8):
        for y in (y0 - 0.2, y1 - 0.8):
            m.box("concrete", x, x + 1.0, y, y + 1.0, 0.2, h)
    m.box("company", x0 - 0.3, x1 + 0.3, y0 - 0.3, y1 + 0.3, h, h + 1.0)
    m.box("metal", -2, 4, -3, 3, h + 1.0, h + 2.6)
    # Entrance canopy and steps at the front.
    m.box("company", x1, x1 + 3.5, -3.5, 3.5, 3.0, 3.4)
    for y in (-3.2, 2.9):
        m.box("metal", x1 + 3.0, x1 + 3.3, y, y + 0.3, 0.2, 3.0)
    m.box("door", x1 + 0.05, x1 + 0.15, -1.5, 1.5, 0.2, 2.6)
    m.box("concrete", x1, x1 + 2.0, -3, 3, 0.2, 0.45)
    # Flagpole with a company flag.
    m.box("metal", 12.4, 12.6, 9.4, 9.6, 0.2, 13)
    m.box("company", 12.45, 12.55, 9.6, 12.6, 10.8, 12.8)
    # Hedges.
    for y in (-12.5, 11.5):
        m.box("grass", -1, 13, y, y + 1, 0.2, 1.1)
    m.save(f"{GROUP}_company_hq.glb")
    return f"{GROUP}_company_hq.glb"


# ---------------------------------------------------------------------------------------------------

def build():
    buildings = []
    files = {}
    for gfx, (name, fn) in AIRPORT_TILES.items():
        filename = f"{GROUP}_apt_{name}.glb"
        if filename not in files:
            m = Model()
            fn(m)
            finish(m)
            m.save(filename)
            files[filename] = []
        files[filename].append(gfx)
    for filename, ids in files.items():
        buildings.append({"type": "airport_tile", "ids": ids, "model": filename})
    buildings.append({"type": "dock", "ids": [0], "model": dock_shore()})
    buildings.append({"type": "dock", "ids": [1], "model": dock_water()})
    buildings.append({"type": "buoy", "ids": [0], "model": buoy()})
    buildings.append({"type": "rail_depot", "ids": [0], "model": rail_depot()})
    buildings.append({"type": "road_depot", "ids": [0], "model": road_depot()})
    buildings.append({"type": "road_depot", "ids": [1], "model": road_depot("trolley")})
    buildings.append({"type": "road_depot", "ids": [2], "model": road_depot("tram")})
    buildings.append({"type": "ship_depot", "ids": [0], "model": ship_depot()})
    buildings.append({"type": "object", "ids": [0], "model": transmitter()})
    buildings.append({"type": "object", "ids": [1], "model": lighthouse()})
    buildings.append({"type": "object", "ids": [2], "model": statue()})
    buildings.append({"type": "object", "ids": [4], "model": company_hq()})
    return {"vehicles": [], "buildings": buildings}
