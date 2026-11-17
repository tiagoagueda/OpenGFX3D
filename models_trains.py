"""Rail vehicles not covered by models_base: the multi-headed diesels and high-speed electrics of the
normal railway, and all engines and wagons of the monorail and the maglev (all climates, toyland too).

Monorail vehicles ride on a single beam: their running gear is a narrow housing in the middle that
wraps the beam. Maglev vehicles float over their guideway: no wheels, skirts down the sides.
Monorail and maglev vehicles have a central coupling instead of side buffers.

Bodies are lofts of a rounded cross-section; windows, bands and grilles are painted on the body's
own faces (not stuck on as boxes), so that they show cleanly from every side.
"""

import math

from gfx3d import MATERIALS, Model
from models_base import bogie, buffers, rail_wheels

# Extra colours of this group. Loads start with "load" so that the game treats them as cargo.
MATERIALS.update({
    "trains_yellow": (0.95, 0.80, 0.15),
    "trains_red": (0.80, 0.18, 0.15),
    "trains_white": (0.93, 0.93, 0.92),
    "trains_silver": (0.72, 0.74, 0.78),
    "trains_skirt": (0.26, 0.27, 0.30),
    "trains_toy_pink": (0.95, 0.55, 0.75),
    "trains_toy_green": (0.40, 0.80, 0.35),
    "trains_toy_purple": (0.60, 0.40, 0.85),
    "trains_toy_orange": (0.98, 0.60, 0.20),
    "load_trains_grain": (0.86, 0.72, 0.38),
    "load_trains_copper": (0.62, 0.40, 0.28),
    "load_trains_sugar": (0.96, 0.95, 0.92),
    "load_trains_candyfloss": (0.98, 0.70, 0.85),
    "load_trains_toffee": (0.55, 0.32, 0.14),
    "load_trains_logs": (0.55, 0.40, 0.25),
    "load_trains_steel": (0.50, 0.53, 0.58),
    "load_trains_fruit": (0.90, 0.50, 0.12),
    "load_trains_batteries": (0.25, 0.25, 0.28),
    "load_trains_fizzy": (0.30, 0.75, 0.45),
})


# ---------------------------------------------------------------------------------------------------
# Shapes


def _flip_out(a, b, c, centre):
    """Return the corners so that the triangle faces away from centre."""
    u = [b[i] - a[i] for i in range(3)]
    v = [c[i] - a[i] for i in range(3)]
    n = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]]
    mid = [(a[i] + b[i] + c[i]) / 3 - centre[i] for i in range(3)]
    if sum(n[i] * mid[i] for i in range(3)) < 0:
        return a, c, b
    return a, b, c


def _tri(m, mat, a, b, c, centre):
    if a == b or b == c or a == c:
        return
    m.triangle(mat, *_flip_out(a, b, c, centre))


def profile(w, zb, zt, r, cuts=(), k=3):
    """A cross-section (y, z): flat bottom, straight sides, rounded top corners of radius r.
    cuts: extra points up the sides, as fractions (0-1) of the straight part of the side."""
    r = max(0.01, min(r, w * 0.99, (zt - zb) * 0.99))
    side = zt - r - zb
    pts = [(-w, zb), (w, zb)]
    for t in cuts:
        pts.append((w, zb + side * t))
    for i in range(k + 1):
        a = math.pi / 2 * i / k
        pts.append((w - r + r * math.cos(a), zt - r + r * math.sin(a)))
    for i in range(k + 1):
        a = math.pi / 2 + math.pi / 2 * i / k
        pts.append((-w + r + r * math.cos(a), zt - r + r * math.sin(a)))
    for t in reversed(cuts):
        pts.append((-w, zb + side * t))
    return pts


