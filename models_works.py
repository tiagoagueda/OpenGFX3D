"""Building sites, waypoints, canal locks, disasters and the road works bulldozer.

Building sites stand where a town building or an industry is still being built. The game picks one by the
stage of the work (0 just begun, 1 half way, 2 nearly done) and by the size of the plot:
id = stage * 4 + plot, with plot 0 one tile, 1 two tiles along x, 2 two tiles along y, 3 two by two tiles.
The model is centred on the plot, a tile is 16 across.

Waypoints: 0 on a railway, 1 on a road; the track or road runs along x.

Canal locks, by part: 0 the middle (on the slope), 1 the lower end, 2 the upper end; 3 a leaf of the lower
gates and 4 a leaf of the upper gates. The water rises towards +x. The game puts each part at the height of its
highest corner. The three parts make one long chamber, as ships are longer than a tile; the game draws the
water in it and turns the gate leaves around their hinges as ships pass.

Disasters, by disaster vehicle type, front to +x like other vehicles.
"""

import math
import random

from gfx3d import MATERIALS, Model
from models_industry_other import sphere
from models_infra import beam, frustum

GROUP = "works"
H = 8 * 0.40824829  # one height level in world units

for _name, _colour in {
    "works_soil": (0.46, 0.34, 0.22),
    "works_sand": (0.80, 0.70, 0.48),
    "works_pole": (0.78, 0.70, 0.46),
    "works_plank": (0.62, 0.48, 0.30),
    "works_yellow": (0.95, 0.74, 0.16),
    "works_red": (0.80, 0.18, 0.14),
    "works_white": (0.93, 0.93, 0.90),
    "works_hull": (0.24, 0.26, 0.30),
    "works_envelope": (0.80, 0.80, 0.78),
    "works_ufo": (0.72, 0.76, 0.80),
    "works_ufo_light": (0.50, 0.95, 0.70),
    "works_jet": (0.46, 0.50, 0.44),
}.items():
    MATERIALS.setdefault(_name, _colour)


# Building sites ------------------------------------------------------------------------------------

PLOTS = [(1, 1), (2, 1), (1, 2), (2, 2)]


def bricks(m, x, y, rnd):
    """A pallet with a stack of bricks."""
    m.box("wood", x - 1.0, x + 1.0, y - 0.8, y + 0.8, 0, 0.25)
    for layer in range(rnd.randint(2, 4)):
        m.box("brick", x - 0.9, x + 0.9, y - 0.7, y + 0.7, 0.25 + layer * 0.35, 0.25 + (layer + 1) * 0.35)


def sand_heap(m, x, y, r):
    frustum(m, "works_sand", x, y, 0, r * 0.7, r, r * 0.15, 10, top="works_sand")


def mixer(m, x, y):
    """A small cement mixer on two wheels."""
    m.box("works_red", x - 0.8, x + 0.8, y - 0.5, y + 0.5, 0.4, 0.6)
    m.cylinder("works_red", x - 0.6, x + 0.7, y, 1.3, 0.6, sides=10, caps="dark")
    for d in (-0.6, 0.6):
        m.box("tyre", x - 0.3, x + 0.3, y + d - 0.1, y + d + 0.1, 0, 0.6)


def site_hut(m, x, y, along_x=True):
    """A site office: a cabin on blocks."""
    w, d = (3.0, 1.6) if along_x else (1.6, 3.0)
    m.box("concrete", x - w + 0.2, x + w - 0.2, y - d + 0.2, y + d - 0.2, 0, 0.3)
    m.box("company", x - w, x + w, y - d, y + d, 0.3, 2.8)
    m.box("works_white", x - w - 0.05, x + w + 0.05, y - d - 0.05, y + d + 0.05, 2.8, 3.0)
    m.windows("glass", x - w, x + w, y - d, y + d, 0.3, 2.8, 1, 2, size=(0.9, 0.8), depth=0.04)


def stakes(m, x0, x1, y0, y1):
    """Pegs at the corners, with a line between them, where the walls will go."""
    for x, y in ((x0, y0), (x0, y1), (x1, y0), (x1, y1)):
        m.box("wood", x - 0.12, x + 0.12, y - 0.12, y + 0.12, 0, 1.0)
    for a, b in (((x0, y0), (x1, y0)), ((x0, y1), (x1, y1)), ((x0, y0), (x0, y1)), ((x1, y0), (x1, y1))):
        beam(m, "works_white", (a[0], a[1], 0.8), (b[0], b[1], 0.8), 0.05)


