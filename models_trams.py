"""Trams and trolleybuses of the fork's vehicle NewGRF (newgrf/opengfx3d_trams.grf), all original designs.

They belong to the NewGRF with ID 4F473354 ("OG3T", made by make_trams_grf.py); the ids are the local vehicle ids in
that NewGRF. They start at 100, because ids below 88 would replace the original road vehicles of the game.
Articulated vehicles have one model per part, each with its own id:

  100  Hackney horse tram (1860)            101  Albion single-truck tram (1890)
  102  Corridor bogie tram (1925)           103, 104  Meridian articulated tram (1960), front and rear
  105, 106, 107  Vela low-floor tram (1995), front, middle and rear
  108  Works tram for mail (1900)           109  Penrose trolleybus (1930)
  110  Castor trolleybus (1965)             111, 112  Lyra articulated trolleybus (1990), front and rear
  113  Toyland tram                         114  Toyland trolleybus

A vehicle stands with its middle at the origin, its front along +x and the road at z = 0. Each part is about 8 long,
the length of one road vehicle. Trams take power from the contact wire over their lane, trolleybuses from the pair of
wires over their lane (see models_track.py): pantographs and trolley poles reach up to CONTACT.
"""

import math

from gfx3d import MATERIALS, Model
from models_road import arch, cyl, hexa, sphere
from models_track import CONTACT, PAIR

GRFID = "4F473354"

MATERIALS.update({
    "tram_cream": (0.93, 0.89, 0.76),
    "tram_wood": (0.55, 0.36, 0.20),
    "tram_gold": (0.85, 0.68, 0.28),
    "tram_pole": (0.20, 0.20, 0.22),
    "tram_horse": (0.42, 0.26, 0.14),
    "tram_horse_dark": (0.20, 0.13, 0.08),
    "tram_mail": (0.78, 0.16, 0.14),
    "tram_toy_yellow": (0.99, 0.84, 0.24),
    "tram_toy_pink": (0.96, 0.58, 0.74),
    "tram_toy_blue": (0.32, 0.58, 0.92),
})

W = 2.8
Y0, Y1 = -W / 2, W / 2


def bogies(m, xs, radius=0.42):
    """Tram wheels under the body: small rail wheels, hidden mostly behind a skirt."""
    for x in xs:
        m.box("dark", x - 0.9, x + 0.9, -1.0, 1.0, 0.25, 0.6)
        for dx in (-0.55, 0.55):
            for y in (-0.75, 0.75):
                m.wheel(x + dx, y, radius, 0.2)


def windows(m, x0, x1, z0, z1, n, frame, y0=Y0, y1=Y1):
    """A band of windows along both sides with pillars in the body colour."""
    m.box("glass", x0, x1, y0 + 0.06, y1 - 0.06, z0, z1)
    for i in range(n + 1):
        x = x0 + i * (x1 - x0 - 0.22) / n
        for y in (y0, y1 - 0.1):
            m.box(frame, x, x + 0.22, y, y + 0.1, z0, z1)


def headlight(m, x, z, toward=1):
    m.box("light", x - 0.03 if toward > 0 else x - 0.03, x + 0.06, -0.25, 0.25, z, z + 0.3)


def pantograph(m, x, roof):
    """A diamond pantograph on the roof, its shoe pressed against the contact wire above the lane."""
    m.box("tram_pole", x - 0.6, x + 0.6, -0.5, 0.5, roof, roof + 0.12)
    mid = (roof + CONTACT) / 2
    for a, b in (((x - 0.5, roof + 0.12), (x, mid)), ((x, mid), (x - 0.5, CONTACT - 0.1)),
                 ((x + 0.5, roof + 0.12), (x, mid)), ((x, mid), (x + 0.5, CONTACT - 0.1))):
        strut(m, "tram_pole", (a[0], 0.0, a[1]), (b[0], 0.0, b[1]), 0.05, across=0.8)
    m.box("tram_pole", x - 0.7, x + 0.7, -0.7, 0.7, CONTACT - 0.12, CONTACT - 0.04)


def trolley_pole(m, x_foot, roof, y, length=4.6):
    """One trolley pole from a base on the roof, sloping back up to a wire of the pair."""
    rise = CONTACT - roof - 0.25
    run = math.sqrt(max(length * length - rise * rise, 1.0))
    strut(m, "tram_pole", (x_foot, y, roof + 0.25), (x_foot - run, y, CONTACT - 0.05), 0.06)
    m.box("dark", x_foot - run - 0.15, x_foot - run + 0.15, y - 0.1, y + 0.1, CONTACT - 0.15, CONTACT)


