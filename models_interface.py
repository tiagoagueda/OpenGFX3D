"""Parts of the interface that stand in the 3D world: the posts of labels and the cursor.

Ids: 0 the post under a town name, station name or sign, one unit tall (the game stretches it);
1 a bar along one edge of the selected tiles, from x = 0 to 1 (the game stretches it from corner to corner);
2 a post at a corner of the selected tiles; 3 the arrow that hovers over the tile below the cursor, its tip
at the origin; 4 a bracket for a corner of the tile below the cursor when no tool is in use, along +x and +y.
All but the post take the colour the game gives them.
"""

from gfx3d import Model
from models_infra import frustum

GROUP = "interface"


def save(m, name):
    m.save(f"{GROUP}_{name}.glb")
    return f"{GROUP}_{name}.glb"


def post():
    m = Model()
    m.box("metal", -0.18, 0.18, -0.18, 0.18, 0, 1)
    return save(m, "label_post")


def edge():
    m = Model()
    m.box("company", 0, 1, -0.3, 0.3, 0, 0.35)
    return save(m, "cursor_edge")


def corner():
    m = Model()
    m.box("company", -0.45, 0.45, -0.45, 0.45, 0, 2.2)
    m.box("company", -0.7, 0.7, -0.7, 0.7, 2.2, 2.5)
    return save(m, "cursor_corner")


def arrow():
    m = Model()
    frustum(m, "company", 0, 0, 0, 2.6, 0.0, 2.2, 4, top="company", rot=0.785398)
    m.box("company", -0.7, 0.7, -0.7, 0.7, 2.6, 5.4)
    return save(m, "cursor_arrow")


def bracket():
    m = Model()
    m.box("company", 0, 5, 0, 0.8, 0, 0.5)
    m.box("company", 0, 0.8, 0.8, 5, 0, 0.5)
    return save(m, "cursor_bracket")


def build():
    models = [post(), edge(), corner(), arrow(), bracket()]
    return {"vehicles": [], "buildings": [{"type": "interface", "ids": [i], "model": model} for i, model in enumerate(models)]}