def scaffold(m, x0, x1, y0, y1, top, levels):
    """Scaffolding around a building: poles, a rail at each working level, and planks to stand on."""
    out = 0.9
    sx0, sx1, sy0, sy1 = x0 - out, x1 + out, y0 - out, y1 + out
    pole = 0.09

    def spots(a, b):
        n = max(1, round((b - a) / 3.5))
        return [a + (b - a) * i / n for i in range(n + 1)]

    for x in spots(sx0, sx1):
        for y in (sy0, sy1, y0 - 0.15, y1 + 0.15):
            m.box("works_pole", x - pole, x + pole, y - pole, y + pole, 0, top)
    for y in spots(sy0, sy1)[1:-1]:
        for x in (sx0, sx1, x0 - 0.15, x1 + 0.15):
            m.box("works_pole", x - pole, x + pole, y - pole, y + pole, 0, top)
    for z in levels:
        # Planks all around, and a rail along the outside.
        m.box("works_plank", sx0, sx1, sy0, y0 - 0.1, z - 0.08, z)
        m.box("works_plank", sx0, sx1, y1 + 0.1, sy1, z - 0.08, z)
        m.box("works_plank", sx0, x0 - 0.1, y0 - 0.1, y1 + 0.1, z - 0.08, z)
        m.box("works_plank", x1 + 0.1, sx1, y0 - 0.1, y1 + 0.1, z - 0.08, z)
        r = z + 1.0
        m.box("works_pole", sx0, sx1, sy0 - pole, sy0 + pole, r - pole, r + pole)
        m.box("works_pole", sx0, sx1, sy1 - pole, sy1 + pole, r - pole, r + pole)
        m.box("works_pole", sx0 - pole, sx0 + pole, sy0, sy1, r - pole, r + pole)
        m.box("works_pole", sx1 - pole, sx1 + pole, sy0, sy1, r - pole, r + pole)
    # A ladder up one side.
    lx = sx1 - 0.6
    for y in (sy0 + 0.3, sy0 + 0.9):
        m.box("works_pole", lx - 0.05, lx + 0.05, y - 0.05, y + 0.05, 0, top)
    z = 0.4
    while z < top:
        m.box("works_pole", lx - 0.04, lx + 0.04, sy0 + 0.3, sy0 + 0.9, z - 0.04, z + 0.04)
        z += 0.5


def walls(m, x0, x1, y0, y1, z0, z1, gaps=True):
    """Unfinished brick walls, with holes for windows and doors."""
    t = 0.45
    m.box("brick", x0, x1, y0, y0 + t, z0, z1)
    m.box("brick", x0, x1, y1 - t, y1, z0, z1)
    m.box("brick", x0, x0 + t, y0 + t, y1 - t, z0, z1)
    m.box("brick", x1 - t, x1, y0 + t, y1 - t, z0, z1)
    if gaps:
        # Dark openings on the faces, where windows will go.
        m.windows("dark", x0, x1, y0, y1, z0, z1, max(1, round((z1 - z0) / 2.6)), max(1, round((x1 - x0) / 4.5)), size=(1.2, 1.3), depth=0.03)


def crane(m, x, y, height, jib, turn):
    """A tower crane: a lattice mast, a jib with a counterweight, and a hook."""
    c, s = math.cos(turn), math.sin(turn)
    m.box("concrete", x - 1.0, x + 1.0, y - 1.0, y + 1.0, 0, 0.5)
    w = 0.5
    for dx, dy in ((-w, -w), (-w, w), (w, -w), (w, w)):
        m.box("works_yellow", x + dx - 0.1, x + dx + 0.1, y + dy - 0.1, y + dy + 0.1, 0.5, height)
    z = 1.5
    while z < height:
        m.box("works_yellow", x - w, x + w, y - w, y + w, z - 0.06, z + 0.06)
        z += 1.5
    m.box("works_yellow", x - 0.7, x + 0.7, y - 0.7, y + 0.7, height, height + 1.0)  # cab
    m.box("glass", x + 0.2, x + 0.75, y - 0.6, y + 0.6, height + 0.3, height + 0.9)
    tip = (x + c * jib, y + s * jib, height + 1.2)
    back = (x - c * jib * 0.3, y - s * jib * 0.3, height + 1.2)
    beam(m, "works_yellow", back, tip, 0.5)
    beam(m, "works_yellow", (x, y, height + 1.0), (x, y, height + 2.8), 0.3)  # top of the mast
    beam(m, "metal", (x, y, height + 2.8), tip, 0.06)
    beam(m, "metal", (x, y, height + 2.8), back, 0.06)
    m.box("concrete", back[0] - 0.6, back[0] + 0.6, back[1] - 0.6, back[1] + 0.6, height + 0.3, height + 1.0)  # counterweight
    hx, hy = x + c * jib * 0.7, y + s * jib * 0.7
    beam(m, "metal", (hx, hy, height + 1.0), (hx, hy, height * 0.5), 0.05)
    m.box("works_red", hx - 0.2, hx + 0.2, hy - 0.2, hy + 0.2, height * 0.5 - 0.5, height * 0.5)


