"""Land: trees of all climates, farm fields with their crops, rough land and rocks.

Trees stand on their own spot of a tile (the game puts up to four on a tile and scales the growing ones), so each
tree model is one tree with its foot at the origin. Fields, rough land and rocks cover a whole tile (16 x 16) with
the ground at z = 0; the game tilts them along the slope of the tile.

These models are drawn thousands of times, so they are kept to a small number of triangles.
"""

import math
import random

from gfx3d import MATERIALS, Model
from models_industry_other import cone, rod, sphere, tank

GROUP = "land"

for name, colour in {
    "trunk": (0.36, 0.25, 0.16),
    "trunk_birch": (0.86, 0.85, 0.80),
    "trunk_palm": (0.52, 0.42, 0.28),
    "leaf": (0.20, 0.42, 0.14),
    "leaf_light": (0.36, 0.56, 0.20),
    "leaf_dark": (0.10, 0.30, 0.12),
    "leaf_blue": (0.16, 0.36, 0.34),
    "leaf_olive": (0.40, 0.46, 0.20),
    "leaf_yellow": (0.80, 0.66, 0.16),
    "leaf_orange": (0.82, 0.42, 0.12),
    "leaf_red": (0.62, 0.18, 0.10),
    "leaf_jungle": (0.12, 0.46, 0.18),
    "leaf_palm": (0.30, 0.54, 0.16),
    "leaf_dry": (0.55, 0.55, 0.25),
    "snow": (0.93, 0.95, 0.98),
    "cactus": (0.30, 0.52, 0.26),
    "flower": (0.86, 0.30, 0.40),
    "toy_pink": (0.95, 0.50, 0.70),
    "toy_blue": (0.30, 0.55, 0.95),
    "toy_yellow": (0.98, 0.85, 0.20),
    "toy_green": (0.40, 0.85, 0.35),
    "toy_purple": (0.62, 0.36, 0.86),
    "toy_red": (0.92, 0.22, 0.20),
    "toy_white": (0.95, 0.95, 0.95),
    "toy_stick": (0.92, 0.88, 0.80),
    "soil": (0.44, 0.31, 0.19),
    "soil_dark": (0.34, 0.23, 0.14),
    "sprout": (0.40, 0.54, 0.22),
    "crop_green": (0.32, 0.46, 0.18),
    "crop_lush": (0.25, 0.40, 0.15),
    "crop_yellow": (0.62, 0.58, 0.26),
    "wheat": (0.78, 0.64, 0.32),
    "stubble": (0.76, 0.66, 0.38),
    "hay": (0.84, 0.74, 0.40),
    "corn": (0.36, 0.56, 0.18),
    "stone": (0.56, 0.54, 0.50),
    "stone_dark": (0.42, 0.40, 0.38),
    "tuft": (0.34, 0.46, 0.18),
    "tuft_dry": (0.50, 0.50, 0.26),
}.items():
    MATERIALS["land_" + name] = colour


def mat(name):
    return "land_" + name


def fname(name):
    return f"{GROUP}_{name}.glb"


# ---------------------------------------------------------------------------------------------------------------
# Tree shapes. Each draws one tree with its foot at the origin; sizes are about those of the 2D game's trees.


def trunk(m, h, r=0.35, material="trunk"):
    tank(m, mat(material), 0, 0, 0, h, r, sides=5)


def round_tree(m, leaf, h=8.0, r=2.6, trunk_h=3.0, trunk_mat="trunk", lumps=2):
    """A deciduous tree: a trunk and a crown of a few blobs."""
    trunk(m, trunk_h + 0.6, 0.35, trunk_mat)
    zc = trunk_h + (h - trunk_h) / 2
    sphere(m, mat(leaf), 0, 0, zc, r, rz=(h - trunk_h) / 2, seg=7, rings=5)
    rnd = random.Random(hash((leaf, h, r)) & 0xFFFF)
    for k in range(lumps):
        a = 2 * math.pi * (k + rnd.random() * 0.5) / lumps
        sphere(m, mat(leaf), 0.45 * r * math.cos(a), 0.45 * r * math.sin(a), zc + 0.35 * r, 0.6 * r, seg=6, rings=4)