def loft(m, sections, mat, cap_front=None, cap_back=None):
    """Join cross-sections (x, points) along x. mat is a material or a function (segment, strip, mid) -> material,
    mid being the middle of the face. The ends are closed with flat caps (default: the material of strip 0)."""
    n = len(sections[0][1])
    pts = [[(x, y, z) for (y, z) in p] for x, p in sections]
    allp = [q for s in pts for q in s]
    centre = [sum(q[i] for q in allp) / len(allp) for i in range(3)]
    get = mat if callable(mat) else (lambda j, i, mid: mat)
    for j in range(len(pts) - 1):
        a, b = pts[j], pts[j + 1]
        for i in range(n):
            i2 = (i + 1) % n
            mid = [(a[i][q] + b[i][q] + a[i2][q] + b[i2][q]) / 4 for q in range(3)]
            mm = get(j, i, mid)
            _tri(m, mm, a[i], b[i], b[i2], centre)
            _tri(m, mm, a[i], b[i2], a[i2], centre)
    for s, cap, outward in ((pts[0], cap_back, -1), (pts[-1], cap_front, 1)):
        c = tuple(sum(q[i] for q in s) / n for i in range(3))
        cm = cap or get(0, 0, c)
        for i in range(n):
            t = (s[i], s[(i + 1) % n], c)
            u = [t[1][q] - t[0][q] for q in range(3)]
            v = [t[2][q] - t[0][q] for q in range(3)]
            if (u[1] * v[2] - u[2] * v[1]) * outward < 0:
                t = (t[0], t[2], t[1])
            if t[0] != t[1]:
                m.triangle(cm, *t)


def body(m, x0, x1, base, w=1.45, zb=1.1, zt=3.2, r=0.5, front=(), back=(), nose=None, glass=(), nose_segs=(),
         cap_front=None, cap_back=None, paint=()):
    """A body from x0 to x1, with noses: front/back are lists of (length, w, zb, zt, r) sections beyond the ends.
    Nose segments count outward from the body from 0; glass names those whose upper part is the windscreen,
    nose_segs those in the material nose. paint: rectangles (material, xa, xb, za, zb) on both sides of
    the straight part; later ones win."""
    k = 3
    side = zt - r - zb
    cuts = sorted({round((z - zb) / side, 4) for p in paint for z in p[3:5] if zb + 0.01 < z < zt - r - 0.01})
    xs = {x0, x1}
    steps = max(1, int(round((x1 - x0) / 1.0)))
    xs.update(x0 + (x1 - x0) * i / steps for i in range(steps + 1))
    xs.update(x for p in paint for x in p[1:3] if x0 < x < x1)
    xs = sorted(xs)
    secs = []
    for d, bw, bzb, bzt, br in reversed(back):
        secs.append((x0 - d, profile(bw, bzb, bzt, br, cuts)))
    for x in xs:
        secs.append((x, profile(w, zb, zt, r, cuts)))
    for d, fw, fzb, fzt, fr in front:
        secs.append((x1 + d, profile(fw, fzb, fzt, fr, cuts)))
    nb, nbody = len(back), len(xs) - 1
    ns = len(cuts) + 1
    upper = range(ns + 1, ns + 2 * k + 2)
    sides_ = set(range(1, ns + 1)) | set(range(ns + 2 * k + 2, 2 * ns + 2 * k + 2))

    def material(j, i, mid):
        if nb <= j < nb + nbody:
            if i in sides_:
                for mat, xa, xb, za, zb2 in reversed(paint):
                    if xa <= mid[0] <= xb and za <= mid[2] <= zb2:
                        return mat
            return base
        seg = nb - 1 - j if j < nb else j - nb - nbody
        if seg in glass and i in upper:
            return "glass"
        if nose and seg in nose_segs:
            return nose
        return base
    loft(m, secs, material, cap_front, cap_back)


def windows(x0, x1, z0, z1, count, gap=0.3, mat="glass"):
    step = (x1 - x0) / count
    return [(mat, x0 + i * step + gap / 2, x0 + (i + 1) * step - gap / 2, z0, z1) for i in range(count)]


def pantograph(m, x=0.0, z=3.5):
    m.box("dark", x - 0.6, x + 0.6, -0.6, 0.6, z - 0.05, z + 0.15)
    m.quad("metal", (x - 0.5, -0.5, z + 0.15), (x + 0.5, -0.5, z + 0.15), (x + 0.1, -0.5, z + 1.05), (x - 0.1, -0.5, z + 1.05))
    m.quad("metal", (x + 0.5, 0.5, z + 0.15), (x - 0.5, 0.5, z + 0.15), (x - 0.1, 0.5, z + 1.05), (x + 0.1, 0.5, z + 1.05))
    m.box("metal", x - 0.12, x + 0.12, -0.9, 0.9, z + 1.0, z + 1.15)


def headlights(m, x, z=1.5, y=0.75, size=0.2):
    for yy in (-y, y):
        m.box("light", x - 0.1, x + 0.06, yy - size, yy + size, z - size * 0.7, z + size * 0.7)


