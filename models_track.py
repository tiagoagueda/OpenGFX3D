"""Track: the pieces that the 3D view lays on rail tiles in place of the track of the 2D game.

Each piece runs along x with its middle at the origin and the ground at z = 0. Straight pieces cross a whole tile
(16 long); diagonal pieces join the middles of two neighbouring tile edges (8 * sqrt(2) long). The game lays one
piece for each track on a tile, tilted along slopes.

Index type `track`, ids: 0 and 1 normal railway (also electrified), 2 and 3 monorail, 4 and 5 maglev; the even
id is the straight piece, the odd one the diagonal piece.

Signals: index type `signal`, id = type * 4 + variant * 2 + state, with the type as in the game (0 block, 1 entry,
2 exit, 3 combo, 4 path, 5 one-way path), variant 0 light and 1 semaphore, state 0 red and 1 green. A signal stands
at the origin and faces +x, towards the trains it is for; the track is on its -y side.
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
    "post": (0.52, 0.53, 0.55),
    "head": (0.12, 0.12, 0.13),
    "red_on": (1.00, 0.16, 0.10),
    "red_off": (0.30, 0.08, 0.07),
    "green_on": (0.25, 1.00, 0.35),
    "green_off": (0.07, 0.22, 0.10),
    "white": (0.92, 0.92, 0.88),
    "yellow": (0.95, 0.78, 0.15),
    "orange": (0.95, 0.45, 0.10),
    "arm_red": (0.80, 0.12, 0.10),
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


SIGNAL_HEIGHT = 5.2


def type_marks(m, kind, z):
    """Bands and plates on the post that tell the kinds of signals apart, below the head at height z."""
    if kind in (1, 3):  # entry: yellow band; combo: yellow and orange
        m.box(mat("yellow"), -0.17, 0.17, -0.17, 0.17, z - 0.9, z - 0.55)
    if kind in (2, 3):  # exit: orange band
        m.box(mat("orange"), -0.17, 0.17, -0.17, 0.17, z - 1.4, z - 1.05)
    if kind in (4, 5):  # path signals: a white plate with a black edge on the front
        m.box(mat("head"), 0.15, 0.2, -0.42, 0.42, z - 1.45, z - 0.55)
        m.box(mat("white"), 0.2, 0.24, -0.34, 0.34, z - 1.37, z - 0.63)
    if kind == 5:  # one-way path signal: a no-entry disc on the back
        m.box(mat("arm_red"), -0.24, -0.15, -0.36, 0.36, z - 1.36, z - 0.64)
        m.box(mat("white"), -0.27, -0.24, -0.26, 0.26, z - 1.06, z - 0.94)


def light_signal(kind, green):
    m = Model()
    top = SIGNAL_HEIGHT
    m.box(mat("concrete"), -0.4, 0.4, -0.4, 0.4, -0.05, 0.25)
    m.box(mat("post"), -0.12, 0.12, -0.12, 0.12, 0.25, top - 1.6)
    head0, head1 = top - 1.8, top
    m.box(mat("head"), -0.25, 0.25, -0.38, 0.38, head0, head1)
    m.box(mat("head"), 0.25, 0.3, -0.45, 0.45, head1 - 0.05, head1 + 0.05)  # sun shade
    for colour, z, on in (("red", head1 - 0.48, not green), ("green", head0 + 0.48, green)):
        m.box(mat(f"{colour}_{'on' if on else 'off'}"), 0.25, 0.32, -0.24, 0.24, z - 0.24, z + 0.24)
    type_marks(m, kind, head0)
    return m


def semaphore_signal(kind, green):
    m = Model()
    top = SIGNAL_HEIGHT
    m.box(mat("concrete"), -0.4, 0.4, -0.4, 0.4, -0.05, 0.25)
    m.box(mat("sleeper"), -0.11, 0.11, -0.11, 0.11, 0.25, top + 0.3)
    m.pyramid(mat("head"), -0.15, 0.15, -0.15, 0.15, top + 0.3, top + 0.6)
    # The arm turns around a pivot on the front of the post; it points towards the track (-y).
    pivot_z = top - 0.4
    angle = math.radians(40 if green else 0)
    c, s = math.cos(angle), math.sin(angle)

    arm = Model()
    arm.box(mat("arm_red"), 0.13, 0.22, -2.0, 0.0, -0.2, 0.2)
    arm.box(mat("white"), 0.22, 0.24, -1.75, -1.55, -0.2, 0.2)
    # Raising the arm turns its far end (-y) up, around the x axis.
    for material, (positions, normals) in arm.parts.items():
        turn = lambda p: (p[0], p[1] * c + p[2] * s, p[2] * c - p[1] * s)
        target_p, target_n = m.parts.setdefault(material, ([], []))
        target_p.extend((q[0], q[1], q[2] + pivot_z) for q in map(turn, positions))
        target_n.extend(map(turn, normals))
    # The lamp below the pivot shows the colour too.
    lamp = pivot_z - 0.7
    m.box(mat("head"), 0.11, 0.3, -0.18, 0.18, lamp - 0.2, lamp + 0.2)
    m.box(mat("green_on" if green else "red_on"), 0.3, 0.34, -0.12, 0.12, lamp - 0.12, lamp + 0.12)
    type_marks(m, kind, lamp - 0.3)
    return m


def build():
    buildings = []
    for kind in range(6):
        for variant, make in enumerate((light_signal, semaphore_signal)):
            for green in (0, 1):
                name = f"{GROUP}_signal_{kind}_{'semaphore' if variant else 'light'}_{'green' if green else 'red'}.glb"
                make(kind, green).save(name)
                buildings.append({"type": "signal", "ids": [kind * 4 + variant * 2 + green], "model": name})
    for kind, (make, base) in {"rail": (rail_piece, 0), "monorail": (monorail_piece, 2), "maglev": (maglev_piece, 4)}.items():
        for shape, length, offset in (("straight", STRAIGHT, 0), ("diagonal", DIAGONAL, 1)):
            name = f"{GROUP}_{kind}_{shape}.glb"
            make(length).save(name)
            buildings.append({"type": "track", "ids": [base + offset], "model": name})
    return {"vehicles": [], "buildings": buildings}


# ---------------------------------------------------------------------------------------------------
# Overhead wires (catenary) for electrified railways.
#
# Index type `catenary`, ids: 0 a pylon beside straight track, 1 a pylon beside diagonal track, 2 the wires of
# a straight piece, 3 the wires of a diagonal piece; for trams and electric roads, 4 the wires from the middle of a
# tile to one edge (along x from 0 to 8) and 5 a pole beside the road that reaches 6.4 to its middle. A pylon
# stands at its origin with its arm along +x, towards the track; the wires run along x like the track pieces, at
# the height of the contact wire above the rails.

CONTACT = 4.7  # height of the contact wire above the ground, just above the trains
MESSENGER = 5.5  # height of the wire it hangs from
PYLON_TOP = 6.2

for _name, _colour in {
    "mast": (0.42, 0.45, 0.42),
    "wire": (0.30, 0.27, 0.24),
    "insulator": (0.62, 0.40, 0.28),
}.items():
    MATERIALS[f"{GROUP}_{_name}"] = _colour


def pylon(reach):
    m = Model()
    m.box(mat("concrete"), -0.35, 0.35, -0.35, 0.35, -0.05, 0.3)
    # A lattice mast: four corner posts with cross pieces.
    for x in (-0.18, 0.18):
        for y in (-0.18, 0.18):
            m.box(mat("mast"), x - 0.05, x + 0.05, y - 0.05, y + 0.05, 0.3, PYLON_TOP)
    z = 0.8
    while z < PYLON_TOP - 0.2:
        m.box(mat("mast"), -0.2, 0.2, -0.2, 0.2, z, z + 0.06)
        z += 0.7
    # The arm reaches over the track; a stay holds the far end up, a short drop carries the contact wire.
    m.box(mat("mast"), 0.0, reach + 0.3, -0.06, 0.06, MESSENGER - 0.06, MESSENGER + 0.06)
    m.box(mat("mast"), 0.0, reach * 0.8, -0.04, 0.04, CONTACT + 0.1, CONTACT + 0.18)
    m.box(mat("insulator"), 0.1, 0.4, -0.08, 0.08, MESSENGER - 0.08, MESSENGER + 0.08)
    m.box(mat("insulator"), 0.1, 0.35, -0.07, 0.07, CONTACT + 0.07, CONTACT + 0.21)
    steps = 6
    for i in range(steps):
        x0 = i * reach / steps
        z0 = PYLON_TOP - 0.1 - i * (PYLON_TOP - MESSENGER - 0.1) / steps
        z1 = PYLON_TOP - 0.1 - (i + 1) * (PYLON_TOP - MESSENGER - 0.1) / steps
        m.box(mat("mast"), x0, x0 + reach / steps, -0.04, 0.04, min(z0, z1) - 0.04, max(z0, z1) + 0.04)
    m.box(mat("wire"), reach - 0.03, reach + 0.03, -0.03, 0.03, CONTACT, MESSENGER)
    return m


def wires(length, x0=None):
    m = Model()
    x0 = -length / 2 if x0 is None else x0
    x1 = x0 + length
    # Thicker than real wires, so they still show from far away.
    m.box(mat("wire"), x0, x1, -0.09, 0.09, CONTACT - 0.09, CONTACT + 0.09)
    m.box(mat("wire"), x0, x1, -0.07, 0.07, MESSENGER - 0.07, MESSENGER + 0.07)
    count = max(1, round(length / 2.4))
    for i in range(count):
        x = x0 + (i + 0.5) * length / count
        m.box(mat("wire"), x - 0.04, x + 0.04, -0.04, 0.04, CONTACT, MESSENGER)
    return m


_build_track = build


def build():
    entries = _build_track()
    for i, (name, model) in enumerate((
            ("pylon_straight", pylon(4.0)),
            ("pylon_diagonal", pylon(2.83)),
            ("wires_straight", wires(STRAIGHT)),
            ("wires_diagonal", wires(DIAGONAL)),
            ("wires_tram", wires(8, 0)),
            ("pole_tram", pylon(6.4)))):
        filename = f"{GROUP}_catenary_{name}.glb"
        model.save(filename)
        entries["buildings"].append({"type": "catenary", "ids": [i], "model": filename})
    return entries
