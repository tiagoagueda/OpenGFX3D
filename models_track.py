"""Track: the pieces that the 3D view lays on rail tiles in place of the track of the 2D game.

Each piece runs along x with its middle at the origin and the ground at z = 0. Straight pieces cross a whole tile
(16 long); diagonal pieces join the middles of two neighbouring tile edges (8 * sqrt(2) long). The game lays one
piece for each track on a tile, tilted along slopes.

Index type `track`, ids: 0 and 1 normal railway (also electrified), 2 and 3 monorail, 4 and 5 maglev; the even
id is the straight piece, the odd one the diagonal piece.
"""

import math

from gfx3d import MATERIALS, Model

GROUP = "track"

for name, colour in {
    "ballast": (0.47, 0.44, 0.40),
    "sleeper": (0.32, 0.24, 0.17),
    "rail": (0.55, 0.55, 0.58),
    "rail_side": (0.36, 0.30, 0.26),
    "concrete": (0.70, 0.69, 0.66),
    "guide": (0.30, 0.31, 0.34),
}.items():
    MATERIALS[f"{GROUP}_{name}"] = colour


def mat(name):
    return f"{GROUP}_{name}"


STRAIGHT = 16.0
DIAGONAL = 8.0 * math.sqrt(2)


def bed(m, x0, x1, bottom, top, height):
    """A ballast bed with sloping sides along x."""
    b, t = bottom / 2, top / 2
    z0, z1 = -0.05, height
    m.quad(mat("ballast"), (x0, -t, z1), (x1, -t, z1), (x1, t, z1), (x0, t, z1))
    m.quad(mat("ballast"), (x0, -b, z0), (x1, -b, z0), (x1, -t, z1), (x0, -t, z1))
    m.quad(mat("ballast"), (x1, b, z0), (x0, b, z0), (x0, t, z1), (x1, t, z1))
    m.quad(mat("ballast"), (x1, -b, z0), (x1, b, z0), (x1, t, z1), (x1, -t, z1))
    m.quad(mat("ballast"), (x0, b, z0), (x0, -b, z0), (x0, -t, z1), (x0, t, z1))


def rail_piece(length):
    m = Model()
    x0, x1 = -length / 2, length / 2
    bed(m, x0, x1, 7.4, 5.4, 0.22)
    count = max(1, round(length / 1.6))
    step = length / count
    for i in range(count):
        x = x0 + (i + 0.5) * step
        m.box(mat("sleeper"), x - 0.35, x + 0.35, -2.0, 2.0, 0.22, 0.34)
    for y in (-1.2, 1.2):
        m.box(mat("rail_side"), x0, x1, y - 0.12, y + 0.12, 0.34, 0.5)
        m.box(mat("rail"), x0, x1, y - 0.13, y + 0.13, 0.5, 0.56)
    return m


def monorail_piece(length):
    m = Model()
    x0, x1 = -length / 2, length / 2
    count = max(1, round(length / 5.3))
    step = length / count
    for i in range(count):
        x = x0 + (i + 0.5) * step
        m.box(mat("concrete"), x - 0.5, x + 0.5, -0.9, 0.9, -0.05, 0.2)
    m.box(mat("concrete"), x0, x1, -0.45, 0.45, 0.2, 0.62)
    m.box(mat("guide"), x0, x1, -0.47, 0.47, 0.62, 0.68)
    return m


def maglev_piece(length):
    m = Model()
    x0, x1 = -length / 2, length / 2
    m.box(mat("concrete"), x0, x1, -1.6, 1.6, -0.05, 0.15)
    m.box(mat("concrete"), x0, x1, -0.9, 0.9, 0.15, 0.72)
    for y in (-0.92, 0.92):
        m.box(mat("guide"), x0, x1, y - 0.06, y + 0.06, 0.3, 0.7)
    m.box(mat("guide"), x0, x1, -0.5, 0.5, 0.72, 0.76)
    return m


def build():
    buildings = []
    for kind, (make, base) in {"rail": (rail_piece, 0), "monorail": (monorail_piece, 2), "maglev": (maglev_piece, 4)}.items():
        for shape, length, offset in (("straight", STRAIGHT, 0), ("diagonal", DIAGONAL, 1)):
            name = f"{GROUP}_{kind}_{shape}.glb"
            make(length).save(name)
            buildings.append({"type": "track", "ids": [base + offset], "model": name})
    return {"vehicles": [], "buildings": buildings}