# ---------------------------------------------------------------------------------------------------
# Running gear


def coupler(m, x0, x1, z=1.0):
    """The central coupling of monorail and maglev vehicles, in place of side buffers."""
    for x, d in ((x0, -0.3), (x1, 0.3)):
        m.box("dark", min(x - d, x + d), max(x - d, x + d), -0.35, 0.35, z - 0.2, z + 0.2)
        m.box("metal", min(x + d, x + 1.3 * d), max(x + d, x + 1.3 * d), -0.45, 0.45, z - 0.25, z + 0.25)


def mono_gear(m, x0, x1, xs=None):
    """Running gear on the single beam: housings over the beam with skirts that wrap down its sides."""
    xs = xs or ((x0 + 1.5), (x1 - 1.5))
    m.box("dark", x0 + 0.2, x1 - 0.2, -0.95, 0.95, 0.9, 1.15)  # underframe
    for x in xs:
        m.box("dark", x - 1.0, x + 1.0, -0.75, 0.75, 0.7, 0.9)
        for y0, y1 in ((-0.75, -0.5), (0.5, 0.75)):
            m.box("trains_skirt", x - 0.9, x + 0.9, y0, y1, 0.05, 0.7)
    coupler(m, x0, x1)


def maglev_gear(m, x0, x1, z=1.1):
    """Skirts down both sides that wrap the guideway, a dark underside, a glowing line; no wheels."""
    m.box("dark", x0 + 0.3, x1 - 0.3, -1.0, 1.0, z - 0.25, z)
    for y0, y1 in ((-1.4, -0.95), (0.95, 1.4)):
        m.box("trains_skirt", x0 + 0.3, x1 - 0.3, y0, y1, 0.3, z)
    for y0, y1 in ((-1.43, -1.4), (1.4, 1.43)):
        m.box("light", x0 + 0.6, x1 - 0.6, y0, y1, 0.42, 0.52)
    coupler(m, x0, x1)


def gear(m, kind, x0, x1):
    if kind == "mono":
        mono_gear(m, x0, x1)
    else:
        maglev_gear(m, x0, x1)


# ---------------------------------------------------------------------------------------------------
# Normal railway: multi-headed diesels and high-speed electrics (the rear head is the same model reversed)


def turner_turbo():
    """A streamlined diesel power car with a rounded nose and a few seats behind the engine room."""
    m = Model()
    x0, x1 = -3.8, 2.4
    front = [(0.8, 1.42, 1.1, 3.0, 0.8), (1.4, 1.25, 1.1, 2.3, 0.7)]
    paint = [("company_dark", x0, x1, 1.1, 1.6), ("trains_white", x0, x1, 2.75, 2.85)]
    paint += windows(-1.0, 2.2, 2.1, 2.65, 3)
    paint += windows(-3.6, -1.4, 1.75, 2.5, 4, gap=0.25, mat="dark")  # grilles
    body(m, x0, x1, "company", zt=3.3, r=0.55, front=front, glass=(0,), paint=paint)
    m.box("dark", x0 + 0.2, 3.6, -1.35, 1.35, 0.85, 1.1)
    m.box("dark", -3.0, -1.6, -0.5, 0.5, 3.25, 3.45)  # exhaust housing
    headlights(m, 3.75, z=1.55, y=0.7)
    bogie(m, -2.4)
    bogie(m, 2.2)
    buffers(m, x0, 3.8)
    m.save("trains_turner_turbo.glb")


def hst_power_car():
    """A high-speed diesel power car with a wedge nose and a yellow front."""
    m = Model()
    x0, x1 = -3.8, 2.0
    front = [(1.1, 1.4, 1.1, 2.75, 0.6), (1.85, 1.15, 1.1, 1.75, 0.5)]
    paint = [("company_dark", x0, x1, 1.6, 2.0), ("glass", -3.4, -2.6, 2.3, 2.75)]
    paint += windows(-2.2, 1.6, 2.25, 2.85, 5, gap=0.25, mat="dark")  # grilles
    body(m, x0, x1, "company", zt=3.25, r=0.45, front=front, glass=(0,), nose="trains_yellow", nose_segs=(1,),
         cap_front="trains_yellow", paint=paint)
    m.box("dark", x0 + 0.2, 3.6, -1.35, 1.35, 0.85, 1.1)
    m.box("dark", -0.8, 0.6, -0.5, 0.5, 3.2, 3.4)
    headlights(m, 3.82, z=1.35, y=0.6)
    bogie(m, -2.4)
    bogie(m, 1.9)
    buffers(m, x0, 3.85, z=1.0)
    m.save("trains_hst_power_car.glb")


