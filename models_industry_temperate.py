"""Industry tiles of the temperate climate: coal mine, power station, sawmill, forest, oil refinery, oil rig,
farm, iron ore mine, oil wells, bank and steel mill. (The factory is in models_base.py.)

Every model is one tile, 16 by 16, front (+x) to the south-west. In an industry layout of build_industry.h a tile
at offset (dx, dy) sits dx tiles towards +x and dy tiles towards +y of the first tile, so the models are made to
fit together that way. Animated tiles keep one static model.
"""

import math

from gfx3d import MATERIALS, Model, rotated_z

GROUP = "industry_temperate"

MATERIALS.update({
    "indt_coal": (0.15, 0.14, 0.14),
    "indt_spoil": (0.40, 0.37, 0.34),
    "indt_steel": (0.36, 0.38, 0.42),
    "indt_redsteel": (0.58, 0.24, 0.17),
    "indt_yellow": (0.90, 0.74, 0.20),
    "indt_white": (0.93, 0.93, 0.91),
    "indt_earth": (0.50, 0.41, 0.28),
    "indt_sand": (0.70, 0.62, 0.45),
    "indt_ore": (0.58, 0.34, 0.22),
    "indt_ore_dark": (0.44, 0.26, 0.18),
    "indt_hay": (0.86, 0.75, 0.38),
    "indt_leaf": (0.20, 0.40, 0.17),
    "indt_leaf_dark": (0.13, 0.30, 0.13),
    "indt_bark": (0.36, 0.25, 0.16),
    "indt_log": (0.60, 0.44, 0.28),
    "indt_logend": (0.82, 0.68, 0.46),
    "indt_plank": (0.84, 0.72, 0.50),
    "indt_glow": (1.00, 0.55, 0.15),
    "indt_asphalt": (0.34, 0.34, 0.35),
    "indt_ceramic": (0.62, 0.46, 0.34),
    "indt_cow": (0.95, 0.94, 0.90),
})


def fname(name):
    return f"{GROUP}_{name}.glb"


# ---------------------------------------------------------------------------------------------------------------
# Shape helpers


def _sub(a, b):
    return [a[i] - b[i] for i in range(3)]


def _cross(u, v):
    return [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]]


def _unit(v):
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]


def poly_out(m, material, pts, centre):
    """A flat polygon (fan), turned so that it faces away from centre."""
    n = _cross(_sub(pts[1], pts[0]), _sub(pts[2], pts[0]))
    mid = [sum(p[i] for p in pts) / len(pts) for i in range(3)]
    if sum(n[i] * (mid[i] - centre[i]) for i in range(3)) < 0:
        pts = pts[::-1]
    for i in range(1, len(pts) - 1):
        m.triangle(material, pts[0], pts[i], pts[i + 1])


def beam(m, material, p0, p1, w, h=None):
    """A square bar from p0 to p1."""
    h = h or w
    u = _unit(_sub(p1, p0))
    helper = [0, 0, 1] if abs(u[2]) < 0.9 else [1, 0, 0]
    s = [x * w / 2 for x in _unit(_cross(u, helper))]
    t = [x * h / 2 for x in _unit(_cross(s, u))]

    def c(p, i, j):
        return tuple(p[k] + i * s[k] + j * t[k] for k in range(3))

    centre = [(p0[k] + p1[k]) / 2 for k in range(3)]
    ring = [(1, 1), (-1, 1), (-1, -1), (1, -1)]
    for k in range(4):
        (i0, j0), (i1, j1) = ring[k], ring[(k + 1) % 4]
        poly_out(m, material, [c(p0, i0, j0), c(p0, i1, j1), c(p1, i1, j1), c(p1, i0, j0)], centre)
    poly_out(m, material, [c(p0, i, j) for i, j in ring], centre)
    poly_out(m, material, [c(p1, i, j) for i, j in ring], centre)


def frustum(m, material, x, y, z0, z1, r0, r1, sides=10, top=None, rot=0.0, sy=1.0):
    """An upright cone or cylinder (r0 at the bottom, r1 at the top); a closed top unless r1 is 0."""
    top = top or material
    a = [(x + r0 * math.cos(rot + 2 * math.pi * i / sides), y + sy * r0 * math.sin(rot + 2 * math.pi * i / sides)) for i in range(sides)]
    b = [(x + r1 * math.cos(rot + 2 * math.pi * i / sides), y + sy * r1 * math.sin(rot + 2 * math.pi * i / sides)) for i in range(sides)]
    for i in range(sides):
        j = (i + 1) % sides
        if r1 > 0:
            m.quad(material, (a[i][0], a[i][1], z0), (a[j][0], a[j][1], z0), (b[j][0], b[j][1], z1), (b[i][0], b[i][1], z1))
            m.triangle(top, (x, y, z1), (b[i][0], b[i][1], z1), (b[j][0], b[j][1], z1))
        else:
            m.triangle(material, (a[i][0], a[i][1], z0), (a[j][0], a[j][1], z0), (x, y, z1))


def tank(m, material, x, y, z0, z1, r, sides=12, roof=None):
    """A round storage tank with a low conical roof."""
    frustum(m, material, x, y, z0, z1, r, r, sides)
    frustum(m, roof or material, x, y, z1, z1 + r * 0.25, r, 0, sides)


def heap(m, material, x, y, r, h, sides=8, sy=1.0, flat=0.35):
    """A pile of loose material: a flattened cone."""
    frustum(m, material, x, y, 0, h * 0.6, r, r * flat + r * 0.25, sides, sy=sy, rot=0.3)
    frustum(m, material, x, y, h * 0.6, h, r * flat + r * 0.25, r * flat * 0.4, sides, sy=sy, rot=0.3)


def ground(m, material, x0=-8, x1=8, y0=-8, y1=8, z=0.06):
    m.box(material, x0, x1, y0, y1, 0, z)


def railing(m, x0, x1, y0, y1, z, h=1.0, material="indt_yellow"):
    """A thin railing around a rectangle at height z."""
    for (a, b) in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
        beam(m, material, (a[0], a[1], z + h), (b[0], b[1], z + h), 0.15)
        beam(m, material, (a[0], a[1], z), (a[0], a[1], z + h), 0.15)


def lattice_tower(m, material, x, y, z0, z1, r0, r1, bays=4, w=0.3):
    """A four-legged steel tower, tapering from half-width r0 to r1, with cross bracing."""
    corners = [(1, 1), (-1, 1), (-1, -1), (1, -1)]

    def p(c, f):
        r = r0 + (r1 - r0) * f
        return (x + c[0] * r, y + c[1] * r, z0 + (z1 - z0) * f)

    for c in corners:
        beam(m, material, p(c, 0), p(c, 1), w)
    for k in range(bays):
        f0, f1 = k / bays, (k + 1) / bays
        for i in range(4):
            a, b = corners[i], corners[(i + 1) % 4]
            beam(m, material, p(a, f1), p(b, f1), w * 0.7)
            beam(m, material, p(a, f0), p(b, f1), w * 0.5)


def conifer(m, x, y, h, r):
    beam(m, "indt_bark", (x, y, 0), (x, y, h * 0.35), r * 0.25)
    frustum(m, "indt_leaf_dark", x, y, h * 0.2, h * 0.7, r, 0, 7, rot=x)
    frustum(m, "indt_leaf", x, y, h * 0.5, h, r * 0.7, 0, 7, rot=y)


def broadleaf(m, x, y, h, r):
    beam(m, "indt_bark", (x, y, 0), (x, y, h * 0.5), r * 0.25)
    frustum(m, "indt_leaf", x, y, h * 0.35, h * 0.7, r * 0.6, r, 8)
    frustum(m, "indt_leaf", x, y, h * 0.7, h, r, r * 0.3, 8)


def gable_roof_y(m, material, gable, x0, x1, y0, y1, z0, z1):
    """A pitched roof with its ridge along y."""
    xm = (x0 + x1) / 2
    m.quad(material, (x1, y0, z0), (x1, y1, z0), (xm, y1, z1), (xm, y0, z1))
    m.quad(material, (x0, y1, z0), (x0, y0, z0), (xm, y0, z1), (xm, y1, z1))
    m.triangle(gable, (x0, y0, z0), (x1, y0, z0), (xm, y0, z1))
    m.triangle(gable, (x1, y1, z0), (x0, y1, z0), (xm, y1, z1))


def log(m, x0, x1, y, z, r):
    m.cylinder("indt_log", x0, x1, y, z, r, sides=7, caps="indt_logend")


def conveyor(m, p0, p1, w=1.2):
    """A covered belt conveyor on a few legs."""
    beam(m, "indt_steel", p0, p1, w, 0.8)
    beam(m, "company_dark", (p0[0], p0[1], p0[2] + 0.5), (p1[0], p1[1], p1[2] + 0.5), w * 0.9, 0.4)
    n = max(1, int(math.dist(p0[:2], p1[:2]) / 6))
    for k in range(1, n + 1):
        f = k / (n + 1)
        q = [p0[i] + (p1[i] - p0[i]) * f for i in range(3)]
        if q[2] > 0.8:
            beam(m, "indt_steel", (q[0], q[1], 0), (q[0], q[1], q[2] - 0.4), 0.3)


