#!/usr/bin/env python3
"""The toolkit for the models of the OpenGFX3D package: materials and the Model class.

The models are simple shapes written straight to binary glTF files, so they need no modelling program.

Shapes are described with x towards the front of the vehicle, y to its left and z up, in world units
(a tile is 16 long), with the ground at z = 0 and the middle of the vehicle at x = y = 0.
"""

import json
import math
import re
import struct

# Colours as seen on screen, 0 to 1. "company" is multiplied with the colour of the owner.
# Materials named "load..." are the cargo: the game draws them only when the vehicle is loaded, and lets
# them sink into the vehicle as it gets emptier, by up to their own height.
MATERIALS = {
    "company": (1.00, 1.00, 1.00),
    "company_dark": (0.72, 0.72, 0.72),
    "glass": (0.16, 0.22, 0.30),
    "tyre": (0.10, 0.10, 0.10),
    "hub": (0.60, 0.60, 0.60),
    "dark": (0.22, 0.22, 0.24),
    "roof": (0.86, 0.86, 0.84),
    "light": (1.00, 0.95, 0.70),
    "cargo": (0.70, 0.71, 0.74),
    "cargo_dark": (0.50, 0.51, 0.54),
    "wall": (0.80, 0.74, 0.64),
    "brick": (0.62, 0.32, 0.24),
    "stone": (0.66, 0.64, 0.60),
    "tiles": (0.52, 0.24, 0.18),
    "slate": (0.30, 0.31, 0.36),
    "concrete": (0.74, 0.74, 0.72),
    "metal": (0.55, 0.57, 0.60),
    "frame": (0.92, 0.92, 0.90),
    "door": (0.36, 0.24, 0.16),
    "platform": (0.64, 0.62, 0.58),
    "edge": (0.90, 0.82, 0.30),
    "grass": (0.30, 0.48, 0.20),
    "boiler": (0.14, 0.15, 0.16),
    "brass": (0.80, 0.64, 0.30),
    "wood": (0.50, 0.36, 0.22),
    "rust": (0.42, 0.30, 0.24),
    "load_coal": (0.17, 0.16, 0.16),
    "load_ore": (0.56, 0.42, 0.30),
}

# The surface textures of make_model_textures.py: name -> how many world units one repeat covers.
# The file is tex_<name>.png. The game multiplies the texture with the colour of the material.
TEXTURES = {
    "brick": 4.0,
    "stone": 6.0,
    "rubble": 4.0,
    "rooftiles": 4.0,
    "slate": 4.0,
    "thatch": 4.0,
    "planks": 4.0,
    "bark": 3.0,
    "concrete": 8.0,
    "plaster": 8.0,
    "panel": 4.0,
    "metal": 4.0,
    "corrugated": 2.0,
    "paving": 4.0,
    "asphalt": 4.0,
    "gravel": 3.0,
    "foliage": 5.0,
    "grass": 4.0,
    "soil": 4.0,
    "crops": 2.0,
    "glass": 4.0,
    "glass_grid": 3.3,
    "water": 6.0,
    "snow": 6.0,
    "fabric": 2.0,
    "rust": 4.0,
}

# The average brightness of every texture; save() makes the colour of the material lighter by as much.
TEXTURE_MEAN = 0.88

# Which texture a material gets: the first rule whose pattern is found in the name of the material.
# None is a plain colour. Materials that match no rule stay plain too (lamps, markings, toys, ...).
TEXTURE_RULES = [
    (r"toy|lamp|^light$|marking|line$|glow|_on$|_off$|wire|cable|insulator|flag|crowd|seats|flower", None),
    (r"wood_end|logend|drum|bottle|battery|bubble|cow|fruit|toffee|candyfloss|cola|paper", None),
    (r"glass_(blue|dark|roof)", "glass_grid"),
    (r"glass|ice$", "glass"),
    (r"brick", "brick"),
    (r"fence_stone|land_stone", "rubble"),
    (r"stone", "stone"),
    (r"thatch|hay|stubble|wheat", "thatch"),
    (r"slate|bluetile|bluedark|roofblue", "slate"),
    (r"corrugated", "corrugated"),
    (r"tiles|[a-z]_roof$|redroof|brownroof|sandroof|ceramic", "rooftiles"),
    (r"bark|trunk", "bark"),
    (r"plank|wood|sleeper|crate|^door$|logs?$|ships_deck", "planks"),
    (r"concrete|platform|kerb|planter", "concrete"),
    (r"paving|path$", "paving"),
    (r"asphalt|tarmac|runway", "asphalt"),
    (r"ballast|gravel", "gravel"),
    (r"crop|corn", "crops"),
    (r"leaf|leaves|foliage|hedge|conifer|cactus|tuft|sprout", "foliage"),
    (r"grass|pitch$", "grass"),
    (r"soil|earth|dirt|spoil|coal|ore$|ore_|copper$|sand$|grain", "soil"),
    (r"snow|sugar", "snow"),
    (r"water", "water"),
    (r"canvas|envelope", "fabric"),
    (r"rust|steel_brown", "rust"),
    (r"^company|^roof$|^cargo|hull|skirt|armour|antifoul|^(ships|air|trains|road|works|indt|io|infra)_(white|red|yellow|silver|grey|black|orange|blue|green)$", "panel"),
    (r"steel|metal|boiler|chrome|silver|mast|track_post|pole|rail", "metal"),
    (r"^wall$|stucco|beige|cream|pink$|houses_[a-z]+_(white|green|red|yellow)$", "plaster"),
]

