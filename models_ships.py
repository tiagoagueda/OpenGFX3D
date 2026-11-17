"""Ships of the base game: oil tankers, passenger ferries, the hovercraft, cargo ships and the toyland ships.

Ships are about 14 to 20 long and 5 to 6 wide, with the waterline at z = 0 and the front to +x.
The module also holds a few shape helpers (lofts of rings, wings, cylinders along y) that models_air uses.
"""

import math

from gfx3d import MATERIALS, Model

for _name, _colour in {
    "ships_antifoul": (0.55, 0.16, 0.14),
    "ships_deck": (0.46, 0.30, 0.22),
    "ships_deck_green": (0.32, 0.42, 0.30),
    "ships_planks": (0.70, 0.56, 0.38),
    "ships_white": (0.93, 0.93, 0.90),
    "ships_black": (0.12, 0.12, 0.13),
    "ships_skirt": (0.18, 0.18, 0.20),
    "ships_orange": (0.95, 0.50, 0.12),
    "ships_toy_red": (0.90, 0.20, 0.18),
    "ships_toy_yellow": (0.98, 0.84, 0.18),
    "ships_toy_green": (0.30, 0.75, 0.30),
    "ships_toy_pink": (0.95, 0.55, 0.75),
    "ships_toy_purple": (0.58, 0.36, 0.78),
    "ships_toy_cyan": (0.35, 0.82, 0.88),
    "load_ships_crates": (0.62, 0.46, 0.28),
    "load_ships_box_red": (0.72, 0.22, 0.18),
    "load_ships_box_green": (0.24, 0.52, 0.30),
    "load_ships_box_yellow": (0.88, 0.70, 0.20),
    "load_ships_box_grey": (0.62, 0.64, 0.66),
    "load_ships_toys": (0.95, 0.45, 0.60),
    "load_ships_toys_blue": (0.30, 0.55, 0.95),
}.items():
    MATERIALS.setdefault(_name, _colour)


# Shape helpers --------------------------------------------------------------------------------------


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _centroid(points):
    n = len(points)
    return (sum(p[0] for p in points) / n, sum(p[1] for p in points) / n, sum(p[2] for p in points) / n)


def tri_away(m, material, a, b, c, away):
    """A triangle turned so that its front faces away from the point away."""
    u, v = _sub(b, a), _sub(c, a)
    n = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
    if n[0] * n[0] + n[1] * n[1] + n[2] * n[2] < 1e-12:
        return
    cen = _centroid((a, b, c))
    d = _sub(cen, away)
    if n[0] * d[0] + n[1] * d[1] + n[2] * d[2] < 0:
        b, c = c, b
    m.triangle(material, a, b, c)


def loft(m, rings, material, cap0=True, cap1=True):
    """A closed solid through rings of points (all with the same count, in the same order around).

    material is one name or one name per edge of the ring (edge k joins point k and k + 1).
    cap0 / cap1: True for the edge material, a name, or False for no cap. Works for convex sections.
    """
    n = len(rings[0])
    mats = [material] * n if isinstance(material, str) else list(material)
    cents = [_centroid(r) for r in rings]
    for i in range(len(rings) - 1):
        a_ring, b_ring = rings[i], rings[i + 1]
        away = tuple((cents[i][j] + cents[i + 1][j]) / 2 for j in range(3))
        for k in range(n):
            a, b = a_ring[k], a_ring[(k + 1) % n]
            c, d = b_ring[(k + 1) % n], b_ring[k]
            tri_away(m, mats[k], a, b, c, away)
            tri_away(m, mats[k], a, c, d, away)
    for cap, idx, nxt in ((cap0, 0, 1), (cap1, len(rings) - 1, len(rings) - 2)):
        if cap is False:
            continue
        mat = mats[0] if cap is True else cap
        ring, cen = rings[idx], cents[idx]
        for k in range(n):
            tri_away(m, mat, cen, ring[k], ring[(k + 1) % n], cents[nxt])


def ellipse_ring(x, yc, zc, ry, rz, sides=12, start=0.0):
    return [(x, yc + ry * math.cos(start + 2 * math.pi * k / sides), zc + rz * math.sin(start + 2 * math.pi * k / sides)) for k in range(sides)]


def body(m, material, stations, sides=12, yc=0.0, cap0=True, cap1=True):
    """A rounded body along x through stations (x, zc, ry, rz)."""
    rings = [ellipse_ring(x, yc, zc, max(ry, 0.02), max(rz, 0.02), sides) for x, zc, ry, rz in stations]
    loft(m, rings, material, cap0, cap1)


def ycylinder(m, material, x, y0, y1, z, r, sides=12, caps=None):
    """A cylinder with its axis along y."""
    rings = []
    for y in (y0, y1):
        rings.append([(x + r * math.cos(2 * math.pi * k / sides), y, z + r * math.sin(2 * math.pi * k / sides)) for k in range(sides)])
    loft(m, rings, material, caps or True, caps or True)