# ---------------------------------------------------------------------------------------------------------------
# Coal mine: gfx 0/1 headframe, 2 screening plant beside it (+y), 3 bunker, 4 coal stock, 5 spoil heap, 6 coal yard.


def coal_headframe():
    m = Model()
    ground(m, "indt_earth")
    m.box("indt_coal", -7.5, 7.5, -7.5, 7.5, 0, 0.1)
    # Winding house at the back.
    m.box("brick", -7, -2, -6, 2, 0, 4.5)
    m.prism_roof("slate", "brick", -7.3, -1.7, -6.4, 2.4, 4.5, 6)
    m.windows("glass", -7, -2, -6, 2, 0.8, 4, 1, 2, size=(1.0, 1.6))
    # Headframe over the shaft, with sheave wheels on top.
    sx, sy = 2.5, -1.5
    m.box("concrete", sx - 3, sx + 3, sy - 3, sy + 3, 0, 0.6)
    lattice_tower(m, "indt_redsteel", sx, sy, 0.6, 15.5, 2.6, 1.0, bays=5, w=0.4)
    # Back legs leaning towards the winding house.
    for yy in (sy - 1.0, sy + 1.0):
        beam(m, "indt_redsteel", (-1.8, yy, 4.5), (sx - 0.6, yy, 15.5), 0.45)
    m.box("indt_redsteel", sx - 1.5, sx + 1.5, sy - 1.5, sy + 1.5, 15.3, 15.8)
    for yy in (sy - 0.7, sy + 0.7):
        m.cylinder("indt_steel", sx - 1.1, sx + 1.1, yy, 16.6, 0.25, sides=6)  # stand
    # The sheave wheels themselves are a moving part, see coal_sheave().
    # Ropes down to the winding house.
    for yy in (sy - 0.7, sy + 0.7):
        beam(m, "dark", (sx - 1.2, yy, 16.8), (-2.0, yy, 4.0), 0.08)
    # Pit-head cage house at the foot.
    m.box("company", sx - 2, sx + 4.5, sy + 3.2, sy + 7.5, 0, 3.4)
    m.prism_roof("slate", "company", sx - 2.2, sx + 4.7, sy + 3.0, sy + 7.7, 3.4, 4.6)
    m.box("door", sx + 4.5, sx + 4.6, sy + 4.5, sy + 6.2, 0, 2.4)
    m.save(fname("coal_headframe"))
    return fname("coal_headframe")


COAL_SHEAVES = [(2.5, -1.5 - 0.7, 16.8), (2.5, -1.5 + 0.7, 16.8)]


def coal_sheave():
    """One sheave wheel on top of the coal mine's headframe, turning around y while the mine works."""
    m = Model()
    m.sheave("dark", "indt_steel", 1.3, 0.3, count=4, sides=14)
    rotated_z(m, 1)
    m.save(fname("coal_sheave"))
    return fname("coal_sheave")


def coal_plant():
    """Screening and washing plant next to the headframe, with a conveyor rising to it."""
    m = Model()
    ground(m, "indt_earth")
    m.box("brick", -6, 6, -1, 7, 0, 7.5)
    m.prism_roof("slate", "brick", -6.3, 6.3, -1.4, 7.4, 7.5, 9.5)
    m.windows("glass", -6, 6, -1, 7, 1, 7, 2, 4, size=(1.1, 1.5))
    m.box("brick", 1, 4, 1.5, 4.5, 7.5, 12)  # boiler chimney stub
    m.box("dark", 0.8, 4.2, 1.3, 4.7, 11.5, 12)
    # Loading bay underneath: coal falls into wagons along the front.
    m.box("indt_steel", 2, 7.5, -6.5, -1, 3.5, 6)
    for x in (2.3, 7.2):
        for y in (-6.2, -1.3):
            beam(m, "indt_steel", (x, y, 0), (x, y, 3.5), 0.35)
    m.box("indt_coal", 2.5, 7, -6, -1.5, 0, 0.6)
    # Conveyor from the shaft (at -y, the headframe tile) up into the plant.
    conveyor(m, (-3, -8, 2.5), (-3, -1, 6.5))
    m.save(fname("coal_plant"))
    return fname("coal_plant")


def coal_bunker():
    """A coal bunker on legs, with a lorry loading space under it."""
    m = Model()
    ground(m, "indt_earth")
    m.box("indt_asphalt", -7, 7, -3.5, 3.5, 0.06, 0.12)
    for x in (-4, 4):
        for y in (-3, 3):
            beam(m, "indt_steel", (x, y, 0), (x, y, 5.5), 0.5)
    m.box("company_dark", -4.6, 4.6, -3.6, 3.6, 5.5, 10)
    # Hopper bottom.
    pts_top = [(-4.6, -3.6), (4.6, -3.6), (4.6, 3.6), (-4.6, 3.6)]
    pts_bot = [(-1.5, -1.2), (1.5, -1.2), (1.5, 1.2), (-1.5, 1.2)]
    for i in range(4):
        j = (i + 1) % 4
        poly_out(m, "indt_steel", [(*pts_top[i], 5.5), (*pts_top[j], 5.5), (*pts_bot[j], 3.8), (*pts_bot[i], 3.8)], (0, 0, 6))
    m.box("indt_coal", -4.3, 4.3, -3.3, 3.3, 10, 10.4)
    heap(m, "indt_coal", 0, 0, 3.0, 1.4, sides=8)
    # A gallery on top, where the conveyor comes in.
    for k in (-1, 1):
        m.box("indt_steel", -4.6, 4.6, k * 3.6 - 0.1, k * 3.6 + 0.1, 10, 11)
    # Coal stock around the foot.
    for (x, y, r, h) in ((6, 6, 1.8, 1.4), (-6, 6, 1.5, 1.1), (6, -6, 1.6, 1.2)):
        heap(m, "indt_coal", x, y, r, h)
    m.save(fname("coal_bunker"))
    return fname("coal_bunker")


def coal_stock():
    """A big stockpile of coal."""
    m = Model()
    ground(m, "indt_earth")
    heap(m, "indt_coal", -1, 0, 7, 5.2, sides=10, sy=0.9)
    heap(m, "indt_coal", 5, -5, 2.6, 2.2)
    heap(m, "indt_coal", 4.5, 5.5, 2.3, 1.8)
    m.save(fname("coal_stock"))
    return fname("coal_stock")


def spoil_heap():
    """A grey spoil tip with a tipping track up its side."""
    m = Model()
    ground(m, "indt_earth")
    frustum(m, "indt_spoil", 0, 0, 0, 7, 7.6, 2.5, 10, rot=0.2)
    frustum(m, "indt_spoil", 0, 0, 7, 8, 2.5, 1.6, 10, rot=0.2)
    # Track up the slope with a tipping wagon at the top.
    beam(m, "indt_steel", (7.5, -3.5, 0.2), (1.2, -1.6, 7.9), 0.25)
    beam(m, "indt_steel", (7.5, -2.3, 0.2), (1.2, -0.4, 7.9), 0.25)
    m.box("rust", -0.5, 1.6, -1.8, 0, 8, 9.2)
    m.save(fname("spoil_heap"))
    return fname("spoil_heap")


def coal_yard():
    """Coal yard: loading track ground, small piles and a fuel store."""
    m = Model()
    ground(m, "indt_earth")
    m.box("indt_coal", -7, 1, -7, 7, 0.06, 0.1)
    for y in (-3, 3):
        heap(m, "indt_coal", -3, y, 3.2, 2.4)
    heap(m, "indt_coal", 4, -4, 2.6, 1.8)
    # Small wooden shed and a tub wagon.
    m.box("wood", 1.5, 7, 2, 7, 0, 3.2)
    gable_roof_y(m, "slate", "wood", 1.3, 7.2, 1.8, 7.2, 3.2, 4.5)
    m.box("rust", 3, 6.2, -7.2, -5.2, 0.5, 2)
    m.box("indt_coal", 3.2, 6.0, -7.0, -5.4, 2, 2.4)
    for x in (3.6, 5.6):
        m.cylinder("dark", x - 0.2, x + 0.2, -6.2, 0.45, 0.45, sides=6)  # wheels seen end-on along y
    m.save(fname("coal_yard"))
    return fname("coal_yard")


# ---------------------------------------------------------------------------------------------------------------
# Power station: 7 boiler house, 8 chimney, 9 cooling tower, 10 transformer yard (the sparks).


def power_boiler():
    m = Model()
    ground(m, "concrete")
    m.box("brick", -7, 7, -7, 7, 0, 11)
    m.box("concrete", -7.2, 7.2, -7.2, 7.2, 11, 11.6)
    m.box("brick", -5, 3, -4, 4, 11.6, 14)  # raised boiler house
    m.box("concrete", -5.2, 3.2, -4.2, 4.2, 14, 14.4)
    m.windows("glass", -7, 7, -7, 7, 1.5, 10.5, 3, 5, size=(1.2, 2.2))
    m.windows("glass", -5, 3, -4, 4, 12, 13.6, 1, 3, size=(1.2, 1.0))
    m.box("door", 7, 7.1, -1.6, 1.6, 0, 3.5)
    m.save(fname("power_boiler"))
    return fname("power_boiler")