def building_site(stage, plot):
    tx, ty = PLOTS[plot]
    hx, hy = tx * 8, ty * 8
    rnd = random.Random(stage * 10 + plot)
    m = Model()
    # The plot: bare earth, a little inside the edges so the pavement or grass still shows.
    m.box("works_soil", -hx + 0.6, hx - 0.6, -hy + 0.6, hy - 0.6, 0, 0.06)
    # The building takes most of the plot; stuff lies on the side towards +x and +y.
    x0, x1, y0, y1 = -hx + 2.2, hx - 3.6, -hy + 2.2, hy - 3.2
    if stage == 0:
        stakes(m, x0, x1, y0, y1)
        # Trenches for the foundations.
        t = 0.6
        for a, b, c, d in ((x0, x1, y0, y0 + t), (x0, x1, y1 - t, y1), (x0, x0 + t, y0, y1), (x1 - t, x1, y0, y1)):
            m.box("dark", a, b, c, d, 0.06, 0.08)
        sand_heap(m, hx - 2.2, -hy + 2.5, 1.6)
        bricks(m, hx - 2.0, hy - 2.0, rnd)
        if tx * ty > 1:
            mixer(m, x1 - 2.5, hy - 2.0)
            site_hut(m, -hx + 4.0, hy - 2.0)
    else:
        top = 3.2 if stage == 1 else 6.2 + (tx * ty > 1) * 3.0
        m.box("concrete", x0 - 0.3, x1 + 0.3, y0 - 0.3, y1 + 0.3, 0.06, 0.45)
        walls(m, x0, x1, y0, y1, 0.45, top)
        if stage == 2:
            # A floor half way up, and the timbers of the roof.
            m.box("concrete", x0 + 0.45, x1 - 0.45, y0 + 0.45, y1 - 0.45, top * 0.5 - 0.2, top * 0.5)
            ridge = top + 2.4
            ym = (y0 + y1) / 2
            n = max(2, round((x1 - x0) / 1.6))
            for i in range(n + 1):
                x = x0 + (x1 - x0) * i / n
                beam(m, "wood", (x, y0, top), (x, ym, ridge), 0.18)
                beam(m, "wood", (x, y1, top), (x, ym, ridge), 0.18)
            beam(m, "wood", (x0, ym, ridge), (x1, ym, ridge), 0.22)
        levels = [z for z in (2.4, 4.8, 7.2) if z < top - 0.5]
        scaffold(m, x0, x1, y0, y1, top + 1.0, levels)
        bricks(m, hx - 1.8, -hy + 2.0, rnd)
        if stage == 1:
            sand_heap(m, hx - 1.8, hy - 1.8, 1.2)
        else:
            m.box("works_plank", hx - 2.6, hx - 1.0, hy - 3.0, hy - 1.0, 0, 0.6)  # a stack of timber
        if tx * ty > 1:
            mixer(m, hx - 2.0, 0)
        if tx * ty == 4 and stage == 2:
            crane(m, hx - 2.0, hy - 2.0, top + 8.0, 14.0, math.radians(200))
    name = f"{GROUP}_site_{stage}_{tx}x{ty}.glb"
    m.save(name)
    return name


# Waypoints -----------------------------------------------------------------------------------------