def zcylinder(m, material, x, y, z0, z1, r, sides=12, rx=None, top=None):
    """A closed cylinder standing upright (rx makes it oval)."""
    rx = rx or r
    rings = [[(x + rx * math.cos(2 * math.pi * k / sides), y + r * math.sin(2 * math.pi * k / sides), z) for k in range(sides)] for z in (z0, z1)]
    loft(m, rings, material, True, top or True)


def block(m, material, corners, caps=True):
    """A solid with 4 corners at the bottom/back and 4 at the top/front: two rings of four points."""
    loft(m, [corners[:4], corners[4:]], material, caps, caps)


def wing(m, material, x_root, chord_root, x_tip, chord_tip, y_root, y_tip, z_root, z_tip, thick=0.25, both=True):
    """A wing panel from the root to the tip; x_root / x_tip are the leading edges. both mirrors it."""
    sides = (1, -1) if both else (1,)
    for s in sides:
        rings = []
        for x, c, y, z, t in ((x_root, chord_root, y_root, z_root, thick), (x_tip, chord_tip, y_tip, z_tip, thick * 0.6)):
            rings.append([(x, s * y, z), (x - 0.3 * c, s * y, z + t / 2), (x - c, s * y, z), (x - 0.3 * c, s * y, z - t / 2)])
        loft(m, rings, material)


def fin(m, material, x_root, chord_root, x_tip, chord_tip, z_root, z_tip, y=0.0, thick=0.22):
    """An upright fin; x_root / x_tip are the leading edges."""
    rings = []
    for x, c, z, t in ((x_root, chord_root, z_root, thick), (x_tip, chord_tip, z_tip, thick * 0.6)):
        rings.append([(x, y, z), (x - 0.3 * c, y + t / 2, z), (x - c, y, z), (x - 0.3 * c, y - t / 2, z)])
    loft(m, rings, material)


# Ship parts -----------------------------------------------------------------------------------------


def hull(m, length, width, freeboard, draft=0.7, bow=0.3, stern=0.08, sheer=0.6, yc=0.0,
         upper="company", lower="ships_antifoul", deck="ships_deck", transom=0.82, round_bow=False, band=None):
    """A ship's hull from stern (-x) to bow (+x), with a flat deck. bow is the fraction of the length
    that narrows to the stem; the deck rises by sheer towards the bow."""
    x0, x1 = -length / 2, length / 2
    w = width / 2
    bow_len = length * bow
    xs = [x0, x0 + length * stern * 0.5, x0 + length * stern]
    xs += [x0 + length * stern + (length * (1 - stern - bow)) * t for t in (0.5, 1.0)]
    xb = x1 - bow_len
    xs += [xb + bow_len * t for t in (0.25, 0.5, 0.72, 0.88, 1.0)]
    rings = []
    for x in xs:
        if x < x0 + length * stern:
            t = (x - x0) / (length * stern)
            f = transom + (1 - transom) * math.sqrt(t)
        elif x > xb:
            t = (x - xb) / bow_len
            f = math.sqrt(max(0.0, 1 - t * t)) if round_bow else (1 - t ** 1.7)
            f = max(f, 0.04 if not round_bow else 0.25)
        else:
            f = 1.0
        hw = w * f
        d = freeboard + sheer * max(0.0, (x - xb) / bow_len) ** 1.5
        b = -draft
        if x > xb and not round_bow:
            b = -draft + (draft + freeboard * 0.25) * ((x - xb) / bow_len) ** 2
        if x < x0 + length * stern * 0.5:
            b = -draft * 0.5
        wl = 0.0 if b < -0.02 else min(b + 0.02, d - 0.05)
        bz0, bz1 = (band[0], band[1]) if band else (d - 0.2, d - 0.1)
        bz0 = min(max(bz0, wl + 0.01), d - 0.02)
        bz1 = min(max(bz1, bz0 + 0.01), d - 0.01)
        rings.append([(x, yc - hw, d), (x, yc - hw, bz1), (x, yc - hw, bz0), (x, yc - hw, wl), (x, yc - hw * 0.7, b),
                      (x, yc + hw * 0.7, b), (x, yc + hw, wl), (x, yc + hw, bz0), (x, yc + hw, bz1), (x, yc + hw, d)])
    bm = band[2] if band else upper
    loft(m, rings, [upper, bm, upper, lower, lower, lower, upper, bm, upper, deck], cap0=upper, cap1=upper)
    return freeboard


def windows_row(m, x0, x1, y0, y1, z, h=0.45, count=6, w=0.5, front=True, mat="glass"):
    """Windows along both long sides of a superstructure, and across its front."""
    for i in range(count):
        xc = x0 + (i + 0.5) * (x1 - x0) / count
        m.box(mat, xc - w / 2, xc + w / 2, y0 - 0.05, y0, z, z + h)
        m.box(mat, xc - w / 2, xc + w / 2, y1, y1 + 0.05, z, z + h)
    if front:
        n = max(2, int((y1 - y0) / 0.9))
        for i in range(n):
            yc = y0 + (i + 0.5) * (y1 - y0) / n
            m.box(mat, x1, x1 + 0.05, yc - w / 2, yc + w / 2, z, z + h)