def power_chimney():
    m = Model()
    ground(m, "concrete")
    m.box("brick", -7, 1, -7, 7, 0, 8)
    m.prism_roof("slate", "brick", -7.2, 1.2, -7.2, 7.2, 8, 10)
    m.windows("glass", -7, 1, -7, 7, 1.5, 7, 2, 4, size=(1.1, 1.6))
    frustum(m, "brick", 4, 0, 0, 1.5, 3.2, 3.2, 12)
    frustum(m, "brick", 4, 0, 1.5, 27, 2.6, 1.6, 12)
    m.chimney("dark", 4, 0, 26.2, 27.4, 1.75, 12)
    for z in (20.0, 24.0):
        r = 2.6 - (z - 1.5) / 25.5 * 1.0 + 0.12
        frustum(m, "indt_white", 4, 0, z, z + 0.7, r, r - 0.03, 12)
    beam(m, "indt_steel", (1, 0, 6), (3, 0, 6), 1.0)  # flue
    m.save(fname("power_chimney"))
    return fname("power_chimney")


def power_cooling():
    m = Model()
    ground(m, "concrete")
    radii = [(0, 6.6), (3.0, 5.4), (6.0, 4.6), (8.5, 4.5), (10.5, 4.9)]
    for k in range(len(radii) - 1):
        (z0, r0), (z1, r1) = radii[k], radii[k + 1]
        frustum(m, "concrete", 0, 0, z0, z1, r0, r1, 16)
    # Hollow top: darker water/vapour inside, slightly below the rim.
    frustum(m, "dark", 0, 0, 10.0, 10.3, 4.6, 4.6, 16)
    for i in range(12):
        a = 2 * math.pi * i / 12
        beam(m, "concrete", (6.6 * math.cos(a), 6.6 * math.sin(a), 0), (6.4 * math.cos(a), 6.4 * math.sin(a), 0.9), 0.4)
    m.save(fname("power_cooling"))
    return fname("power_cooling")


def power_transformer():
    m = Model()
    ground(m, "indt_spoil")
    m.box("concrete", -7, 7, -7, 7, 0, 0.2)
    # Two transformers with cooling fins.
    for y in (-4, 3):
        m.box("indt_steel", -2, 2, y - 1.5, y + 1.5, 0.2, 3)
        m.box("dark", -2.3, 2.3, y - 1.2, y + 1.2, 0.6, 2.4)
        for dx in (-1.2, 0, 1.2):
            frustum(m, "indt_ceramic", dx, y, 3, 4.6, 0.35, 0.2, 6)
    # Gantries carrying the lines away.
    for x in (-5.5, 5.5):
        for y in (-6.5, 6.5):
            lattice_tower(m, "indt_steel", x, y, 0.2, 9, 0.6, 0.4, bays=3, w=0.2)
        beam(m, "indt_steel", (x, -6.5, 9), (x, 6.5, 9), 0.4)
        for y in (-4, -0.5, 3):
            frustum(m, "indt_ceramic", x, y, 7.6, 9, 0.25, 0.25, 6)
            beam(m, "dark", (x, y, 7.6), (0, y if abs(y) > 1 else -4, 4.4), 0.06)
    m.save(fname("power_transformer"))
    return fname("power_transformer")


# ---------------------------------------------------------------------------------------------------------------
# Sawmill: 11 mill hall, 12 open shed with planks, 13 boiler house with dust cyclone, 14 log piles, 15 plank stacks.


def sawmill_hall():
    m = Model()
    ground(m, "indt_earth")
    m.box("wood", -6, 6, -8, 8, 0, 6)
    gable_roof_y(m, "slate", "wood", -6.5, 6.5, -8, 8, 6, 9)
    m.box("slate", -1, 1, -8, 8, 9, 10)  # roof lantern
    m.box("glass", -1.05, 1.05, -7, 7, 9.2, 9.8)
    for y in (-5, 0, 5):
        m.box("glass", 6, 6.08, y - 1, y + 1, 2.5, 4.5)
        m.box("glass", -6.08, -6, y - 1, y + 1, 2.5, 4.5)
    m.box("dark", 6, 6.1, -2, 2, 0, 4)  # big door where the logs go in
    # Log entering on a deck.
    m.box("wood", 6, 8, -2.5, 2.5, 0, 0.8)
    m.cylinder("indt_log", 6.2, 8, 0, 1.4, 0.6, sides=7, caps="indt_logend")
    m.save(fname("sawmill_hall"))
    return fname("sawmill_hall")


def sawmill_shed():
    m = Model()
    ground(m, "indt_earth")
    for x in (-6.5, 6.5):
        for y in (-6, 0, 6):
            beam(m, "wood", (x, y, 0), (x, y, 5), 0.5)
    m.prism_roof("slate", "wood", -7.5, 7.5, -7, 7, 5, 7.5)
    for (y0, y1, h) in ((-6, -1.5, 2.6), (0.5, 5.5, 2.0)):
        for k in range(int(h / 0.5)):
            z = k * 0.5
            m.box("indt_plank", -5.5, 5.5, y0, y1, z + 0.1, z + 0.45)
            m.box("wood", -5.2, -4.8, y0, y1, z, z + 0.1)
            m.box("wood", 4.8, 5.2, y0, y1, z, z + 0.1)
    m.save(fname("sawmill_shed"))
    return fname("sawmill_shed")


def sawmill_boiler():
    m = Model()
    ground(m, "indt_earth")
    m.box("brick", -6, 4, -6, 6, 0, 6)
    m.prism_roof("slate", "brick", -6.3, 4.3, -6.4, 6.4, 6, 8)
    m.windows("glass", -6, 4, -6, 6, 1, 5.5, 1, 3, size=(1.2, 1.8))
    frustum(m, "brick", -3, 3, 0, 15, 1.2, 0.9, 10)
    m.chimney("dark", -3, 3, 14.6, 15.4, 1.0, 10)
    # Sawdust cyclone on a frame.
    cx, cy = 5.5, -3.5
    for dx in (-1.2, 1.2):
        for dy in (-1.2, 1.2):
            beam(m, "indt_steel", (cx + dx, cy + dy, 0), (cx + dx, cy + dy, 5), 0.3)
    frustum(m, "indt_steel", cx, cy, 4, 6.5, 0.4, 1.6, 10)
    frustum(m, "indt_steel", cx, cy, 6.5, 9, 1.6, 1.6, 10)
    beam(m, "indt_steel", (cx, cy, 9), (0, cy, 7.5), 0.6)
    heap(m, "indt_hay", cx, cy, 1.8, 1.4)  # sawdust under it
    m.save(fname("sawmill_boiler"))
    return fname("sawmill_boiler")


def sawmill_logs():
    m = Model()
    ground(m, "indt_earth")
    for (x0, x1, y0, rows) in ((-7, 3, -7, 3), (-7, 3, 1, 2)):
        r = 0.7
        n = 4
        for row in range(rows):
            for k in range(n - row):
                y = y0 + r + row * r + k * 2 * r
                log(m, x0, x1, y, r + row * 1.25 * r, r)
    # A log crane gantry.
    for y in (-7.5, 7.5):
        beam(m, "indt_redsteel", (5.5, y, 0), (5.5, y, 7), 0.5)
    beam(m, "indt_redsteel", (5.5, -7.5, 7), (5.5, 7.5, 7), 0.7)
    beam(m, "dark", (5.5, 1, 7), (5.5, 1, 4.5), 0.08)
    m.box("dark", 5, 6, 0.5, 1.5, 4.0, 4.5)
    log(m, 4.2, 7.2, 4.5, 0.6, 0.6)
    m.save(fname("sawmill_logs"))
    return fname("sawmill_logs")


def sawmill_planks():
    m = Model()
    ground(m, "indt_earth")
    for (x0, x1, y0, y1, h) in ((-7, -1, -6.5, -1, 3.0), (1, 7, -6.5, -1, 2.0), (-7, -1, 1, 6.5, 2.4), (1, 7, 1, 6.5, 1.4)):
        k = 0
        z = 0
        while z < h:
            m.box("wood", x0 + 0.4, x0 + 0.8, y0, y1, z, z + 0.15)
            m.box("wood", x1 - 0.8, x1 - 0.4, y0, y1, z, z + 0.15)
            m.box("indt_plank", x0, x1, y0, y1, z + 0.15, z + 0.5)
            z += 0.5
    m.save(fname("sawmill_planks"))
    return fname("sawmill_planks")


# ---------------------------------------------------------------------------------------------------------------
# Forest: 16 trees, 17 a cleared patch with stumps and a log pile.


