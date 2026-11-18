#!/usr/bin/env python3
"""Models for power lines: pylons, substations and the pieces of wire between them.

Index type `power`, ids:
  0 a pylon, the line running along x through it;
  1 an overhead substation, wires arriving at its gantry along x;
  2 an underground substation, the same yard without a gantry;
  3 a transition pylon, where an overhead line along x goes into the ground;
  4 one piece of conductor, 16 long along x, centred on the origin; the game stretches it from pylon to pylon;
  5 a cable marker post, set over underground cables;
  6 one piece of underground cable as the power network view shows it: a bright strip on the ground, 16 long along x.

The game hangs three conductors from every pylon and gantry, at WIRE_Z above its foot and PHASE apart
across the line (y = -PHASE, 0, +PHASE), and an earth wire from the top of the pylon. These numbers must
match the ones in the game (src/viewport3d/terrain_mesh.cpp, AddPowerModels()).
"""

from gfx3d import MATERIALS, Model
from models_infra import beam

GROUP = "power"

# Three height levels of the game (8 pixels each, 0.408 world units per pixel): where the wires hang.
WIRE_Z = 3 * 8 * 0.40824829
PHASE = 2.6
TOP = WIRE_Z + 2.6  # The peak of a pylon, where the earth wire runs.
ARM_Z = WIRE_Z + 0.9  # The cross arm; the insulators hang from it down to the wire.

for _name, _colour in {
    "steel": (0.56, 0.58, 0.58),
    "steel_dark": (0.40, 0.42, 0.42),
    "insulator": (0.78, 0.80, 0.84),
    "conductor": (0.25, 0.24, 0.22),
    "transformer": (0.36, 0.42, 0.38),
    "gravel": (0.62, 0.60, 0.55),
    "concrete": (0.74, 0.74, 0.72),
    "hut": (0.80, 0.74, 0.62),
    "hut_roof": (0.40, 0.30, 0.26),
    "door": (0.36, 0.30, 0.24),
    "fence": (0.50, 0.52, 0.52),
    "warning": (0.92, 0.78, 0.18),
    "marker": (0.95, 0.55, 0.10),
    "marker_post": (0.88, 0.86, 0.80),
    "cable": (1.00, 0.45, 0.05),
}.items():
    MATERIALS[f"{GROUP}_{_name}"] = _colour


def mat(name):
    return f"{GROUP}_{name}"


def insulator(m, x, y, z_top, z_bottom):
    """A string of insulator discs hanging from z_top to z_bottom."""
    m.box(mat("steel_dark"), x - 0.04, x + 0.04, y - 0.04, y + 0.04, z_bottom - 0.1, z_top)
    n = 4
    for i in range(n):
        z = z_bottom + (i + 0.5) * (z_top - z_bottom) / n
        m.box(mat("insulator"), x - 0.17, x + 0.17, y - 0.17, y + 0.17, z - 0.06, z + 0.06)


def lattice_tower(m, half_base, half_top, z0, z1, levels):
    """Four corner legs leaning in from half_base to half_top, braced on every face."""
    def corner(sx, sy, z):
        t = (z - z0) / (z1 - z0)
        h = half_base + (half_top - half_base) * t
        return [sx * h, sy * h, z]

    corners = ((1, 1), (-1, 1), (-1, -1), (1, -1))
    for sx, sy in corners:
        beam(m, mat("steel"), corner(sx, sy, z0), corner(sx, sy, z1), 0.22)
    for i in range(levels):
        za = z0 + (z1 - z0) * i / levels
        zb = z0 + (z1 - z0) * (i + 1) / levels
        for k in range(4):
            a, b = corners[k], corners[(k + 1) % 4]
            # One diagonal per face and level, alternating, and a ring at the top of the level.
            if (i + k) % 2 == 0:
                beam(m, mat("steel_dark"), corner(*a, za), corner(*b, zb), 0.1)
            else:
                beam(m, mat("steel_dark"), corner(*b, za), corner(*a, zb), 0.1)
            beam(m, mat("steel_dark"), corner(*a, zb), corner(*b, zb), 0.1)