def trolley_poles(m, x_foot, roof):
    m.box("tram_pole", x_foot - 0.6, x_foot + 0.4, -0.7, 0.7, roof, roof + 0.25)
    for y in (-PAIR, PAIR):
        trolley_pole(m, x_foot, roof, y)


def strut(m, mat, a, b, r, across=None):
    """A thin square bar from a to b; with across, a flat bar that wide across y (for pantograph arms)."""
    dx, dy, dz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    length = math.sqrt(dx * dx + dy * dy + dz * dz)
    ux, uy, uz = dx / length, dy / length, dz / length
    # Two directions across the bar.
    if abs(uz) < 0.9:
        px, py, pz = -uy, ux, 0.0
    else:
        px, py, pz = 1.0, 0.0, 0.0
    n = math.sqrt(px * px + py * py + pz * pz)
    px, py, pz = px / n, py / n, pz / n
    qx, qy, qz = uy * pz - uz * py, uz * px - ux * pz, ux * py - uy * px
    wy = (across / 2) if across else r
    corners = []
    for p in (a, b):
        ring = []
        for sp, sq in ((1, 1), (-1, 1), (-1, -1), (1, -1)):
            if across:
                ring.append((p[0] + sq * r * qx, p[1] + sp * wy, p[2] + sq * r * qz))
            else:
                ring.append((p[0] + sp * r * px + sq * r * qx, p[1] + sp * r * py + sq * r * qy, p[2] + sp * r * pz + sq * r * qz))
        corners.append(ring)
    hexa(m, mat, corners[0] + corners[1])


# --- Trams -------------------------------------------------------------------------------------------------------

def horse_tram():
    """A small open-platform car drawn by two horses; the horses walk ahead within the length of one vehicle."""
    m = Model()
    x0, x1 = -4.2, 1.6
    m.box("dark", x0 + 0.3, x1 - 0.3, -0.9, 0.9, 0.3, 0.7)
    for x in (x0 + 1.4, x1 - 1.4):
        for y in (-0.9, 0.9):
            m.wheel(x, y, 0.45, 0.15)
    m.box("company", x0 + 0.8, x1 - 0.8, Y0 + 0.2, Y1 - 0.2, 0.7, 1.7)
    m.box("tram_gold", x0 + 0.8, x1 - 0.8, Y0 + 0.18, Y1 - 0.18, 1.45, 1.55)
    windows(m, x0 + 0.8, x1 - 0.8, 1.7, 2.6, 4, "tram_cream", Y0 + 0.2, Y1 - 0.2)
    m.box("tram_cream", x0 + 0.8, x1 - 0.8, Y0 + 0.2, Y1 - 0.2, 2.6, 2.75)
    # Open platforms at both ends with a rail, under the overhanging roof; seats on top (an "omnibus" garden seat).
    for xa, xb in ((x0, x0 + 0.8), (x1 - 0.8, x1)):
        m.box("tram_wood", xa, xb, Y0 + 0.3, Y1 - 0.3, 0.7, 0.8)
        m.box("dark", xa, xa + 0.06, Y0 + 0.3, Y1 - 0.3, 0.8, 1.6)
    m.box("tram_wood", x0, x1, Y0 + 0.1, Y1 - 0.1, 2.75, 2.85)
    m.box("dark", x0 + 0.2, x1 - 0.2, Y0 + 0.15, Y0 + 0.2, 2.85, 3.3)
    m.box("dark", x0 + 0.2, x1 - 0.2, Y1 - 0.2, Y1 - 0.15, 2.85, 3.3)
    m.box("tram_wood", x0 + 0.6, x1 - 0.6, -0.4, 0.4, 2.85, 3.15)
    # Shafts and two horses side by side.
    m.box("tram_wood", x1, x1 + 1.6, -0.8, -0.7, 1.0, 1.1)
    m.box("tram_wood", x1, x1 + 1.6, 0.7, 0.8, 1.0, 1.1)
    for y in (-0.45, 0.45):
        hx = x1 + 1.5
        m.box("tram_horse", hx - 0.9, hx + 0.9, y - 0.3, y + 0.3, 1.1, 1.9)
        m.box("tram_horse", hx + 0.6, hx + 1.2, y - 0.18, y + 0.18, 1.7, 2.3)
        m.box("tram_horse", hx + 1.1, hx + 1.6, y - 0.16, y + 0.16, 1.95, 2.25)
        m.box("tram_horse_dark", hx + 0.6, hx + 1.0, y - 0.05, y + 0.05, 2.1, 2.45)
        for lx in (hx - 0.7, hx + 0.7):
            m.box("tram_horse", lx - 0.1, lx + 0.1, y - 0.25, y - 0.05, 0.0, 1.15)
            m.box("tram_horse", lx - 0.1, lx + 0.1, y + 0.05, y + 0.25, 0.0, 1.15)
        m.box("tram_horse_dark", hx - 1.1, hx - 0.9, y - 0.06, y + 0.06, 1.1, 1.8)
    return m


