"""Bridges: one piece of deck for each tile of a bridge, the ramps at its ends, and the pillars below.

All pieces run along x over one tile (16 long) with their middle at the origin. The top of the deck, where the
vehicles drive, is at z = 0. The game puts track or road on top, tilts ramps up to the bridge, and stretches
pillars from the ground up to the deck: a pillar is one unit high (from z = 0 to z = 1) and only gets taller.

Index type `bridge`, ids: bridge type * 4 + piece, with the bridge types of the game (0 wooden, 1 concrete,
2 girder steel, 3 suspension concrete, 4 and 5 suspension steel, 6 to 8 cantilever steel, 9 girder steel,
10 and 11 tubular steel, 12 tubular silicon) and pieces 0 deck, 1 ramp, 2 pillar. Id 64 is the road surface
that the game lays on road bridges.
"""

import math

from gfx3d import MATERIALS, Model

GROUP = "bridge"

for name, colour in {
    "wood": (0.50, 0.36, 0.22),
    "wood_dark": (0.36, 0.25, 0.15),
    "concrete": (0.68, 0.67, 0.63),
    "concrete_dark": (0.55, 0.54, 0.51),
    "steel_grey": (0.45, 0.50, 0.56),
    "steel_red": (0.62, 0.22, 0.17),
    "steel_brown": (0.45, 0.30, 0.20),
    "steel_yellow": (0.85, 0.66, 0.20),
    "steel_blue": (0.25, 0.38, 0.60),
    "steel_green": (0.24, 0.45, 0.32),
    "steel_white": (0.85, 0.86, 0.86),
    "cable": (0.25, 0.25, 0.27),
    "asphalt": (0.30, 0.30, 0.32),
    "marking": (0.90, 0.90, 0.85),
}.items():
    MATERIALS[f"{GROUP}_{name}"] = colour


def mat(name):
    return f"{GROUP}_{name}"


def beam(m, material, a, b, r):
    """A beam with a square section of half width r from point a to point b."""
    d = [b[i] - a[i] for i in range(3)]
    length = math.sqrt(sum(c * c for c in d))
    d = [c / length for c in d]
    up = (0, 0, 1) if abs(d[2]) < 0.9 else (1, 0, 0)
    u = [d[1] * up[2] - d[2] * up[1], d[2] * up[0] - d[0] * up[2], d[0] * up[1] - d[1] * up[0]]
    n = math.sqrt(sum(c * c for c in u))
    u = [c / n * r for c in u]
    v = [d[1] * u[2] - d[2] * u[1], d[2] * u[0] - d[0] * u[2], d[0] * u[1] - d[1] * u[0]]
    offsets = [(1, 1), (-1, 1), (-1, -1), (1, -1)]
    corner = lambda p, k: tuple(p[i] + offsets[k][0] * u[i] + offsets[k][1] * v[i] for i in range(3))
    for k in range(4):
        k2 = (k + 1) % 4
        pa, pb, pc, pd = corner(a, k), corner(b, k), corner(b, k2), corner(a, k2)
        # Wind each side so that its normal points away from the axis.
        e1 = [pb[i] - pa[i] for i in range(3)]
        e2 = [pc[i] - pa[i] for i in range(3)]
        normal = [e1[1] * e2[2] - e1[2] * e2[1], e1[2] * e2[0] - e1[0] * e2[2], e1[0] * e2[1] - e1[1] * e2[0]]
        out = [pa[i] + pc[i] - a[i] - b[i] for i in range(3)]
        if sum(normal[i] * out[i] for i in range(3)) < 0:
            pb, pd = pd, pb
        m.quad(material, pa, pb, pc, pd)


X0, X1 = -8.0, 8.0
HALF = 5.0  # half the width of the deck


def deck(m, top, under, thickness=0.9):
    m.box(mat(top), X0, X1, -HALF, HALF, -0.12, 0)
    m.box(mat(under), X0, X1, -HALF + 0.3, HALF - 0.3, -thickness, -0.12)


def parapets(m, material, height=0.9, posts=None):
    for side in (-1, 1):
        y = side * (HALF - 0.15)
        if posts:
            count = 8
            for i in range(count + 1):
                x = X0 + 0.1 + i * (X1 - X0 - 0.2) / count
                m.box(mat(posts), x - 0.1, x + 0.1, y - 0.1, y + 0.1, 0, height)
            m.box(mat(material), X0, X1, y - 0.08, y + 0.08, height - 0.15, height)
            m.box(mat(material), X0, X1, y - 0.06, y + 0.06, height * 0.45, height * 0.45 + 0.1)
        else:
            m.box(mat(material), X0, X1, y - 0.15, y + 0.15, 0, height)


