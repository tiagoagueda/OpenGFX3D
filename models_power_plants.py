#!/usr/bin/env python3
"""Industry tiles of the power plants that the power lines fork adds to the base game.

Index type `industry_tile`, ids (the game's industry tiles, see src/industry_type.h):
  175 oil power station: turbine hall with a tall exhaust stack;
  176 oil power station: oil tanks in a bund;
  177 solar power plant: rows of panels;
  178 solar power plant: inverter house with a transformer;
  179 wind farm: a wind turbine; its rotor is a moving part (power_plant_wind_rotor.glb);
  180 hydro power station: dam across a river flowing along x;
  181 hydro power station: dam across a river flowing along y;
  182 hydro power station: powerhouse on the bank.

The oil power station also uses tile 10, the transformer yard of the coal power station.
Every model is one tile, 16 by 16, centred on the origin, front (+x) to the south-west, as in
models_industry_temperate.py. The panels and turbines have no ground plate: they stand on the land as it is.
make_sprites.py draws the 2D sprites of the game from these models.
"""

import math

from gfx3d import MATERIALS, Model, rotated_z
from models_industry_temperate import beam, frustum, ground, railing, tank

GROUP = "power_plant"

for _name, _colour in {
    "cladding": (0.78, 0.80, 0.80),
    "cladding_dark": (0.56, 0.60, 0.62),
    "stack": (0.70, 0.70, 0.68),
    "panel": (0.10, 0.16, 0.34),
    "panel_frame": (0.70, 0.72, 0.74),
    "grass": (0.36, 0.52, 0.25),
    "gravel": (0.62, 0.60, 0.55),
    "tower": (0.93, 0.94, 0.94),
    "blade": (0.96, 0.96, 0.95),
    "dam": (0.70, 0.69, 0.65),
    "dam_dark": (0.42, 0.42, 0.42),
    "water_foam": (0.85, 0.92, 0.95),
    "reservoir": (0.20, 0.38, 0.54),
    "pipe": (0.42, 0.46, 0.50),
    "transformer": (0.36, 0.42, 0.38),
    "insulator": (0.62, 0.46, 0.34),
}.items():
    MATERIALS[f"{GROUP}_{_name}"] = _colour

# Where the rotor of a wind turbine turns, in the tile of the turbine; the game turns the rotor model around x there.
WIND_HUB = (1.9, 0.0, 34.0)
WIND_RADIUS = 11.0


def mat(name):
    return f"{GROUP}_{name}"


def fname(name):
    return f"{GROUP}_{name}.glb"


def transformer(m, x, y):
    m.box("concrete", x - 2.2, x + 2.2, y - 1.8, y + 1.8, 0.0, 0.4)
    m.box(mat("transformer"), x - 1.5, x + 1.5, y - 1.1, y + 1.1, 0.4, 3.2)
    for i in range(6):
        fx = x - 1.3 + i * 0.52
        for sy in (-1, 1):
            m.box(mat("transformer"), fx - 0.05, fx + 0.05, y + sy * 1.1, y + sy * 1.6, 0.7, 2.9)
    for dx in (-0.8, 0.0, 0.8):
        frustum(m, mat("insulator"), x + dx, y, 3.2, 4.5, 0.25, 0.15, 6)


def oil_hall():
    """The turbine hall: a clad steel shed with a company stripe, and a tall exhaust stack at the back."""
    m = Model()
    ground(m, "concrete")
    m.box(mat("cladding"), -7, 5, -7, 7, 0, 9)
    m.box("company", -7.05, 5.05, -7.05, 7.05, 7.2, 8.0)
    m.box(mat("cladding_dark"), -7.2, 5.2, -7.2, 7.2, 9, 9.5)
    # Roof vents.
    for y in (-4, 0, 4):
        m.box(mat("cladding_dark"), -3, 1, y - 0.8, y + 0.8, 9.5, 10.4)
    m.windows("glass", -7, 5, -7, 7, 2, 6.5, 1, 4, size=(1.6, 2.6))
    m.box("door", 5, 5.1, -2, 2, 0, 4.5)
    # Exhaust stack and the duct from the hall.
    frustum(m, mat("stack"), -4.5, -4.5, 9, 26, 1.4, 1.1, 12)
    for z in (20.0, 24.5):
        frustum(m, "company", -4.5, -4.5, z, z + 0.8, 1.25, 1.2, 12)
    frustum(m, "dark", -4.5, -4.5, 26, 26.2, 0.9, 0.9, 12)
    m.box(mat("pipe"), 5, 7.5, 3.5, 5.5, 0, 2.5)  # air intake
    return m


