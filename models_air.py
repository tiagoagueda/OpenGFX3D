"""Aircraft of the base game: propeller planes, airliners, supersonic jets, helicopters and the toyland ones.

Small planes are about 10 long, big jets 16 to 20, front to +x, wheels on z = 0 (the game handles the
flying height). Helicopters are made without their main rotor, which the game draws as its own vehicle.
The shape helpers come from models_ships.
"""

import math

from gfx3d import MATERIALS, Model
from models_ships import body, fin, loft, sides_only, wing, ycylinder, zcylinder

for _name, _colour in {
    "air_white": (0.94, 0.94, 0.93),
    "air_grey": (0.66, 0.68, 0.71),
    "air_silver": (0.76, 0.77, 0.78),
    "air_dark": (0.20, 0.21, 0.23),
    "air_toy_red": (0.92, 0.22, 0.20),
    "air_toy_yellow": (0.98, 0.84, 0.20),
    "air_toy_green": (0.34, 0.76, 0.32),
    "air_toy_orange": (0.98, 0.56, 0.16),
    "air_toy_pink": (0.95, 0.56, 0.76),
    "air_toy_purple": (0.60, 0.38, 0.80),
}.items():
    MATERIALS.setdefault(_name, _colour)


# Parts ----------------------------------------------------------------------------------------------


def belly_mats(top, belly, sides=12):
    """Edge materials for a body ring: the lower part in belly, the rest in top."""
    return [belly if math.sin(2 * math.pi * (k + 0.5) / sides) < -0.6 else top for k in range(sides)]


def fuselage(m, length, r, zc, nose=None, tail=None, tail_up=None, top="air_white", belly="company", x_mid=0.0, rz=None):
    rz = rz or r
    nose = nose if nose is not None else 2.2 * r
    tail = tail if tail is not None else 3.2 * r
    tail_up = tail_up if tail_up is not None else 0.55 * rz
    xn, xt = x_mid + length / 2, x_mid - length / 2
    stations = [
        (xn, zc - 0.2 * rz, 0.08 * r, 0.08 * rz),
        (xn - 0.3 * nose, zc - 0.08 * rz, 0.62 * r, 0.6 * rz),
        (xn - 0.65 * nose, zc, 0.9 * r, 0.9 * rz),
        (xn - nose, zc, r, rz),
        (xt + tail, zc, r, rz),
        (xt + 0.45 * tail, zc + tail_up * 0.6, 0.6 * r, 0.6 * rz),
        (xt, zc + tail_up, 0.12 * r, 0.22 * rz),
    ]
    body(m, belly_mats(top, belly), stations)
    return xn, xt


def cabin_windows(m, x0, x1, r, zc, h=0.28, stripe="company"):
    for s in (1, -1):
        y0, y1 = (r - 0.04, r + 0.03) if s > 0 else (-r - 0.03, -r + 0.04)
        m.box("glass", x0, x1, y0, y1, zc + 0.08, zc + 0.08 + h)
        if stripe:
            m.box(stripe, x0 - 0.6, x1 + 0.3, y0, y1, zc - 0.18, zc - 0.04)


def windscreen(m, x, r, zc, length=0.6):
    """Cockpit glazing as a sloping band over the nose."""
    m.box("glass", x - length, x, -0.55 * r, 0.55 * r, zc + 0.35 * r, zc + 0.72 * r)


def gear(m, x_nose, x_main, y_main, z_body, r=0.32, twin=False):
    m.wheel(x_nose, 0, r * 0.85, 0.2)
    m.box("air_dark", x_nose - 0.06, x_nose + 0.06, -0.06, 0.06, r, z_body)
    for s in (1, -1):
        ys = [s * y_main] if not twin else [s * (y_main - 0.18), s * (y_main + 0.18)]
        for y in ys:
            m.wheel(x_main, y, r, 0.26)
        m.box("air_dark", x_main - 0.08, x_main + 0.08, s * y_main - 0.06, s * y_main + 0.06, r, z_body)


def tail_gear(m, x_tail, z_body, r=0.2):
    m.wheel(x_tail, 0, r, 0.14)
    m.box("air_dark", x_tail - 0.05, x_tail + 0.05, -0.05, 0.05, r, z_body)


def jet_engine(m, x, y, z, length, r, pylon_to=None, mat="air_grey"):
    m.cylinder(mat, x - length / 2, x + length / 2, y, z, r, sides=10, caps="air_dark")
    m.cylinder("air_dark", x - length / 2 - 0.2, x - length / 2, y, z, r * 0.6, sides=8)  # exhaust
    if pylon_to is not None:
        z0, z1 = sorted((z, pylon_to))
        m.box(mat, x - length * 0.3, x + length * 0.2, y - 0.07, y + 0.07, z0, z1)


def prop(m, x, y, z, radius, blades_mat="air_dark", spinner="air_silver"):
    body(m, spinner, [(x - 0.1, z, 0.22, 0.22), (x + 0.15, z, 0.2, 0.2), (x + 0.35, z, 0.03, 0.03)], sides=8, yc=y)
    m.box(blades_mat, x + 0.02, x + 0.1, y - 0.07, y + 0.07, z - radius, z + radius)
    m.box(blades_mat, x + 0.02, x + 0.1, y - radius, y + radius, z - 0.07, z + 0.07)


def prop_nacelle(m, x0, x1, y, z, r, mat="air_silver", wing_z=None):
    body(m, mat, [(x1, z, r * 0.8, r * 0.8), (x1 - 0.3, z, r, r), (x0 + 0.5, z, r * 0.8, r * 0.8), (x0, z, 0.1, 0.1)], sides=10, yc=y)
    prop(m, x1, y, z, r * 2.6)