def forest_trees():
    m = Model()
    ground(m, "grass")
    trees = [(-5, -5, 11, 2.4), (-5.5, 1, 12, 2.6), (-4.5, 6, 10, 2.2), (0, -2, 13, 2.8), (0.5, 4.5, 11.5, 2.4),
             (5, -5.5, 10, 2.2), (4.5, 0.5, 12, 2.5), (5.5, 5.5, 9.5, 2.1), (-1.5, -6.5, 9, 2.0)]
    for x, y, h, r in trees:
        conifer(m, x, y, h, r)
    m.save(fname("forest_trees"))
    return fname("forest_trees")


def forest_cleared():
    m = Model()
    ground(m, "indt_earth")
    for (x, y) in ((-5, -5), (-4, 3), (0, -1), (3, 5), (5, -4), (-1, 6)):
        frustum(m, "indt_bark", x, y, 0, 0.7, 0.55, 0.5, 7, top="indt_logend")
    for k, y in enumerate((-2.5, -1.3, -0.1)):
        log(m, -6, 4, y, 0.55, 0.55)
    for y in (-1.9, -0.7):
        log(m, -6, 4, y, 1.5, 0.55)
    conifer(m, 6, 6, 8, 1.8)
    m.save(fname("forest_cleared"))
    return fname("forest_cleared")


# ---------------------------------------------------------------------------------------------------------------
# Oil refinery: 18 storage tanks, 19 distillation column, 20 flare stack, 21 row of columns, 22 process plant,
# 23 control building. Tanks and columns take the refinery's colour.


def refinery_tanks():
    m = Model()
    ground(m, "indt_asphalt")
    tank(m, "company", -3, -3, 0, 4.5, 3.6, 16, roof="indt_white")
    tank(m, "company", 3.5, 3.5, 0, 3.5, 3.0, 14, roof="indt_white")
    tank(m, "indt_white", 4, -4, 0, 2.5, 2.0, 12)
    m.box("concrete", -7.5, 7.5, -7.5, -7.2, 0, 0.8)  # bund wall
    m.box("concrete", -7.5, 7.5, 7.2, 7.5, 0, 0.8)
    m.box("concrete", -7.5, -7.2, -7.5, 7.5, 0, 0.8)
    m.box("concrete", 7.2, 7.5, -7.5, 7.5, 0, 0.8)
    beam(m, "indt_steel", (-3, -6.5, 0.6), (6, -6.5, 0.6), 0.4)
    m.save(fname("refinery_tanks"))
    return fname("refinery_tanks")


def column(m, x, y, z1, r, platforms=3):
    frustum(m, "company", x, y, 0, z1, r, r, 10)
    frustum(m, "company_dark", x, y, z1, z1 + r * 0.6, r, r * 0.3, 10)
    for k in range(1, platforms + 1):
        z = z1 * k / (platforms + 1)
        frustum(m, "indt_steel", x, y, z, z + 0.25, r + 0.5, r + 0.5, 10)


def refinery_column():
    m = Model()
    ground(m, "indt_asphalt")
    m.box("concrete", -3.5, 3.5, -3.5, 3.5, 0, 0.5)
    column(m, -1, -0.5, 21, 1.6, 4)
    column(m, 2.5, 3, 12, 1.0, 2)
    beam(m, "indt_steel", (-1, -0.5, 17), (-1, 6, 17), 0.4)
    beam(m, "indt_steel", (-1, 6, 17), (-1, 6, 0), 0.4)
    beam(m, "indt_steel", (2.5, 3, 10), (2.5, 7, 10), 0.35)
    # Ladder cage.
    beam(m, "indt_yellow", (-2.8, -0.5, 0.5), (-2.8, -0.5, 21), 0.2)
    m.save(fname("refinery_column"))
    return fname("refinery_column")


def refinery_flare():
    m = Model()
    ground(m, "indt_asphalt")
    lattice_tower(m, "indt_steel", 0, 0, 0, 23, 2.2, 0.7, bays=6, w=0.3)
    frustum(m, "indt_redsteel", 0, 0, 0, 25, 0.5, 0.45, 8)
    frustum(m, "indt_white", 0, 0, 19, 21, 0.55, 0.52, 8)
    frustum(m, "indt_glow", 0, 0, 25, 26.5, 0.6, 0, 6)
    m.save(fname("refinery_flare"))
    return fname("refinery_flare")


def refinery_columns_row():
    m = Model()
    ground(m, "indt_asphalt")
    for k, (y, h, r) in enumerate(((-5, 16, 1.6), (0, 18, 1.8), (5, 14, 1.5))):
        column(m, 1, y, h, r, 3)
    # Pipe rack behind them.
    for y in (-7, -2.5, 2.5, 7):
        beam(m, "indt_steel", (-4, y, 0), (-4, y, 5), 0.35)
    for z in (4.2, 5.0):
        beam(m, "indt_steel", (-4, -8, z), (-4, 8, z), 0.6)
    for y in (-5, 0, 5):
        beam(m, "indt_steel", (-4, y, 5.0), (1, y, 5.0), 0.4)
    m.save(fname("refinery_columns_row"))
    return fname("refinery_columns_row")


def refinery_plant():
    m = Model()
    ground(m, "indt_asphalt")
    # Steel structure with decks.
    for x in (-6, -1, 4):
        for y in (-6, 0, 6):
            beam(m, "indt_steel", (x, y, 0), (x, y, 10), 0.4)
    for z in (4, 7.5):
        m.box("indt_steel", -6.3, 4.3, -6.3, -1.5, z - 0.2, z)
        m.box("indt_steel", -6.3, 4.3, 1.5, 6.3, z - 0.2, z)
    m.box("indt_steel", -6.3, 1.5, -2.5, 2.5, 9.8, 10)
    for y in (-6, 0, 6):
        beam(m, "indt_steel", (-6, y, 10), (4, y, 10), 0.3)
    # Vessels on the decks.
    m.cylinder("company", -5, 3, -3, 5.4, 1.2, 10, caps="company_dark")
    m.cylinder("company", -5, 3, 3, 5.4, 1.2, 10, caps="company_dark")
    tank(m, "company", -2.5, 0, 10, 13, 1.6, 10, roof="company_dark")
    m.box("indt_redsteel", 1, 3.5, -5, -1, 0, 3.5)  # furnace
    frustum(m, "indt_redsteel", 2.2, -3, 3.5, 15, 0.6, 0.6, 8)
    # Spheres, as stacked cones, on the free front strip.
    for y in (-3.5, 3.5):
        frustum(m, "indt_steel", 6.5, y, 0, 1.2, 0.3, 0.3, 6)
        frustum(m, "indt_white", 6.5, y, 1.2, 2.8, 0.6, 1.4, 12)
        frustum(m, "indt_white", 6.5, y, 2.8, 4.4, 1.4, 0.6, 12)
    m.save(fname("refinery_plant"))
    return fname("refinery_plant")


def refinery_office():
    m = Model()
    ground(m, "indt_asphalt")
    m.box("indt_white", -4, 4, -6, 6, 0, 3.6)
    m.box("concrete", -4.2, 4.2, -6.2, 6.2, 3.6, 4.0)
    m.windows("glass", -4, 4, -6, 6, 0.8, 3.2, 1, 4, size=(1.3, 1.2))
    m.box("door", 4, 4.1, -0.6, 0.6, 0, 2.4)
    m.box("company", -2, 2, -4, -1, 4.0, 5.0)  # roof plant
    frustum(m, "indt_steel", -2, 4, 4, 7, 0.15, 0.1, 5)  # aerial
    for y in (-6.5, 6.5):
        m.box("indt_yellow", 5.5, 7.5, y - 0.15, y + 0.15, 0, 0.5)  # car park kerbs
    m.save(fname("refinery_office"))
    return fname("refinery_office")


# ---------------------------------------------------------------------------------------------------------------
# Oil rig, on the sea: 24 deck (beside the heliport, which is a station tile), 25 crane, 26 derrick,
# 27 accommodation, 28 tanks and flare boom. Waterline at z = 0.

DECK = 5.0


def rig_base(m, legs=True):
    if legs:
        for x in (-6.5, 6.5):
            for y in (-6.5, 6.5):
                frustum(m, "indt_yellow", x, y, -1.5, DECK, 0.9, 0.9, 8)
        beam(m, "indt_steel", (-6.5, -6.5, 1.5), (6.5, 6.5, DECK - 0.5), 0.35)
        beam(m, "indt_steel", (6.5, -6.5, 1.5), (-6.5, 6.5, DECK - 0.5), 0.35)
    m.box("indt_steel", -8, 8, -8, 8, DECK - 1.2, DECK - 0.2)
    m.box("indt_asphalt", -8, 8, -8, 8, DECK - 0.2, DECK)


def oilrig_deck():
    m = Model()
    rig_base(m)
    for x in (-6, -2, 2, 6):
        beam(m, "indt_steel", (x, -7, DECK + 0.6), (x, 7, DECK + 0.6), 0.5)  # pipework
    m.box("company", -6, -2, 3, 7, DECK, DECK + 2.5)
    m.box("indt_white", 2, 6.5, -7, -3, DECK, DECK + 2)
    railing(m, -7.8, 7.8, -7.8, 7.8, DECK, 1.0)
    m.save(fname("oilrig_deck"))
    return fname("oilrig_deck")