def sides_only(m, material, x0, x1, y0, y1, z0, z1, out=0.02, front=True, back=True):
    """The four walls of a box, standing just outside it: a band around something without hidden faces."""
    x0, x1, y0, y1 = x0 - out, x1 + out, y0 - out, y1 + out
    if front:
        m.quad(material, (x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1))
    if back:
        m.quad(material, (x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1))
    m.quad(material, (x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1))
    m.quad(material, (x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1))


def funnel(m, x, y, z0, z1, r, mat="company", top="ships_black", rx=None):
    zcylinder(m, mat, x, y, z0, z1 - 0.35, r, rx=rx)
    zcylinder(m, top, x, y, z1 - 0.35, z1, r * 1.02, rx=(rx or r) * 1.02)


def lifeboat(m, x, y, z, length=1.3, mat="ships_orange"):
    body(m, mat, [(x - length / 2, z, 0.2, 0.18), (x, z, 0.3, 0.25), (x + length / 2, z, 0.12, 0.12)], sides=8)


def mast(m, x, z0, z1, y=0.0, yard=1.4):
    m.box("ships_black", x - 0.07, x + 0.07, y - 0.07, y + 0.07, z0, z1)
    if yard:
        m.box("ships_black", x - 0.05, x + 0.05, y - yard / 2, y + yard / 2, z1 - 0.6, z1 - 0.5)


def railing(m, x0, x1, y0, y1, z, mat="ships_white"):
    for ya, yb in ((y0, y0 + 0.06), (y1 - 0.06, y1)):
        m.box(mat, x0, x1, ya, yb, z + 0.35, z + 0.42)


def bridge(m, x0, x1, y0, y1, z0, levels, h=0.85, mat="ships_white", win=6, wings=0.0):
    """Stacked decks of a superstructure, each a bit smaller than the one below, with windows."""
    z = z0
    for i in range(levels):
        m.box(mat, x0, x1, y0, y1, z, z + h)
        windows_row(m, x0 + 0.1, x1 - 0.1, y0, y1, z + 0.3, h=0.32, count=win, w=0.35)
        z += h
        if i < levels - 1:
            x0 += 0.15
    if wings:
        m.box(mat, x1 - 0.6, x1, y0 - wings, y1 + wings, z - h * 0.35, z - 0.1)
    m.box("dark", x0 - 0.05, x1 + 0.05, y0 - 0.05, y1 + 0.05, z, z + 0.08)
    return z + 0.08


def hatch_with_load(m, x0, x1, y0, y1, z, coaming=0.45, load="load_ships_crates", heap=0.5):
    """A cargo hold opening: a coaming on the deck and the load showing above it."""
    t = 0.12
    m.box("company_dark", x0, x1, y0, y0 + t, z, z + coaming)
    m.box("company_dark", x0, x1, y1 - t, y1, z, z + coaming)
    m.box("company_dark", x0, x0 + t, y0, y1, z, z + coaming)
    m.box("company_dark", x1 - t, x1, y0, y1, z, z + coaming)
    m.box("dark", x0 + t, x1 - t, y0 + t, y1 - t, z, z + 0.05)
    # Crates: two layers of boxes, as high as the coaming plus the heap.
    nx = max(1, int((x1 - x0 - 2 * t) / 0.9))
    ny = max(1, int((y1 - y0 - 2 * t) / 0.9))
    dx, dy = (x1 - x0 - 2 * t) / nx, (y1 - y0 - 2 * t) / ny
    for i in range(nx):
        for j in range(ny):
            top = z + coaming + heap * (0.6 + 0.4 * ((i + j) % 2))
            m.box(load, x0 + t + i * dx + 0.04, x0 + t + (i + 1) * dx - 0.04, y0 + t + j * dy + 0.04, y0 + t + (j + 1) * dy - 0.04, z + 0.05, top)


def stern_details(m, x, z_deck):
    m.box("ships_black", x - 0.2, x + 0.1, -0.1, 0.1, -0.6, 0.2)  # rudder


# Ships ----------------------------------------------------------------------------------------------