# Propeller planes -----------------------------------------------------------------------------------


def trimotor():
    """Sampson U52: a 1950s three-engined, corrugated-metal-looking airliner with fixed gear."""
    m = Model()
    L, r, zc = 10.0, 0.7, 1.35
    xn, xt = fuselage(m, L, r, zc, nose=1.0, tail=3.0, top="air_silver", belly="company", rz=0.85)
    for x in (2.6, 1.6, 0.6, -0.4, -1.4):
        m.box("air_grey", x - 0.04, x + 0.04, -r - 0.02, r + 0.02, zc - 0.5, zc + 0.5)  # ribs
    cabin_windows(m, -2.0, 2.4, r, zc + 0.1, h=0.3)
    windscreen(m, 3.6, r, zc + 0.1, 0.5)
    wing(m, "air_silver", 2.6, 2.3, 1.6, 1.1, 0, 6.2, zc - 0.55, zc - 0.2, thick=0.35)
    prop_nacelle(m, xn - 0.5, xn + 0.1, 0, zc, 0.4)
    for s in (1, -1):
        prop_nacelle(m, 1.6, 3.0, s * 2.2, zc - 0.45, 0.32)
    fin(m, "company", xt + 1.6, 1.6, xt + 0.6, 0.7, zc + 0.4, zc + 2.0)
    wing(m, "air_silver", xt + 1.6, 1.2, xt + 1.0, 0.6, 0, 2.0, zc + 0.45, zc + 0.5, thick=0.15)
    # Fixed gear with spats.
    for s in (1, -1):
        m.wheel(1.8, s * 1.6, 0.4, 0.26)
        m.box("air_dark", 1.7, 1.9, s * 1.6 - 0.06, s * 1.6 + 0.06, 0.4, zc - 0.5)
        m.quad("air_dark", (1.8, s * 1.6, zc - 0.6), (1.8, s * 0.3, zc - 0.5), (1.8, s * 0.3, zc - 0.4), (1.8, s * 1.6, zc - 0.5))
        m.quad("air_dark", (1.8, s * 1.6, zc - 0.5), (1.8, s * 0.3, zc - 0.4), (1.8, s * 0.3, zc - 0.5), (1.8, s * 1.6, zc - 0.6))
    tail_gear(m, xt + 0.8, zc + 0.3)
    m.save("air_trimotor.glb")


def turboprop_airliner():
    """Coleman Count: a four-engined turboprop airliner of the late 1950s, low wing, tricycle gear."""
    m = Model()
    L, r, zc = 12.5, 0.8, 1.55
    xn, xt = fuselage(m, L, r, zc, nose=1.8, tail=3.4)
    cabin_windows(m, -2.8, 3.6, r, zc)
    windscreen(m, xn - 0.9, r, zc)
    wing(m, "air_white", 1.8, 2.6, 0.6, 1.0, 0, 7.0, zc - 0.55, zc - 0.15, thick=0.35)
    for s in (1, -1):
        for y, z in ((2.0, zc - 0.5), (3.9, zc - 0.38)):
            prop_nacelle(m, 0.0, 2.6, s * y, z, 0.33, mat="air_white")
    fin(m, "company", xt + 2.2, 2.0, xt + 0.8, 1.0, zc + 0.3, zc + 2.6)
    wing(m, "air_white", xt + 1.8, 1.4, xt + 1.0, 0.7, 0, 2.6, zc + 0.35, zc + 0.45, thick=0.18)
    gear(m, xn - 1.6, 0.6, 2.0, zc - 0.5)
    m.save("air_turboprop_airliner.glb")


def commuter_prop():
    """Bakewell Cotswald LB-3: a small high-winged twin-propeller commuter plane."""
    m = Model()
    L, r, zc = 10.0, 0.72, 1.3
    xn, xt = fuselage(m, L, r, zc, nose=1.4, tail=3.0, belly="company_dark")
    m.box("company", -2.8, 3.6, -r - 0.05, r + 0.05, zc - 0.15, zc + 0.02)  # cheatline
    cabin_windows(m, -2.2, 2.8, r, zc + 0.1, h=0.25)
    windscreen(m, xn - 0.6, r, zc + 0.05, 0.6)
    wing(m, "air_white", 1.8, 1.7, 1.4, 1.1, 0, 6.2, zc + r - 0.05, zc + r + 0.05, thick=0.3)
    for s in (1, -1):
        prop_nacelle(m, 0.0, 2.4, s * 1.9, zc + 0.45, 0.32, mat="air_white")
        m.box("air_white", 0.0, 1.0, s * 1.9 - 0.18, s * 1.9 + 0.18, zc - 0.3, zc + 0.4)  # gear pod
    fin(m, "company", xt + 1.8, 1.6, xt + 0.7, 0.9, zc + 0.3, zc + 2.3)
    wing(m, "air_white", xt + 1.0, 0.8, xt + 0.6, 0.5, 0, 2.2, zc + 2.0, zc + 2.0, thick=0.14)  # T-tail
    gear(m, xn - 1.2, 0.4, 1.9, zc - 0.3, r=0.28)
    m.save("air_commuter_prop.glb")


# Jets -----------------------------------------------------------------------------------------------