def single_truck_tram():
    """An 1890s tram: a short closed saloon on one truck, open end platforms, a clerestory roof and a trolley pole."""
    m = Model()
    x0, x1 = -4.1, 4.1
    m.box("dark", -1.6, 1.6, -1.0, 1.0, 0.25, 0.6)
    for x in (-1.0, 1.0):
        for y in (-0.75, 0.75):
            m.wheel(x, y, 0.45, 0.2)
    m.box("company", x0 + 1.2, x1 - 1.2, Y0, Y1, 0.6, 1.8)
    m.box("tram_gold", x0 + 1.2, x1 - 1.2, Y0 - 0.02, Y1 + 0.02, 1.55, 1.65)
    windows(m, x0 + 1.2, x1 - 1.2, 1.8, 2.7, 5, "tram_cream")
    m.box("tram_cream", x0 + 1.2, x1 - 1.2, Y0, Y1, 2.7, 2.85)
    for xa, xb, s in ((x0, x0 + 1.2, -1), (x1 - 1.2, x1, 1)):
        m.box("company", xa, xb, Y0 + 0.2, Y1 - 0.2, 0.55, 1.4)  # dash panel
        m.box("dark", xa, xb, Y0 + 0.2, Y1 - 0.2, 1.4, 1.48)
        xe = xb if s > 0 else xa
        m.box("dark", xe - 0.05, xe + 0.05, Y0 + 0.3, Y0 + 0.4, 1.4, 2.85)
        m.box("dark", xe - 0.05, xe + 0.05, Y1 - 0.4, Y1 - 0.3, 1.4, 2.85)
        headlight(m, xe, 1.0, s)
    m.box("roof", x0 + 0.1, x1 - 0.1, Y0 + 0.1, Y1 - 0.1, 2.85, 3.0)
    m.box("glass", x0 + 1.4, x1 - 1.4, -0.7, 0.7, 3.0, 3.25)
    m.box("roof", x0 + 1.3, x1 - 1.3, -0.8, 0.8, 3.25, 3.35)
    # One trolley pole for the single contact wire, sloping back from the middle of the roof.
    m.box("tram_pole", -0.4, 0.4, -0.4, 0.4, 3.35, 3.55)
    rise = CONTACT - 3.55
    strut(m, "tram_pole", (0.0, 0.0, 3.5), (-math.sqrt(4.4 ** 2 - rise ** 2), 0.0, CONTACT - 0.05), 0.06)
    return m


def bogie_tram(mail=False):
    """A 1920s enclosed bogie tram with a bow collector; or, with mail, a works tram carrying mail bags."""
    m = Model()
    x0, x1 = -4.3, 4.3
    bogies(m, (-2.4, 2.4))
    body = "tram_mail" if mail else "company"
    m.box(body, x0 + 0.3, x1 - 0.3, Y0, Y1, 0.6, 1.9)
    for x, s in ((x0, -1), (x1, 1)):
        xn = x + 0.3 * -s
        hexa(m, body, [(xn, Y0 + 0.1, 0.6), (x, -0.8, 0.6), (x, 0.8, 0.6), (xn, Y1 - 0.1, 0.6),
                       (xn, Y0 + 0.1, 1.9), (x, -0.8, 1.9), (x, 0.8, 1.9), (xn, Y1 - 0.1, 1.9)])
        headlight(m, x, 1.0, s)
        m.box("glass", min(x, xn) - 0.02, max(x, xn) + 0.02, -0.7, 0.7, 1.9, 2.75)
    m.box("tram_cream" if not mail else "dark", x0 + 0.3, x1 - 0.3, Y0 - 0.02, Y1 + 0.02, 1.6, 1.7)
    if mail:
        m.box("tram_mail", x0 + 0.3, x1 - 0.3, Y0, Y1, 1.9, 2.75)
        for x in (-2.0, 0.6):
            m.box("dark", x, x + 1.4, Y0 - 0.02, Y1 + 0.02, 0.9, 2.55)  # sliding doors
        m.box("tram_gold", -0.6, 0.6, Y0 - 0.03, Y1 + 0.03, 2.1, 2.4)
    else:
        windows(m, x0 + 0.3, x1 - 0.3, 1.9, 2.75, 7, "company")
    m.box("roof", x0, x1, Y0 + 0.05, Y1 - 0.05, 2.75, 2.9)
    arch(m, "roof", x0 + 0.2, x1 - 0.2, Y0 + 0.1, Y1 - 0.1, 2.9, 0.35)
    # A bow collector: a frame leaning back from the roof, its bow along the wire.
    m.box("tram_pole", -0.5, 0.5, -0.7, 0.7, 3.2, 3.32)
    for y in (-0.6, 0.6):
        strut(m, "tram_pole", (0.3, y, 3.3), (-1.4, y * 0.7, CONTACT - 0.1), 0.05)
    m.box("tram_pole", -1.55, -1.25, -0.8, 0.8, CONTACT - 0.12, CONTACT - 0.02)
    return m