def oil_tanker_old():
    """MPS Oil Tanker (1950s): bridge amidships, engine house and funnel aft, catwalk and pipes."""
    m = Model()
    L, W = 17.0, 5.0
    d = hull(m, L, W, 1.2, bow=0.24, sheer=1.0, deck="ships_deck")
    x0 = -L / 2
    # Bridge amidships.
    m.box("ships_white", -0.6, 1.6, -2.0, 2.0, d, d + 0.9)
    zt = bridge(m, -0.4, 1.3, -1.7, 1.7, d + 0.9, 2, h=0.8, win=4, wings=0.25)
    mast(m, 0.2, zt, zt + 1.4)
    # Engine house aft with a tall funnel.
    m.box("ships_white", x0 + 0.6, x0 + 4.0, -2.1, 2.1, d, d + 1.0)
    bridge(m, x0 + 0.9, x0 + 3.2, -1.7, 1.7, d + 1.0, 1, h=0.8, win=4)
    funnel(m, x0 + 2.0, 0, d + 1.8, d + 3.6, 0.55, rx=0.75)
    lifeboat(m, x0 + 2.2, -2.0, d + 1.5)
    lifeboat(m, x0 + 2.2, 2.0, d + 1.5)
    # Catwalk, pipes and tank hatches on the tank deck.
    for xa, xb in ((-4.5, -0.6), (1.6, 5.4)):
        m.box("metal", xa, xb, -0.25, 0.25, d + 0.7, d + 0.8)
        for x in range(int(xa) + 1, int(xb) + 1, 2):
            m.box("dark", x - 0.06, x + 0.06, -0.06, 0.06, d, d + 0.7)
        for y in (-0.8, 0.8):
            m.cylinder("dark", xa, xb, y, d + 0.15, 0.12, sides=6)
        for x in (xa + 0.8, (xa + xb) / 2, xb - 0.8):
            for y in (-1.4, 1.4):
                m.box("metal", x - 0.3, x + 0.3, y - 0.3, y + 0.3, d, d + 0.25)
    mast(m, 6.2, d + 0.6, d + 3.0, yard=0)
    stern_details(m, x0, d)
    m.save("ships_oil_tanker_old.glb")


def oil_tanker_modern():
    """CS-Inc. Oil Tanker (1990s): a big tanker with all its tall superstructure at the stern."""
    m = Model()
    L, W = 19.5, 5.8
    d = hull(m, L, W, 1.4, bow=0.2, sheer=0.4, deck="ships_deck_green", round_bow=True)
    x0 = -L / 2
    m.box("ships_deck_green", 6.6, 8.0, -2.4, 2.4, d, d + 0.5)  # forecastle
    # Superstructure aft: a tall block with bridge wings, and the funnel behind.
    zt = bridge(m, x0 + 1.4, x0 + 4.0, -2.3, 2.3, d, 4, h=0.75, win=5, wings=0.4)
    m.box("metal", x0 + 2.4, x0 + 2.6, -0.8, 0.8, zt, zt + 1.0)  # radar mast
    m.box("metal", x0 + 2.45, x0 + 2.55, -1.0, 1.0, zt + 0.8, zt + 0.9)
    m.box("company", x0 + 0.4, x0 + 1.4, -0.7, 0.7, d, d + 3.6)
    m.box("ships_black", x0 + 0.38, x0 + 1.42, -0.72, 0.72, d + 3.6, d + 4.0)
    m.box("ships_white", x0 + 0.38, x0 + 1.42, -0.72, 0.72, d + 2.3, d + 2.6)
    lifeboat(m, x0 + 1.0, -2.5, d + 1.0, length=1.2)
    # Deck: a pipe bundle along the middle, manifold and crane amidships.
    for y in (-0.5, -0.2, 0.2, 0.5):
        m.cylinder("ships_white" if y > 0 else "metal", x0 + 4.2, 6.6, y, d + 0.25, 0.1, sides=6)
    m.box("ships_white", -0.6, 0.6, -2.4, 2.4, d, d + 0.5)  # manifold
    m.box("ships_white", 0.0, 0.2, 1.6, 1.8, d + 0.5, d + 2.0)  # crane
    m.box("ships_white", -1.2, 0.2, 1.65, 1.75, d + 1.8, d + 1.95)
    for x in (-5.0, -2.5, 2.5, 5.0):
        for y in (-1.5, 1.5):
            m.chimney("metal", x, y, d, d + 0.3, 0.3, sides=8)
    m.box("metal", x0 + 4.2, 6.6, -0.05, 0.05, d + 0.5, d + 0.6)  # catwalk
    mast(m, 7.6, d + 0.5, d + 2.4, yard=0)
    stern_details(m, x0, d)
    m.save("ships_oil_tanker_modern.glb")


def ferry_old():
    """MPS Passenger Ferry (1950s): two decks of white superstructure, one funnel, lifeboats."""
    m = Model()
    L, W = 16.0, 5.0
    d = hull(m, L, W, 1.3, bow=0.26, sheer=0.5, deck="ships_planks")
    x0 = -L / 2
    m.box("ships_white", -5.6, 3.8, -2.2, 2.2, d, d + 1.0)
    windows_row(m, -5.4, 3.6, -2.2, 2.2, d + 0.35, h=0.4, count=10, w=0.4)
    m.box("ships_planks", -5.8, 4.0, -2.3, 2.3, d + 1.0, d + 1.08)
    m.box("ships_white", -4.0, 2.8, -1.8, 1.8, d + 1.08, d + 1.9)
    windows_row(m, -3.8, 2.6, -1.8, 1.8, d + 1.35, h=0.35, count=8, w=0.4)
    railing(m, -5.8, 4.0, -2.3, 2.3, d + 1.08)
    zt = bridge(m, 1.6, 2.8, -1.6, 1.6, d + 1.9, 1, h=0.75, win=2, wings=0.5)
    funnel(m, -1.0, 0, d + 1.9, d + 3.6, 0.6, rx=0.8)
    for x in (-3.4, -2.0, 0.6):
        for y in (-2.0, 2.0):
            lifeboat(m, x, y, d + 1.45, length=1.1)
    mast(m, 5.5, d + 0.3, d + 3.6)
    mast(m, 3.0, zt, zt + 1.0, yard=0)
    stern_details(m, x0, d)
    m.save("ships_ferry_old.glb")