def early_jet():
    """FFP Dart and its kin (1960s): a short jet with two engines at the tail and a T-tail."""
    m = Model()
    L, r, zc = 15.0, 0.85, 1.75
    xn, xt = fuselage(m, L, r, zc, nose=2.0, tail=3.6)
    cabin_windows(m, -3.6, 4.8, r, zc)
    windscreen(m, xn - 1.0, r, zc)
    wing(m, "air_white", 1.6, 3.0, -1.4, 1.1, 0, 7.0, zc - 0.6, zc - 0.25, thick=0.35)
    for s in (1, -1):
        jet_engine(m, -4.6, s * (r + 0.55), zc + 0.35, 2.4, 0.45)
        m.box("air_grey", -4.9, -4.1, s * (r - 0.1) - 0.05, s * (r + 0.2) + 0.05, zc + 0.25, zc + 0.45)
    fin(m, "company", xt + 2.8, 2.4, xt + 1.0, 1.4, zc + 0.3, zc + 3.0)
    wing(m, "air_white", xt + 1.5, 1.3, xt + 0.6, 0.7, 0, 2.8, zc + 2.95, zc + 3.0, thick=0.16)
    gear(m, xn - 1.8, -0.5, 1.6, zc - 0.6)
    m.save("air_early_jet.glb")


def twinjet():
    """Darwin 200-600 and the Airtaxi A2x/A3x: a twin-engined jet airliner with engines under the wings."""
    m = Model()
    L, r, zc = 16.0, 0.95, 1.85
    xn, xt = fuselage(m, L, r, zc, nose=2.1, tail=3.8)
    cabin_windows(m, -4.0, 5.2, r, zc)
    windscreen(m, xn - 1.0, r, zc)
    wing(m, "air_white", 2.2, 3.4, -1.6, 1.0, 0, 8.0, zc - 0.65, zc - 0.15, thick=0.38)
    for s in (1, -1):
        jet_engine(m, 0.9, s * 2.8, zc - 1.0, 2.4, 0.55, pylon_to=zc - 0.5)
        fin(m, "company", -1.4, 0.8, -1.7, 0.5, zc - 0.15, zc + 0.6, y=s * 8.0, thick=0.1)  # winglets
    fin(m, "company", xt + 3.0, 2.8, xt + 1.0, 1.4, zc + 0.4, zc + 3.6)
    wing(m, "air_white", xt + 2.2, 1.6, xt + 0.9, 0.8, 0, 3.4, zc + 0.5, zc + 0.75, thick=0.18)
    gear(m, xn - 2.0, 0.0, 1.8, zc - 0.65)
    m.save("air_twinjet.glb")


def trijet():
    """Bakewell Luckett LB-10 / LB-11, Guru Galaxy: a wide-bodied jet with a third engine in the tail."""
    m = Model()
    L, r, zc = 18.5, 1.2, 2.05
    xn, xt = fuselage(m, L, r, zc, nose=2.6, tail=4.2, tail_up=0.6)
    cabin_windows(m, -4.6, 6.2, r, zc + 0.1)
    windscreen(m, xn - 1.2, r, zc, 0.7)
    wing(m, "air_white", 2.6, 4.0, -2.0, 1.2, 0, 9.0, zc - 0.85, zc - 0.25, thick=0.42)
    for s in (1, -1):
        jet_engine(m, 1.0, s * 3.4, zc - 1.15, 2.6, 0.62, pylon_to=zc - 0.7)
    # Tail engine through the fin.
    jet_engine(m, xt + 2.0, 0, zc + 1.7, 2.6, 0.55, pylon_to=zc + 0.8)
    fin(m, "company", xt + 3.0, 2.0, xt + 1.4, 1.4, zc + 2.2, zc + 4.2)
    m.box("company", xt + 1.6, xt + 3.0, -0.12, 0.12, zc + 0.6, zc + 2.2)
    wing(m, "air_white", xt + 2.6, 1.8, xt + 1.2, 0.9, 0, 3.8, zc + 0.5, zc + 0.8, thick=0.2)
    gear(m, xn - 2.4, -0.2, 2.0, zc - 0.9, r=0.38, twin=True)
    m.save("air_trijet.glb")


def highwing_quadjet():
    """Bakewell Luckett LB-8, Yate YAe46: a high-winged jet with four small engines and a T-tail."""
    m = Model()
    L, r, zc = 14.5, 0.95, 1.45
    xn, xt = fuselage(m, L, r, zc, nose=1.8, tail=3.6)
    cabin_windows(m, -3.4, 4.4, r, zc)
    windscreen(m, xn - 0.9, r, zc)
    wing(m, "air_white", 1.8, 2.8, 0.6, 1.0, 0, 7.0, zc + r - 0.1, zc + r - 0.45, thick=0.38)
    for s in (1, -1):
        for y, x in ((2.1, 1.4), (3.7, 1.0)):
            jet_engine(m, x, s * y, zc + 0.25, 1.8, 0.4, pylon_to=zc + 0.8)
        m.box("air_white", -0.6, 0.8, s * (r - 0.2) - 0.25, s * (r - 0.2) + 0.25, 0.5, zc - 0.2)  # gear blister
    fin(m, "company", xt + 2.8, 2.4, xt + 1.0, 1.4, zc + 0.3, zc + 3.0)
    wing(m, "air_white", xt + 1.6, 1.4, xt + 0.6, 0.7, 0, 3.0, zc + 2.95, zc + 3.0, thick=0.16)
    gear(m, xn - 1.6, 0.0, r - 0.2, 0.5, r=0.3)
    m.save("air_highwing_quadjet.glb")