def oilrig_crane():
    m = Model()
    rig_base(m)
    frustum(m, "indt_yellow", 2, -2, DECK, DECK + 6, 1.2, 1.0, 10)
    m.box("indt_yellow", 0.5, 4.2, -3.3, -0.7, DECK + 6, DECK + 8)
    m.box("glass", 4.2, 4.3, -3, -1, DECK + 6.5, DECK + 7.6)
    # Boom reaching out over the sea.
    beam(m, "indt_yellow", (2, -2.5, DECK + 7), (-7, 9, DECK + 13), 0.6)
    beam(m, "indt_yellow", (2, -1.5, DECK + 7), (-7, 9, DECK + 13), 0.6)
    beam(m, "dark", (-7, 9, DECK + 13), (-7, 9, DECK + 5), 0.06)
    m.box("indt_redsteel", -7.5, -6.5, 8.5, 9.5, DECK + 4.4, DECK + 5)
    # Containers.
    for (x, y, mat) in ((-5, -5, "company"), (-5, -2.5, "indt_redsteel"), (5, 4, "indt_white")):
        m.box(mat, x - 2.4, x + 2.4, y - 1.1, y + 1.1, DECK, DECK + 2.2)
    railing(m, -7.8, 7.8, -7.8, 7.8, DECK, 1.0)
    m.save(fname("oilrig_crane"))
    return fname("oilrig_crane")


def oilrig_derrick():
    m = Model()
    rig_base(m)
    m.box("indt_white", -4.5, 4.5, -4.5, 4.5, DECK, DECK + 2.5)  # drill floor
    lattice_tower(m, "indt_white", 0, 0, DECK + 2.5, DECK + 21, 3.6, 0.9, bays=7, w=0.35)
    m.box("indt_redsteel", -1.2, 1.2, -1.2, 1.2, DECK + 21, DECK + 22.2)
    m.box("company", 4.5, 7.5, -6, 6, DECK, DECK + 3.2)  # pipe deck store
    for y in (-5, -3.5, -2, 4):
        m.cylinder("indt_steel", -7, -1, y, DECK + 0.4, 0.35, sides=6)
    m.save(fname("oilrig_derrick"))
    return fname("oilrig_derrick")


def oilrig_quarters():
    m = Model()
    rig_base(m)
    m.box("indt_white", -6, 5, -7, 7, DECK, DECK + 3.2)
    m.box("company", -6, 3, -7, 4, DECK + 3.2, DECK + 6.4)
    m.box("indt_white", -6, 1, -7, 1, DECK + 6.4, DECK + 9.2)
    for (x0, x1, y0, y1, z0, z1) in ((-6, 5, -7, 7, DECK, DECK + 3.2), (-6, 3, -7, 4, DECK + 3.2, DECK + 6.4), (-6, 1, -7, 1, DECK + 6.4, DECK + 9.2)):
        m.windows("glass", x0, x1, y0, y1, z0 + 0.6, z1 - 0.4, 1, 4, size=(1.0, 1.0))
    m.box("indt_steel", -6.2, 1.2, -7.2, 1.2, DECK + 9.2, DECK + 9.5)
    # Radio mast and lifeboats.
    frustum(m, "indt_steel", -4, -5, DECK + 9.5, DECK + 15, 0.25, 0.1, 5)
    for y in (-5, 2):
        m.box("indt_glow", 6, 7.8, y - 1.6, y + 1.6, DECK + 0.6, DECK + 2.0)
    m.save(fname("oilrig_quarters"))
    return fname("oilrig_quarters")


def oilrig_tanks():
    m = Model()
    rig_base(m)
    for (x, y) in ((-4, -4), (-4, 1.5)):
        tank(m, "indt_white", x, y, DECK, DECK + 4, 2.4, 12)
    m.box("indt_steel", 1, 6, -6, -1, DECK, DECK + 3)  # compressor house
    # Flare boom out over the water.
    beam(m, "indt_steel", (4, 4, DECK), (10, 10, DECK + 9), 0.6)
    beam(m, "indt_steel", (5, 3, DECK), (10, 10, DECK + 9), 0.4)
    frustum(m, "indt_glow", 10, 10, DECK + 9, DECK + 11, 0.7, 0, 6)
    railing(m, -7.8, 7.8, -7.8, 7.8, DECK, 1.0)
    m.save(fname("oilrig_tanks"))
    return fname("oilrig_tanks")


# ---------------------------------------------------------------------------------------------------------------
# Oil wells: 29 (and the animation frames 30-32): a pump jack.


def oil_well():
    m = Model()
    ground(m, "indt_sand")
    m.box("concrete", -5.5, 4.5, -1.5, 1.5, 0, 0.6)
    # A-frame (samson post).
    for y in (-1.1, 1.1):
        beam(m, "indt_steel", (-2.5, y, 0.6), (0, y * 0.4, 6), 0.35)
        beam(m, "indt_steel", (2.0, y, 0.6), (0, y * 0.4, 6), 0.35)
    m.box("indt_steel", 4.6, 5.4, -0.4, 0.4, 0, 1.4)  # wellhead
    # Crank and counterweights, motor.
    for y in (-1.0, 1.0):
        m.box("dark", -5.2, -3.4, y - 0.2, y + 0.2, 2.0, 4.2)
        beam(m, "indt_steel", (-4.3, y, 3.2), (-4.6, y * 0.8, 5.4), 0.25)
    m.box("indt_steel", -5.3, -3.4, -0.7, 0.7, 0.6, 2.6)  # gearbox
    m.box("company_dark", -5.4, -3.6, 1.4, 2.6, 0.6, 1.8)  # motor
    # Little pipe away, fence posts.
    beam(m, "dark", (5, 0.4, 0.3), (5, 7.5, 0.3), 0.3)
    m.box("indt_steel", -6, -5, 4, 7, 0, 2.2)  # meter hut
    m.save(fname("oil_well"))
    oil_well_beam()
    return fname("oil_well")


# The walking beam rocks on top of the samson post while the well pumps; the game moves it.
OIL_WELL_PIVOT = (0, 0, 6)


def oil_well_beam():
    m = Model()
    # Walking beam with horse head at the front and counterweights at the back.
    beam(m, "company", (-5, 0, 5.4), (4, 0, 6.6), 0.6, 0.8)
    pts = [(3.6, 6.1), (5.2, 7.2), (5.6, 5.8), (5.0, 4.4), (3.6, 5.6)]
    for y0, y1 in ((-0.45, 0.45),):
        for i in range(1, len(pts) - 1):
            m.triangle("company_dark", (pts[0][0], y0, pts[0][1]), (pts[i + 1][0], y0, pts[i + 1][1]), (pts[i][0], y0, pts[i][1]))
            m.triangle("company_dark", (pts[0][0], y1, pts[0][1]), (pts[i][0], y1, pts[i][1]), (pts[i + 1][0], y1, pts[i + 1][1]))
        for i in range(len(pts)):
            a, b = pts[i], pts[(i + 1) % len(pts)]
            poly_out(m, "company_dark", [(a[0], y0, a[1]), (b[0], y0, b[1]), (b[0], y1, b[1]), (a[0], y1, a[1])], (4.5, 0, 6))
    beam(m, "dark", (5.0, 0, 4.4), (5.0, 0, 1.4), 0.08)  # bridle
    # The part turns around its origin, so move the pivot there.
    for positions, _ in m.parts.values():
        positions[:] = [tuple(p[k] - OIL_WELL_PIVOT[k] for k in range(3)) for p in positions]
    m.save(fname("oil_well_beam"))


# ---------------------------------------------------------------------------------------------------------------
# Farm: 33 farmhouse, 34 barn, 35 stable (these three take the farm's colour), 36 implement shed with hay,
# 37 silos, 38 stack yard with livestock.


def farm_house():
    m = Model()
    ground(m, "grass")
    m.box("company", -4, 4, -5, 3, 0, 6.2)
    m.prism_roof("tiles", "company", -4.5, 4.5, -5.5, 3.5, 6.2, 9.2)
    m.box("brick", -1, 0, 0.5, 1.5, 7.5, 10.2)
    m.windows("glass", -4, 4, -5, 3, 0.6, 6, 2, 2, size=(1.1, 1.3))
    m.box("door", 4, 4.1, -2.3, -1.1, 0, 2.3)
    m.box("indt_earth", 4, 8, -2.4, -1, 0.06, 0.1)  # path
    # Garden fence and a tree.
    for (a, b) in (((-7.5, 4.5), (7.5, 4.5)), ((-7.5, 4.5), (-7.5, 7.5))):
        beam(m, "wood", (a[0], a[1], 0.9), (b[0], b[1], 0.9), 0.15)
    broadleaf(m, 5.5, 5.5, 7, 2.0)
    m.save(fname("farm_house"))
    return fname("farm_house")


