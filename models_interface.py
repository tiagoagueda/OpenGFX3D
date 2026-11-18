"""Parts of the interface that stand in the 3D world: the posts of labels and the cursor.

Ids: 0 the post under a town name, station name or sign, one unit tall (the game stretches it);
1 a bar along one edge of the selected tiles, from x = 0 to 1 (the game stretches it from corner to corner);
2 a post at a corner of the selected tiles; 3 the arrow that hovers over the tile below the cursor, its tip
at the origin; 4 a bracket for a corner of the tile below the cursor when no tool is in use, along +x and +y;
5 half of a plate that marks a tile, such as one in the catchment area of a station: the triangle from the
origin to x = 1 and y = 1, flat (the game puts two of them on each tile, tilted to follow the ground);
6 half a piece of road for the preview of the road tools: from the middle of a tile (the origin) to its edge
at x = 8, with kerbs along both sides and a dashed line down the middle (the game shows it see-through).
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


def mark():
    m = Model()
    m.triangle("company", (0, 0, 0), (1, 0, 0), (0, 1, 0))
    return save(m, "tile_mark")


def road_piece():
    m = Model()
    m.box("company", 0, 8, -4.6, 4.6, 0, 0.3)
    for y in (-4.6, 4.0):
        m.box("company", 0, 8, y, y + 0.6, 0.3, 0.75)
    for x in (0.5, 4.5):
        m.box("company", x, x + 2.5, -0.25, 0.25, 0.3, 0.42)
    return save(m, "road_piece")


def build():
    models = [post(), edge(), corner(), arrow(), bracket(), mark(), road_piece()]
    return {"vehicles": [], "buildings": [{"type": "interface", "ids": [i], "model": model} for i, model in enumerate(models)]}