def jumbo():
    """Darwin 300: a jumbo jet with a hump over the cockpit and four engines."""
    m = Model()
    L, r, zc = 20.0, 1.35, 2.25
    xn, xt = fuselage(m, L, r, zc, nose=2.8, tail=4.6, tail_up=0.6)
    # Upper deck hump.
    body(m, "air_white", [(xn - 1.0, zc + 0.3, 0.1, 0.1), (xn - 1.8, zc + 0.6, 0.8, 0.9), (xn - 3.4, zc + 0.6, 0.95, 1.1),
                          (xn - 6.8, zc + 0.3, 0.9, 1.05), (xn - 8.4, zc + 0.1, 0.4, 0.6)], sides=10)
    cabin_windows(m, -5.6, 6.6, r, zc + 0.1)
    m.box("glass", xn - 6.4, xn - 2.4, -0.98, 0.98, zc + 1.15, zc + 1.35)
    m.box("glass", xn - 1.9, xn - 1.5, -0.55, 0.55, zc + 1.0, zc + 1.4)
    wing(m, "air_white", 2.6, 4.6, -3.0, 1.2, 0, 9.8, zc - 0.95, zc - 0.25, thick=0.45)
    for s in (1, -1):
        for y, x in ((3.4, 0.8), (6.2, -0.9)):
            jet_engine(m, x, s * y, zc - 1.25 + y * 0.05, 2.4, 0.6, pylon_to=zc - 0.75 + y * 0.05)
    fin(m, "company", xt + 3.6, 3.0, xt + 1.4, 1.5, zc + 0.5, zc + 4.6)
    wing(m, "air_white", xt + 2.6, 2.0, xt + 1.0, 0.9, 0, 4.4, zc + 0.6, zc + 0.95, thick=0.22)
    gear(m, xn - 2.8, -0.4, 1.6, zc - 1.0, r=0.4, twin=True)
    gear(m, xn - 2.8, 0.8, 2.6, zc - 0.9, r=0.4, twin=True)
    m.save("air_jumbo.glb")


def supersonic():
    """Yate Haugan: a slender supersonic airliner with a delta wing and a drooped nose."""
    m = Model()
    L, r, zc = 19.0, 0.7, 2.0
    xn, xt = L / 2, -L / 2
    stations = [(xn, zc - 0.55, 0.04, 0.04), (xn - 1.0, zc - 0.25, 0.3, 0.3), (xn - 2.6, zc, 0.6, 0.6),
                (xn - 4.0, zc, r, r), (xt + 2.0, zc, r, r), (xt + 0.6, zc + 0.15, 0.45, 0.45), (xt, zc + 0.2, 0.15, 0.2)]
    body(m, belly_mats("air_white", "air_white"), stations)
    m.box("glass", xn - 3.2, xn - 2.4, -0.4, 0.4, zc + 0.25, zc + 0.55)
    cabin_windows(m, -5.0, 5.0, r, zc - 0.05, h=0.18)
    sides_only(m, "company", -6.0, 5.2, -r, r, zc - 0.25, zc - 0.12, front=False, back=False, out=0.01)
    # Ogival delta wing: two panels, the inner one long.
    wing(m, "air_white", 3.6, 11.0, -3.6, 4.0, 0, 2.4, zc - 0.5, zc - 0.5, thick=0.35)
    wing(m, "air_white", -3.6, 4.0, -6.6, 1.6, 2.4, 4.6, zc - 0.5, zc - 0.55, thick=0.2)
    for s in (1, -1):
        m.box("air_grey", -7.2, -3.6, s * 1.3 - 0.75, s * 1.3 + 0.75, zc - 1.05, zc - 0.5)  # engine boxes
        m.box("air_dark", -7.3, -7.2, s * 1.3 - 0.65, s * 1.3 + 0.65, zc - 0.95, zc - 0.6)
        m.box("air_dark", -3.6, -3.5, s * 1.3 - 0.65, s * 1.3 + 0.65, zc - 0.95, zc - 0.6)
    fin(m, "company", xt + 4.2, 3.4, xt + 1.0, 1.0, zc + 0.3, zc + 3.0)
    gear(m, xn - 4.0, -2.6, 1.3, zc - 1.0, r=0.36, twin=True)
    m.save("air_supersonic.glb")


# Future aircraft ------------------------------------------------------------------------------------


def future_commuter():
    """AirTaxi A34-1000, Yate Z-Shuttle, Kelling K1: small futuristic planes with canards, a pusher fan and twin fins."""
    m = Model()
    L, r, zc = 12.0, 0.8, 1.5
    xn, xt = fuselage(m, L, r, zc, nose=2.4, tail=2.2, tail_up=0.3, belly="company")
    cabin_windows(m, -2.4, 2.6, r, zc + 0.05, h=0.22)
    m.box("glass", xn - 2.6, xn - 1.4, -0.55, 0.55, zc + 0.3, zc + 0.75)
    wing(m, "air_white", 3.8, 1.0, 3.4, 0.5, 0, 2.2, zc + 0.1, zc + 0.3, thick=0.15)  # canard
    wing(m, "air_white", -0.8, 3.2, -3.4, 1.2, 0, 5.8, zc - 0.4, zc - 0.1, thick=0.32)
    for s in (1, -1):
        fin(m, "company", -3.5, 1.3, -4.2, 0.7, zc - 0.1, zc + 1.6, y=s * 5.6, thick=0.14)
    # Ducted pusher fan at the tail.
    m.cylinder("company", xt - 0.2, xt + 1.0, 0, zc + 0.5, 0.75, sides=14, caps="air_dark")
    m.box("air_white", xt + 0.4, xt + 1.4, -0.12, 0.12, zc + 0.1, zc + 0.5)
    gear(m, xn - 2.0, -1.0, 1.4, zc - 0.5, r=0.28)
    m.save("air_future_commuter.glb")