def ferry_catamaran():
    """FFP Passenger Ferry (2000s): a fast catamaran with a sleek, dark-glazed cabin."""
    m = Model()
    L = 17.0
    for yc in (-1.9, 1.9):
        hull(m, L, 1.8, 0.9, draft=0.5, bow=0.35, sheer=0.3, yc=yc, deck="ships_white")
    x0 = -L / 2
    sides_only(m, "company", x0 + 0.3, 6.5, -2.75, 2.75, 0.75, 1.6, out=0)  # bridge deck between the hulls
    m.quad("company", (x0 + 0.3, 2.75, 0.75), (6.5, 2.75, 0.75), (6.5, -2.75, 0.75), (x0 + 0.3, -2.75, 0.75))
    m.box("ships_white", x0 + 0.3, 6.5, -2.8, 2.8, 1.6, 1.7)
    # Cabin with a raked, glazed front.
    rings = []
    for x, top in ((x0 + 1.4, 3.0), (3.4, 3.0), (5.6, 1.9)):
        rings.append([(x, -2.5, 1.7), (x, 2.5, 1.7), (x, 2.5, top), (x, -2.5, top)])
    loft(m, rings[:2], "ships_white", cap1=False)
    loft(m, rings[1:], ["ships_white", "ships_white", "glass", "ships_white"], cap0=False)
    sides_only(m, "glass", x0 + 1.6, 4.0, -2.5, 2.5, 2.05, 2.6, front=False, back=False)
    sides_only(m, "company", x0 + 1.4, 3.4, -2.5, 2.5, 1.7, 1.95, front=False, back=False)
    # Wheelhouse on the roof and a small mast.
    m.box("ships_white", 1.4, 3.2, -1.2, 1.2, 3.0, 3.7)
    m.box("glass", 3.2, 3.25, -1.0, 1.0, 3.25, 3.6)
    m.box("glass", 1.6, 3.0, -1.25, 1.25, 3.25, 3.55)
    m.box("metal", 0.6, 0.75, -0.1, 0.1, 3.0, 4.4)
    m.box("metal", 0.62, 0.72, -0.7, 0.7, 4.1, 4.2)
    for yc in (-1.9, 1.9):
        m.cylinder("dark", x0 - 0.3, x0 + 0.2, yc, 0.3, 0.3, sides=8)  # water jets
    m.save("ships_ferry_catamaran.glb")


def hovercraft():
    """Bakewell 300 Hovercraft: a black skirt, a long cabin and two propellers on pylons at the back."""
    m = Model()
    L, W = 15.0, 6.0
    rings = []
    for z, s in ((0.0, 0.92), (0.55, 1.0), (1.0, 0.97)):
        ring = []
        hl, hw, r = L / 2 * s, W / 2 * s, 1.6
        for k in range(16):
            a = 2 * math.pi * k / 16
            cx = (hl - r) * (1 if math.cos(a) >= 0 else -1)
            cy = (hw - r) * (1 if math.sin(a) >= 0 else -1)
            ring.append((cx + r * math.cos(a), cy + r * math.sin(a), z))
        rings.append(ring)
    loft(m, rings, "ships_skirt", cap0=False, cap1=False)
    loft(m, [rings[-1], [(x, y, 1.25) for x, y, z in rings[-1]]], "company", cap0=False)
    # Cabin with a sloping front.
    rings = [[(x, -2.2, 1.25), (x, 2.2, 1.25), (x, 2.2, 2.6), (x, -2.2, 2.6)] for x in (-5.0, 4.4)]
    rings.append([(5.6, -1.8, 1.25), (5.6, 1.8, 1.25), (4.9, 1.9, 2.4), (4.9, -1.9, 2.4)])
    loft(m, rings, "ships_white")
    windows_row(m, -4.6, 4.2, -2.2, 2.2, 1.75, h=0.45, count=12, w=0.45, front=False)
    sides_only(m, "company", -5.0, 4.4, -2.2, 2.2, 1.3, 1.5, front=False)
    m.box("ships_white", 1.8, 3.6, -0.9, 0.9, 2.6, 3.2)  # control cabin
    m.box("glass", 3.6, 3.65, -0.8, 0.8, 2.75, 3.1)
    # Propeller pylons, spinners, blades and rudder fins.
    for y in (-1.5, 1.5):
        m.box("ships_white", -5.3, -4.5, y - 0.2, y + 0.2, 2.6, 4.0)
        body(m, "ships_white", [(-5.6, 4.2, 0.05, 0.05), (-5.4, 4.2, 0.3, 0.3), (-4.4, 4.2, 0.35, 0.35), (-3.9, 4.2, 0.1, 0.1)], sides=8, yc=y)
        m.box("dark", -5.55, -5.45, y - 0.12, y + 0.12, 2.9, 5.5)
        m.box("dark", -5.55, -5.45, y - 1.3, y + 1.3, 4.08, 4.32)
        fin(m, "company", -6.0, 1.0, -6.3, 0.8, 1.25, 3.4, y=y * 1.6, thick=0.15)
    m.save("ships_hovercraft.glb")