def conifer(m, leaf, h=10.0, r=2.4, tiers=3, snow=False):
    """A fir or spruce: tiers of cones on a short trunk."""
    trunk(m, 1.6, 0.3)
    z0 = 1.0
    step = (h - z0) / (tiers + 0.6)
    for t in range(tiers):
        rr = r * (1 - 0.22 * t)
        za = z0 + t * step
        cone(m, mat(leaf), 0, 0, za, za + step * 1.6, rr, sides=7)
        if snow:
            # Snow on the upper part of each tier.
            zs = za + step * 0.6
            cone(m, mat("snow"), 0, 0, zs, za + step * 1.65, rr * (1 - 0.6 / 1.6) + 0.12, sides=7)


def poplar(m, leaf, h=11.0, r=1.4):
    trunk(m, 2.2, 0.3)
    sphere(m, mat(leaf), 0, 0, 1.5 + (h - 1.5) / 2, r, rz=(h - 1.5) / 2, seg=7, rings=5)


def birch(m, leaf, h=8.5, snow=False):
    trunk(m, h * 0.7, 0.28, "trunk_birch")
    sphere(m, mat(leaf), 0, 0, h * 0.62, 1.8, rz=h * 0.3, seg=7, rings=5)
    if snow:
        sphere(m, mat("snow"), 0, 0, h * 0.62 + 0.25, 1.75, rz=h * 0.28, seg=7, rings=5, upper=True)


def bare_tree(m, h=7.5):
    """A thin leafless tree (a dead one, or one in winter)."""
    trunk(m, h * 0.6, 0.3)
    for k in range(4):
        a = 2 * math.pi * k / 4 + 0.4
        rod(m, mat("trunk"), (0, 0, h * 0.45), (1.8 * math.cos(a), 1.8 * math.sin(a), h * (0.85 + 0.05 * k)), 0.12, 4, caps=False)


def palm(m, h=9.0, lean=0.8, fronds=6, leaf="leaf_palm"):
    top = (lean, 0, h)
    rod(m, mat("trunk_palm"), (0, 0, 0), top, 0.32, 5)
    for k in range(fronds):
        a = 2 * math.pi * k / fronds
        tip = (top[0] + 3.2 * math.cos(a), 3.2 * math.sin(a), h - 1.6)
        mid = (top[0] + 1.6 * math.cos(a), 1.6 * math.sin(a), h + 0.5)
        side = (-0.6 * math.sin(a), 0.6 * math.cos(a), 0)
        for p, q in ((top, mid), (mid, tip)):
            m.quad(mat(leaf), (p[0] - side[0], p[1] - side[1], p[2]), (p[0] + side[0], p[1] + side[1], p[2]),
                   (q[0] + side[0], q[1] + side[1], q[2]), (q[0] - side[0], q[1] - side[1], q[2]))
            m.quad(mat(leaf), (q[0] - side[0], q[1] - side[1], q[2]), (q[0] + side[0], q[1] + side[1], q[2]),
                   (p[0] + side[0], p[1] + side[1], p[2]), (p[0] - side[0], p[1] - side[1], p[2]))


def jungle_tree(m, leaf, h=10.0, r=3.2):
    """A tall rainforest tree with a flat wide crown and a lower layer of leaves."""
    trunk(m, h - 1.5, 0.4)
    sphere(m, mat(leaf), 0, 0, h - 1.0, r, rz=1.4, seg=8, rings=4)
    sphere(m, mat(leaf), 0.6, 0.4, h * 0.55, r * 0.6, rz=1.1, seg=6, rings=4)


def acacia(m, leaf="leaf_olive", h=7.0):
    rod(m, mat("trunk"), (0, 0, 0), (0.5, 0, h * 0.55), 0.3, 5)
    rod(m, mat("trunk"), (0.5, 0, h * 0.55), (1.6, 0.6, h - 1.0), 0.2, 4)
    rod(m, mat("trunk"), (0.5, 0, h * 0.55), (-0.8, -0.6, h - 1.0), 0.2, 4)
    sphere(m, mat(leaf), 0.4, 0, h - 0.6, 3.2, rz=0.8, seg=8, rings=4)