def footings(m, half):
    for sx in (-1, 1):
        for sy in (-1, 1):
            m.box(mat("concrete"), sx * half - 0.35, sx * half + 0.35, sy * half - 0.35, sy * half + 0.35, -0.3, 0.25)


def pylon():
    m = Model()
    footings(m, 1.6)
    lattice_tower(m, 1.6, 0.45, 0.2, ARM_Z, 5)
    # The peak above the arm, carrying the earth wire.
    lattice_tower(m, 0.45, 0.12, ARM_Z, TOP, 2)
    # The cross arm across the line (along y), a triangular truss.
    reach = PHASE + 0.4
    for x in (-0.35, 0.35):
        beam(m, mat("steel"), [x, -reach, ARM_Z], [x, reach, ARM_Z], 0.14)
        beam(m, mat("steel_dark"), [x, -reach, ARM_Z], [x * 0.3, -0.45, ARM_Z + 1.1], 0.09)
        beam(m, mat("steel_dark"), [x, reach, ARM_Z], [x * 0.3, 0.45, ARM_Z + 1.1], 0.09)
    for y in (-reach, -PHASE * 0.5, PHASE * 0.5, reach):
        beam(m, mat("steel_dark"), [-0.35, y, ARM_Z], [0.35, y, ARM_Z], 0.09)
    for y in (-PHASE, 0.0, PHASE):
        insulator(m, 0, y, ARM_Z, WIRE_Z)
    # A danger sign on the leg facing the viewer of the 2D game.
    m.box(mat("warning"), 1.25, 1.32, -0.35, 0.35, 1.6, 2.2)
    return m


def transition_pylon():
    m = pylon()
    # Down leads from the wires to cable sealing ends on a platform in the tower, and cable ducts into the ground.
    m.box(mat("steel"), -1.2, 1.2, -PHASE - 0.3, PHASE + 0.3, 3.6, 3.75)
    for y in (-PHASE, 0.0, PHASE):
        beam(m, mat("conductor"), [0.0, y, WIRE_Z], [0.0, y, 4.9], 0.08)
        m.box(mat("insulator"), -0.18, 0.18, y - 0.18, y + 0.18, 3.75, 4.9)
        m.box(mat("steel_dark"), -0.12, 0.12, y - 0.12, y + 0.12, 0.0, 3.6)
    m.box(mat("concrete"), -0.6, 0.6, -PHASE - 0.4, PHASE + 0.4, -0.2, 0.35)
    return m


def transformer(m, x, y):
    """A transformer: a tank with cooling fins, bushings on top and a conservator drum."""
    m.box(mat("concrete"), x - 2.0, x + 2.0, y - 1.6, y + 1.6, 0.0, 0.4)
    m.box(mat("transformer"), x - 1.4, x + 1.4, y - 1.0, y + 1.0, 0.4, 3.2)
    for i in range(6):
        fx = x - 1.25 + i * 0.5
        for sy in (-1, 1):
            m.box(mat("transformer"), fx - 0.05, fx + 0.05, y + sy * 1.0, y + sy * 1.55, 0.7, 2.9)
    for i in range(3):
        bx = x - 0.8 + i * 0.8
        m.box(mat("insulator"), bx - 0.12, bx + 0.12, y - 0.12, y + 0.12, 3.2, 4.4)
    m.cylinder(mat("transformer"), x - 1.2, x + 1.2, y - 0.6, 3.9, 0.35)


