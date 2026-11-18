"""People who walk along the pavements of towns.

Index type `pedestrian`, ids:
    0 to 3 a person in trousers, 4 to 7 a person in a dress or skirt: four steps of walking, shown one after
      the other (0 the left foot in front, 1 passing, 2 the right foot in front, 3 passing).
A person stands with the feet at the origin and walks along +x. The shirt or dress is in the material "company",
which the game colours, so the same models make people in many colours.
"""

import math

from gfx3d import MATERIALS, Model

GROUP = "people"

for name, colour in {
    "skin": (0.86, 0.68, 0.55),
    "hair": (0.24, 0.17, 0.12),
    "trousers": (0.20, 0.24, 0.34),
    "shoes": (0.12, 0.11, 0.10),
}.items():
    MATERIALS[f"{GROUP}_{name}"] = colour


def mat(name):
    return f"{GROUP}_{name}"


HIP = 0.98  # height of the hips
LEG = 0.94  # length of a leg to the sole
SHOULDER = 1.62  # height of the shoulders
ARM = 0.72


def turned_box(m, material, pivot, angle, x0, x1, y0, y1, z0, z1):
    """A box in the frame of a limb hanging from pivot, turned forward by angle (radians) around the y axis."""
    c, s = math.cos(angle), math.sin(angle)

    def p(x, y, z):
        # Turn around y: a limb that hangs down (-z) swings forward (+x) for a positive angle.
        return (pivot[0] + x * c - z * s, pivot[1] + y, pivot[2] + x * s + z * c)

    corners = {(i, j, k): p((x0, x1)[i], (y0, y1)[j], (z0, z1)[k]) for i in (0, 1) for j in (0, 1) for k in (0, 1)}
    q = lambda a, b, cc, d: m.quad(material, corners[a], corners[b], corners[cc], corners[d])
    q((1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1))  # front
    q((0, 1, 0), (0, 0, 0), (0, 0, 1), (0, 1, 1))  # back
    q((1, 1, 0), (0, 1, 0), (0, 1, 1), (1, 1, 1))  # left
    q((0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1))  # right
    q((0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1))  # top
    q((0, 1, 0), (1, 1, 0), (1, 0, 0), (0, 0, 0))  # bottom


def person(step, dress):
    m = Model()
    swing = (0.42, 0.0, -0.42, 0.0)[step]
    bob = 0.0 if step in (0, 2) else 0.05
    for side, sign in ((0.13, 1), (-0.13, -1)):
        a = swing * sign
        pivot = (0, side, HIP + bob)
        # Legs (with shoes); under a dress the legs are bare below the hem.
        if dress:
            turned_box(m, mat("skin"), pivot, a, -0.07, 0.07, -0.07, 0.07, -LEG + 0.08, -0.35)
        else:
            turned_box(m, mat("trousers"), pivot, a, -0.09, 0.09, -0.09, 0.09, -LEG + 0.08, 0.0)
        turned_box(m, mat("shoes"), pivot, a, -0.08, 0.2, -0.08, 0.08, -LEG + 0.02, -LEG + 0.12)
        # Arms swing the other way.
        arm = (0, side * 2.05, SHOULDER + bob)
        turned_box(m, "company", arm, -a * 0.8, -0.07, 0.07, -0.07, 0.07, -0.42, 0.0)
        turned_box(m, mat("skin"), arm, -a * 0.8, -0.06, 0.06, -0.06, 0.06, -ARM, -0.42)
    z = HIP + bob
    if dress:
        # A dress that widens towards the hem.
        m.box("company", -0.15, 0.15, -0.21, 0.21, z - 0.05, SHOULDER + bob)
        m.box("company", -0.22, 0.22, -0.26, 0.26, z - 0.4, z + 0.05)
    else:
        m.box(mat("trousers"), -0.13, 0.13, -0.22, 0.22, z - 0.08, z + 0.1)
        m.box("company", -0.14, 0.14, -0.22, 0.22, z + 0.1, SHOULDER + bob)
    m.box(mat("skin"), -0.05, 0.05, -0.05, 0.05, SHOULDER + bob, SHOULDER + bob + 0.1)  # neck
    m.box(mat("skin"), -0.11, 0.12, -0.1, 0.1, SHOULDER + bob + 0.1, SHOULDER + bob + 0.36)  # head
    # Hair on top and at the back; longer for the second figure.
    m.box(mat("hair"), -0.13, 0.1, -0.11, 0.11, SHOULDER + bob + 0.3, SHOULDER + bob + 0.4)
    m.box(mat("hair"), -0.14, -0.06, -0.11, 0.11, SHOULDER + bob + (0.0 if dress else 0.14), SHOULDER + bob + 0.36)
    return m


def build():
    buildings = []
    for figure, dress in (("trousers", False), ("dress", True)):
        for step in range(4):
            filename = f"{GROUP}_{figure}_{step}.glb"
            person(step, dress).save(filename)
            buildings.append({"type": "pedestrian", "ids": [step + (4 if dress else 0)], "model": filename, "far": ""})
    return {"vehicles": [], "buildings": buildings}