def future_airliner():
    """Kelling K6 / K7, Darwin 700: futuristic airliners with raked wingtips and engines on top of the tail."""
    m = Model()
    L, r, zc = 18.0, 1.1, 1.95
    xn, xt = fuselage(m, L, r, zc, nose=3.2, tail=4.2, tail_up=0.4)
    cabin_windows(m, -4.4, 5.0, r, zc + 0.05, h=0.22)
    m.box("glass", xn - 2.4, xn - 1.6, -0.6, 0.6, zc + 0.4, zc + 0.8)
    wing(m, "air_white", 2.4, 4.6, -2.6, 1.4, 0, 8.0, zc - 0.7, zc - 0.05, thick=0.4)
    wing(m, "company", -2.6, 1.4, -4.2, 0.4, 8.0, 9.2, zc - 0.05, zc + 0.3, thick=0.15)  # raked tips
    for s in (1, -1):
        jet_engine(m, xt + 3.0, s * 1.0, zc + 1.4, 2.8, 0.55, pylon_to=zc + 0.6, mat="air_white")
        # V-tail: panels leaning out at 45 degrees, thick across their own plane.
        rings = []
        for x, c, y, z, t in ((xt + 2.4, 2.0, 0.2, zc + 0.6, 0.24), (xt + 0.6, 1.0, 2.4, zc + 2.8, 0.14)):
            ny, nz = -s * 0.707 * t / 2, 0.707 * t / 2
            rings.append([(x, s * y, z), (x - 0.3 * c, s * y + ny, z + nz), (x - c, s * y, z), (x - 0.3 * c, s * y - ny, z - nz)])
        loft(m, rings, "company")
    gear(m, xn - 2.6, -0.2, 1.8, zc - 0.75, r=0.36, twin=True)
    m.save("air_future_airliner.glb")


def future_supersonic():
    """FFP Hyperdart 2 and Dinger 1000: a future supersonic jet with an arrow wing, canards and twin fins."""
    m = Model()
    L, r, zc = 19.0, 0.8, 1.9
    xn, xt = L / 2, -L / 2
    stations = [(xn, zc - 0.1, 0.03, 0.03), (xn - 2.0, zc, 0.45, 0.4), (xn - 4.5, zc, r, 0.75),
                (xt + 3.0, zc, r, 0.75), (xt + 0.8, zc + 0.1, 0.55, 0.5), (xt, zc + 0.1, 0.3, 0.3)]
    body(m, belly_mats("air_white", "company"), stations)
    m.box("glass", xn - 3.4, xn - 2.2, -0.35, 0.35, zc + 0.3, zc + 0.62)
    cabin_windows(m, -4.0, 4.5, r, zc - 0.05, h=0.16)
    wing(m, "air_white", 6.4, 3.0, 5.4, 1.2, 0, 2.2, zc - 0.1, zc - 0.1, thick=0.16)  # canards
    wing(m, "air_white", 2.0, 9.6, -6.6, 2.0, 0, 5.6, zc - 0.45, zc - 0.3, thick=0.4)
    for s in (1, -1):
        m.cylinder("air_grey", -8.4, -4.6, s * 1.5, zc - 0.85, 0.5, sides=10, caps="air_dark")
        fin(m, "company", xt + 4.4, 2.6, xt + 2.2, 1.0, zc + 0.3, zc + 2.6, y=s * 1.2, thick=0.16)
    gear(m, xn - 5.0, -3.0, 1.6, zc - 0.9, r=0.34, twin=True)
    m.save("air_future_supersonic.glb")


def blended_wing():
    """Dinger 200: a huge future airliner whose body flows into its wings."""
    m = Model()
    zc = 2.2
    rings = []
    for x, hw, h in ((7.0, 0.3, 0.2), (5.8, 1.8, 0.9), (3.0, 3.6, 1.2), (-0.5, 4.4, 1.1), (-3.0, 4.6, 0.9)):
        rings.append([(x, -hw, zc), (x, -hw * 0.6, zc - h * 0.7), (x, hw * 0.6, zc - h * 0.7), (x, hw, zc),
                      (x, hw * 0.6, zc + h), (x, -hw * 0.6, zc + h)])
    loft(m, rings, ["air_white", "company", "air_white", "air_white", "air_white", "air_white"])
    m.box("glass", 5.4, 6.2, -1.0, 1.0, zc + 0.55, zc + 0.85)
    wing(m, "air_white", 0.4, 3.8, -4.6, 1.4, 4.4, 10.0, zc, zc + 0.6, thick=0.5)
    for s in (1, -1):
        fin(m, "company", -4.0, 1.4, -5.0, 0.8, zc + 0.5, zc + 2.2, y=s * 9.8, thick=0.12)
        fin(m, "company", -1.4, 2.0, -2.9, 1.0, zc + 0.7, zc + 2.8, y=s * 2.4, thick=0.18)
    for y in (-1.6, 0, 1.6):
        jet_engine(m, -2.0, y, zc + 1.3, 2.4, 0.5, pylon_to=zc + 0.8)
    gear(m, 4.6, -0.6, 2.4, zc - 0.8, r=0.4, twin=True)
    m.save("air_blended_wing.glb")


# Helicopters ----------------------------------------------------------------------------------------