_texture_of = {}


def texture_of(material):
    """The texture of a material, or None for a plain colour."""
    if material not in _texture_of:
        _texture_of[material] = next((texture for pattern, texture in TEXTURE_RULES if re.search(pattern, material)), None)
    return _texture_of[material]


def texture_coordinates(positions, normals, size):
    """Where each corner is in a texture that repeats every `size` world units.

    The texture is laid flat on each surface: on walls its top points up, on sloping surfaces up the slope,
    and on level ones to +y; it carries on across surfaces that lie in the same plane."""
    result = []
    for p, n in zip(positions, normals):
        length = math.hypot(n[0], n[1])
        if abs(n[2]) > 0.999 or length < 1e-6:
            u, v = p[0], p[1]
        else:
            ux, uy = -n[1] / length, n[0] / length  # Level, along the surface.
            vx, vy, vz = -n[2] * uy, n[2] * ux, n[0] * uy - n[1] * ux  # Up the surface.
            u = p[0] * ux + p[1] * uy
            v = p[0] * vx + p[1] * vy + p[2] * vz
        # In glTF the top of the image is at 0.
        result.append((u / size, -v / size))
    return result


class Model:
    def __init__(self):
        self.parts = {}  # material -> (positions, normals), three corners per triangle

    def triangle(self, material, a, b, c):
        u = [b[i] - a[i] for i in range(3)]
        v = [c[i] - a[i] for i in range(3)]
        n = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]]
        length = math.sqrt(sum(x * x for x in n)) or 1.0
        n = [x / length for x in n]
        positions, normals = self.parts.setdefault(material, ([], []))
        positions.extend([a, b, c])
        normals.extend([n, n, n])

    def quad(self, material, a, b, c, d):
        """Four corners, counter-clockwise when seen from outside."""
        self.triangle(material, a, b, c)
        self.triangle(material, a, c, d)

    def box(self, material, x0, x1, y0, y1, z0, z1):
        self.quad(material, (x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1))  # front
        self.quad(material, (x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1))  # back
        self.quad(material, (x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1))  # left
        self.quad(material, (x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1))  # right
        self.quad(material, (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1))  # top
        self.quad(material, (x0, y1, z0), (x1, y1, z0), (x1, y0, z0), (x0, y0, z0))  # bottom

    def prism_roof(self, material, gable, x0, x1, y0, y1, z0, z1):
        """A pitched roof with its ridge along x, and the gable ends filled with another material."""
        ym = (y0 + y1) / 2
        self.quad(material, (x0, y0, z0), (x1, y0, z0), (x1, ym, z1), (x0, ym, z1))
        self.quad(material, (x1, y1, z0), (x0, y1, z0), (x0, ym, z1), (x1, ym, z1))
        self.triangle(gable, (x1, y0, z0), (x1, y1, z0), (x1, ym, z1))
        self.triangle(gable, (x0, y1, z0), (x0, y0, z0), (x0, ym, z1))

    def pyramid(self, material, x0, x1, y0, y1, z0, z1):
        xm, ym = (x0 + x1) / 2, (y0 + y1) / 2
        top = (xm, ym, z1)
        self.triangle(material, (x1, y0, z0), (x1, y1, z0), top)
        self.triangle(material, (x1, y1, z0), (x0, y1, z0), top)
        self.triangle(material, (x0, y1, z0), (x0, y0, z0), top)
        self.triangle(material, (x0, y0, z0), (x1, y0, z0), top)

    def windows(self, material, x0, x1, y0, y1, z0, z1, rows, per_side, size=(1.4, 1.5), depth=0.08):
        """Windows on all four walls of a box, as thin boxes standing out of the walls."""
        w, h = size
        for row in range(rows):
            zc = z0 + (row + 0.5) * (z1 - z0) / rows
            for i in range(per_side):
                xc = x0 + (i + 0.5) * (x1 - x0) / per_side
                self.box(material, xc - w / 2, xc + w / 2, y0 - depth, y0, zc - h / 2, zc + h / 2)
                self.box(material, xc - w / 2, xc + w / 2, y1, y1 + depth, zc - h / 2, zc + h / 2)
                yc = y0 + (i + 0.5) * (y1 - y0) / per_side
                self.box(material, x0 - depth, x0, yc - w / 2, yc + w / 2, zc - h / 2, zc + h / 2)
                self.box(material, x1, x1 + depth, yc - w / 2, yc + w / 2, zc - h / 2, zc + h / 2)

    def wheel(self, x, y, radius, width, sides=12):
        """A wheel with its axle along y, standing on the ground."""
        y0, y1 = y - width / 2, y + width / 2
        ring = [(x + radius * math.cos(2 * math.pi * i / sides), radius + radius * math.sin(2 * math.pi * i / sides)) for i in range(sides)]
        for i in range(sides):
            (ax, az), (bx, bz) = ring[i], ring[(i + 1) % sides]
            self.quad("tyre", (ax, y1, az), (ax, y0, az), (bx, y0, bz), (bx, y1, bz))
            self.triangle("hub", (x, y1, radius), (ax, y1, az), (bx, y1, bz))
            self.triangle("hub", (x, y0, radius), (bx, y0, bz), (ax, y0, az))

    def cylinder(self, material, x0, x1, y, z, radius, sides=14, caps=None):
        """A cylinder lying along x; the ends take the material caps, or the same material."""
        caps = caps or material
        ring = [(y + radius * math.cos(2 * math.pi * i / sides), z + radius * math.sin(2 * math.pi * i / sides)) for i in range(sides)]
        for i in range(sides):
            (ay, az), (by, bz) = ring[i], ring[(i + 1) % sides]
            self.quad(material, (x0, ay, az), (x1, ay, az), (x1, by, bz), (x0, by, bz))
            self.triangle(caps, (x1, y, z), (x1, by, bz), (x1, ay, az))
            self.triangle(caps, (x0, y, z), (x0, ay, az), (x0, by, bz))

    def chimney(self, material, x, y, z0, z1, radius, sides=10):
        """A cylinder standing upright, open at the top."""
        ring = [(x + radius * math.cos(2 * math.pi * i / sides), y + radius * math.sin(2 * math.pi * i / sides)) for i in range(sides)]
        for i in range(sides):
            (ax, ay), (bx, by) = ring[i], ring[(i + 1) % sides]
            self.quad(material, (ax, ay, z0), (bx, by, z0), (bx, by, z1), (ax, ay, z1))
            self.triangle("boiler", (x, y, z1 - 0.3), (ax, ay, z1), (bx, by, z1))

    def sheave(self, rim, spokes, radius, width, count=6, sides=16):
        """A spoked wheel (a winding wheel, a sheave) turning around the x axis, centred on the origin."""
        x0, x1 = -width / 2, width / 2
        inner = radius * 0.8
        ring = [(math.cos(2 * math.pi * i / sides), math.sin(2 * math.pi * i / sides)) for i in range(sides)]
        for i in range(sides):
            (ac, as_), (bc, bs) = ring[i], ring[(i + 1) % sides]
            self.quad(rim, (x0, radius * ac, radius * as_), (x1, radius * ac, radius * as_), (x1, radius * bc, radius * bs), (x0, radius * bc, radius * bs))
            self.quad(rim, (x1, inner * ac, inner * as_), (x0, inner * ac, inner * as_), (x0, inner * bc, inner * bs), (x1, inner * bc, inner * bs))
            for x, sign in ((x1, 1), (x0, -1)):
                a, b = (x, radius * ac, radius * as_), (x, radius * bc, radius * bs)
                c, d = (x, inner * bc, inner * bs), (x, inner * ac, inner * as_)
                if sign > 0:
                    self.quad(rim, d, c, b, a)
                else:
                    self.quad(rim, a, b, c, d)
        for k in range(count):
            ang = math.pi * k / count
            ca, sa = math.cos(ang), math.sin(ang)
            w = 0.12 * radius
            # A flat spoke across the whole wheel, drawn on both faces.
            p = [(-inner * ca - w * sa, -inner * sa + w * ca), (inner * ca - w * sa, inner * sa + w * ca),
                 (inner * ca + w * sa, inner * sa - w * ca), (-inner * ca + w * sa, -inner * sa - w * ca)]
            xs = width * 0.15
            self.quad(spokes, *[(xs, a, b) for a, b in p[::-1]])
            self.quad(spokes, *[(-xs, a, b) for a, b in p])
        self.box(spokes, -width * 0.4, width * 0.4, -0.15 * radius, 0.15 * radius, -0.15 * radius, 0.15 * radius)

    def save(self, filename):
        binary = bytearray()
        views, accessors, materials, primitives = [], [], [], []
        images, textures = [], {}

        def add(vectors):
            # glTF has x to the left, y up and z to the front.
            data = b"".join(struct.pack("<3f", v[1], v[2], v[0]) for v in vectors)
            views.append({"buffer": 0, "byteOffset": len(binary), "byteLength": len(data)})
            binary.extend(data)
            converted = [(v[1], v[2], v[0]) for v in vectors]
            accessors.append({
                "bufferView": len(views) - 1, "componentType": 5126, "count": len(vectors), "type": "VEC3",
                "min": [min(v[i] for v in converted) for i in range(3)],
                "max": [max(v[i] for v in converted) for i in range(3)],
            })
            return len(accessors) - 1

        def add_coordinates(coordinates):
            data = b"".join(struct.pack("<2f", *c) for c in coordinates)
            views.append({"buffer": 0, "byteOffset": len(binary), "byteLength": len(data)})
            binary.extend(data)
            accessors.append({"bufferView": len(views) - 1, "componentType": 5126, "count": len(coordinates), "type": "VEC2"})
            return len(accessors) - 1

        for name, (positions, normals) in self.parts.items():
            attributes = {"POSITION": add(positions), "NORMAL": add(normals)}
            colour = MATERIALS[name]
            surface = {"metallicFactor": 0.0, "roughnessFactor": 0.8}
            texture = texture_of(name)
            if texture is not None:
                # The texture is multiplied with the colour and is darker than white on average; make up for that.
                colour = [min(c / TEXTURE_MEAN, 1.0) for c in colour]
                if texture not in textures:
                    textures[texture] = len(images)
                    images.append({"uri": f"tex_{texture}.png"})
                surface["baseColorTexture"] = {"index": textures[texture]}
                attributes["TEXCOORD_0"] = add_coordinates(texture_coordinates(positions, normals, TEXTURES[texture]))
            # glTF stores colours as amounts of light, not as seen on screen.
            surface["baseColorFactor"] = [round(c ** 2.2, 4) for c in colour] + [1.0]
            materials.append({"name": name, "pbrMetallicRoughness": surface})
            primitives.append({"attributes": attributes, "material": len(materials) - 1})

        scene = {
            "asset": {"version": "2.0", "generator": "OpenGFX3D make_models.py"},
            "scene": 0,
            "scenes": [{"nodes": [0]}],
            "nodes": [{"mesh": 0}],
            "meshes": [{"primitives": primitives}],
            "materials": materials,
            "accessors": accessors,
            "bufferViews": views,
            "buffers": [{"byteLength": len(binary)}],
        }
        if images:
            # The images are files of the package that the models share, not copies inside each model.
            scene["images"] = images
            scene["textures"] = [{"source": i, "sampler": 0} for i in range(len(images))]
            scene["samplers"] = [{"wrapS": 10497, "wrapT": 10497}]
        text = json.dumps(scene, separators=(",", ":")).encode()
        text += b" " * (-len(text) % 4)
        binary += b"\0" * (-len(binary) % 4)
        with open(filename, "wb") as f:
            f.write(struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(text) + 8 + len(binary)))
            f.write(struct.pack("<II", len(text), 0x4E4F534A) + text)
            f.write(struct.pack("<II", len(binary), 0x004E4942) + bytes(binary))


def move_origin(model, at):
    """Moves a model drawn in the frame of a building so that the point at becomes its origin (for moving parts)."""
    for positions, _ in model.parts.values():
        positions[:] = [tuple(p[k] - at[k] for k in range(3)) for p in positions]


def rotated_z(model, quarter_turns):
    """Turns a model by quarter turns around the z axis (counter-clockwise seen from above)."""
    for positions, normals in model.parts.values():
        for lst in (positions, normals):
            for _ in range(quarter_turns % 4):
                lst[:] = [(-p[1], p[0], p[2]) for p in lst]