def high_speed_electric(filename, nose_start, nose_colour, tip_z=1.7):
    """A TGV-like power car: a long tapering nose, a pantograph, the company colour as a band."""
    m = Model()
    x0, x1 = -3.8, nose_start
    L = 3.85 - nose_start
    front = [(L * 0.45, 1.42, 1.1, 2.95, 0.8), (L * 0.8, 1.2, 1.1, 2.3, 0.6), (L, 0.75, 1.1, tip_z, 0.35)]
    paint = [("company_dark", x0, x1, 1.1, 1.3), ("company", x0, x1, 1.6, 2.1)]
    paint += windows(-3.4, -0.6, 2.3, 2.8, 4, gap=0.3, mat="dark")  # grilles
    body(m, x0, x1, "trains_white", zt=3.15, r=0.55, front=front, glass=(1,), nose=nose_colour, nose_segs=(1, 2),
         cap_front=nose_colour, paint=paint)
    m.box("dark", x0 + 0.2, 3.4, -1.3, 1.3, 0.85, 1.1)
    pantograph(m, -1.6, 3.15)
    headlights(m, 3.2, z=1.45, y=0.6, size=0.15)
    bogie(m, -2.5)
    bogie(m, 1.6)
    buffers(m, x0, 3.85, z=1.0)
    m.save(filename)


# ---------------------------------------------------------------------------------------------------
# Monorail engines


def mono_x2001():
    """A monorail locomotive with a rounded cab at each end."""
    m = Model()
    x0, x1 = -2.8, 2.8
    nose = [(0.5, 1.4, 1.15, 2.95, 0.8), (1.0, 1.2, 1.15, 2.2, 0.7)]
    paint = [("trains_silver", x0, x1, 1.15, 1.5), ("company_dark", x0, x1, 2.0, 2.2)]
    paint += windows(-2.3, 2.3, 2.45, 2.9, 5, gap=0.35, mat="dark")
    body(m, x0, x1, "company", zb=1.15, zt=3.3, r=0.7, front=nose, back=nose, glass=(0,), paint=paint)
    pantograph(m, 0, 3.3)
    headlights(m, 3.8, z=1.55, y=0.6, size=0.15)
    headlights(m, -3.76, z=1.55, y=0.6, size=0.15)
    mono_gear(m, -3.7, 3.7, xs=(-2.3, 2.3))
    m.save("trains_mono_x2001.glb")


def mono_z1():
    """The front car of a monorail multiple unit, with seats behind the cab."""
    m = Model()
    x0, x1 = -3.8, 2.3
    front = [(0.7, 1.4, 1.15, 2.95, 0.85), (1.45, 1.1, 1.15, 1.95, 0.6)]
    paint = [("company", x0, x1, 1.15, 1.7), ("company_dark", x0, x1, 2.85, 2.95)]
    paint += windows(x0 + 0.2, x1 - 0.3, 2.05, 2.75, 5)
    body(m, x0, x1, "trains_white", zb=1.15, zt=3.3, r=0.75, front=front, glass=(0,), nose="company", nose_segs=(1,),
         cap_front="company", paint=paint)
    headlights(m, 3.72, z=1.5, y=0.5, size=0.15)
    mono_gear(m, -3.8, 3.8, xs=(-2.4, 2.4))
    m.save("trains_mono_z1.glb")