def rail_waypoint():
    """A gantry over the track with the company's sign on it."""
    m = Model()
    for y in (-6.0, 6.0):
        m.box("concrete", -0.6, 0.6, y - 0.6, y + 0.6, 0, 0.4)
        m.box("metal", -0.18, 0.18, y - 0.18, y + 0.18, 0.4, 7.2)
    m.box("metal", -0.25, 0.25, -6.3, 6.3, 7.0, 7.5)
    m.box("company", -0.1, 0.1, -2.8, 2.8, 5.4, 6.9)
    m.box("works_white", -0.14, 0.14, -2.2, 2.2, 5.9, 6.4)
    # A lamp on each post.
    for y in (-6.0, 6.0):
        m.box("light", -0.3, 0.3, y - 0.3, y + 0.3, 7.5, 7.9)
    m.save(f"{GROUP}_waypoint_rail.glb")
    return f"{GROUP}_waypoint_rail.glb"


def road_waypoint():
    """Posts on both sides of the road with the company's sign."""
    m = Model()
    for y in (-7.0, 7.0):
        m.box("concrete", -0.4, 0.4, y - 0.4, y + 0.4, 0, 0.2)
        m.box("metal", -0.1, 0.1, y - 0.1, y + 0.1, 0.2, 3.6)
        m.box("company", -0.08, 0.08, y - 0.9, y + 0.9, 2.4, 3.6)
        m.box("works_white", -0.1, 0.1, y - 0.6, y + 0.6, 2.8, 3.2)
    m.save(f"{GROUP}_waypoint_road.glb")
    return f"{GROUP}_waypoint_road.glb"


# Canal locks ---------------------------------------------------------------------------------------

DEPTH = 0.5 * H  # how deep the bed is below the lower water
TOP = 0.8  # how far the walls stand above the upper water
LEAF = 6.5  # length of a gate leaf


def lock_gate_leaf(z0, z1):
    """One leaf of a pair of mitre gates, hinged at the origin and reaching along +x, from z0 up to z1.
    The game turns it open and closed. A walkway with a railing runs along the top, and the balance beam
    reaches back from the hinge over the wall."""
    m = Model()
    m.box("wood", 0.0, LEAF, -0.25, 0.25, z0, z1)
    # Planks across the face, a little darker every so often.
    for k in range(1, int((z1 - z0) / 1.2)):
        z = z0 + k * 1.2
        m.box("dark", 0.0, LEAF, -0.27, 0.27, z - 0.06, z + 0.06)
    m.box("wood", 0.0, LEAF, -0.55, 0.25, z1 - 0.12, z1)  # walkway
    for x in (0.4, LEAF / 2, LEAF - 0.3):
        m.box("works_white", x - 0.05, x + 0.05, -0.55, -0.45, z1, z1 + 0.6)
    beam(m, "works_white", (0.2, -0.5, z1 + 0.6), (LEAF - 0.3, -0.5, z1 + 0.6), 0.05)
    # The balance beam, painted white with a black end.
    m.box("works_white", -3.6, 0.3, -0.18, 0.18, z1 + 0.15, z1 + 0.55)
    m.box("dark", -4.0, -3.6, -0.2, 0.2, z1 + 0.13, z1 + 0.57)
    return m


def lock_walls(m, x0, x1, top, bottom):
    """The walls on both sides of the chamber, from x0 to x1."""
    for y0, y1 in ((-8.0, -6.4), (6.4, 8.0)):
        m.quad("stone", (x0, y0, bottom), (x1, y0, bottom), (x1, y0, top), (x0, y0, top))
        m.quad("stone", (x1, y1, bottom), (x0, y1, bottom), (x0, y1, top), (x1, y1, top))
        m.quad("concrete", (x0, y0, top), (x1, y0, top), (x1, y1, top), (x0, y1, top))
        m.quad("stone", (x0, y1, bottom), (x0, y0, bottom), (x0, y0, top), (x0, y1, top))
        m.quad("stone", (x1, y0, bottom), (x1, y1, bottom), (x1, y1, top), (x1, y0, top))


