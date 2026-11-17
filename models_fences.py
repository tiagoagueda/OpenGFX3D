"""Fences, hedges and walls: the edges of rail tiles and farm fields.

Each one runs along x for one tile edge (16 long), with its middle at the origin, standing on z = 0 and centred on
y = 0. The game shears it along slopes and stretches it for the diagonal fences of rail tiles.

Index type `fence`, ids: 0 the fence along railways; 1 to 6 the edges of fields as the game numbers them
(1 hedge, 2 hedge with a gate, 3 wooden fence, 4 hedge with yellow flowers, 5 hedge with red flowers, 6 stone wall).
"""

import random

from gfx3d import MATERIALS, Model

GROUP = "fence"

for name, colour in {
    "rail_post": (0.58, 0.62, 0.68),
    "rail_wire": (0.72, 0.75, 0.80),
    "wood": (0.48, 0.35, 0.22),
    "wood_light": (0.62, 0.47, 0.30),
    "hedge": (0.20, 0.42, 0.16),
    "hedge_dark": (0.15, 0.34, 0.13),
    "yellow": (0.95, 0.85, 0.25),
    "red": (0.88, 0.22, 0.20),
    "stone": (0.58, 0.56, 0.52),
    "stone_dark": (0.46, 0.44, 0.41),
}.items():
    MATERIALS[f"{GROUP}_{name}"] = colour


def mat(name):
    return f"{GROUP}_{name}"


LENGTH = 16.0
X0, X1 = -LENGTH / 2, LENGTH / 2


def rail_fence():
    m = Model()
    count = 8
    for i in range(count + 1):
        x = X0 + 0.1 + i * (LENGTH - 0.2) / count
        m.box(mat("rail_post"), x - 0.09, x + 0.09, -0.09, 0.09, 0, 1.3)
    for z in (0.55, 1.15):
        m.box(mat("rail_wire"), X0, X1, -0.04, 0.04, z, z + 0.08)
    return m


def wooden_fence(m=None, x0=X0, x1=X1):
    m = m or Model()
    count = max(1, round((x1 - x0) / 2.6))
    for i in range(count + 1):
        x = x0 + 0.12 + i * (x1 - x0 - 0.24) / count
        m.box(mat("wood"), x - 0.12, x + 0.12, -0.12, 0.12, 0, 1.25)
    for z in (0.35, 0.75, 1.05):
        m.box(mat("wood_light"), x0, x1, -0.06, 0.06, z, z + 0.14)
    return m


def hedge(seed, flowers=None, gate=False):
    rng = random.Random(seed)
    m = Model()
    x = X0
    gap = (-1.6, 1.6) if gate else None
    while x < X1 - 0.01:
        step = min(rng.uniform(1.0, 1.8), X1 - x)
        if gap and x + step > gap[0] and x < gap[1]:
            if x < gap[0]:
                step = gap[0] - x
            else:
                x = gap[1]
                continue
        w = rng.uniform(0.75, 1.0)
        h = rng.uniform(1.15, 1.6)
        m.box(mat(rng.choice(("hedge", "hedge", "hedge_dark"))), x, x + step, -w / 2, w / 2, 0, h)
        if flowers:
            for _ in range(rng.randint(1, 3)):
                fx = rng.uniform(x + 0.15, x + step - 0.15)
                fy = rng.choice((-1, 1)) * (w / 2)
                fz = rng.uniform(0.4, h - 0.2)
                m.box(mat(flowers), fx - 0.13, fx + 0.13, fy - 0.05, fy + 0.05, fz - 0.13, fz + 0.13)
            fx = rng.uniform(x + 0.2, x + step - 0.2)
            m.box(mat(flowers), fx - 0.15, fx + 0.15, -0.15, 0.15, h, h + 0.08)
        x += step
    if gate:
        for gx in gap:
            m.box(mat("wood"), gx - 0.14, gx + 0.14, -0.14, 0.14, 0, 1.4)
        for z in (0.35, 0.8, 1.15):
            m.box(mat("wood_light"), gap[0], gap[1], -0.05, 0.05, z, z + 0.12)
        m.box(mat("wood_light"), -0.07, 0.07, -0.05, 0.05, 0.35, 1.25)
    return m


def stone_wall(seed):
    rng = random.Random(seed)
    m = Model()
    m.box(mat("stone_dark"), X0, X1, -0.32, 0.32, 0, 0.75)
    # Stones along the top and sides, so the wall looks laid by hand.
    x = X0
    while x < X1 - 0.01:
        step = min(rng.uniform(0.5, 0.9), X1 - x)
        h = rng.uniform(0.8, 0.98)
        m.box(mat("stone"), x + 0.02, x + step - 0.02, -0.35, 0.35, 0.72, h)
        x += step
    for row in (0.12, 0.42):
        x = X0 + rng.uniform(0, 0.4)
        while x < X1 - 0.5:
            step = rng.uniform(0.5, 0.9)
            side = rng.choice((-1, 1))
            m.box(mat("stone"), x, min(x + step - 0.06, X1), side * 0.32 - 0.02, side * 0.32 + 0.02, row, row + 0.24)
            x += step
    return m


def build():
    models = {
        0: ("rail", rail_fence()),
        1: ("hedge", hedge(1)),
        2: ("hedge_gate", hedge(2, gate=True)),
        3: ("wooden", wooden_fence()),
        4: ("hedge_yellow", hedge(4, flowers="yellow")),
        5: ("hedge_red", hedge(5, flowers="red")),
        6: ("stone_wall", stone_wall(6)),
    }
    buildings = []
    for i, (name, model) in models.items():
        filename = f"{GROUP}_{name}.glb"
        model.save(filename)
        buildings.append({"type": "fence", "ids": [i], "model": filename})
    return {"vehicles": [], "buildings": buildings}