def bush_tree(m, leaf, h=5.0, r=2.2, flowers=False):
    trunk(m, 1.2, 0.3)
    sphere(m, mat(leaf), 0, 0, h / 2 + 0.4, r, rz=h / 2, seg=7, rings=5)
    if flowers:
        for k in range(5):
            a = 2 * math.pi * k / 5
            sphere(m, mat("flower"), r * 0.8 * math.cos(a), r * 0.8 * math.sin(a), h / 2 + 0.8 + 0.6 * (k % 2), 0.4, seg=4, rings=3)


def cactus(m, h=6.0):
    tank(m, mat("cactus"), 0, 0, 0, h, 0.7, sides=6)
    sphere(m, mat("cactus"), 0, 0, h, 0.7, seg=6, rings=3, upper=True)
    for (y, z0, z1) in ((1.0, 2.2, 4.2), (-1.0, 3.0, 5.0)):
        rod(m, mat("cactus"), (0, 0, z0), (0, y * 1.6, z0), 0.4, 5)
        tank(m, mat("cactus"), 0, y * 1.6, z0 - 0.3, z1, 0.4, sides=5)


def lollipop(m, colour, h=7.0, r=2.2):
    tank(m, mat("toy_stick"), 0, 0, 0, h - r, 0.25, sides=5)
    sphere(m, mat(colour), 0, 0, h - r * 0.8, r, seg=8, rings=5)


def toy_cone(m, colour, h=8.0, r=2.4):
    tank(m, mat("toy_stick"), 0, 0, 0, 1.6, 0.3, sides=5)
    cone(m, mat(colour), 0, 0, 1.4, h, r, sides=8)


def toy_cube(m, colour, h=6.5, s=1.8):
    tank(m, mat("toy_stick"), 0, 0, 0, h - 2 * s, 0.3, sides=5)
    m.box(mat(colour), -s, s, -s, s, h - 2 * s, h)


def toy_stack(m, colours, h=8.0):
    tank(m, mat("toy_stick"), 0, 0, 0, 1.4, 0.3, sides=5)
    z = 1.2
    for k, c in enumerate(colours):
        r = 2.0 - 0.45 * k
        sphere(m, mat(c), 0, 0, z + r * 0.8, r, rz=r * 0.8, seg=7, rings=4)
        z += r * 1.5