def farm_barn():
    m = Model()
    ground(m, "indt_earth")
    m.box("company", -6, 6, -5.5, 5.5, 0, 5)
    # Gambrel roof, ridge along x.
    pts = [(-5.5, 5), (-4.2, 8.2), (0, 9.8), (4.2, 8.2), (5.5, 5)]
    for i in range(len(pts) - 1):
        (ya, za), (yb, zb) = pts[i], pts[i + 1]
        m.quad("slate", (-6.4, ya * 1.07, za), (6.4, ya * 1.07, za), (6.4, yb * 1.07, zb), (-6.4, yb * 1.07, zb))
        # Make it face outwards: the quad above has ccw order seen from outside when going -y to +y over the top.
    for x, sgn in ((6, 1), (-6, -1)):
        gable = [(x, y, z) for (y, z) in pts]
        poly_out(m, "company", gable, (0, 0, 6))
    m.box("door", 6, 6.1, -2, 2, 0, 4)
    m.box("indt_white", 6.05, 6.15, -2.2, 2.2, 4, 4.3)
    m.box("glass", 6, 6.1, -0.6, 0.6, 6.2, 7.4)  # hay loft door
    m.save(fname("farm_barn"))
    return fname("farm_barn")


def farm_stable():
    m = Model()
    ground(m, "indt_earth")
    m.box("company", -6, 2, -7, 7, 0, 3.6)
    m.prism_roof("tiles", "company", -6.4, 2.4, -7.4, 7.4, 3.6, 5)
    for y in (-5, -1.7, 1.7, 5):
        m.box("door", 2, 2.1, y - 0.9, y + 0.9, 0, 2.2)
        m.box("indt_white", 2.02, 2.12, y - 1.0, y + 1.0, 2.2, 2.4)
    # Paddock in front with a horse-ish cow.
    for y in (-7.5, 7.5):
        beam(m, "wood", (2.5, y, 0.9), (7.5, y, 0.9), 0.15)
    beam(m, "wood", (7.5, -7.5, 0.9), (7.5, 7.5, 0.9), 0.15)
    for x in (2.5, 5, 7.5):
        for y in (-7.5, 0, 7.5):
            beam(m, "wood", (x, y, 0), (x, y, 1.1), 0.18)
    animal(m, 5, -3, "indt_bark")
    animal(m, 4.5, 3.5, "indt_cow")
    m.save(fname("farm_stable"))
    return fname("farm_stable")


def animal(m, x, y, material, rot=False):
    """A cow-sized animal standing along x."""
    m.box(material, x - 0.9, x + 0.9, y - 0.4, y + 0.4, 0.8, 1.6)
    m.box(material, x + 0.9, x + 1.5, y - 0.3, y + 0.3, 1.2, 1.9)
    for dx in (-0.7, 0.7):
        for dy in (-0.25, 0.25):
            m.box("dark", x + dx - 0.1, x + dx + 0.1, y + dy - 0.1, y + dy + 0.1, 0, 0.8)


def farm_shed():
    m = Model()
    ground(m, "indt_earth")
    for x in (-6, 0):
        for y in (-7, 0, 7):
            beam(m, "wood", (x, y, 0), (x, y, 4.2), 0.4)
    m.box("wood", -6.6, -6.2, -7.3, 7.3, 0, 4.2)  # back wall
    poly_out(m, "slate", [(-6.6, -7.5, 4.6), (0.6, -7.5, 4.0), (0.6, 7.5, 4.0), (-6.6, 7.5, 4.6)], (0, 0, 0))
    poly_out(m, "slate", [(-6.6, -7.5, 4.45), (0.6, -7.5, 3.85), (0.6, 7.5, 3.85), (-6.6, 7.5, 4.45)], (0, 0, 9))
    # Hay bales inside and a tractor out front.
    for k in range(3):
        for j in range(2):
            m.box("indt_hay", -5.8 + j * 2.4, -3.6 + j * 2.4, -6.5 + k * 2.2, -4.5 + k * 2.2, 0, 1.2)
    m.box("indt_hay", -5.8, -3.6, -6.5, -2.2, 1.2, 2.4)
    tx, ty = 4, 3
    m.box("indt_redsteel", tx - 1.8, tx + 1.2, ty - 0.6, ty + 0.6, 0.6, 1.5)
    m.box("indt_redsteel", tx - 1.8, tx - 0.4, ty - 0.8, ty + 0.8, 1.5, 3.0)
    m.box("glass", tx - 1.7, tx - 0.5, ty - 0.85, ty + 0.85, 2.1, 2.8)
    for (wx, r) in ((tx - 1.2, 0.8), (tx + 0.8, 0.5)):
        m.wheel(wx, ty - 0.9, r, 0.5, sides=10)
        m.wheel(wx, ty + 0.9, r, 0.5, sides=10)
    m.save(fname("farm_shed"))
    return fname("farm_shed")


def farm_silos():
    m = Model()
    ground(m, "concrete")
    for (x, y, h) in ((-2, -3.5, 13), (-2, 3, 13)):
        frustum(m, "indt_steel", x, y, 0, h, 3.0, 3.0, 14)
        frustum(m, "indt_white", x, y, h, h + 1.6, 3.0, 0.4, 14)
        for z in (3, 6, 9, 12):
            frustum(m, "indt_white", x, y, z, z + 0.3, 3.2, 3.2, 14)
    # Elevator leg and spouts.
    m.box("indt_steel", 2.5, 3.6, -0.5, 0.6, 0, 16)
    m.box("indt_steel", 2, 4, -1, 1.1, 16, 17.5)
    for y in (-3.5, 3):
        beam(m, "indt_steel", (2.6, 0, 16.2), (-1, y * 0.85, 14.4), 0.3)
    m.box("indt_redsteel", 4, 6.5, -1.8, 1.8, 0, 1.2)  # intake pit
    m.save(fname("farm_silos"))
    return fname("farm_silos")


def farm_yard():
    m = Model()
    ground(m, "grass")
    # Fenced yard.
    for (a, b) in (((-7.5, -7.5), (7.5, -7.5)), ((7.5, -7.5), (7.5, 7.5)), ((7.5, 7.5), (-7.5, 7.5)), ((-7.5, 7.5), (-7.5, -7.5))):
        for z in (0.5, 1.0):
            beam(m, "wood", (a[0], a[1], z), (b[0], b[1], z), 0.15)
    for x in (-7.5, -2.5, 2.5, 7.5):
        for y in (-7.5, 7.5):
            beam(m, "wood", (x, y, 0), (x, y, 1.2), 0.2)
            beam(m, "wood", (y, x, 0), (y, x, 1.2), 0.2)
    # Haystacks.
    for (x, y) in ((-4, -4), (-4, 1)):
        frustum(m, "indt_hay", x, y, 0, 2.8, 2.0, 2.2, 10)
        frustum(m, "indt_hay", x, y, 2.8, 5.0, 2.2, 0, 10)
    m.box("wood", -6, -2, 4, 6.5, 0.4, 1.0)  # trough
    for (x, y, mat) in ((3, -3, "indt_cow"), (4.5, 2.5, "indt_cow"), (1, 5, "indt_bark"), (5, -6, "indt_cow")):
        animal(m, x, y, mat)
    m.save(fname("farm_yard"))
    return fname("farm_yard")


# ---------------------------------------------------------------------------------------------------------------
# Steel mill: a 2x2 block of 52 blast furnace (back), 53 hot blast stoves (back, +y), 54 casting house with
# chimneys (front), 55 yard (front, +y); and pairs of 56 (back) and 57 (front) halls along x.
# The walls take the mill's colour.


def steel_furnace():
    m = Model()
    ground(m, "indt_spoil")
    # Furnace body: a tall shaft standing near the casting house (+x), with downcomer and skip incline.
    fx, fy = 3, -1
    frustum(m, "indt_redsteel", fx, fy, 0, 4, 3.0, 3.4, 12)
    frustum(m, "indt_redsteel", fx, fy, 4, 13, 3.4, 2.4, 12)
    frustum(m, "dark", fx, fy, 13, 15, 2.4, 1.6, 12)
    lattice_tower(m, "indt_steel", fx, fy, 0, 17, 4.0, 2.2, bays=4, w=0.35)
    for dy in (-0.8, 0.8):
        beam(m, "indt_steel", (fx, fy + dy, 15), (fx, fy + dy, 20), 0.6)
    beam(m, "indt_steel", (fx - 0.4, fy, 20), (fx + 0.4, fy + 6.0, 20), 0.7)  # gas offtake towards the stoves
    beam(m, "indt_steel", (fx, fy + 6.0, 20), (fx, fy + 9.5, 11), 0.9)
    # Skip incline from the stock house at the back.
    beam(m, "indt_steel", (-7.5, fy - 0.5, 1.5), (fx - 1.0, fy, 16), 0.9, 0.6)
    beam(m, "indt_steel", (-7.5, fy + 0.5, 1.5), (fx - 1.0, fy, 16), 0.9, 0.6)
    m.box("company", -8, -3, -8, 0, 0, 4)
    m.box("concrete", -8.2, -2.8, -8.2, 0.2, 4, 4.4)
    heap(m, "indt_ore", -5, 5, 2.6, 2.4)
    m.save(fname("steel_furnace"))
    return fname("steel_furnace")