def toy_paddle_ferry():
    """Chugger-Chug Passenger Ferry: a chubby toy paddle steamer with a big striped funnel."""
    m = Model()
    L, W = 14.0, 5.6
    d = hull(m, L, W, 1.2, draft=0.6, bow=0.3, sheer=0.6, upper="ships_toy_red", lower="ships_toy_yellow",
             deck="ships_planks", round_bow=True, transom=0.9, band=(0.9, 1.15, "company"))
    m.box("ships_toy_yellow", -4.5, 2.5, -2.0, 2.0, d, d + 1.4)
    for x in (-3.6, -2.2, -0.8, 0.6, 2.0):
        for y in (-2.05, 2.0):
            ycylinder(m, "glass", x, y, y + 0.05, d + 0.75, 0.35, sides=10)
    m.box("ships_toy_cyan", -4.8, 2.8, -2.3, 2.3, d + 1.4, d + 1.6)
    m.box("ships_toy_yellow", 1.0, 2.4, -1.2, 1.2, d + 1.6, d + 2.4)
    m.box("glass", 2.4, 2.45, -1.0, 1.0, d + 1.85, d + 2.25)
    m.box("ships_toy_cyan", 0.9, 2.5, -1.3, 1.3, d + 2.4, d + 2.55)
    # Fat funnel with stripes.
    zcylinder(m, "ships_toy_red", -1.6, 0, d + 1.6, d + 2.4, 0.75, sides=14)
    zcylinder(m, "ships_white", -1.6, 0, d + 2.4, d + 2.8, 0.78, sides=14)
    zcylinder(m, "ships_toy_red", -1.6, 0, d + 2.8, d + 3.4, 0.8, sides=14)
    zcylinder(m, "ships_black", -1.6, 0, d + 3.4, d + 3.6, 0.85, sides=14)
    # Paddle wheels in boxes on the sides.
    for s in (-1, 1):
        y_in, y_out = s * 2.7, s * 3.3
        ycylinder(m, "company", -0.8, min(y_in, y_out), max(y_in, y_out), 0.8, 1.15, sides=14)
        ycylinder(m, "ships_toy_yellow", -0.8, min(y_out, y_out + s * 0.05), max(y_out, y_out + s * 0.05), 0.8, 0.5, sides=10)
    m.box("ships_toy_red", 5.2, 5.6, -0.1, 0.1, d + 0.4, d + 1.6)  # flag pole
    m.box("ships_toy_yellow", 5.0, 5.4, -0.08, 0.08, d + 1.2, d + 1.6)
    m.save("ships_toy_paddle_ferry.glb")


def toy_bubble_ferry():
    """Shivershake Passenger Ferry: a later toy ferry, sleek, with a big glass dome and fins."""
    m = Model()
    L, W = 16.0, 5.4
    d = hull(m, L, W, 1.2, draft=0.6, bow=0.4, sheer=0.7, upper="ships_toy_purple", lower="ships_toy_pink",
             deck="ships_toy_pink", round_bow=False, transom=0.85, band=(0.8, 1.05, "company"))
    # Long rounded cabin and a glass dome.
    body(m, "ships_toy_pink", [(-6.0, d, 0.6, 0.4), (-5.4, d + 0.4, 1.9, 0.9), (2.0, d + 0.4, 2.1, 1.0),
                               (4.4, d + 0.2, 1.4, 0.7), (5.4, d, 0.3, 0.2)], sides=14)
    for x in (-4.4, -3.0, -1.6, -0.2, 1.2):
        for y in (-2.0, 1.95):
            ycylinder(m, "glass", x, y, y + 0.1, d + 0.55, 0.32, sides=10)
    body(m, "glass", [(0.0, d + 1.2, 0.05, 0.05), (0.4, d + 1.2, 1.0, 0.8), (1.6, d + 1.2, 1.1, 0.9), (2.8, d + 1.2, 0.5, 0.4), (3.0, d + 1.2, 0.05, 0.05)], sides=12)
    # Two swept toy funnels at the back.
    for y in (-1.0, 1.0):
        rings = [[(-4.0, y - 0.35, d + 1.0), (-3.0, y - 0.35, d + 1.0), (-3.0, y + 0.35, d + 1.0), (-4.0, y + 0.35, d + 1.0)],
                 [(-5.0, y - 0.3, d + 2.8), (-4.2, y - 0.3, d + 2.8), (-4.2, y + 0.3, d + 2.8), (-5.0, y + 0.3, d + 2.8)]]
        loft(m, rings, "ships_toy_cyan")
        m.box("company", -5.05, -4.15, y - 0.32, y + 0.32, d + 2.8, d + 3.1)
    m.save("ships_toy_bubble_ferry.glb")