# Tree type -> (name, drawing function). Types as in the game: 0x00 temperate (12), 0x0C sub-arctic (8),
# 0x14 rainforest (7), 0x1B cactus, 0x1C sub-tropical (4), 0x20 toyland (9).
TREES = {
    0x00: ("oak", lambda m: round_tree(m, "leaf", 8.5, 2.8)),
    0x01: ("fir", lambda m: conifer(m, "leaf_dark", 10.5, 2.4, 3)),
    0x02: ("lime", lambda m: round_tree(m, "leaf_light", 8.0, 2.6)),
    0x03: ("birch", lambda m: birch(m, "leaf_light")),
    0x04: ("poplar", lambda m: poplar(m, "leaf")),
    0x05: ("red_maple", lambda m: round_tree(m, "leaf_red", 7.5, 2.6)),
    0x06: ("golden_beech", lambda m: round_tree(m, "leaf_yellow", 8.0, 2.6)),
    0x07: ("blue_spruce", lambda m: conifer(m, "leaf_blue", 9.5, 2.2, 3)),
    0x08: ("orange_elm", lambda m: round_tree(m, "leaf_orange", 8.0, 2.5)),
    0x09: ("pine", lambda m: conifer(m, "leaf_dark", 12.0, 2.0, 4)),
    0x0A: ("chestnut", lambda m: round_tree(m, "leaf_dark", 9.0, 3.0, lumps=3)),
    0x0B: ("young_ash", lambda m: round_tree(m, "leaf_olive", 7.0, 2.2)),
    0x0C: ("arctic_fir", lambda m: conifer(m, "leaf_dark", 10.5, 2.4, 3)),
    0x0D: ("arctic_spruce", lambda m: conifer(m, "leaf_blue", 9.5, 2.2, 3)),
    0x0E: ("arctic_pine", lambda m: conifer(m, "leaf_dark", 12.0, 2.0, 4)),
    0x0F: ("arctic_birch", lambda m: birch(m, "leaf_olive")),
    0x10: ("arctic_larch", lambda m: conifer(m, "leaf_olive", 10.0, 2.2, 3)),
    0x11: ("arctic_bare", lambda m: bare_tree(m)),
    0x12: ("arctic_round", lambda m: round_tree(m, "leaf_dark", 7.5, 2.4)),
    0x13: ("arctic_tall_fir", lambda m: conifer(m, "leaf", 12.5, 2.2, 4)),
    0x14: ("jungle_tall", lambda m: jungle_tree(m, "leaf_jungle")),
    0x15: ("jungle_palm", lambda m: palm(m, 9.5)),
    0x16: ("jungle_broad", lambda m: jungle_tree(m, "leaf_dark", 8.5, 3.4)),
    0x17: ("banana", lambda m: palm(m, 6.0, 0.3, 7, "leaf_light")),
    0x18: ("jungle_round", lambda m: round_tree(m, "leaf_jungle", 8.5, 2.8, lumps=3)),
    0x19: ("flowering_bush", lambda m: bush_tree(m, "leaf_jungle", 5.5, 2.4, True)),
    0x1A: ("tall_palm", lambda m: palm(m, 11.0, 1.2)),
    0x1B: ("cactus", lambda m: cactus(m)),
    0x1C: ("date_palm", lambda m: palm(m, 9.0, 0.6, 6, "leaf_olive")),
    0x1D: ("acacia", lambda m: acacia(m)),
    0x1E: ("dry_bush", lambda m: bush_tree(m, "leaf_dry", 4.5, 2.0)),
    0x1F: ("olive", lambda m: round_tree(m, "leaf_olive", 6.5, 2.4)),
    0x20: ("toy_lollipop_pink", lambda m: lollipop(m, "toy_pink")),
    0x21: ("toy_cone_green", lambda m: toy_cone(m, "toy_green")),
    0x22: ("toy_cube_blue", lambda m: toy_cube(m, "toy_blue")),
    0x23: ("toy_lollipop_yellow", lambda m: lollipop(m, "toy_yellow", 8.0, 2.4)),
    0x24: ("toy_stack", lambda m: toy_stack(m, ("toy_red", "toy_white", "toy_red"))),
    0x25: ("toy_cone_purple", lambda m: toy_cone(m, "toy_purple", 9.0, 2.2)),
    0x26: ("toy_lollipop_red", lambda m: lollipop(m, "toy_red", 6.5, 2.0)),
    0x27: ("toy_cube_yellow", lambda m: toy_cube(m, "toy_yellow", 7.0, 1.6)),
    0x28: ("toy_stack_green", lambda m: toy_stack(m, ("toy_green", "toy_yellow", "toy_blue"))),
}

# Trees above the snow line: the game draws the sub-arctic ones with snow on them; their ids are the type + 0x40.
SNOWY = {
    0x0C: ("arctic_fir_snow", lambda m: conifer(m, "leaf_dark", 10.5, 2.4, 3, snow=True)),
    0x0D: ("arctic_spruce_snow", lambda m: conifer(m, "leaf_blue", 9.5, 2.2, 3, snow=True)),
    0x0E: ("arctic_pine_snow", lambda m: conifer(m, "leaf_dark", 12.0, 2.0, 4, snow=True)),
    0x0F: ("arctic_birch_snow", lambda m: birch(m, "leaf_olive", snow=True)),
    0x10: ("arctic_larch_snow", lambda m: conifer(m, "leaf_olive", 10.0, 2.2, 3, snow=True)),
    0x11: ("arctic_bare_snow", lambda m: bare_tree(m)),
    0x12: ("arctic_round_snow", lambda m: (round_tree(m, "leaf_dark", 7.5, 2.4),
                                           sphere(m, mat("snow"), 0, 0, 5.35, 2.5, rz=2.35, seg=7, rings=4, upper=True))),
    0x13: ("arctic_tall_fir_snow", lambda m: conifer(m, "leaf", 12.5, 2.2, 4, snow=True)),
}