def steel_stoves():
    m = Model()
    ground(m, "indt_spoil")
    for y in (-5, 0, 5):
        frustum(m, "indt_steel", 0, y, 0, 15, 2.1, 2.1, 12)
        frustum(m, "indt_steel", 0, y, 15, 16.6, 2.1, 0.8, 12)
        frustum(m, "dark", 0, y, 2, 2.4, 2.15, 2.15, 12)
    beam(m, "indt_redsteel", (-3, -7, 3), (-3, 7, 3), 1.0)  # hot blast main
    for y in (-5, 0, 5):
        beam(m, "indt_redsteel", (-3, y, 3), (-1.6, y, 3), 0.6)
    beam(m, "indt_steel", (2.5, -8, 11), (2.5, 6, 11), 0.9)  # gas main from the furnace
    frustum(m, "brick", 5.5, 5.5, 0, 18, 1.0, 0.7, 10)  # stove chimney
    m.chimney("dark", 5.5, 5.5, 17.6, 18.3, 0.8, 10)
    m.save(fname("steel_stoves"))
    return fname("steel_stoves")


def steel_casthouse():
    m = Model()
    ground(m, "indt_spoil")
    m.box("company", -6, 7, -7, 7, 0, 7)
    m.prism_roof("slate", "company", -6.4, 7.4, -7.4, 7.4, 7, 9.5)
    m.box("slate", -6.4, 7.4, -1, 1, 9.3, 10.3)  # ventilation ridge
    for y in (-4.5, 4.5):
        frustum(m, "brick", -3, y, 9, 19, 0.9, 0.7, 10)
        m.chimney("dark", -3, y, 18.6, 19.3, 0.75, 10)
    m.windows("glass", -6, 7, -7, 7, 2, 6, 1, 4, size=(1.6, 2.6))
    m.box("indt_glow", 7, 7.1, -2, 2, 0, 3.5)  # open door with the glow of molten iron
    m.save(fname("steel_casthouse"))
    return fname("steel_casthouse")


def steel_yard():
    m = Model()
    ground(m, "indt_spoil")
    m.box("concrete", -7.5, 7.5, -7.5, 7.5, 0.06, 0.15)
    # Torpedo ladle car on a short track and ingot stacks.
    for y in (-5.7, -4.3):
        beam(m, "indt_steel", (-8, y, 0.2), (8, y, 0.2), 0.2)
    m.cylinder("indt_redsteel", -4, 3, -5, 1.6, 1.2, 10, caps="dark")
    m.box("dark", -4.5, 3.5, -5.8, -4.2, 0.2, 0.7)
    for (x, y) in ((-5, 2), (-1, 2), (3, 2), (-5, 5.5), (-1, 5.5)):
        for k in range(3):
            for j in range(3 - k % 2):
                if k % 2 == 0:
                    m.box("indt_steel", x - 1.5 + j * 1.1, x - 0.6 + j * 1.1, y - 1.3, y + 1.3, k * 0.6, k * 0.6 + 0.6)
                else:
                    m.box("indt_steel", x - 1.5, x + 1.5, y - 1.3 + j * 1.1, y - 0.4 + j * 1.1, k * 0.6, k * 0.6 + 0.6)
    heap(m, "indt_ore_dark", 5.5, 4.5, 2.3, 2.0)
    m.save(fname("steel_yard"))
    return fname("steel_yard")


def steel_hall_back():
    m = Model()
    ground(m, "indt_spoil")
    m.box("company", -8, 8, -7, 7, 0, 9)
    m.prism_roof("slate", "company", -8, 8, -7.4, 7.4, 9, 11.5)
    m.box("slate", -8, 8, -1.2, 1.2, 11.3, 12.4)  # clerestory
    m.box("glass", -7.5, 7.5, -1.25, 1.25, 11.5, 12.1)
    m.windows("glass", -8, 8, -7, 7, 2, 8, 2, 4, size=(1.5, 2.0))
    m.box("company_dark", -8.1, -7.95, -2, 2, 0, 5)  # end door
    m.save(fname("steel_hall_back"))
    return fname("steel_hall_back")


def steel_hall_front():
    m = Model()
    ground(m, "indt_spoil")
    m.box("company", -8, 3, -7, 7, 0, 9)
    m.prism_roof("slate", "company", -8, 3.4, -7.4, 7.4, 9, 11.5)
    m.box("slate", -8, 3, -1.2, 1.2, 11.3, 12.4)
    m.box("glass", -8, 2.6, -1.25, 1.25, 11.5, 12.1)
    m.windows("glass", -8, 3, -7, 7, 2, 8, 2, 3, size=(1.5, 2.0))
    m.box("indt_glow", 3, 3.1, -2, 2, 0, 4)
    m.box("company", 3, 7, -7, -1, 0, 5)  # lean-to annex
    m.box("slate", 3, 7.3, -7.3, -0.7, 5, 5.4)
    for (x, y) in ((5, 3.5),):
        frustum(m, "brick", x, y, 0, 16, 1.1, 0.8, 10)
        m.chimney("dark", x, y, 15.6, 16.3, 0.85, 10)
    m.save(fname("steel_hall_front"))
    return fname("steel_hall_front")


# ---------------------------------------------------------------------------------------------------------------
# Bank (temperate): 58 back half, 59 front half with the portico, at offsets (0, 0) and (1, 0).


def bank_back():
    m = Model()
    ground(m, "indt_asphalt")
    m.box("stone", -7, 8, -7, 7, 0, 9)
    m.box("concrete", -7.3, 8, -7.3, 7.3, 9, 9.8)
    m.windows("glass", -7, 8, -7, 7, 1.5, 8.5, 2, 4, size=(1.2, 2.2))
    # Dome over the banking hall.
    frustum(m, "stone", 0, 0, 9.8, 11.5, 4.2, 4.2, 14)
    radii = [(11.5, 4.2), (12.8, 3.8), (13.8, 2.9), (14.5, 1.6), (14.8, 0)]
    for k in range(len(radii) - 1):
        (z0, r0), (z1, r1) = radii[k], radii[k + 1]
        frustum(m, "indt_ceramic" if False else "slate", 0, 0, z0, z1, r0, r1, 14)
    m.save(fname("bank_back"))
    return fname("bank_back")


def bank_front():
    m = Model()
    ground(m, "indt_asphalt")
    m.box("stone", -8, 3, -7, 7, 0, 9)
    m.box("concrete", -8, 3.3, -7.3, 7.3, 9, 9.8)
    m.windows("glass", -8, 3, -7, 7, 1.5, 8.5, 2, 3, size=(1.2, 2.2))
    # Steps, columns and pediment facing the street.
    for k in range(3):
        m.box("stone", 3, 7.6 - k * 0.6, -6, 6, k * 0.35, (k + 1) * 0.35)
    for y in (-5, -3, -1, 1, 3, 5):
        frustum(m, "indt_white", 5.6, y, 1.05, 8.3, 0.55, 0.48, 10)
        m.box("indt_white", 5.0, 6.2, y - 0.6, y + 0.6, 8.3, 8.7)
    m.box("indt_white", 3, 6.6, -6.4, 6.4, 8.7, 9.6)  # entablature
    # Pediment: a gable facing +x.
    m.quad("slate", (3, -6.6, 9.6), (6.8, -6.6, 9.6), (6.8, 0, 12.0), (3, 0, 12.0))
    m.quad("slate", (6.8, 6.6, 9.6), (3, 6.6, 9.6), (3, 0, 12.0), (6.8, 0, 12.0))
    m.triangle("indt_white", (6.8, -6.6, 9.6), (6.8, 6.6, 9.6), (6.8, 0, 12.0))
    m.box("door", 3, 3.1, -1.2, 1.2, 1.05, 4.5)
    m.save(fname("bank_front"))
    return fname("bank_front")


# ---------------------------------------------------------------------------------------------------------------
# Iron ore mine: one 4x4 picture (gfx 100 + 4 * dx + dy at offset (dx, dy)), built as one scene of 64 by 64
# and cut into tiles: a terraced open pit, spoil heaps, a crusher, a conveyor and an ore stockpile.


class _Shifted(Model):
    def __init__(self, dx, dy):
        super().__init__()
        self.dx, self.dy = dx, dy

    def triangle(self, material, a, b, c):
        f = lambda p: (p[0] - self.dx, p[1] - self.dy, p[2])
        super().triangle(material, f(a), f(b), f(c))


class Scene:
    """Boxes that are cut at the tile edges, and other shapes that each go to the tile they stand on."""

    def __init__(self):
        self.boxes = []
        self.shapes = []

    def box(self, *args):
        self.boxes.append(args)

    def shape(self, x, y, fn):
        self.shapes.append((x, y, fn))

    def tile(self, tx, ty):
        cx, cy = tx * 16 + 8, ty * 16 + 8
        m = _Shifted(cx, cy)
        for (mat, x0, x1, y0, y1, z0, z1) in self.boxes:
            a0, a1 = max(x0, cx - 8), min(x1, cx + 8)
            b0, b1 = max(y0, cy - 8), min(y1, cy + 8)
            if a1 - a0 > 1e-6 and b1 - b0 > 1e-6:
                m.box(mat, a0, a1, b0, b1, z0, z1)
        for (x, y, fn) in self.shapes:
            if cx - 8 <= x < cx + 8 and cy - 8 <= y < cy + 8:
                fn(m)
        return m