def mono_z99():
    """Toyland monorail engine: a round, bubbly body with a big round lamp and bright bands."""
    m = Model()
    rings = [(-1.6 + 0.5 * i, 1.2) for i in range(9)] + [(2.4, 1.05), (3.0, 1.05), (3.0, 0.75), (3.35, 0.75)]

    def boiler(j, i, mid):
        if mid[0] > 3.0:
            return "trains_toy_green"
        if mid[0] > 2.4:
            return "trains_toy_orange"
        if 0.4 < mid[0] < 0.9:
            return "trains_toy_green"
        return "company"
    loft(m, [(x, [(r * math.cos(2 * math.pi * i / 16), 2.3 + r * math.sin(2 * math.pi * i / 16)) for i in range(16)])
             for x, r in rings], boiler, cap_front="light", cap_back="trains_toy_orange")
    paint = windows(-3.4, -1.7, 2.6, 3.3, 1, gap=0.2)
    body(m, -3.6, -1.6, "company_dark", zb=1.1, zt=3.6, r=0.4, paint=paint, cap_front="glass")  # cab
    m.box("trains_toy_purple", -3.8, -1.4, -1.5, 1.5, 3.58, 3.82)
    m.chimney("trains_toy_green", 1.5, 0, 3.2, 4.0, 0.3)
    mono_gear(m, -3.7, 3.6, xs=(-2.3, 2.1))
    m.save("trains_mono_z99.glb")


# ---------------------------------------------------------------------------------------------------
# Maglev engines


def maglev_engine(filename, front_len, back_len, tip_z, base="trains_white", nose=None, eye=False, fins=False, roof=False):
    m = Model()
    x0, x1 = -3.8 + back_len, 3.8 - front_len

    def nose_secs(n):
        return [(n * 0.4, 1.42, 1.1, 2.95, 0.85), (n * 0.8, 1.2, 1.1, 2.25, 0.65), (n, 0.7, 1.1, tip_z, 0.35)]
    paint = [("company", x0, x1, 1.5, 2.0), ("company_dark", x0, x1, 2.0, 2.15)]
    paint += windows(x0 + 0.2, x1 - 0.2, 2.35, 2.75, max(1, int((x1 - x0) / 1.3)), gap=0.4, mat="dark")
    body(m, x0, x1, base, zt=3.1, r=0.75, front=nose_secs(front_len), back=nose_secs(back_len) if back_len else (),
         glass=(1,), nose=nose, nose_segs=(1, 2), cap_front=nose or base, cap_back=nose or base, paint=paint)
    if eye:
        m.cylinder("light", 3.65, 3.85, 0, 1.55, 0.3, sides=12)
    else:
        headlights(m, 3.8 - front_len * 0.12, z=1.4, y=0.5, size=0.13)
    if fins:
        for y in (-0.8, 0.8):
            m.quad(base, (-3.0, y, 2.9), (-1.2, y, 2.9), (-2.6, y, 3.9), (-3.2, y, 3.9))
            m.quad(base, (-1.2, y, 2.9), (-3.0, y, 2.9), (-3.2, y, 3.9), (-2.6, y, 3.9))
    if roof:
        m.box("dark", -1.2, 1.2, -0.5, 0.5, 3.05, 3.3)
    maglev_gear(m, -3.7, 3.7)
    m.save(filename)


def rocketeer():
    """Toyland maglev engine: a rocket with a pointed nose cone and tail fins."""
    m = Model()
    sections = []
    xs = ((-3.7, 0.9), (-3.4, 1.25), (-2.4, 1.27), (-1.8, 1.28), (-1.2, 1.29), (-0.6, 1.3), (0.0, 1.3), (0.6, 1.3),
          (1.2, 1.3), (2.4, 1.1), (3.2, 0.7), (3.75, 0.15))
    for x, r in xs:
        ring = [(r * math.cos(2 * math.pi * i / 14), 2.3 + r * math.sin(2 * math.pi * i / 14)) for i in range(14)]
        sections.append((x, ring))

    def mat(j, i, mid):
        if j >= 9:
            return "trains_red"
        if j in (3, 5, 7) and 2.6 < mid[2] < 3.3 and abs(mid[1]) > 0.6:
            return "glass"  # portholes
        if j == 1:
            return "trains_yellow"
        return "company"
    loft(m, sections, mat, cap_back="dark")
    m.cylinder("trains_toy_orange", -3.85, -3.7, 0, 2.3, 0.7, sides=12)  # exhaust glow
    for y in (-1, 1):
        m.quad("trains_yellow", (-3.6, 1.1 * y, 2.0), (-1.8, 1.1 * y, 2.0), (-3.3, 1.9 * y, 1.6), (-3.8, 1.9 * y, 1.6))
        m.quad("trains_yellow", (-1.8, 1.1 * y, 2.0), (-3.6, 1.1 * y, 2.0), (-3.8, 1.9 * y, 1.6), (-3.3, 1.9 * y, 1.6))
    m.quad("trains_yellow", (-3.6, 0, 3.5), (-1.8, 0, 3.5), (-3.3, 0, 4.4), (-3.8, 0, 4.4))
    m.quad("trains_yellow", (-1.8, 0, 3.5), (-3.6, 0, 3.5), (-3.8, 0, 4.4), (-3.3, 0, 4.4))
    maglev_gear(m, -3.7, 3.7)
    m.save("trains_maglev_rocketeer.glb")