def modern_part(cab_front, cab_rear, panto=False, low_floor=False, body="company"):
    """One part of an articulated modern tram: rounded cabs where it ends, a bellows where it joins another part."""
    m = Model()
    x0, x1 = -4.1, 4.1
    floor = 0.35 if low_floor else 0.6
    if low_floor:
        m.box("dark", -1.2, 1.2, -1.0, 1.0, 0.1, 0.4)
        for x in (-0.6, 0.6):
            for y in (-0.75, 0.75):
                m.wheel(x, y, 0.32, 0.18)
    else:
        bogies(m, (0.0,))
    xa = x0 + (0.9 if cab_rear else 0.25)
    xb = x1 - (0.9 if cab_front else 0.25)
    m.box(body, xa, xb, Y0, Y1, floor, 1.6)
    windows(m, xa, xb, 1.6, 2.85, 4, body)
    m.box(body, xa, xb, Y0, Y1, 2.85, 3.1)
    m.box("tram_cream", xa, xb, Y0 - 0.02, Y1 + 0.02, 1.35, 1.5)
    m.box("roof", xa + 0.2, xb - 0.2, -1.1, 1.1, 3.1, 3.35)  # roof equipment
    for has_cab, xe, s in ((cab_front, x1, 1), (cab_rear, x0, -1)):
        xi = xb if s > 0 else xa
        if has_cab:
            # A sloping nose with a big windscreen.
            hexa(m, body, [(xi, Y0, floor), (xe, Y0 + 0.25, floor), (xe, Y1 - 0.25, floor), (xi, Y1, floor),
                           (xi, Y0, 1.6), (xe, Y0 + 0.25, 1.6), (xe, Y1 - 0.25, 1.6), (xi, Y1, 1.6)])
            hexa(m, "glass", [(xi, Y0 + 0.05, 1.6), (xe, Y0 + 0.3, 1.6), (xe, Y1 - 0.3, 1.6), (xi, Y1 - 0.05, 1.6),
                              (xi, Y0 + 0.05, 2.85), (xe - 0.45 * s, Y0 + 0.3, 2.85), (xe - 0.45 * s, Y1 - 0.3, 2.85), (xi, Y1 - 0.05, 2.85)])
            hexa(m, body, [(xi, Y0, 2.85), (xe - 0.45 * s, Y0 + 0.3, 2.85), (xe - 0.45 * s, Y1 - 0.3, 2.85), (xi, Y1, 2.85),
                           (xi, Y0, 3.1), (xe - 0.5 * s, Y0 + 0.3, 3.1), (xe - 0.5 * s, Y1 - 0.3, 3.1), (xi, Y1, 3.1)])
            for y in (-0.9, 0.6):
                m.box("light", xe - 0.06 if s > 0 else xe, xe + 0.06 if s > 0 else xe + 0.06, y, y + 0.3, 0.9, 1.1)
        else:
            # Half of the bellows between two parts.
            m.box("dark", min(xi, xe), max(xi, xe), Y0 + 0.15, Y1 - 0.15, floor, 3.0)
    if panto:
        pantograph(m, 0.0, 3.35)
    return m


def toy_tram():
    m = modern_part(True, True, panto=True, body="tram_toy_blue")
    sphere(m, "tram_toy_yellow", 0.0, 0.0, 3.4, 0.35)
    for x in (-2.0, 2.0):
        cyl(m, "tram_toy_pink", "y", (x, 2.2), 0.35, Y0 - 0.05, Y1 + 0.05, sides=10)
    return m