# ---------------------------------------------------------------------------------------------------------------
# Fields, by the game's field state 0-8: ploughed, then the crop growing in seven steps, then harvested with hay.


def rows(m, material, height, width=1.2, count=7, margin=1.0, base=0.0):
    """Rows of a crop along x, as long ridges with a triangular top."""
    span = 16 - 2 * margin
    for i in range(count):
        y = -8 + margin + (i + 0.5) * span / count
        y0, y1 = y - width / 2, y + width / 2
        x0, x1 = -8 + margin, 8 - margin
        m.triangle(material, (x1, y0, base), (x1, y1, base), (x1, y, base + height))
        m.triangle(material, (x0, y1, base), (x0, y0, base), (x0, y, base + height))
        m.quad(material, (x0, y0, base), (x1, y0, base), (x1, y, base + height), (x0, y, base + height))
        m.quad(material, (x1, y1, base), (x0, y1, base), (x0, y, base + height), (x1, y, base + height))


def tufts(m, material, height, r, count=7, per_row=7, margin=1.2, seed=0):
    """Rows of small plants as little pyramids."""
    rnd = random.Random(seed)
    span = 16 - 2 * margin
    for i in range(count):
        y = -8 + margin + (i + 0.5) * span / count
        for j in range(per_row):
            x = -8 + margin + (j + 0.5) * span / per_row + rnd.uniform(-0.3, 0.3)
            h = height * rnd.uniform(0.8, 1.15)
            m.pyramid(material, x - r, x + r, y - r, y + r, 0, h)


def field(m, state):
    if state == 0:  # ploughed: furrows of dark soil
        rows(m, mat("soil_dark"), 0.25, 1.6, 8, 0.6)
    elif state == 1:  # sown, the first shoots
        rows(m, mat("soil_dark"), 0.18, 1.4, 7)
        tufts(m, mat("sprout"), 0.5, 0.25, 7, 9, seed=1)
    elif state == 2:  # young plants
        tufts(m, mat("sprout"), 0.9, 0.45, 7, 8, seed=2)
    elif state == 3:  # green rows
        rows(m, mat("crop_green"), 1.0, 1.5, 7)
    elif state == 4:  # full green crop
        rows(m, mat("crop_lush"), 1.4, 1.6, 7, 0.8)
    elif state == 5:  # ripening
        rows(m, mat("crop_yellow"), 1.6, 1.7, 7, 0.8)
    elif state == 6:  # ripe wheat
        rows(m, mat("wheat"), 1.8, 1.7, 7, 0.8)
    elif state == 7:  # harvested: stubble
        rows(m, mat("stubble"), 0.3, 1.8, 7, 0.8)
    elif state == 8:  # stubble with hay bales
        rows(m, mat("stubble"), 0.3, 1.8, 7, 0.8)
        rnd = random.Random(8)
        for (x, y) in ((-4.5, -4), (1.5, -4.5), (-2, 1), (4.5, 0.5), (-4.5, 5), (2, 5)):
            m.cylinder(mat("hay"), x - 0.9, x + 0.9, y + rnd.uniform(-0.5, 0.5), 1.0, 1.0, sides=8)


# ---------------------------------------------------------------------------------------------------------------
# Rough land and rocks; each has a few versions that the game picks by tile.


def boulder(m, material, x, y, r, h, seed):
    rnd = random.Random(seed)
    sides = 6
    ring = [(x + r * rnd.uniform(0.75, 1.1) * math.cos(2 * math.pi * i / sides), y + r * rnd.uniform(0.75, 1.1) * math.sin(2 * math.pi * i / sides)) for i in range(sides)]
    mid = [(x + 0.55 * (px - x), y + 0.55 * (py - y)) for px, py in ring]
    top = (x + rnd.uniform(-0.2, 0.2) * r, y + rnd.uniform(-0.2, 0.2) * r, h)
    for i in range(sides):
        a, b = ring[i], ring[(i + 1) % sides]
        c, d = mid[i], mid[(i + 1) % sides]
        m.quad(material, (a[0], a[1], -0.1), (b[0], b[1], -0.1), (d[0], d[1], h * 0.7), (c[0], c[1], h * 0.7))
        m.triangle(material, (c[0], c[1], h * 0.7), (d[0], d[1], h * 0.7), top)