def helicopter():
    """Tricario Helicopter: a small helicopter with a glass nose, tail boom and skids (main rotor left out)."""
    m = Model()
    zc = 1.5
    body(m, belly_mats("company", "company_dark"), [(3.0, zc - 0.2, 0.1, 0.1), (2.5, zc, 0.8, 0.8), (1.0, zc + 0.1, 1.05, 1.05),
                                                     (-0.8, zc + 0.1, 0.95, 0.95), (-1.6, zc + 0.3, 0.45, 0.5)])
    body(m, "glass", [(3.05, zc - 0.1, 0.05, 0.05), (2.6, zc + 0.1, 0.75, 0.7), (1.6, zc + 0.35, 0.8, 0.75), (1.1, zc + 0.4, 0.05, 0.05)], sides=10)
    body(m, "company", [(-1.4, zc + 0.35, 0.35, 0.35), (-5.6, zc + 0.6, 0.14, 0.16), (-5.9, zc + 0.6, 0.05, 0.05)], sides=8)
    fin(m, "company", -5.1, 0.8, -5.7, 0.5, zc + 0.5, zc + 1.6, thick=0.12)
    ycylinder(m, "air_dark", -5.5, -0.22, -0.16, zc + 1.0, 0.55, sides=12)  # tail rotor
    m.box("air_grey", -1.2, 0.8, -0.5, 0.5, zc + 0.9, zc + 1.4)  # engine
    zcylinder(m, "air_dark", 0.0, 0, zc + 1.4, zc + 1.9, 0.15, sides=8)  # rotor mast
    for s in (1, -1):
        m.box("air_dark", -1.6, 2.2, s * 0.95 - 0.07, s * 0.95 + 0.07, 0.0, 0.12)
        m.box("air_dark", 2.2, 2.5, s * 0.95 - 0.07, s * 0.95 + 0.07, 0.05, 0.3)
        for x in (-0.8, 1.2):
            m.box("air_dark", x - 0.05, x + 0.05, s * 0.95 - 0.05, s * 0.95 + 0.05, 0.1, zc - 0.7)
            m.box("air_dark", x - 0.05, x + 0.05, min(s * 0.95, s * 0.5), max(s * 0.95, s * 0.5), zc - 0.75, zc - 0.65)
    m.save("air_helicopter.glb")


def helicopter_large():
    """Guru X2 Helicopter: a big twin-engined helicopter with wheels, side windows and a large tail."""
    m = Model()
    zc = 1.8
    body(m, belly_mats("company", "company_dark"), [(4.6, zc - 0.3, 0.1, 0.1), (4.0, zc - 0.05, 0.85, 0.8), (2.6, zc + 0.1, 1.2, 1.2),
                                                     (-1.8, zc + 0.1, 1.2, 1.2), (-2.8, zc + 0.4, 0.6, 0.7)])
    m.box("glass", 3.2, 4.1, -0.7, 0.7, zc + 0.3, zc + 0.75)
    cabin_windows(m, -1.4, 2.4, 1.2, zc - 0.05, h=0.35)
    body(m, "company", [(-2.6, zc + 0.5, 0.45, 0.5), (-7.4, zc + 0.9, 0.18, 0.2), (-7.7, zc + 0.9, 0.05, 0.05)], sides=8)
    fin(m, "company", -6.8, 1.2, -7.6, 0.8, zc + 0.8, zc + 2.4, thick=0.14)
    wing(m, "company", -6.2, 0.7, -6.4, 0.5, 0, 1.4, zc + 0.85, zc + 0.85, thick=0.1)
    ycylinder(m, "air_dark", -7.3, -0.26, -0.2, zc + 1.6, 0.75, sides=12)
    for s in (1, -1):
        m.cylinder("air_white", -1.4, 1.4, s * 0.55, zc + 1.45, 0.38, sides=10, caps="air_dark")
    zcylinder(m, "air_dark", 0.2, 0, zc + 1.6, zc + 2.2, 0.18, sides=8)
    # Wheels on sponsons.
    m.wheel(3.0, 0, 0.3, 0.2)
    m.box("air_dark", 2.95, 3.05, -0.05, 0.05, 0.3, zc - 0.9)
    for s in (1, -1):
        m.box("company_dark", -1.0, 0.8, s * 1.15 - 0.3, s * 1.15 + 0.3, zc - 1.0, zc - 0.5)
        m.wheel(-0.1, s * 1.3, 0.36, 0.24)
        m.box("air_dark", -0.15, -0.05, s * 1.3 - 0.05, s * 1.3 + 0.05, 0.36, zc - 0.9)
    m.save("air_helicopter_large.glb")


# Toyland --------------------------------------------------------------------------------------------