# --- Trolleybuses ------------------------------------------------------------------------------------------------

def trolleybus(style, poles=True, front=True, rear=True, body="company"):
    """A trolleybus body: 'round' (1930s), 'square' (1960s), 'modern' (articulated) or 'toy'."""
    m = Model()
    x0, x1 = -4.3, 4.3
    for x in ((-2.6, 2.6) if front and rear else ((2.0,) if front else (-1.8,))):
        for y in (Y0 + 0.2, Y1 - 0.2):
            m.wheel(x, y, 0.6, 0.42)
    m.box("dark", x0 + 0.2, x1 - 0.2, Y0 + 0.2, Y1 - 0.2, 0.45, 0.75)
    xa = x0 if rear else x0 + 0.25
    xb = x1 if front else x1 - 0.25
    low = 0.75
    m.box(body, xa, xb, Y0, Y1, low, 1.9)
    m.box("tram_cream" if style != "toy" else "tram_toy_yellow", xa, xb, Y0 - 0.02, Y1 + 0.02, 1.65, 1.8)
    windows(m, xa + (0.9 if rear else 0), xb - (0.9 if front else 0), 1.9, 2.9, 5, body)
    if style == "round":
        arch(m, body, xa, xb, Y0, Y1, 2.9, 0.45)
    else:
        m.box(body, xa, xb, Y0, Y1, 2.9, 3.15)
    roof = 3.35 if style == "round" else 3.15
    for has_end, xe, s in ((front, x1, 1), (rear, x0, -1)):
        if has_end:
            xi = xe - 0.9 * s
            m.box("glass", min(xi, xe) - 0.01, max(xi, xe) + 0.01, Y0 + 0.08, Y1 - 0.08, 1.9, 2.9)
            m.box("company_dark" if style != "toy" else body, min(xe, xe - 0.08 * s), max(xe, xe - 0.08 * s), Y0, Y1, 1.9, 2.05)
            m.box("dark", min(xe, xe + 0.15 * s), max(xe, xe + 0.15 * s), Y0, Y1, 0.6, 0.95)
            for y in (Y0 + 0.2, Y1 - 0.6):
                m.box("light", min(xe, xe + 0.06 * s), max(xe, xe + 0.06 * s), y, y + 0.4, 1.1, 1.4)
        else:
            m.box("dark", min(xe, xe - 0.25 * s), max(xe, xe - 0.25 * s), Y0 + 0.15, Y1 - 0.15, low, 3.0)
    if style == "toy":
        for x in (-1.5, 1.5):
            sphere(m, "tram_toy_pink", x, 0.0, roof + 0.1, 0.4)
    if poles:
        # Poles stand on a gantry over the rear axle and slope back, a little longer than the bus.
        trolley_poles(m, -1.2 if (front and rear) else 1.6, roof)
    return m


def build():
    models = [
        ("tram_horse.glb", horse_tram, [100]),
        ("tram_albion.glb", single_truck_tram, [101]),
        ("tram_corridor.glb", bogie_tram, [102]),
        ("tram_meridian_front.glb", lambda: modern_part(True, False, panto=True), [103]),
        ("tram_meridian_rear.glb", lambda: modern_part(False, True), [104]),
        ("tram_vela_front.glb", lambda: modern_part(True, False, low_floor=True), [105]),
        ("tram_vela_middle.glb", lambda: modern_part(False, False, panto=True, low_floor=True), [106]),
        ("tram_vela_rear.glb", lambda: modern_part(False, True, low_floor=True), [107]),
        ("tram_works_mail.glb", lambda: bogie_tram(mail=True), [108]),
        ("trolleybus_penrose.glb", lambda: trolleybus("round"), [109]),
        ("trolleybus_castor.glb", lambda: trolleybus("square"), [110]),
        ("trolleybus_lyra_front.glb", lambda: trolleybus("modern", poles=False, rear=False), [111]),
        ("trolleybus_lyra_rear.glb", lambda: trolleybus("modern", front=False), [112]),
        ("tram_toy.glb", toy_tram, [113]),
        ("trolleybus_toy.glb", lambda: trolleybus("toy", body="tram_toy_pink"), [114]),
    ]
    vehicles = []
    for filename, make, ids in models:
        make().save(filename)
        vehicles.append({"type": "road", "grfid": GRFID, "ids": ids, "model": filename})
    return {"vehicles": vehicles, "buildings": []}