def oil_tanks():
    m = Model()
    ground(m, "indt_asphalt")
    tank(m, "company", -2.2, -2.2, 0, 7.5, 4.2, 16, roof="indt_white")
    tank(m, "indt_white", 4.0, 4.0, 0, 5.5, 2.6, 14)
    for a, b in (((-7.5, -7.5), (7.5, -7.5)), ((7.5, -7.5), (7.5, 7.5)), ((7.5, 7.5), (-7.5, 7.5)), ((-7.5, 7.5), (-7.5, -7.5))):
        x0, x1 = sorted((a[0], b[0]))
        y0, y1 = sorted((a[1], b[1]))
        m.box("concrete", x0 - 0.15, x1 + 0.15, y0 - 0.15, y1 + 0.15, 0, 0.9)
    beam(m, mat("pipe"), (2.0, -2.2, 0.8), (7.5, -2.2, 0.8), 0.45)
    beam(m, mat("pipe"), (4.0, 1.4, 0.8), (4.0, -2.2, 0.8), 0.35)
    # A ladder up the big tank.
    m.box("indt_steel", 1.95, 2.15, -0.6, 0.6, 0, 7.6)
    return m


def solar_row(m, x, y0, y1):
    """One row of panels along y, tilted to face the sun in the south-west (+x)."""
    low, high, depth = 0.9, 2.9, 2.8
    xf, xb = x + depth / 2, x - depth / 2
    t = 0.08
    m.quad(mat("panel"), (xf, y0, low + t), (xf, y1, low + t), (xb, y1, high + t), (xb, y0, high + t))
    m.quad(mat("panel_frame"), (xb, y0, high), (xb, y1, high), (xf, y1, low), (xf, y0, low))
    m.box(mat("panel_frame"), xf - 0.08, xf + 0.08, y0, y1, low - 0.1, low + t + 0.02)
    for y in (y0 + 0.4, (y0 + y1) / 2, y1 - 0.4):
        m.box(mat("panel_frame"), xf - 0.5, xf - 0.3, y - 0.1, y + 0.1, 0, low + 0.2)
        m.box(mat("panel_frame"), xb + 0.3, xb + 0.5, y - 0.1, y + 0.1, 0, high)


def solar_panels():
    m = Model()
    for x in (-5.4, -1.8, 1.8, 5.4):
        solar_row(m, x, -7.4, 7.4)
    return m


def solar_inverter():
    m = Model()
    ground(m, mat("gravel"))
    m.box("concrete", -6.5, -0.5, -6.5, 0.5, 0, 3.6)
    m.box(mat("cladding_dark"), -6.7, -0.3, -6.7, 0.7, 3.6, 4.0)
    m.box("company", -6.55, -0.45, -6.55, 0.55, 2.8, 3.2)
    m.box("door", -0.5, -0.4, -4.0, -2.4, 0, 2.4)
    transformer(m, 3.6, -3.8)
    solar_row(m, -1.8, 2.4, 7.4)
    solar_row(m, 1.8, 2.4, 7.4)
    solar_row(m, 5.4, 2.4, 7.4)
    # Fence posts along the yard.
    for y in (-7.3, -3.0, 1.5):
        m.box("indt_steel", 7.2, 7.4, y - 0.1, y + 0.1, 0, 1.6)
    beam(m, "indt_steel", (7.3, -7.3, 1.5), (7.3, 1.5, 1.5), 0.08)
    return m


def wind_tower():
    """A wind turbine without its rotor: tapering tower, nacelle and hub."""
    m = Model()
    frustum(m, "concrete", 0, 0, 0, 0.5, 2.2, 2.2, 14)
    frustum(m, mat("tower"), 0, 0, 0.5, 33.2, 1.15, 0.6, 14)
    m.box("door", 1.05, 1.15, -0.4, 0.4, 0.5, 2.5)
    # The nacelle, facing the wind from +x, with the company colour on its side.
    hx, hy, hz = WIND_HUB
    m.box(mat("tower"), -2.6, hx - 0.6, -0.9, 0.9, 32.9, 35.0)
    m.box("company", -2.0, 0.6, -0.92, 0.92, 33.6, 34.2)
    m.cylinder(mat("tower"), hx - 0.7, hx - 0.1, hy, hz, 0.75, sides=12)
    return m


def wind_rotor():
    """The rotor of a wind turbine, turning around x: hub and three blades in the y-z plane, centred on the origin."""
    m = Model()
    m.cylinder(mat("tower"), -0.1, 0.9, 0, 0, 0.65, sides=12)
    frustum(m, mat("tower"), 0.9, 0, -0.35, 0.35, 0.5, 0.2, 10, rot=0.0)
    for k in range(3):
        a = math.pi / 2 + 2 * math.pi * k / 3
        c, s = math.cos(a), math.sin(a)
        # A blade: wide near the root, narrow at the tip, slightly twisted.
        root, tip = 0.6, WIND_RADIUS
        w0, w1 = 0.55, 0.18

        def p(r, w, d):
            return (0.3 + d, r * c - w * s, r * s + w * c)
        quads = [
            (p(root, -w0, -0.08), p(tip, -w1, -0.04), p(tip, w1, -0.04), p(root, w0, -0.08)),
            (p(root, w0, 0.08), p(tip, w1, 0.04), p(tip, -w1, 0.04), p(root, -w0, 0.08)),
        ]
        for q in quads:
            m.quad(mat("blade"), *q)
        m.quad(mat("blade"), p(root, w0, -0.08), p(tip, w1, -0.04), p(tip, w1, 0.04), p(root, w0, 0.08))
        m.quad(mat("blade"), p(root, -w0, 0.08), p(tip, -w1, 0.04), p(tip, -w1, -0.04), p(root, -w0, -0.08))
    return m