def cargo_ship_old():
    """Yate Cargo ship (1950s): forecastle, holds with derrick masts, white midships-aft superstructure."""
    m = Model()
    L, W = 17.0, 5.0
    d = hull(m, L, W, 1.2, bow=0.24, sheer=1.0, deck="ships_deck")
    x0 = -L / 2
    for xa, xb in ((2.6, 5.2), (-0.5, 2.0), (-6.2, -4.2)):
        hatch_with_load(m, xa, xb, -1.5, 1.5, d)
    # Derrick masts between the holds, with booms.
    for x, boom in ((2.3, 1), (-3.9, -1)):
        m.box("ships_black", x - 0.1, x + 0.1, -0.1, 0.1, d, d + 3.6)
        m.box("ships_black", x - 0.06, x + 0.06, -0.9, 0.9, d + 2.8, d + 2.92)
        for y in (-0.5, 0.5):
            m.quad("ships_black", (x, y - 0.05, d + 0.7), (x, y + 0.05, d + 0.7), (x + boom * 2.0, y + 0.05, d + 2.2), (x + boom * 2.0, y - 0.05, d + 2.2))
            m.quad("ships_black", (x, y + 0.05, d + 0.7), (x, y - 0.05, d + 0.7), (x + boom * 2.0, y - 0.05, d + 2.2), (x + boom * 2.0, y + 0.05, d + 2.2))
    # Superstructure and funnel.
    m.box("ships_white", -3.6, -0.9, -2.05, 2.05, d, d + 0.9)
    zt = bridge(m, -2.4, -1.1, -1.7, 1.7, d + 0.9, 2, h=0.75, win=3, wings=0.3)
    funnel(m, -3.0, 0, d + 0.9, d + 3.2, 0.5, rx=0.65)
    lifeboat(m, -3.2, -1.9, d + 1.3, length=1.0)
    lifeboat(m, -3.2, 1.9, d + 1.3, length=1.0)
    m.box("ships_white", x0 + 0.4, -6.4, -1.9, 1.9, d, d + 0.6)  # poop deck
    mast(m, 6.4, d + 0.6, d + 3.0, yard=0)
    stern_details(m, x0, d)
    m.save("ships_cargo_ship_old.glb")


def container_ship():
    """Bakewell Cargo ship (2000s): a container ship with stacks of containers and the bridge aft."""
    m = Model()
    L, W = 20.0, 5.8
    d = hull(m, L, W, 1.3, bow=0.2, sheer=0.5, deck="ships_deck_green", round_bow=True)
    x0 = -L / 2
    m.box("company", 7.0, 8.4, -2.3, 2.3, d, d + 0.7)  # forecastle with a breakwater
    m.box("ships_white", 6.8, 7.0, -2.4, 2.4, d, d + 1.0)
    zt = bridge(m, x0 + 2.0, x0 + 3.6, -2.4, 2.4, d, 4, h=0.75, win=4, wings=0.3)
    m.box("metal", x0 + 2.6, x0 + 2.8, -0.6, 0.6, zt, zt + 0.9)
    m.box("company", x0 + 0.6, x0 + 1.8, -0.8, 0.8, d, d + 3.0)  # funnel casing
    m.box("ships_black", x0 + 0.58, x0 + 1.82, -0.82, 0.82, d + 3.0, d + 3.3)
    # Container bays: hatch covers and stacks of 20 ft boxes in four colours.
    colours = ["load_ships_box_red", "load_ships_box_green", "load_ships_box_yellow", "load_ships_box_grey"]
    bay_len, gap = 1.6, 0.15
    for b in range(8):
        xa = x0 + 4.0 + b * (bay_len + gap)
        m.box("company_dark", xa, xa + bay_len, -2.5, 2.5, d, d + 0.25)
        tiers = 3 if 1 <= b <= 5 else 2
        for r in range(4):
            ya = -2.4 + r * 1.2
            for t in range(tiers):
                mat = colours[(b * 3 + r * 5 + t * 7) % 4]
                m.box(mat, xa + 0.05, xa + bay_len - 0.05, ya + 0.05, ya + 1.15, d + 0.25 + t * 0.85, d + 0.25 + (t + 1) * 0.85 - 0.05)
    mast(m, 7.9, d + 0.7, d + 2.8, yard=0)
    stern_details(m, x0, d)
    m.save("ships_container_ship.glb")