def rocks(m, seed):
    rnd = random.Random(100 + seed)
    for k in range(7):
        x, y = rnd.uniform(-6, 6), rnd.uniform(-6, 6)
        r = rnd.uniform(0.9, 2.2)
        boulder(m, mat("stone" if k % 3 else "stone_dark"), x, y, r, r * rnd.uniform(0.6, 1.0), seed * 10 + k)


def rough(m, seed):
    rnd = random.Random(200 + seed)
    for k in range(3):
        x, y = rnd.uniform(-6, 6), rnd.uniform(-6, 6)
        boulder(m, mat("stone"), x, y, rnd.uniform(0.4, 0.8), 0.5, seed * 10 + k)
    for k in range(9):
        x, y = rnd.uniform(-7, 7), rnd.uniform(-7, 7)
        r = rnd.uniform(0.35, 0.6)
        m.pyramid(mat("tuft" if k % 2 else "tuft_dry"), x - r, x + r, y - r, y + r, 0, rnd.uniform(0.5, 1.0))
        m.pyramid(mat("tuft"), x - r + 0.3, x + r + 0.3, y - r * 0.6, y + r * 0.6, 0, rnd.uniform(0.4, 0.8))


VARIANTS = 4  # versions of rough land and of rocks
TREE_SCALE = 1.3  # the trees of the 2D game are a little bigger than these models


# ---------------------------------------------------------------------------------------------------------------
# Far away versions: each material of a tree becomes one simple shape of the same size and colour.


def far_version(model):
    """A version of a model with a few triangles per material: a cone for cone-like parts, else a double cone."""
    far = Model()
    sides = 5
    for material, (positions, _) in model.parts.items():
        xs = [p[0] for p in positions]
        ys = [p[1] for p in positions]
        zs = [p[2] for p in positions]
        x, y = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        z0, z1 = min(zs), max(zs)
        r = max(max(xs) - min(xs), max(ys) - min(ys)) / 2
        if r < 0.05 or z1 - z0 < 0.05:
            continue
        # Where is it widest? Cones are widest near the bottom.
        widest = max(positions, key=lambda p: (p[0] - x) ** 2 + (p[1] - y) ** 2)[2]
        zw = min(max(widest, z0), z1)
        ring = [(x + r * math.cos(2 * math.pi * i / sides), y + r * math.sin(2 * math.pi * i / sides)) for i in range(sides)]
        for i in range(sides):
            (ax, ay), (bx, by) = ring[i], ring[(i + 1) % sides]
            far.triangle(material, (ax, ay, zw), (bx, by, zw), (x, y, z1))
            if zw - z0 > 0.05:
                far.triangle(material, (bx, by, zw), (ax, ay, zw), (x, y, z0))
    return far


# ---------------------------------------------------------------------------------------------------------------


def build():
    buildings = []
    for tree_type, (name, draw) in list(TREES.items()) + [(t + 0x40, v) for t, v in SNOWY.items()]:
        m = Model()
        draw(m)
        m.save(fname("tree_" + name))
        far_version(m).save(fname("tree_" + name + "_far"))
        buildings.append({"type": "tree", "ids": [tree_type], "model": fname("tree_" + name), "scale": TREE_SCALE,
                          "far": fname("tree_" + name + "_far")})
    for state in range(9):
        m = Model()
        field(m, state)
        m.save(fname(f"field_{state}"))
        buildings.append({"type": "field", "ids": [state], "model": fname(f"field_{state}")})
    for kind, draw in (("rough", rough), ("rocks", rocks)):
        for v in range(VARIANTS):
            m = Model()
            draw(m, v)
            m.save(fname(f"{kind}_{v}"))
            # Small stones and tufts are left out far away.
            buildings.append({"type": kind, "ids": [v], "model": fname(f"{kind}_{v}"), "far": ""})
    return {"vehicles": [], "buildings": buildings}