def side_girders(m, material, height):
    for side in (-1, 1):
        y = side * (HALF + 0.05)
        m.box(mat(material), X0, X1, y - 0.25, y + 0.25, -1.2, height)
        for i in range(5):
            x = X0 + 1.6 + i * 3.2
            m.box(mat(material), x - 0.12, x + 0.12, y - 0.35 * side - 0.12, y + 0.12, -1.2, height)


def truss(m, material, height, panels=4):
    """Two side trusses with diagonals, joined over the top."""
    step = (X1 - X0) / panels
    for side in (-1, 1):
        y = side * (HALF + 0.1)
        m.box(mat(material), X0, X1, y - 0.18, y + 0.18, -0.4, 0.2)
        m.box(mat(material), X0, X1, y - 0.18, y + 0.18, height - 0.3, height)
        for i in range(panels + 1):
            x = X0 + i * step
            m.box(mat(material), x - 0.15, x + 0.15, y - 0.15, y + 0.15, 0, height)
        for i in range(panels):
            xa = X0 + i * step
            if i % 2:
                beam(m, mat(material), (xa, y, 0), (xa + step, y, height - 0.2), 0.11)
            else:
                beam(m, mat(material), (xa, y, height - 0.2), (xa + step, y, 0), 0.11)
    for i in range(panels + 1):
        x = X0 + i * step
        m.box(mat(material), x - 0.12, x + 0.12, -HALF - 0.1, HALF + 0.1, height - 0.25, height)


def suspension(m, material):
    """A main cable on each side, sagging between the ends of the tile, with hangers to the deck."""
    for side in (-1, 1):
        y = side * (HALF + 0.05)
        m.box(mat(material), X0, X1, y - 0.12, y + 0.12, -0.8, 0.6)
        n = 16
        points = []
        for k in range(n + 1):
            x = X0 + k * (X1 - X0) / n
            t = (x / (X1 - X0)) * 2
            points.append((x, 3.2 + 3.0 * t * t))
        for (xa, za), (xb, zb) in zip(points, points[1:]):
            beam(m, mat("cable"), (xa, y, za), (xb, y, zb), 0.12)
        for (x, z) in points[1:-1:2]:
            m.box(mat("cable"), x - 0.05, x + 0.05, y - 0.05, y + 0.05, 0.6, z)
        # Tower posts at both ends of the tile, as at every pillar of a long suspension bridge.
        for x in (X0 + 0.3, X1 - 0.3):
            m.box(mat(material), x - 0.3, x + 0.3, y - 0.3, y + 0.3, -0.8, 6.6)
    for x in (X0 + 0.3, X1 - 0.3):
        m.box(mat(material), x - 0.25, x + 0.25, -HALF, HALF, 6.0, 6.6)


def tube(m, material):
    """Hoops over the deck, joined by bars along it, like a tube of steel."""
    rings = 4
    segments = 8
    radius = HALF + 0.4
    arc = [(radius * math.cos(math.pi * k / segments), radius * 0.95 * math.sin(math.pi * k / segments)) for k in range(segments + 1)]
    for i in range(rings + 1):
        x = X0 + 0.15 + i * (X1 - X0 - 0.3) / rings
        for (ya, za), (yb, zb) in zip(arc, arc[1:]):
            beam(m, mat(material), (x, ya, za), (x, yb, zb), 0.16)
    for y, z in arc[1:-1]:
        beam(m, mat(material), (X0, y, z), (X1, y, z), 0.1)
    for side in (-1, 1):
        m.box(mat(material), X0, X1, side * radius - 0.2, side * radius + 0.2, -0.8, 0.3)
        # Crossed bracing in the sides.
        step = (X1 - X0) / rings
        for i in range(rings):
            xa = X0 + i * step
            y0, z0 = arc[0] if side > 0 else arc[-1]
            y1, z1 = arc[2] if side > 0 else arc[-3]
            beam(m, mat(material), (xa, side * radius, 0.2), (xa + step, y1, z1), 0.07)


STYLES = {
    0: dict(top="wood", under="wood_dark", rail="wood", posts="wood", pillar="trestle", colour="wood_dark"),
    1: dict(top="concrete", under="concrete_dark", rail="concrete", pillar="column", colour="concrete_dark"),
    2: dict(top="concrete", under="steel_grey", rail="steel_grey", girder="steel_grey", pillar="steel", colour="steel_grey"),
    3: dict(top="concrete", under="concrete_dark", rail="steel_grey", posts="steel_grey", suspension="concrete", pillar="column", colour="concrete_dark"),
    4: dict(top="concrete", under="steel_yellow", rail="steel_yellow", posts="steel_yellow", suspension="steel_yellow", pillar="steel", colour="steel_yellow"),
    5: dict(top="concrete", under="steel_red", rail="steel_red", posts="steel_red", suspension="steel_red", pillar="steel", colour="steel_red"),
    6: dict(top="concrete", under="steel_brown", truss="steel_brown", pillar="steel", colour="steel_brown"),
    7: dict(top="concrete", under="steel_yellow", truss="steel_yellow", pillar="steel", colour="steel_yellow"),
    8: dict(top="concrete", under="steel_red", truss="steel_red", pillar="steel", colour="steel_red"),
    9: dict(top="concrete", under="steel_blue", rail="steel_blue", girder="steel_blue", pillar="steel", colour="steel_blue"),
    10: dict(top="concrete", under="steel_green", tube="steel_green", pillar="steel", colour="steel_green"),
    11: dict(top="concrete", under="steel_red", tube="steel_red", pillar="steel", colour="steel_red"),
    12: dict(top="concrete", under="steel_white", tube="steel_white", pillar="column", colour="steel_white"),
}


