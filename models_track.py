"""Track: the pieces that the 3D view lays on rail tiles in place of the track of the 2D game.

Each piece runs along x with its middle at the origin and the ground at z = 0. Straight pieces cross a whole tile
(16 long); diagonal pieces join the middles of two neighbouring tile edges (8 * sqrt(2) long). The game lays one
piece for each track on a tile, tilted along slopes.

Index type `track`, ids: 0 and 1 normal railway (also electrified), 2 and 3 monorail, 4 and 5 maglev; the even
id is the straight piece, the odd one the diagonal piece. 6, 7 and 8 are joints for the three kinds, which the game puts
where straight track meets diagonal track: a short piece that turns left by 45 degrees at the origin, from along
-22.5 degrees to along +22.5 degrees, mitred there; for a turn to the right the game puts it the other way around.

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


JOINT = 1.6  # how far a joint reaches along each of the two pieces it joins
BEND = math.radians(22.5)  # half the turn where straight track meets diagonal track


def _face(m, material, points, outward):
    """A flat face with its front towards `outward`."""
    a, b, c = points[0], points[1], points[2]
    u = [b[i] - a[i] for i in range(3)]
    v = [c[i] - a[i] for i in range(3)]
    n = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]]
    if sum(n[i] * outward[i] for i in range(3)) < 0:
        points = list(reversed(points))
    if len(points) == 3:
        m.triangle(material, *points)
    else:
        m.quad(material, *points)


def bent_strip(m, material, bottom, top, z0, z1):
    """A strip along a bend that turns left by 2 * BEND at the origin, mitred there, reaching JOINT along both sides of
    it; `bottom` and `top` are its edges (from right to left of the way along) at the bottom and at the top."""
    c, s = math.cos(BEND), math.sin(BEND)
    d1, n1 = (c, -s), (s, c)
    d2, n2 = (c, s), (-s, c)

    def at(o, z, part):
        if part == 0:
            return (-JOINT * d1[0] + o * n1[0], -JOINT * d1[1] + o * n1[1], z)
        if part == 1:
            return (0.0, o / c, z)
        return (JOINT * d2[0] + o * n2[0], JOINT * d2[1] + o * n2[1], z)

    for part in (0, 1):
        n = n1 if part == 0 else n2
        _face(m, material, [at(top[0], z1, part), at(top[0], z1, part + 1), at(top[1], z1, part + 1), at(top[1], z1, part)], (0, 0, 1))
        _face(m, material, [at(bottom[1], z0, part), at(bottom[1], z0, part + 1), at(top[1], z1, part + 1), at(top[1], z1, part)], (n[0], n[1], 0))
        _face(m, material, [at(bottom[0], z0, part), at(bottom[0], z0, part + 1), at(top[0], z1, part + 1), at(top[0], z1, part)], (-n[0], -n[1], 0))
    _face(m, material, [at(bottom[0], z0, 0), at(bottom[1], z0, 0), at(top[1], z1, 0), at(top[0], z1, 0)], (-d1[0], -d1[1], 0))
    _face(m, material, [at(bottom[0], z0, 2), at(bottom[1], z0, 2), at(top[1], z1, 2), at(top[0], z1, 2)], (d2[0], d2[1], 0))


def rail_joint():
    """The bed and rails where straight track turns into diagonal track, without sleepers of its own."""
    m = Model()
    bent_strip(m, mat("ballast"), (-3.7, 3.7), (-2.7, 2.7), -0.05, 0.22)
    for y in (-1.2, 1.2):
        bent_strip(m, mat("rail_side"), (y - 0.12, y + 0.12), (y - 0.12, y + 0.12), 0.34, 0.5)
        bent_strip(m, mat("rail"), (y - 0.13, y + 0.13), (y - 0.13, y + 0.13), 0.5, 0.56)
    return m


def monorail_joint():
    m = Model()
    bent_strip(m, mat("concrete"), (-0.45, 0.45), (-0.45, 0.45), 0.2, 0.62)
    bent_strip(m, mat("guide"), (-0.47, 0.47), (-0.47, 0.47), 0.62, 0.68)
    return m


def maglev_joint():
    m = Model()
    bent_strip(m, mat("concrete"), (-1.6, 1.6), (-1.6, 1.6), -0.05, 0.15)
    bent_strip(m, mat("concrete"), (-0.9, 0.9), (-0.9, 0.9), 0.15, 0.72)
    for y in (-0.92, 0.92):
        bent_strip(m, mat("guide"), (y - 0.06, y + 0.06), (y - 0.06, y + 0.06), 0.3, 0.7)
    bent_strip(m, mat("guide"), (-0.5, 0.5), (-0.5, 0.5), 0.72, 0.76)
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
    # Where straight track meets diagonal track, a short piece turned halfway between them fills the gap.
    for kind, (make, base) in {"rail": (rail_joint, 6), "monorail": (monorail_joint, 7), "maglev": (maglev_joint, 8)}.items():
        name = f"{GROUP}_{kind}_joint.glb"
        make().save(name)
        buildings.append({"type": "track", "ids": [base], "model": name})
    return {"vehicles": [], "buildings": buildings}


# ---------------------------------------------------------------------------------------------------
# Overhead wires (catenary) for electrified railways.
#
# Index type `catenary`, ids: 0 a pylon beside straight track, 1 a pylon beside diagonal track, 2 the wires of
# a straight piece, 3 the wires of a diagonal piece; for trams and electric roads, 4 the contact wires over both lanes from
# the middle of a tile to one edge (along x from 0 to 8) and 5 a pole beside the road that holds them (6.4 - 3 and
# 6.4 + 3 from the pole); for trolleybuses
# on electrified road, 6 the wire pairs over both lanes from the middle of a tile to one edge, 7 a pole beside the
# road whose arm holds both pairs (6.4 - 3 and 6.4 + 3 from the pole), 8 the frogs and span wires hung over the middle
# of a junction, 9 the insulated crossing over the middle of a tile where tram wire meets trolleybus wires, and 10
# the wire pairs across a whole tile, centred like id 2, for bridges; 11 the tram contact wires across a whole tile,
# for bridges. A
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


LANE = 3.0  # road vehicles drive 3 either side of the middle of the road
PAIR = 0.45  # each trolleybus wire is this far either side of the middle of its lane


def tram_wires(length, x0=None):
    """A contact wire over each lane, where the trams' pantographs and poles reach it."""
    m = Model()
    x0 = -length / 2 if x0 is None else x0
    x1 = x0 + length
    for lane in (-LANE, LANE):
        m.box(mat("wire"), x0, x1, lane - 0.08, lane + 0.08, CONTACT - 0.08, CONTACT + 0.08)
        m.box(mat("wire"), x0, x1, lane - 0.06, lane + 0.06, MESSENGER - 0.06, MESSENGER + 0.06)
        count = max(1, round(length / 2.4))
        for i in range(count):
            x = x0 + (i + 0.5) * length / count
            m.box(mat("wire"), x - 0.04, x + 0.04, lane - 0.04, lane + 0.04, CONTACT, MESSENGER)
    return m