def toy_tug_cargo():
    """Mightymover Cargo ship: a stubby toy tug with its cabin forward and an open hold of toy blocks."""
    m = Model()
    L, W = 14.0, 5.6
    d = hull(m, L, W, 1.1, draft=0.6, bow=0.28, sheer=0.7, upper="ships_toy_yellow", lower="ships_toy_red",
             deck="ships_toy_green", round_bow=True, transom=0.92, band=(0.7, 1.0, "ships_black"))
    # Cabin forward.
    m.box("ships_toy_red", 2.0, 4.2, -1.6, 1.6, d, d + 1.6)
    m.box("ships_toy_yellow", 1.9, 4.3, -1.7, 1.7, d + 1.6, d + 1.8)
    for y in (-1.65, 1.6):
        ycylinder(m, "glass", 3.1, y, y + 0.05, d + 1.0, 0.38, sides=10)
    m.box("glass", 4.2, 4.25, -1.2, 1.2, d + 0.9, d + 1.4)
    zcylinder(m, "company", 1.2, 0, d, d + 2.6, 0.5, sides=12)
    zcylinder(m, "ships_black", 1.2, 0, d + 2.6, d + 2.9, 0.55, sides=12)
    # Open hold with toy blocks.
    hatch_with_load(m, -5.8, 0.4, -2.2, 2.2, d, coaming=0.6, load="load_ships_toys", heap=0.4)
    for i, (x, y) in enumerate(((-4.6, -1.0), (-2.4, 0.9), (-0.8, -0.6))):
        m.box("load_ships_toys_blue", x - 0.45, x + 0.45, y - 0.45, y + 0.45, d + 0.05, d + 1.5)
    m.save("ships_toy_tug_cargo.glb")


def toy_hover_cargo():
    """Powernaut Cargo ship: a later toy freighter, round-ended, with a crane and a big cargo well."""
    m = Model()
    L, W = 17.0, 5.8
    d = hull(m, L, W, 1.3, draft=0.6, bow=0.3, sheer=0.3, upper="ships_toy_cyan", lower="ships_toy_purple",
             deck="ships_toy_yellow", round_bow=True, transom=0.95, band=(0.85, 1.1, "company"))
    # Round bridge pod at the back.
    zcylinder(m, "ships_toy_yellow", -5.6, 0, d, d + 1.6, 1.6, sides=16)
    zcylinder(m, "glass", -5.6, 0, d + 1.6, d + 2.2, 1.5, sides=16)
    zcylinder(m, "ships_toy_purple", -5.6, 0, d + 2.2, d + 2.5, 1.7, sides=16)
    m.box("metal", -5.7, -5.5, -0.1, 0.1, d + 2.5, d + 3.6)
    zcylinder(m, "ships_toy_red", -5.6, 0, d + 3.6, d + 3.9, 0.25, sides=8)
    # Cargo well with crates.
    hatch_with_load(m, -3.6, 3.0, -2.3, 2.3, d, coaming=0.7, load="load_ships_crates", heap=0.6)
    # Crane on the foredeck.
    zcylinder(m, "ships_toy_red", 4.6, 0, d, d + 1.8, 0.45, sides=10)
    m.quad("ships_toy_red", (4.6, -0.15, d + 1.7), (4.6, 0.15, d + 1.7), (1.4, 0.15, d + 3.0), (1.4, -0.15, d + 3.0))
    m.quad("ships_toy_red", (4.6, 0.15, d + 1.7), (4.6, -0.15, d + 1.7), (1.4, -0.15, d + 3.0), (1.4, 0.15, d + 3.0))
    m.box("ships_black", 1.38, 1.46, -0.03, 0.03, d + 1.6, d + 3.0)
    m.box("ships_toy_yellow", 1.1, 1.7, -0.3, 0.3, d + 1.4, d + 1.6)
    m.save("ships_toy_freighter.glb")


def build():
    oil_tanker_old()
    oil_tanker_modern()
    ferry_old()
    ferry_catamaran()
    hovercraft()
    toy_paddle_ferry()
    toy_bubble_ferry()
    cargo_ship_old()
    container_ship()
    toy_tug_cargo()
    toy_hover_cargo()
    entries = [
        ([0], "ships_oil_tanker_old.glb"),
        ([1], "ships_oil_tanker_modern.glb"),
        ([2], "ships_ferry_old.glb"),
        ([3], "ships_ferry_catamaran.glb"),
        ([4], "ships_hovercraft.glb"),
        ([5], "ships_toy_paddle_ferry.glb"),
        ([6], "ships_toy_bubble_ferry.glb"),
        ([7], "ships_cargo_ship_old.glb"),
        ([8], "ships_container_ship.glb"),
        ([9], "ships_toy_tug_cargo.glb"),
        ([10], "ships_toy_freighter.glb"),
    ]
    return {"vehicles": [{"type": "ship", "ids": ids, "model": f} for ids, f in entries], "buildings": []}
