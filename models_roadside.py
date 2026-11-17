"""Things along roads: street lamps, trees in the pavement, pavements and tram rails.

Index type `roadside`, ids:
    0 a street lamp standing at its origin, its arm reaching along +x over the road;
    1 a tree in the pavement, standing at its origin;
    2 a straight piece of pavement, running along x over a whole tile edge (16 long) with its middle at the
      origin; the kerb is on its +y side, towards the road;
    3 a square of pavement for the corner of a tile, centred on the origin;
    4 tram rails from the middle of a tile to one edge: along x from 0 to 8, laid into the road.
"""

import math

from gfx3d import MATERIALS, Model

GROUP = "roadside"

for name, colour in {
    "pole": (0.30, 0.32, 0.34),
    "lamp": (1.00, 0.95, 0.75),
    "paving": (0.66, 0.64, 0.60),
    "kerb": (0.78, 0.77, 0.74),
    "bark": (0.40, 0.29, 0.19),
    "leaves": (0.24, 0.50, 0.20),
    "leaves_light": (0.32, 0.58, 0.25),
    "planter": (0.50, 0.47, 0.42),
    "rail": (0.58, 0.58, 0.60),
}.items():
    MATERIALS[f"{GROUP}_{name}"] = colour


def mat(name):
    return f"{GROUP}_{name}"


PAVEMENT = 2.6  # width of a pavement
KERB = 0.16  # height of the kerb above the road


def street_lamp():
    m = Model()
    m.box(mat("pole"), -0.2, 0.2, -0.2, 0.2, 0, 0.4)
    m.box(mat("pole"), -0.09, 0.09, -0.09, 0.09, 0.4, 4.6)
    m.box(mat("pole"), -0.07, 1.5, -0.07, 0.07, 4.5, 4.62)
    m.box(mat("pole"), 1.1, 1.7, -0.2, 0.2, 4.35, 4.55)
    m.box(mat("lamp"), 1.15, 1.65, -0.15, 0.15, 4.28, 4.36)
    return m


def roadside_tree():
    m = Model()
    m.box(mat("planter"), -0.55, 0.55, -0.55, 0.55, 0, 0.2)
    m.box(mat("bark"), -0.13, 0.13, -0.13, 0.13, 0.2, 2.6)
    # A rounded crown of a few boxes.
    for (x, y, z, r, leaves) in ((0, 0, 3.4, 1.2, "leaves"), (0.5, 0.3, 2.9, 0.8, "leaves_light"),
                                 (-0.5, -0.2, 3.0, 0.8, "leaves_light"), (0.1, -0.5, 4.1, 0.7, "leaves")):
        m.box(mat(leaves), x - r, x + r, y - r, y + r, z - r * 0.8, z + r * 0.8)
    return m


def pavement():
    m = Model()
    m.box(mat("paving"), -8, 8, -PAVEMENT / 2, PAVEMENT / 2 - 0.2, 0, KERB)
    m.box(mat("kerb"), -8, 8, PAVEMENT / 2 - 0.2, PAVEMENT / 2, 0, KERB + 0.02)
    return m


def pavement_corner():
    m = Model()
    m.box(mat("paving"), -PAVEMENT / 2, PAVEMENT / 2, -PAVEMENT / 2, PAVEMENT / 2, 0, KERB)
    return m


def tram_rails():
    m = Model()
    for y in (-1.2, 1.2):
        m.box(mat("rail"), 0, 8, y - 0.12, y + 0.12, 0, 0.05)
    return m


def build():
    buildings = []
    for i, (name, make) in enumerate((("lamp", street_lamp), ("tree", roadside_tree), ("pavement", pavement),
                                      ("pavement_corner", pavement_corner), ("tram_rails", tram_rails))):
        filename = f"{GROUP}_{name}.glb"
        make().save(filename)
        buildings.append({"type": "roadside", "ids": [i], "model": filename})
    return {"vehicles": [], "buildings": buildings}