def tram_pole(reach=6.4):
    """A pole beside the road whose arm carries both tram contact wires, reach - LANE and reach + LANE from it."""
    m = pylon(reach + LANE)
    for x in (reach - LANE, reach + LANE):
        m.box(mat("insulator"), x - 0.1, x + 0.1, -0.1, 0.1, MESSENGER, MESSENGER + 0.2)
        m.box(mat("wire"), x - 0.03, x + 0.03, -0.03, 0.03, CONTACT, MESSENGER)
    return m


def trolley_wires(length, x0=None):
    """Two pairs of trolleybus wires, one over each lane, hung from a thinner messenger wire every few metres."""
    m = Model()
    x0 = -length / 2 if x0 is None else x0
    x1 = x0 + length
    for lane in (-LANE, LANE):
        for side in (-PAIR, PAIR):
            y = lane + side
            m.box(mat("wire"), x0, x1, y - 0.07, y + 0.07, CONTACT - 0.07, CONTACT + 0.07)
        count = max(1, round(length / 2.4))
        for i in range(count):
            x = x0 + (i + 0.5) * length / count
            # A spreader bar keeps the two wires of a pair apart, with an insulator over each wire.
            m.box(mat("mast"), x - 0.06, x + 0.06, lane - PAIR - 0.12, lane + PAIR + 0.12, CONTACT + 0.07, CONTACT + 0.16)
            for side in (-PAIR, PAIR):
                m.box(mat("insulator"), x - 0.08, x + 0.08, lane + side - 0.08, lane + side + 0.08, CONTACT + 0.04, CONTACT + 0.12)
    return m