def toy_biplane():
    """Ploddyphut 100 / 500: a chubby toy biplane with a big propeller."""
    m = Model()
    zc = 1.5
    body(m, belly_mats("air_toy_red", "air_toy_yellow"), [(4.2, zc, 0.6, 0.6), (3.6, zc, 0.95, 0.95), (1.0, zc + 0.1, 1.0, 1.05),
                                                           (-3.2, zc + 0.5, 0.35, 0.4), (-3.6, zc + 0.6, 0.1, 0.1)])
    prop(m, 4.2, 0, zc, 1.4, blades_mat="air_toy_green", spinner="air_toy_yellow")
    m.box("glass", 1.2, 1.9, -0.55, 0.55, zc + 0.9, zc + 1.3)
    m.box("air_toy_yellow", 0.0, 1.2, -0.6, 0.6, zc + 0.95, zc + 1.0)  # cockpit rim
    for z, half in ((zc - 0.5, 4.6), (zc + 1.7, 5.0)):
        rings = [[(x, y, z) for x, y in ((3.0, -half), (1.0, -half), (1.0, half), (3.0, half))],
                 [(x, y, z + 0.28) for x, y in ((3.0, -half), (1.0, -half), (1.0, half), (3.0, half))]]
        loft(m, rings, "air_toy_yellow")
        for s in (1, -1):
            zcylinder(m, "air_toy_red", 2.0, s * half, z, z + 0.29, 1.0, rx=1.0, sides=12)  # round tips
    for s in (1, -1):
        for x in (1.4, 2.6):
            m.box("air_toy_green", x - 0.08, x + 0.08, s * 3.0 - 0.08, s * 3.0 + 0.08, zc - 0.22, zc + 1.7)
        for x in (1.6,):
            m.box("air_toy_green", x - 0.08, x + 0.08, s * 0.7 - 0.08, s * 0.7 + 0.08, zc + 0.8, zc + 1.7)
    fin(m, "company", -2.0, 1.6, -3.3, 1.0, zc + 0.6, zc + 2.0, thick=0.25)
    wing(m, "company", -2.2, 1.3, -2.8, 0.8, 0, 2.0, zc + 0.5, zc + 0.5, thick=0.2)
    for s in (1, -1):
        m.wheel(2.3, s * 1.2, 0.5, 0.35)
        m.box("air_toy_green", 2.2, 2.4, min(s * 0.4, s * 1.2), max(s * 0.4, s * 1.2), 0.45, 0.6)
        m.box("air_toy_green", 2.2, 2.4, s * 0.45 - 0.08, s * 0.45 + 0.08, 0.5, zc - 0.6)
    tail_gear(m, -3.0, zc + 0.4, r=0.3)
    m.save("air_toy_biplane.glb")


def toy_jet():
    """Flashbang X1: a stubby cartoon jet with a round nose and a bubble canopy."""
    m = Model()
    zc = 1.5
    body(m, belly_mats("air_toy_orange", "air_toy_purple"), [(5.0, zc - 0.1, 0.4, 0.4), (4.4, zc, 1.0, 1.0), (2.0, zc + 0.1, 1.3, 1.3),
                                                              (-3.0, zc + 0.2, 1.0, 1.0), (-4.6, zc + 0.4, 0.6, 0.6)])
    body(m, "glass", [(3.8, zc + 0.9, 0.05, 0.05), (3.2, zc + 1.0, 0.6, 0.55), (1.6, zc + 1.0, 0.6, 0.5), (1.0, zc + 1.0, 0.05, 0.05)], sides=10)
    wing(m, "air_toy_yellow", 1.6, 3.4, -1.6, 1.6, 0, 6.0, zc - 0.4, zc - 0.1, thick=0.45)
    for s in (1, -1):
        zcylinder(m, "company", -0.7, s * 6.0, zc - 0.5, zc + 0.6, 0.45, rx=1.1, sides=10)  # tip pods
        m.cylinder("air_toy_purple", -3.2, -1.0, s * 1.5, zc + 0.6, 0.55, sides=10, caps="air_dark")
    m.cylinder("air_dark", -4.9, -4.6, 0, zc + 0.4, 0.45, sides=10)
    fin(m, "company", -2.6, 2.0, -4.2, 1.2, zc + 0.9, zc + 2.8, thick=0.3)
    wing(m, "air_toy_yellow", -3.0, 1.4, -3.8, 0.9, 0, 2.6, zc + 0.6, zc + 0.8, thick=0.2)
    gear(m, 3.4, -0.4, 1.6, zc - 0.9, r=0.42)
    m.save("air_toy_jet.glb")


def toy_jumbo():
    """Juggerplane M1: a big round toy airliner with four fat engines."""
    m = Model()
    zc = 2.2
    body(m, belly_mats("air_toy_green", "air_toy_yellow", 14), [(8.4, zc - 0.2, 0.4, 0.4), (7.6, zc, 1.3, 1.3), (5.0, zc + 0.1, 1.7, 1.75),
                                                             (-4.0, zc + 0.1, 1.6, 1.65), (-7.6, zc + 0.8, 0.6, 0.6), (-8.2, zc + 0.9, 0.2, 0.2)], sides=14)
    m.box("glass", 6.6, 7.6, -0.9, 0.9, zc + 0.8, zc + 1.3)
    for x in range(-4, 6, 2):
        for s in (1, -1):
            ycylinder(m, "glass", float(x), s * 1.66 - 0.05, s * 1.66 + 0.05, zc + 0.4, 0.35, sides=8)
    wing(m, "air_toy_yellow", 2.6, 4.6, -1.8, 2.0, 0, 9.0, zc - 1.0, zc - 0.4, thick=0.55)
    for s in (1, -1):
        for y, x in ((3.4, 1.0), (6.4, -0.5)):
            jet_engine(m, x, s * y, zc - 1.5 + y * 0.05, 2.4, 0.75, pylon_to=zc - 0.8, mat="air_toy_pink")
    fin(m, "company", -5.4, 3.2, -7.8, 1.8, zc + 0.8, zc + 4.4, thick=0.35)
    wing(m, "air_toy_yellow", -5.8, 2.0, -7.4, 1.2, 0, 4.0, zc + 0.9, zc + 1.1, thick=0.25)
    gear(m, 6.0, 0.0, 2.2, zc - 1.2, r=0.5, twin=True)
    m.save("air_toy_jumbo.glb")