def yard(m):
    """The fenced gravel yard, the control hut and two transformers."""
    m.box(mat("gravel"), -7.4, 7.4, -7.4, 7.4, 0.0, 0.12)
    for p0, p1 in (([-7.3, -7.3], [7.3, -7.3]), ([7.3, -7.3], [7.3, 7.3]), ([7.3, 7.3], [-7.3, 7.3]), ([-7.3, 7.3], [-7.3, -7.3])):
        beam(m, mat("fence"), [p0[0], p0[1], 1.6], [p1[0], p1[1], 1.6], 0.08)
        beam(m, mat("fence"), [p0[0], p0[1], 0.6], [p1[0], p1[1], 0.6], 0.06)
    for x in (-7.3, -3.65, 0.0, 3.65, 7.3):
        for y in (-7.3, 7.3):
            m.box(mat("fence"), x - 0.07, x + 0.07, y - 0.07, y + 0.07, 0.0, 1.7)
            m.box(mat("fence"), y - 0.07, y + 0.07, x - 0.07, x + 0.07, 0.0, 1.7)
    transformer(m, 2.4, -3.6)
    transformer(m, 2.4, 3.6)
    # The control hut at the back corner.
    m.box(mat("hut"), -6.6, -3.0, -6.6, -2.4, 0.1, 2.8)
    m.prism_roof(mat("hut_roof"), mat("hut"), -6.8, -2.8, -6.8, -2.2, 2.8, 3.8)
    m.box(mat("door"), -3.0, -2.94, -5.2, -4.2, 0.1, 2.0)


def substation(gantry):
    m = Model()
    yard(m)
    if gantry:
        # A portal frame across the yard (along y) that takes the wires arriving along x.
        reach = PHASE + 0.6
        for y in (-reach - 0.4, reach + 0.4):
            m.box(mat("concrete"), -0.5, 0.5, y - 0.5, y + 0.5, 0.0, 0.3)
            for sx in (-0.3, 0.3):
                for sy in (-0.3, 0.3):
                    beam(m, mat("steel"), [sx, y + sy, 0.2], [sx, y + sy, ARM_Z + 0.3], 0.14)
            for z in (2.0, 4.0, 6.0, 8.0, ARM_Z):
                beam(m, mat("steel_dark"), [-0.3, y - 0.3, z], [0.3, y + 0.3, z], 0.08)
                beam(m, mat("steel_dark"), [0.3, y - 0.3, z], [-0.3, y + 0.3, z], 0.08)
        for x in (-0.3, 0.3):
            beam(m, mat("steel"), [x, -reach - 0.7, ARM_Z + 0.3], [x, reach + 0.7, ARM_Z + 0.3], 0.16)
        for y in (-PHASE, 0.0, PHASE):
            insulator(m, 0, y, ARM_Z + 0.3, WIRE_Z)
            # Droppers from the gantry down to the bushings of the transformers.
            beam(m, mat("conductor"), [0.0, y, WIRE_Z], [2.4, y * 1.4, 4.4], 0.06)
    return m


def conductor():
    m = Model()
    # Thicker than a real wire, so it still shows from far away.
    m.box(mat("conductor"), -8.0, 8.0, -0.07, 0.07, -0.07, 0.07)
    return m


def cable_marker():
    """A short marker post with an orange cap, as set along buried power cables."""
    m = Model()
    m.box(mat("marker_post"), -0.3, 0.3, -0.3, 0.3, 0.0, 2.0)
    m.box(mat("marker"), -0.4, 0.4, -0.4, 0.4, 2.0, 2.9)
    m.box(mat("steel_dark"), -0.41, 0.41, -0.08, 0.08, 2.25, 2.65)
    return m


def cable_view():
    m = Model()
    m.box(mat("cable"), -8.0, 8.0, -0.45, 0.45, 0.0, 0.25)
    return m


def build():
    buildings = []
    for i, (name, model) in enumerate((
            ("pylon", pylon()),
            ("substation_overhead", substation(True)),
            ("substation_underground", substation(False)),
            ("pylon_transition", transition_pylon()),
            ("conductor", conductor()),
            ("cable_marker", cable_marker()),
            ("cable_view", cable_view()))):
        filename = f"{GROUP}_{name}.glb"
        model.save(filename)
        buildings.append({"type": "power", "ids": [i], "model": filename})
    return {"vehicles": [], "buildings": buildings}