# ---------------------------------------------------------------------------------------------------
# Wagons for the monorail and the maglev


def future_carriage(kind, filename, mail=False):
    m = Model()
    x0, x1 = -3.65, 3.65
    if mail:
        paint = [("company", x0, x1, 1.15, 1.6), ("glass", -2.6, -2.0, 2.3, 2.7), ("glass", 2.0, 2.6, 2.3, 2.7),
                 ("dark", -0.7, 0.7, 1.6, 2.95)]
        body(m, x0, x1, "company_dark", zb=1.15, zt=3.3, r=0.7, paint=paint)
    else:
        paint = [("company", x0, x1, 1.15, 1.6), ("company_dark", x0, x1, 2.85, 2.95)]
        paint += windows(x0 + 0.15, x1 - 0.15, 2.05, 2.75, 6)
        body(m, x0, x1, "trains_white", zb=1.15, zt=3.3, r=0.7, paint=paint)
    gear(m, kind, x0, x1)
    m.save(filename)


def future_van(kind, filename, wall, doors="dark", style=None):
    m = Model()
    x0, x1 = -3.6, 3.6
    paint = [("company", x0, x1, 1.15, 1.4)]
    if style == "slats":
        for z in (1.7, 2.1, 2.5, 2.9):
            paint.append(("dark", x0 + 0.2, x1 - 0.2, z - 0.1, z))
    elif style == "armoured":
        for x in (-2.6, -1.6, 1.6, 2.6):
            paint.append(("metal", x - 0.06, x + 0.06, 1.4, 3.0))
    elif style == "toy":
        paint += [("trains_toy_pink", -3.1, -1.9, 1.7, 2.7), ("trains_toy_green", 1.9, 3.1, 1.7, 2.7)]
    paint.append((doors, -0.8, 0.8, 1.45, 2.9))
    body(m, x0, x1, wall, zb=1.15, zt=3.2, r=0.55, paint=paint)
    if style == "reefer":
        m.box("metal", -3.4, -2.6, -0.6, 0.6, 3.15, 3.45)
    gear(m, kind, x0, x1)
    m.save(filename)


def future_open(kind, filename, load, style="heap"):
    """An open wagon; the load fills it."""
    m = Model()
    x0, x1 = -3.6, 3.6
    for y0, y1 in ((-1.42, -1.25), (1.25, 1.42)):
        m.box("company_dark", x0 + 0.1, x1 - 0.1, y0, y1, 1.1, 2.3)
        m.box("company", x0 + 0.1, x1 - 0.1, y0, y1, 2.3, 2.45)
    for xa, xb in ((x0 + 0.1, x0 + 0.27), (x1 - 0.27, x1 - 0.1)):
        m.box("company_dark", xa, xb, -1.25, 1.25, 1.1, 2.45)
    if style == "heap":
        m.box(load, x0 + 0.3, x1 - 0.3, -1.25, 1.25, 1.15, 2.25)
        m.prism_roof(load, load, x0 + 0.3, x1 - 0.3, -1.25, 1.25, 2.25, 2.8)
    else:  # crates in a row
        for i in range(4):
            xa = x0 + 0.35 + i * 1.65
            m.box(load, xa, xa + 1.5, -1.2, 1.2, 1.15, 2.8)
    gear(m, kind, x0, x1)
    m.save(filename)