def toy_rocket():
    """Flashbang Wizzer: a toy supersonic rocket-plane with a pointed nose and big fins."""
    m = Model()
    zc = 1.8
    body(m, belly_mats("air_toy_red", "air_toy_yellow", 14), [(8.5, zc, 0.03, 0.03), (6.0, zc, 0.7, 0.7), (3.0, zc, 1.0, 1.0),
                                                           (-6.0, zc, 1.0, 1.0), (-7.0, zc, 0.8, 0.8)], sides=14)
    m.cylinder("air_dark", -7.4, -7.0, 0, zc, 0.6, sides=12)
    body(m, "glass", [(5.4, zc + 0.6, 0.05, 0.05), (4.6, zc + 0.75, 0.45, 0.4), (3.0, zc + 0.75, 0.45, 0.4), (2.4, zc + 0.7, 0.05, 0.05)], sides=10)
    wing(m, "air_toy_yellow", 1.0, 6.0, -5.6, 1.8, 0, 5.0, zc - 0.3, zc - 0.5, thick=0.35)
    for s in (1, -1):
        fin(m, "company", -4.0, 2.4, -6.0, 1.2, zc - 0.4, zc + 1.4, y=s * 4.8, thick=0.2)  # tip fins
    fin(m, "company", -3.4, 3.0, -6.4, 1.4, zc + 0.6, zc + 3.0, thick=0.3)
    for k in range(3):
        m.box("air_toy_purple", 0.2 - k * 1.6, 0.8 - k * 1.6, -1.02, 1.02, zc - 0.25, zc + 0.25)  # stripes
    gear(m, 4.6, -1.8, 1.8, zc - 0.8, r=0.4)
    m.save("air_toy_rocket.glb")


def toy_helicopter():
    """Powernaut Helicopter: a round toy helicopter with a bubble cabin (main rotor left out)."""
    m = Model()
    zc = 1.7
    body(m, belly_mats("air_toy_yellow", "air_toy_orange", 14), [(2.4, zc, 0.3, 0.3), (2.0, zc, 1.1, 1.1), (0.6, zc + 0.05, 1.35, 1.35),
                                                              (-1.0, zc + 0.1, 1.1, 1.1), (-1.6, zc + 0.3, 0.4, 0.4)], sides=14)
    body(m, "glass", [(2.5, zc + 0.1, 0.05, 0.05), (2.1, zc + 0.3, 0.85, 0.8), (1.1, zc + 0.5, 0.9, 0.85), (0.5, zc + 0.6, 0.05, 0.05)], sides=12)
    body(m, "air_toy_orange", [(-1.4, zc + 0.3, 0.4, 0.4), (-5.0, zc + 0.6, 0.25, 0.25), (-5.3, zc + 0.6, 0.1, 0.1)], sides=10)
    fin(m, "company", -4.4, 1.0, -5.2, 0.6, zc + 0.6, zc + 1.8, thick=0.2)
    ycylinder(m, "air_toy_green", -5.0, -0.32, -0.24, zc + 1.2, 0.6, sides=12)
    zcylinder(m, "company", -0.2, 0, zc + 1.1, zc + 1.6, 0.5, sides=12)
    zcylinder(m, "air_toy_red", -0.2, 0, zc + 1.6, zc + 2.0, 0.2, sides=8)
    for s in (1, -1):
        m.cylinder("air_toy_red", -1.6, 2.2, s * 1.1, 0.2, 0.2, sides=8)
        for x in (-0.8, 1.2):
            m.box("air_toy_red", x - 0.08, x + 0.08, s * 1.1 - 0.08, s * 1.1 + 0.08, 0.3, zc - 0.8)
    m.save("air_toy_helicopter.glb")


def build():
    for f in (trimotor, turboprop_airliner, commuter_prop, early_jet, twinjet, trijet, highwing_quadjet, jumbo,
              supersonic, future_commuter, future_airliner, future_supersonic, blended_wing, helicopter,
              helicopter_large, toy_biplane, toy_jet, toy_jumbo, toy_rocket, toy_helicopter):
        f()
    entries = [
        ([0], "air_trimotor.glb", None),
        ([1], "air_turboprop_airliner.glb", None),
        ([4], "air_commuter_prop.glb", None),
        ([2, 6, 7, 10, 11, 23], "air_early_jet.glb", None),
        ([12, 14, 15, 16, 18, 19, 20, 21], "air_twinjet.glb", None),
        ([8, 9, 17], "air_trijet.glb", None),
        ([5, 22], "air_highwing_quadjet.glb", None),
        ([13], "air_jumbo.glb", None),
        ([3], "air_supersonic.glb", None),
        ([24, 25, 26], "air_future_commuter.glb", None),
        ([27, 28, 29], "air_future_airliner.glb", None),
        ([32], "air_future_supersonic.glb", None),
        ([30], "air_future_supersonic.glb", 0.85),
        ([31], "air_blended_wing.glb", None),
        ([38], "air_helicopter.glb", None),
        ([39], "air_helicopter_large.glb", None),
        ([33], "air_toy_biplane.glb", None),
        ([34], "air_toy_biplane.glb", 1.2),
        ([35], "air_toy_jet.glb", None),
        ([36], "air_toy_jumbo.glb", None),
        ([37], "air_toy_rocket.glb", None),
        ([40], "air_toy_helicopter.glb", None),
    ]
    vehicles = []
    for ids, model, scale in entries:
        e = {"type": "aircraft", "ids": ids, "model": model}
        if scale:
            e["scale"] = scale
        vehicles.append(e)
    return {"vehicles": vehicles, "buildings": []}