def lock(part):
    """The three tiles of a lock are one long chamber, with high walls all along: from the bed below the lower
    water to above the upper water. The gates are models of their own (ids 3 and 4), which the game opens and
    closes as ships pass, and it draws the water in the chamber too."""
    m = Model()
    # Each part stands at the height of its highest corner: the lower part at the lower water, the others at the upper.
    base = H if part == 1 else 0.0
    top, bottom = base + TOP, base - H - DEPTH
    lock_walls(m, -8, 8, top, bottom)
    for x in (-4, 0, 4):
        for y in (-6.8, 6.8):
            m.box("dark", x - 0.2, x + 0.2, y - 0.2, y + 0.2, top, top + 0.5)  # bollards
    if part == 0:
        m.box("works_white", -2.2, 1.0, 7.0, 8.0, top, top + 2.0)  # the lock keeper's hut
        m.prism_roof("works_red", "works_white", -2.4, 1.2, 6.8, 8.2, top + 2.0, top + 2.8)
    else:
        # Ladders down the walls.
        for y in (-6.45, 6.45):
            m.box("metal", 1.6, 1.7, y - 0.05, y + 0.05, bottom, top)
            m.box("metal", 2.5, 2.6, y - 0.05, y + 0.05, bottom, top)
    name = f"{GROUP}_lock_{['middle', 'lower', 'upper'][part]}.glb"
    m.save(name)
    return name


def lock_gates():
    """The leaves of the lower gates, from the bed of the chamber to above the upper water, and of the upper gates,
    which stand on the sill at the bed of the canal above. Each stands at the height of the water outside it."""
    lock_gate_leaf(-DEPTH, H + TOP).save(f"{GROUP}_lock_gate_lower.glb")
    lock_gate_leaf(-DEPTH, TOP).save(f"{GROUP}_lock_gate_upper.glb")
    return f"{GROUP}_lock_gate_lower.glb", f"{GROUP}_lock_gate_upper.glb"


# Disasters -----------------------------------------------------------------------------------------

def ellipsoid_x(m, mat, x, y, z, length, r, seg=12, rings=8):
    """An ellipsoid stretched along x."""
    def point(i, j):
        lat = math.pi * j / rings - math.pi / 2
        lon = 2 * math.pi * i / seg
        return (x + length * math.sin(lat), y + r * math.cos(lat) * math.cos(lon), z + r * math.cos(lat) * math.sin(lon))
    for j in range(rings):
        for i in range(seg):
            a, b, c, d = point(i, j), point(i + 1, j), point(i + 1, j + 1), point(i, j + 1)
            if j == 0:
                m.triangle(mat, a, c, d)
            elif j == rings - 1:
                m.triangle(mat, a, b, c)
            else:
                m.quad(mat, a, b, c, d)


def zeppelin():
    m = Model()
    ellipsoid_x(m, "works_envelope", 0, 0, 4.0, 15.0, 3.6, seg=16, rings=12)
    for i, (dy, dz) in enumerate(((0, 1), (0, -1), (1, 0), (-1, 0))):
        # Tail fins.
        m.quad("works_red", (-10.5, dy * 2.4, 4 + dz * 2.4), (-14.5, dy * 1.0, 4 + dz * 1.0), (-15.5, dy * 5.0, 4 + dz * 5.0), (-12.0, dy * 5.0, 4 + dz * 5.0))
        m.quad("works_red", (-12.0, dy * 5.0, 4 + dz * 5.0), (-15.5, dy * 5.0, 4 + dz * 5.0), (-14.5, dy * 1.0, 4 + dz * 1.0), (-10.5, dy * 2.4, 4 + dz * 2.4))
    m.box("works_hull", -3.0, 3.5, -0.9, 0.9, -0.4, 0.8)  # gondola
    m.windows("glass", -3.0, 3.5, -0.9, 0.9, -0.4, 0.6, 1, 4, size=(0.7, 0.5), depth=0.04)
    for y in (-1.5, 1.5):
        m.box("dark", -6.0, -4.6, y - 0.4, y + 0.4, 0.6, 1.4)  # engine pods
    m.save(f"{GROUP}_zeppelin.glb")
    return f"{GROUP}_zeppelin.glb"