def dam(bottom=-4.0):
    """A concrete dam across a river flowing along x: the wall runs along y from bank to bank. It reaches
    down below the tile (to bottom), so it closes the river on a slope too."""
    m = Model()
    m.box(mat("dam"), -2.6, 2.6, -8, 8, bottom, 4.6)
    m.box(mat("dam_dark"), -2.8, 2.8, -8, 8, 4.6, 5.0)  # road on the crest
    railing(m, -2.6, 2.6, -8, 8, 5.0, h=0.8, material="indt_steel")
    # Spillway gates on both faces, with foam where the water leaves them.
    for y in (-5.0, 0.0, 5.0):
        for sx in (-1, 1):
            m.box(mat("dam_dark"), sx * 2.6 - 0.1, sx * 2.6 + 0.1, y - 1.4, y + 1.4, max(bottom, -1.0), 2.6)
        if bottom < -1.2:
            m.box(mat("water_foam"), 2.6, 4.6, y - 1.6, y + 1.6, -1.2, -0.9)
        # Gate hoists on the crest.
        m.box(mat("cladding_dark"), -1.0, 1.0, y - 1.0, y + 1.0, 5.0, 6.8)
    # Buttress ribs on the downstream face.
    for y in (-7.4, -2.5, 2.5, 7.4):
        m.box(mat("dam"), 2.6, 3.4, y - 0.4, y + 0.4, max(bottom, -3.0), 3.0)
    return m


def dam_x():
    return dam()


def dam_y():
    m = dam()
    rotated_z(m, 1)
    return m


# One height level of the game, in world units.
LEVEL = 8 * 0.40824829


def dam_step():
    """A dam on a river slope, the river flowing along +x down one height level: the reservoir stands high
    behind the wall (at -x, the top of the slope) and the water leaves through the gates at the foot of the
    wall, onto the lower river (at +x). The origin is the foot of the slope, at the lower water."""
    m = dam(bottom=-0.6)
    # The reservoir, held up by the wall at the height of the top of the slope.
    m.box(mat("reservoir"), -8.0, -2.6, -8, 8, LEVEL - 1.2, LEVEL - 0.25)
    # The lower river, and the white water where it pours out of the gates.
    m.box(mat("reservoir"), 2.6, 8.0, -8, 8, -0.6, 0.05)
    for y in (-5.0, 0.0, 5.0):
        m.box(mat("water_foam"), 2.6, 6.2, y - 1.8, y + 1.8, 0.05, 0.25)
        m.box(mat("water_foam"), 6.2, 8.0, y - 1.2, y + 1.2, 0.05, 0.15)
    return m


def powerhouse():
    """The powerhouse on the bank: turbine house, penstocks from the river, and a transformer."""
    m = Model()
    ground(m, "concrete")
    m.box("concrete", -6, 4, -6.5, 3.5, 0, 7.5)
    m.box("company", -6.05, 4.05, -6.55, 3.55, 6.0, 6.7)
    m.box(mat("cladding_dark"), -6.2, 4.2, -6.7, 3.7, 7.5, 8.0)
    m.windows("glass", -6, 4, -6.5, 3.5, 2.0, 5.5, 1, 3, size=(1.4, 2.4))
    m.box("door", 4.0, 4.1, -2.5, 0.5, 0, 3.5)
    # Penstocks coming in from the river side (-y) and the tailrace outlet.
    for x in (-3.5, 0.5):
        beam(m, mat("pipe"), (x, -8.0, 4.5), (x, -6.5, 2.0), 1.2)
    m.box(mat("dam_dark"), -5, 3, -8, -6.5, -0.5, 0.6)
    transformer(m, 1.0, 5.8)
    beam(m, "indt_steel", (-4.5, 7.4, 0), (-4.5, 7.4, 7.0), 0.3)
    beam(m, "indt_steel", (-4.5, 7.4, 7.0), (1.0, 5.8, 4.5), 0.08)
    return m


def build():
    buildings = []
    for gfx, name, make in (
            (175, "oil_hall", oil_hall),
            (176, "oil_tanks", oil_tanks),
            (177, "solar_panels", solar_panels),
            (178, "solar_inverter", solar_inverter),
            (179, "wind_tower", wind_tower),
            (180, "dam_x", dam_x),
            (181, "dam_y", dam_y),
            (182, "powerhouse", powerhouse)):
        filename = fname(name)
        make().save(filename)
        entry = {"type": "industry_tile", "ids": [gfx], "model": filename}
        if gfx == 179:
            rotor = fname("wind_rotor")
            wind_rotor().save(rotor)
            entry["parts"] = [{"model": rotor, "at": list(WIND_HUB), "axis": [1, 0, 0], "spin": 1.6}]
        buildings.append(entry)
    return {"vehicles": [], "buildings": buildings}