def deck_piece(style):
    m = Model()
    deck(m, style["top"], style["under"])
    if "rail" in style:
        parapets(m, style["rail"], posts=style.get("posts"))
    if "girder" in style:
        side_girders(m, style["girder"], 1.4)
    if "suspension" in style:
        suspension(m, style["suspension"])
    if "truss" in style:
        truss(m, style["truss"], 5.6)
    if "tube" in style:
        tube(m, style["tube"])
    return m


def ramp_piece(style):
    """The end of a bridge: deck and parapets on an abutment; the game tilts it up the ramp."""
    m = Model()
    deck(m, style["top"], style["under"], thickness=0.6)
    for side in (-1, 1):
        y = side * (HALF - 0.15)
        m.box(mat(style.get("rail", style["colour"])), X0, X1, y - 0.15, y + 0.15, 0, 0.8)
    # The abutment where the ramp meets the land, and a wing wall on each side.
    m.box(mat("concrete_dark"), X0, X0 + 3, -HALF, HALF, -3.5, -0.12)
    for side in (-1, 1):
        m.box(mat("concrete_dark"), X0, X1, side * HALF - 0.4, side * HALF + 0.4, -3.5, -0.3)
    return m


def pillar_piece(style):
    m = Model()
    kind = style["pillar"]
    colour = style["colour"]
    if kind == "trestle":
        for y in (-3.6, -1.2, 1.2, 3.6):
            m.box(mat("wood"), -0.25, 0.25, y - 0.25, y + 0.25, 0, 1)
        m.box(mat("wood_dark"), -0.15, 0.15, -3.8, 3.8, 0.45, 0.55)
    elif kind == "column":
        m.box(mat(colour), -0.9, 0.9, -3.4, 3.4, 0, 1)
    else:
        for y in (-3.4, 3.4):
            m.box(mat(colour), -0.45, 0.45, y - 0.45, y + 0.45, 0, 1)
        m.box(mat(colour), -0.15, 0.15, -3.4, 3.4, 0.1, 0.9)
    return m


def road_surface():
    m = Model()
    m.box(mat("asphalt"), X0, X1, -3.9, 3.9, 0, 0.06)
    for i in range(4):
        x = X0 + 1 + i * 4
        m.box(mat("marking"), x, x + 2, -0.12, 0.12, 0.06, 0.08)
    return m


def build():
    buildings = []
    for kind, style in STYLES.items():
        for piece, (name, make) in enumerate((("deck", deck_piece), ("ramp", ramp_piece), ("pillar", pillar_piece))):
            filename = f"{GROUP}_{kind}_{name}.glb"
            make(style).save(filename)
            buildings.append({"type": "bridge", "ids": [kind * 4 + piece], "model": filename})
    road_surface().save(f"{GROUP}_road.glb")
    buildings.append({"type": "bridge", "ids": [64], "model": f"{GROUP}_road.glb"})
    return {"vehicles": [], "buildings": buildings}


# ---------------------------------------------------------------------------------------------------
# Tunnel portals and level crossings.
#
# Index type `tunnel`, id 0: the portal of a tunnel. It stands on a tile that the game makes flat, at its lower
# height; +x points out of the tunnel, the face of the portal is at x = -8 and the hill above it is one height
# level (3.27) higher. Wing walls along y = -8 and y = 8 close the sides of the cutting.
#
# Index type `crossing`, ids 0 open and 1 closed: the barriers of a level crossing, with the railway along x and
# the road along y.

LEVEL = 8 * 0.40824829

for _name, _colour in {
    "stone": (0.60, 0.56, 0.50),
    "stone_dark": (0.48, 0.45, 0.40),
    "dark": (0.04, 0.04, 0.05),
    "boom_red": (0.85, 0.15, 0.12),
    "boom_white": (0.95, 0.95, 0.92),
    "lamp_on": (1.00, 0.18, 0.10),
    "lamp_off": (0.30, 0.08, 0.06),
}.items():
    MATERIALS[f"{GROUP}_{_name}"] = _colour