def future_flat(kind, filename, load, style):
    """A flat wagon with stakes, carrying logs or steel."""
    m = Model()
    x0, x1 = -3.6, 3.6
    m.box("company_dark", x0 + 0.1, x1 - 0.1, -1.4, 1.4, 1.1, 1.35)
    for x in (-3.2, -1.1, 1.1, 3.2):
        for y in (-1.35, 1.2):
            m.box("company", x - 0.08, x + 0.08, y, y + 0.15, 1.35, 2.6)
    if style == "logs":
        m.box(load, x0 + 0.3, x1 - 0.3, -1.15, 1.15, 1.35, 1.6)
        for z, ys in ((1.6, (-0.8, 0.0, 0.8)), (2.25, (-0.4, 0.4))):
            for y in ys:
                m.cylinder(load, x0 + 0.3, x1 - 0.3, y, z + 0.38, 0.4, sides=8, caps="wood")
    else:
        for xa in (-3.1, -0.9, 1.3):
            m.box(load, xa, xa + 1.8, -1.0, 1.0, 1.35, 1.75)
            m.box(load, xa + 0.1, xa + 1.7, -0.9, 0.9, 1.75, 2.1)
    gear(m, kind, x0, x1)
    m.save(filename)


def future_hopper(kind, filename, load):
    m = Model()
    x0, x1 = -3.6, 3.6
    m.box("company_dark", x0 + 0.6, x1 - 0.6, -1.42, -1.25, 1.1, 2.85)
    m.box("company_dark", x0 + 0.6, x1 - 0.6, 1.25, 1.42, 1.1, 2.85)
    m.box("company", x0 + 0.6, x1 - 0.6, -1.42, -1.25, 2.85, 3.05)
    m.box("company", x0 + 0.6, x1 - 0.6, 1.25, 1.42, 2.85, 3.05)
    m.box("company_dark", x0 + 0.6, x1 - 0.6, -1.25, 1.25, 1.1, 1.5)
    for xa, xb in ((x0 + 0.1, x0 + 0.6), (x1 - 0.6, x1 - 0.1)):
        out, inner = (xa, xb) if xa < 0 else (xb, xa)
        # A sloping end: a thin wedge, closed at its sides.
        pts = [(out, 3.05), (inner, 1.4), (inner, 3.05)]
        for y in (-1.42, 1.42):
            m.triangle("company_dark", *_flip_out(*[(x, y, z) for x, z in pts], (0, 0, 2.5)))
        loft_end = [(out, -1.42, 3.05), (inner, -1.42, 1.4), (inner, 1.42, 1.4), (out, 1.42, 3.05)]
        a, b, c, d = loft_end
        m.triangle("company_dark", *_flip_out(a, b, c, (0, 0, 2.5)))
        m.triangle("company_dark", *_flip_out(a, c, d, (0, 0, 2.5)))
    m.box(load, x0 + 0.7, x1 - 0.7, -1.3, 1.3, 2.3, 3.0)
    m.prism_roof(load, load, x0 + 0.7, x1 - 0.7, -1.3, 1.3, 3.0, 3.4)
    for x in (-1.0, 1.0):
        m.box("dark", x - 0.4, x + 0.4, -0.6, 0.6, 1.0, 1.15)  # chutes
    gear(m, kind, x0, x1)
    m.save(filename)


def future_tanker(kind, filename, tank, band="company"):
    m = Model()
    x0, x1 = -3.6, 3.6
    m.box("dark", x0 + 0.3, x1 - 0.3, -1.0, 1.0, 1.0, 1.3)
    sections = []
    for x, r in ((x0 + 0.2, 0.75), (x0 + 0.6, 1.08), (-1.75, 1.08), (-1.45, 1.08), (1.45, 1.08), (1.75, 1.08),
                 (x1 - 0.6, 1.08), (x1 - 0.2, 0.75)):
        ring = [(r * math.cos(2 * math.pi * i / 16), 2.3 + r * math.sin(2 * math.pi * i / 16)) for i in range(16)]
        sections.append((x, ring))
    loft(m, sections, lambda j, i, mid: band if j in (2, 4) else tank)
    m.chimney("dark", 0, 0, 3.25, 3.65, 0.4)
    for x in (-2.4, 2.4):
        m.box("dark", x - 0.1, x + 0.1, -1.0, 1.0, 1.3, 1.6)  # cradles
    gear(m, kind, x0, x1)
    m.save(filename)