def trolley_pole():
    """A pole beside the road, at the origin, with a bracket arm along +x that holds the wire pairs of both lanes."""
    m = Model()
    near, far = 6.4 - LANE, 6.4 + LANE
    m.box(mat("concrete"), -0.3, 0.3, -0.3, 0.3, -0.05, 0.25)
    m.box(mat("mast"), -0.14, 0.14, -0.14, 0.14, 0.25, PYLON_TOP)
    m.box(mat("mast"), -0.18, 0.18, -0.18, 0.18, PYLON_TOP, PYLON_TOP + 0.12)
    # The arm, a tie rod from the top of the pole, and a hanger with a spreader bar over each lane.
    m.box(mat("mast"), 0.0, far + 0.4, -0.06, 0.06, CONTACT + 0.5, CONTACT + 0.62)
    steps = 8
    for i in range(steps):
        x0 = i * far / steps
        z0 = PYLON_TOP - 0.1 - i * (PYLON_TOP - CONTACT - 0.7) / steps
        z1 = PYLON_TOP - 0.1 - (i + 1) * (PYLON_TOP - CONTACT - 0.7) / steps
        m.box(mat("mast"), x0, x0 + far / steps, -0.04, 0.04, min(z0, z1) - 0.04, max(z0, z1) + 0.04)
    for x in (near, far):
        m.box(mat("insulator"), x - 0.1, x + 0.1, -0.1, 0.1, CONTACT + 0.3, CONTACT + 0.5)
        m.box(mat("wire"), x - 0.03, x + 0.03, -0.03, 0.03, CONTACT + 0.16, CONTACT + 0.3)
        m.box(mat("mast"), x - PAIR - 0.12, x + PAIR + 0.12, -0.06, 0.06, CONTACT + 0.07, CONTACT + 0.16)
    return m


def trolley_junction():
    """Frogs where the wire pairs of a junction split and cross, hung from span wires across the middle of the tile."""
    m = Model()
    span = CONTACT + 0.45
    for a in (-LANE, LANE):
        m.box(mat("wire"), -8.0, 8.0, a - 0.04, a + 0.04, span - 0.04, span + 0.04)
        m.box(mat("wire"), a - 0.04, a + 0.04, -8.0, 8.0, span - 0.04, span + 0.04)
    for x in (-LANE, LANE):
        for y in (-LANE, LANE):
            # A frog: a flat box where two pairs meet, under its hanger.
            m.box(mat("mast"), x - 0.65, x + 0.65, y - 0.65, y + 0.65, CONTACT + 0.05, CONTACT + 0.2)
            m.box(mat("insulator"), x - 0.35, x + 0.35, y - 0.35, y + 0.35, CONTACT + 0.2, CONTACT + 0.3)
            m.box(mat("wire"), x - 0.03, x + 0.03, y - 0.03, y + 0.03, CONTACT + 0.3, span)
    return m


def tram_trolley_crossing():
    """An insulated crossing where a tram wire passes under trolleybus wires: a frame with insulators round it."""
    m = Model()
    span = CONTACT + 0.45
    m.box(mat("mast"), -LANE - 0.8, LANE + 0.8, -0.5, 0.5, CONTACT + 0.08, CONTACT + 0.18)
    m.box(mat("mast"), -0.5, 0.5, -LANE - 0.8, LANE + 0.8, CONTACT + 0.08, CONTACT + 0.18)
    for x, y in ((-LANE, 0), (LANE, 0), (0, -LANE), (0, LANE), (0, 0)):
        m.box(mat("insulator"), x - 0.3, x + 0.3, y - 0.3, y + 0.3, CONTACT + 0.18, CONTACT + 0.3)
        m.box(mat("wire"), x - 0.03, x + 0.03, y - 0.03, y + 0.03, CONTACT + 0.3, span)
    m.box(mat("wire"), -8.0, 8.0, -0.04, 0.04, span - 0.04, span + 0.04)
    m.box(mat("wire"), -0.04, 0.04, -8.0, 8.0, span - 0.04, span + 0.04)
    return m


_build_track = build


def build():
    entries = _build_track()
    for i, (name, model) in enumerate((
            ("pylon_straight", pylon(4.0)),
            ("pylon_diagonal", pylon(2.83)),
            ("wires_straight", wires(STRAIGHT)),
            ("wires_diagonal", wires(DIAGONAL)),
            ("wires_tram", tram_wires(8, 0)),
            ("pole_tram", tram_pole()),
            ("wires_trolley", trolley_wires(8, 0)),
            ("pole_trolley", trolley_pole()),
            ("junction_trolley", trolley_junction()),
            ("crossing_tram_trolley", tram_trolley_crossing()),
            ("wires_trolley_straight", trolley_wires(STRAIGHT)),
            ("wires_tram_straight", tram_wires(STRAIGHT)))):
        filename = f"{GROUP}_catenary_{name}.glb"
        model.save(filename)
        entries["buildings"].append({"type": "catenary", "ids": [i], "model": filename})
    return entries