def ufo(name, radius, legs):
    m = Model()
    z = 1.6 if legs else 0.0
    frustum(m, "works_ufo", 0, 0, z, z + radius * 0.18, radius * 0.55, radius, 24, bottom=True)
    frustum(m, "works_ufo", 0, 0, z + radius * 0.18, z + radius * 0.3, radius, radius * 0.5, 24)
    sphere(m, "glass", 0, 0, z + radius * 0.3, radius * 0.38, rz=radius * 0.3, seg=16, rings=6, upper=True)
    for i in range(12):
        a = 2 * math.pi * i / 12
        x, y = math.cos(a) * radius * 0.92, math.sin(a) * radius * 0.92
        m.box("works_ufo_light", x - 0.25, x + 0.25, y - 0.25, y + 0.25, z + radius * 0.16, z + radius * 0.2)
    if legs:
        for i in range(4):
            a = 2 * math.pi * (i + 0.5) / 4
            x, y = math.cos(a) * radius * 0.45, math.sin(a) * radius * 0.45
            beam(m, "metal", (x, y, z + 0.5), (x * 1.3, y * 1.3, 0.2), 0.3)
            m.box("metal", x * 1.3 - 0.6, x * 1.3 + 0.6, y * 1.3 - 0.6, y * 1.3 + 0.6, 0, 0.2)
    m.save(f"{GROUP}_{name}.glb")
    return f"{GROUP}_{name}.glb"


def jet(name, colour):
    """A small fighter plane with swept wings and a single fin."""
    m = Model()
    ellipsoid_x(m, colour, 0, 0, 1.2, 6.5, 0.8, seg=10, rings=8)
    ellipsoid_x(m, "glass", 2.6, 0, 1.75, 1.6, 0.45, seg=8, rings=6)
    for s in (-1, 1):
        m.quad(colour, (1.5, 0, 1.0), (-2.5, s * 5.0, 1.0), (-4.0, s * 5.0, 1.0), (-3.0, 0, 1.0))
        m.quad(colour, (-3.0, 0, 1.0), (-4.0, s * 5.0, 1.0), (-2.5, s * 5.0, 1.0), (1.5, 0, 1.0))
        m.quad(colour, (-4.0, 0, 1.2), (-5.6, s * 2.2, 1.2), (-6.4, s * 2.2, 1.2), (-6.2, 0, 1.2))
        m.quad(colour, (-6.2, 0, 1.2), (-6.4, s * 2.2, 1.2), (-5.6, s * 2.2, 1.2), (-4.0, 0, 1.2))
    m.quad(colour, (-3.8, 0, 1.6), (-6.2, 0, 1.6), (-6.8, 0, 4.0), (-5.6, 0, 4.0))
    m.quad(colour, (-5.6, 0, 4.0), (-6.8, 0, 4.0), (-6.2, 0, 1.6), (-3.8, 0, 1.6))
    for s in (-1, 1):
        m.box("dark", -1.0, 0.6, s * 2.6 - 0.15, s * 2.6 + 0.15, 0.5, 0.95)  # missiles under the wings
    m.save(f"{GROUP}_{name}.glb")
    return f"{GROUP}_{name}.glb"


def helicopter():
    """An attack helicopter; the main rotor is a vehicle of its own."""
    m = Model()
    ellipsoid_x(m, "works_jet", 0.5, 0, 1.6, 3.0, 1.1, seg=10, rings=8)
    ellipsoid_x(m, "glass", 2.4, 0, 1.9, 1.3, 0.7, seg=8, rings=6)
    beam(m, "works_jet", (-1.5, 0, 1.9), (-7.5, 0, 2.3), 0.45)
    m.quad("works_jet", (-6.5, 0, 2.2), (-7.8, 0, 2.2), (-8.2, 0, 3.6), (-7.4, 0, 3.6))
    m.quad("works_jet", (-7.4, 0, 3.6), (-8.2, 0, 3.6), (-7.8, 0, 2.2), (-6.5, 0, 2.2))
    for s in (-1, 1):
        m.box("metal", -1.5, 2.0, s * 1.0 - 0.08, s * 1.0 + 0.08, 0, 0.12)  # skids
        m.box("metal", 0.4, 0.55, s * 1.0 - 0.06, s * 1.0 + 0.06, 0.1, 0.8)
        m.box("dark", -0.6, 0.6, s * 1.8 - 0.2, s * 1.8 + 0.2, 1.1, 1.5)  # rocket pods
    m.box("dark", -0.2, 0.2, -0.2, 0.2, 2.6, 3.1)  # rotor mast
    m.save(f"{GROUP}_helicopter.glb")
    return f"{GROUP}_helicopter.glb"