# Wagons of each railway, as offsets in the 27 wagons that follow its engines (same order as rail 27-53).
WAGON_KINDS = [
    ("carriage", [0]),
    ("mail", [1]),
    ("van_goods", [5, 12]),
    ("van_livestock", [4]),
    ("van_armoured", [10]),
    ("van_reefer", [11]),
    ("van_toy", [20, 22, 23]),
    ("open_coal", [2]),
    ("open_fruit", [15]),
    ("open_batteries", [24]),
    ("open_fizzy", [25]),
    ("flat_logs", [7]),
    ("flat_steel", [9]),
    ("hopper_grain", [6]),
    ("hopper_ore", [8]),
    ("hopper_copper", [13]),
    ("hopper_sugar", [17]),
    ("hopper_candyfloss", [18]),
    ("hopper_toffee", [19]),
    ("tanker_oil", [3, 16]),
    ("tanker_water", [14]),
    ("tanker_toy", [21, 26]),
]

HOPPER_LOADS = {"grain": "load_trains_grain", "ore": "load_ore", "copper": "load_trains_copper", "sugar": "load_trains_sugar",
                "candyfloss": "load_trains_candyfloss", "toffee": "load_trains_toffee"}


def make_wagon(kind, name, filename):
    if name == "carriage":
        future_carriage(kind, filename)
    elif name == "mail":
        future_carriage(kind, filename, mail=True)
    elif name == "van_goods":
        future_van(kind, filename, "trains_silver")
    elif name == "van_livestock":
        future_van(kind, filename, "wood", style="slats")
    elif name == "van_armoured":
        future_van(kind, filename, "metal", style="armoured")
    elif name == "van_reefer":
        future_van(kind, filename, "trains_white", doors="trains_silver", style="reefer")
    elif name == "van_toy":
        future_van(kind, filename, "trains_toy_purple", doors="trains_yellow", style="toy")
    elif name == "open_coal":
        future_open(kind, filename, "load_coal")
    elif name == "open_fruit":
        future_open(kind, filename, "load_trains_fruit")
    elif name == "open_batteries":
        future_open(kind, filename, "load_trains_batteries", style="crates")
    elif name == "open_fizzy":
        future_open(kind, filename, "load_trains_fizzy", style="crates")
    elif name == "flat_logs":
        future_flat(kind, filename, "load_trains_logs", "logs")
    elif name == "flat_steel":
        future_flat(kind, filename, "load_trains_steel", "steel")
    elif name.startswith("hopper_"):
        future_hopper(kind, filename, HOPPER_LOADS[name[7:]])
    elif name == "tanker_oil":
        future_tanker(kind, filename, "boiler")
    elif name == "tanker_water":
        future_tanker(kind, filename, "trains_silver")
    elif name == "tanker_toy":
        future_tanker(kind, filename, "trains_toy_pink", band="trains_toy_green")
    else:
        raise ValueError(name)


# ---------------------------------------------------------------------------------------------------


def build():
    vehicles = []

    def add(ids, filename):
        vehicles.append({"type": "train", "ids": ids, "model": filename})

    turner_turbo()
    add([20], "trains_turner_turbo.glb")
    hst_power_car()
    add([22], "trains_hst_power_car.glb")
    high_speed_electric("trains_tim.glb", 1.0, "trains_white", tip_z=1.6)
    add([25], "trains_tim.glb")
    high_speed_electric("trains_asiastar.glb", 0.6, "trains_yellow", tip_z=1.8)
    add([26], "trains_asiastar.glb")

    mono_x2001()
    add([54], "trains_mono_x2001.glb")
    mono_z1()
    add([55], "trains_mono_z1.glb")
    mono_z99()
    add([56], "trains_mono_z99.glb")

    maglev_engine("trains_maglev_leviathan.glb", 1.2, 1.2, 1.9, roof=True)
    add([84], "trains_maglev_leviathan.glb")
    maglev_engine("trains_maglev_cyclops.glb", 1.4, 1.0, 2.0, base="trains_silver", eye=True)
    add([85], "trains_maglev_cyclops.glb")
    maglev_engine("trains_maglev_pegasus.glb", 2.0, 0.9, 1.7, nose="company", fins=True)
    add([86], "trains_maglev_pegasus.glb")
    maglev_engine("trains_maglev_chimaera.glb", 3.0, 0, 1.6, nose="company_dark")
    add([87], "trains_maglev_chimaera.glb")
    rocketeer()
    add([88], "trains_maglev_rocketeer.glb")

    for kind, first in (("mono", 57), ("maglev", 89)):
        for name, offsets in WAGON_KINDS:
            filename = "trains_%s_%s.glb" % (kind, name)
            make_wagon(kind, name, filename)
            add([first + o for o in offsets], filename)

    return {"vehicles": vehicles, "buildings": []}