def wedge(m, material, x0, x1, y0, y1, z_at_x0, z_at_x1):
    """A wall from x0 to x1 whose top falls from z_at_x0 to z_at_x1, standing on z = 0."""
    a, b = (x0, y0, 0), (x1, y0, 0)
    c, d = (x1, y1, 0), (x0, y1, 0)
    ta, tb = (x0, y0, z_at_x0), (x1, y0, z_at_x1)
    tc, td = (x1, y1, z_at_x1), (x0, y1, z_at_x0)
    m.quad(material, a, b, tb, ta)
    m.quad(material, c, d, td, tc)
    m.quad(material, ta, tb, tc, td)
    m.quad(material, b, c, tc, tb)
    m.quad(material, d, a, ta, td)


def tunnel_portal():
    m = Model()
    top = LEVEL + 0.35
    face = X0 + 0.9
    # The face of the portal with the dark mouth of the tunnel in it.
    m.box(mat("stone"), X0 - 0.5, face, -8, -4.0, 0, top)
    m.box(mat("stone"), X0 - 0.5, face, 4.0, 8, 0, top)
    arch = 2.1
    m.box(mat("stone"), X0 - 0.5, face, -4.0, 4.0, arch + 1.0, top)
    segments = 8
    for k in range(segments):
        a0, a1 = math.pi * k / segments, math.pi * (k + 1) / segments
        y0, y1 = 4.0 * math.cos(a0), 4.0 * math.cos(a1)
        z0, z1 = arch + 1.0 * math.sin(a0), arch + 1.0 * math.sin(a1)
        m.box(mat("stone"), X0 - 0.5, face, min(y0, y1), max(y0, y1), max(z0, z1), arch + 1.0)
    m.box(mat("dark"), X0 - 0.5, face - 0.05, -4.0, 4.0, 0, arch + 1.0)
    # A ring of darker stone around the mouth, and a coping along the top.
    for k in range(segments):
        a0, a1 = math.pi * k / segments, math.pi * (k + 1) / segments
        beam(m, mat("stone_dark"), (face + 0.1, 4.3 * math.cos(a0), arch + 1.2 * math.sin(a0)),
             (face + 0.1, 4.3 * math.cos(a1), arch + 1.2 * math.sin(a1)), 0.3)
    for side in (-1, 1):
        m.box(mat("stone_dark"), face - 0.2, face + 0.4, side * 4.3 - 0.3, side * 4.3 + 0.3, 0, arch)
    m.box(mat("stone_dark"), X0 - 0.6, face + 0.2, -8.1, 8.1, top - 0.25, top + 0.1)
    # Wing walls along the sides of the cutting.
    for side in (-1, 1):
        wedge(m, mat("stone"), face, X1, side * 8 - 0.4, side * 8 + 0.4, top, 0.2)
    return m


def crossing(closed):
    m = Model()
    for side in (-1, 1):
        px, py = side * 6.2, side * 6.0
        m.box(mat("concrete_dark"), px - 0.4, px + 0.4, py - 0.4, py + 0.4, 0, 0.25)
        m.box(mat("boom_white"), px - 0.13, px + 0.13, py - 0.13, py + 0.13, 0.25, 2.6)
        # Two lamps on a cross bar, facing the road on both sides of the track.
        m.box(mat("cable"), px - 0.5, px + 0.5, py - 0.08, py + 0.08, 2.2, 2.32)
        for lx in (px - 0.4, px + 0.4):
            m.box(mat("lamp_on" if closed else "lamp_off"), lx - 0.14, lx + 0.14, py - 0.2, py + 0.2, 2.0, 2.28)
        # The boom: across the road when closed, standing up when open; stripes of red and white.
        pivot_z = 1.25
        length = 6.0
        stripes = 6
        for k in range(stripes):
            colour = mat("boom_red" if k % 2 == 0 else "boom_white")
            t0, t1 = k * length / stripes, (k + 1) * length / stripes
            if closed:
                x0, x1 = px - side * t0, px - side * t1
                m.box(colour, min(x0, x1), max(x0, x1), py + side * 0.2 - 0.09, py + side * 0.2 + 0.09, pivot_z - 0.09, pivot_z + 0.09)
            else:
                m.box(colour, px - 0.09, px + 0.09, py + side * 0.2 - 0.09, py + side * 0.2 + 0.09, pivot_z + t0, pivot_z + t1)
    return m


_build_bridges = build


def build():
    entries = _build_bridges()
    tunnel_portal().save("tunnel_portal.glb")
    entries["buildings"].append({"type": "tunnel", "ids": [0], "model": "tunnel_portal.glb"})
    for closed in (0, 1):
        name = f"crossing_{'closed' if closed else 'open'}.glb"
        crossing(closed).save(name)
        entries["buildings"].append({"type": "crossing", "ids": [closed], "model": name})
    return entries