def heli_rotor():
    m = Model()
    for a in (0, math.pi / 2):
        c, s = math.cos(a), math.sin(a)
        w = 0.25
        m.quad("dark", (-5 * c - w * s, -5 * s + w * c, 3.2), (5 * c - w * s, 5 * s + w * c, 3.2), (5 * c + w * s, 5 * s - w * c, 3.2), (-5 * c + w * s, -5 * s - w * c, 3.2))
        m.quad("dark", (-5 * c + w * s, -5 * s - w * c, 3.15), (5 * c + w * s, 5 * s - w * c, 3.15), (5 * c - w * s, 5 * s + w * c, 3.15), (-5 * c - w * s, -5 * s + w * c, 3.15))
    m.save(f"{GROUP}_helicopter_rotor.glb")
    return f"{GROUP}_helicopter_rotor.glb"


def submarine(name, length):
    m = Model()
    r = length * 0.09
    ellipsoid_x(m, "works_hull", 0, 0, 0, length / 2, r, seg=12, rings=10)
    m.box("works_hull", -length * 0.05, length * 0.12, -r * 0.35, r * 0.35, 0, r * 2.2)  # tower
    m.box("works_hull", length * 0.0, length * 0.08, -r * 0.9, r * 0.9, r * 1.6, r * 1.7)  # planes on the tower
    m.box("metal", length * 0.02, length * 0.04, -0.06, 0.06, r * 2.2, r * 3.0)  # periscope
    m.quad("works_hull", (-length * 0.42, 0, 0), (-length * 0.5, 0, 0), (-length * 0.52, 0, r * 1.4), (-length * 0.46, 0, r * 1.4))
    m.quad("works_hull", (-length * 0.46, 0, r * 1.4), (-length * 0.52, 0, r * 1.4), (-length * 0.5, 0, 0), (-length * 0.42, 0, 0))
    m.save(f"{GROUP}_{name}.glb")
    return f"{GROUP}_{name}.glb"


def bulldozer():
    """The bulldozer of the road works: tracks, an engine, a cab and the blade to +x."""
    m = Model()
    for s in (-1, 1):
        m.box("tyre", -1.8, 1.8, s * 1.15 - 0.4, s * 1.15 + 0.4, 0, 0.8)
    m.box("works_yellow", -1.6, 1.0, -0.8, 0.8, 0.5, 1.5)
    m.box("works_yellow", -1.6, -0.2, -0.75, 0.75, 1.5, 2.8)
    m.box("glass", -1.5, -0.3, -0.78, 0.78, 1.8, 2.6)
    m.box("works_yellow", -1.7, -0.1, -0.85, 0.85, 2.8, 2.95)
    m.box("dark", 0.5, 0.7, 0.2, 0.4, 1.5, 2.2)  # exhaust
    m.box("works_yellow", 2.2, 2.5, -1.7, 1.7, 0, 1.1)  # blade
    for s in (-1, 1):
        beam(m, "works_yellow", (0.6, s * 0.7, 0.9), (2.3, s * 0.9, 0.5), 0.2)
    m.save(f"{GROUP}_bulldozer.glb")
    return f"{GROUP}_bulldozer.glb"


def build():
    buildings = []
    for stage in range(3):
        for plot in range(4):
            buildings.append({"type": "construction", "ids": [stage * 4 + plot], "model": building_site(stage, plot)})
    buildings.append({"type": "waypoint", "ids": [0], "model": rail_waypoint()})
    buildings.append({"type": "waypoint", "ids": [1], "model": road_waypoint()})
    for part in range(3):
        buildings.append({"type": "lock", "ids": [part], "model": lock(part)})
    lower_gate, upper_gate = lock_gates()
    buildings.append({"type": "lock", "ids": [3], "model": lower_gate})
    buildings.append({"type": "lock", "ids": [4], "model": upper_gate})
    # Disaster vehicle types: 0 zeppelin, 2 small UFO, 4 plane, 6 helicopter, 8 its rotor, 9 big UFO,
    # 11 the plane that shoots the big UFO, 13 and 14 submarines. The others are shadows.
    disasters = [
        (0, zeppelin()), (2, ufo("ufo_small", 4.5, False)), (4, jet("jet", "works_jet")), (6, helicopter()),
        (8, heli_rotor()), (9, ufo("ufo_big", 12.0, True)), (11, jet("jet_destroyer", "metal")),
        (13, submarine("submarine_small", 14.0)), (14, submarine("submarine_big", 24.0)),
    ]
    for subtype, model in disasters:
        buildings.append({"type": "disaster", "ids": [subtype], "model": model})
    buildings.append({"type": "effect", "ids": [8], "model": bulldozer()})
    return {"vehicles": [], "buildings": buildings}
