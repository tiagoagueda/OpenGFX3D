"""Effects: puffs of smoke and steam, and sparks.

The game makes each puff grow, fade and colour it by the kind of effect, so all puffs share one shape in the
material "company", which takes the colour the game gives. A puff is about one world unit across at scale 1,
with its middle at the origin.
"""

import random

from gfx3d import Model
from models_industry_other import sphere

GROUP = "effects"


def puff():
    m = Model()
    rnd = random.Random(7)
    sphere(m, "company", 0, 0, 0, 1.0, rz=0.85, seg=8, rings=5)
    for _ in range(3):
        sphere(m, "company", rnd.uniform(-0.6, 0.6), rnd.uniform(-0.6, 0.6), rnd.uniform(-0.1, 0.4), rnd.uniform(0.5, 0.7), seg=6, rings=4)
    m.save(f"{GROUP}_puff.glb")
    return f"{GROUP}_puff.glb"


def spark():
    m = Model()
    # Three crossed bars, like a star.
    w = 0.15
    m.box("company", -1, 1, -w, w, -w, w)
    m.box("company", -w, w, -1, 1, -w, w)
    m.box("company", -w, w, -w, w, -1, 1)
    m.save(f"{GROUP}_spark.glb")
    return f"{GROUP}_spark.glb"


def build():
    # Effect vehicle types: 0 chimney smoke, 1 steam, 2 diesel smoke, 3 electric spark, 4 crash smoke,
    # 5 large explosion, 6 breakdown smoke, 7 small explosion, 9 bubble, 10 breakdown smoke of aircraft,
    # 11 copper mine smoke. The bulldozer (8) is in models_works.
    return {"vehicles": [], "buildings": [
        {"type": "effect", "ids": [0, 1, 2, 4, 5, 6, 7, 9, 10, 11], "model": puff(), "scale": 3.0},
        {"type": "effect", "ids": [3], "model": spark(), "scale": 3.0},
    ]}