def iron_mine_scene():
    s = Scene()
    s.box("indt_earth", 0, 64, 0, 64, 0, 0.06)
    # Terraced open pit, centred towards the back left, rising in steps to a rim of spoil.
    px, py = 22, 40
    steps = [(6, 0.1, "indt_ore_dark"), (10, 1.2, "indt_ore"), (14, 2.4, "indt_ore_dark"), (18, 3.6, "indt_ore"), (21, 4.4, "indt_earth")]
    s.box("indt_ore_dark", px - steps[0][0], px + steps[0][0], py - steps[0][0], py + steps[0][0], 0, 0.1)
    for k in range(1, len(steps)):
        r0, r1, z, mat = steps[k - 1][0], steps[k][0], steps[k][1], steps[k][2]
        s.box(mat, px - r1, px + r1, py - r1, py - r0, 0, z)
        s.box(mat, px - r1, px + r1, py + r0, py + r1, 0, z)
        s.box(mat, px - r1, px - r0, py - r0, py + r0, 0, z)
        s.box(mat, px + r0, px + r1, py - r0, py + r0, 0, z)
    # Haul ramp down the front face.
    for k in range(4):
        s.box("indt_earth", px + 6 + k * 3.75, px + 6 + (k + 1) * 3.75, py - 4, py, 0, 0.5 + k * 1.1)
    # Machines in the pit.
    def excavator(m, x=px - 2, y=py + 2):
        m.box("indt_yellow", x - 1.6, x + 1.6, y - 1.4, y + 1.4, 0.1, 1.0)
        m.box("dark", x - 1.8, x + 1.8, y - 1.6, y - 0.9, 0.1, 0.8)
        m.box("dark", x - 1.8, x + 1.8, y + 0.9, y + 1.6, 0.1, 0.8)
        m.box("indt_yellow", x - 1.3, x + 1.0, y - 1.1, y + 1.1, 1.0, 2.6)
        beam(m, "indt_yellow", (x + 0.8, y, 2.0), (x + 3.8, y, 3.6), 0.5)
        beam(m, "indt_yellow", (x + 3.8, y, 3.6), (x + 4.6, y, 1.0), 0.4)
        m.box("dark", x + 4.2, x + 5.2, y - 0.6, y + 0.6, 0.3, 1.1)
    s.shape(px - 2, py + 2, excavator)

    def dumper(x, y, z=0.0):
        def fn(m):
            m.box("indt_yellow", x - 1.8, x + 1.0, y - 0.9, y + 0.9, z + 0.8, z + 2.0)
            m.box("indt_ore", x - 1.6, x + 0.8, y - 0.7, y + 0.7, z + 2.0, z + 2.3)
            m.box("indt_yellow", x + 1.0, x + 1.9, y - 0.9, y + 0.9, z + 0.8, z + 2.4)
            m.box("glass", x + 1.9, x + 1.95, y - 0.7, y + 0.7, z + 1.6, z + 2.2)
            for wx in (x - 1.1, x + 1.3):
                for wy in (y - 1.0, y + 1.0):
                    m.cylinder("tyre", wx - 0.55, wx + 0.55, wy, z + 0.55, 0.55, sides=8)
        return fn
    s.shape(px + 3, py - 7, dumper(px + 3, py - 7, 0.1))
    s.shape(px + 17.5, py - 2, dumper(px + 17.5, py - 2, 4.4 * 0 + 3.8))
    # Spoil heaps at the back right.
    s.shape(9, 10, lambda m: heap(m, "indt_spoil", 9, 10, 8, 6, sides=10, sy=0.9))
    s.shape(24, 6, lambda m: heap(m, "indt_spoil", 24, 6, 5, 3.6))
    # Crusher plant at the front right.
    s.box("concrete", 46, 63, 2, 22, 0, 0.3)
    s.box("company", 48, 58, 4, 14, 0, 10)
    s.box("slate", 47.6, 58.4, 3.6, 14.4, 10, 10.6)
    s.box("indt_steel", 50, 56, 6, 12, 10.6, 13)
    s.box("company_dark", 52, 62, 14, 21, 0, 6)
    s.box("slate", 51.6, 62.4, 13.6, 21.4, 6, 6.5)
    s.box("dark", 62, 62.1, 16, 19.5, 0, 4)  # loading bay
    s.shape(53, 9, lambda m: m.windows("glass", 48, 58, 4, 14, 2, 9, 2, 3, size=(1.4, 1.6)))
    s.shape(57, 17, lambda m: frustum(m, "brick", 57, 18, 6.5, 14, 0.8, 0.6, 8))
    # Conveyor from the top of the pit ramp up to the crusher.
    s.box("indt_earth", 41, 46, 26, 40, 0, 4.4)  # bench at the ramp top
    s.shape(44, 30, lambda m: conveyor(m, (44, 30, 4.8), (50, 15, 11.5)))
    s.shape(44, 30, lambda m: m.box("indt_steel", 42, 46, 28, 32, 4.4, 5.6))  # hopper
    # Conveyor on to the stockpile at the front left, and the stockpile.
    s.shape(56, 22, lambda m: conveyor(m, (56, 21, 5.5), (56, 34, 8)))
    s.shape(56, 40, lambda m: heap(m, "indt_ore", 56, 40, 7, 6.5, sides=10))
    # Small office and a few cars at the front left corner.
    s.box("indt_white", 50, 58, 52, 62, 0, 3.3)
    s.box("concrete", 49.7, 58.3, 51.7, 62.3, 3.3, 3.7)
    s.shape(54, 57, lambda m: m.windows("glass", 50, 58, 52, 62, 0.6, 3.0, 1, 3, size=(1.3, 1.1)))
    s.box("door", 58, 58.1, 56.5, 57.7, 0, 2.3)
    return s


def iron_mine():
    s = iron_mine_scene()
    entries = []
    for dx in range(4):
        for dy in range(4):
            gfx = 100 + 4 * dx + dy
            name = fname(f"iron_mine_{dx}{dy}")
            s.tile(dx, dy).save(name)
            entries.append({"type": "industry_tile", "ids": [gfx], "model": name})
    return entries


# ---------------------------------------------------------------------------------------------------------------


MODELS = [
    (coal_headframe, []),
    (coal_plant, [2]),
    (coal_bunker, [3]),
    (coal_stock, [4]),
    (spoil_heap, [5]),
    (coal_yard, [6]),
    (power_boiler, [7]),
    (power_chimney, [8]),
    (power_cooling, [9]),
    (power_transformer, [10]),
    (sawmill_hall, [11]),
    (sawmill_shed, [12]),
    (sawmill_boiler, [13]),
    (sawmill_logs, [14]),
    (sawmill_planks, [15]),
    (forest_trees, [16]),
    (forest_cleared, [17]),
    (refinery_tanks, [18]),
    (refinery_column, [19]),
    (refinery_flare, [20]),
    (refinery_columns_row, [21]),
    (refinery_plant, [22]),
    (refinery_office, [23]),
    (oilrig_deck, [24]),
    (oilrig_crane, [25]),
    (oilrig_derrick, [26]),
    (oilrig_quarters, [27]),
    (oilrig_tanks, [28]),
    (farm_house, [33]),
    (farm_barn, [34]),
    (farm_stable, [35]),
    (farm_shed, [36]),
    (farm_silos, [37]),
    (farm_yard, [38]),
    (steel_furnace, [52]),
    (steel_stoves, [53]),
    (steel_casthouse, [54]),
    (steel_yard, [55]),
    (steel_hall_back, [56]),
    (steel_hall_front, [57]),
    (bank_back, [58]),
    (bank_front, [59]),
]


def build():
    buildings = []
    for fn, ids in MODELS:
        model = fn()
        if ids:  # tiles with moving parts get their entries below
            buildings.append({"type": "industry_tile", "ids": ids, "model": model})
    # The beam of an oil well stands still while the well does not pump, and rocks while it does.
    well = oil_well()
    beam_part = {"model": fname("oil_well_beam"), "at": list(OIL_WELL_PIVOT), "axis": [0, 1, 0]}
    buildings.append({"type": "industry_tile", "ids": [29], "model": well, "parts": [beam_part]})
    # The coal mine's headframe: 0 stands still, 1 is the one the game animates while the mine works.
    sheave = coal_sheave()
    sheaves = [{"model": sheave, "at": list(at), "axis": [0, 1, 0]} for at in COAL_SHEAVES]
    buildings.append({"type": "industry_tile", "ids": [0], "model": fname("coal_headframe"), "parts": sheaves})
    buildings.append({"type": "industry_tile", "ids": [1], "model": fname("coal_headframe"), "parts": [dict(p, spin=2.5) for p in sheaves]})
    buildings.append({"type": "industry_tile", "ids": [30, 31, 32], "model": well, "parts": [dict(beam_part, swing=0.22, period=2.4)]})
    buildings += iron_mine()
    return {"vehicles": [], "buildings": buildings}
