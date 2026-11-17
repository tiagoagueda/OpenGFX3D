#!/usr/bin/env python3
"""Make the sample models of the OpenGFX3D package.

The models are simple shapes written straight to binary glTF files, so they need no modelling program:

    python3 make_models.py

Shapes are described with x towards the front of the vehicle, y to its left and z up, in world units
(a tile is 16 long), with the ground at z = 0 and the middle of the vehicle at x = y = 0.
"""

import json
import math
import struct

# Colours as seen on screen, 0 to 1. "company" is multiplied with the colour of the owner.
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
}


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

    def save(self, filename):
        binary = bytearray()
        views, accessors, materials, primitives = [], [], [], []

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

        for name, (positions, normals) in self.parts.items():
            # glTF stores colours as amounts of light, not as seen on screen.
            colour = [round(c ** 2.2, 4) for c in MATERIALS[name]] + [1.0]
            materials.append({"name": name, "pbrMetallicRoughness": {"baseColorFactor": colour, "metallicFactor": 0.0, "roughnessFactor": 0.8}})
            primitives.append({"attributes": {"POSITION": add(positions), "NORMAL": add(normals)}, "material": len(materials) - 1})

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
        text = json.dumps(scene, separators=(",", ":")).encode()
        text += b" " * (-len(text) % 4)
        binary += b"\0" * (-len(binary) % 4)
        with open(filename, "wb") as f:
            f.write(struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(text) + 8 + len(binary)))
            f.write(struct.pack("<II", len(text), 0x4E4F534A) + text)
            f.write(struct.pack("<II", len(binary), 0x004E4942) + bytes(binary))


def bus():
    m = Model()
    length, width = 9.0, 3.2
    x0, x1, y0, y1 = -length / 2, length / 2, -width / 2, width / 2
    m.box("dark", x0 + 0.1, x1 - 0.1, y0 + 0.15, y1 - 0.15, 0.45, 0.8)  # underside
    m.box("company", x0, x1, y0, y1, 0.8, 2.0)  # lower body
    m.box("glass", x0 + 0.08, x1 - 0.08, y0 + 0.08, y1 - 0.08, 2.0, 3.0)  # windows
    m.box("roof", x0, x1, y0, y1, 3.0, 3.3)
    m.box("roof", x0 + 0.5, x1 - 0.5, y0 + 0.4, y1 - 0.4, 3.3, 3.42)
    # Pillars between the windows, and the corners.
    for i in range(7):
        x = x0 + i * (length - 0.3) / 6
        for y in (y0, y1 - 0.12):
            m.box("company", x, x + 0.3, y, y + 0.12, 2.0, 3.0)
    for y in (y0, y1 - 0.3):
        m.box("company", x0, x0 + 0.12, y, y + 0.3, 2.0, 3.0)
        m.box("company", x1 - 0.12, x1, y, y + 0.3, 2.0, 3.0)
    m.box("company_dark", x0, x0 + 0.12, y0, y1, 2.0, 2.3)  # below the rear window
    # Bumpers and lights.
    m.box("dark", x1, x1 + 0.15, y0, y1, 0.7, 1.05)
    m.box("dark", x0 - 0.15, x0, y0, y1, 0.7, 1.05)
    for y in (y0 + 0.2, y1 - 0.7):
        m.box("light", x1, x1 + 0.06, y, y + 0.5, 1.2, 1.55)
    for x in (-2.7, 2.7):
        for y in (y0 + 0.2, y1 - 0.2):
            m.wheel(x, y, 0.62, 0.45)
    m.save("bus.glb")


def lorry():
    m = Model()
    length, width = 9.0, 3.1
    x0, x1, y0, y1 = -length / 2, length / 2, -width / 2, width / 2
    m.box("dark", x0, x1 - 0.1, y0 + 0.3, y1 - 0.3, 0.55, 1.0)  # chassis
    # Cab.
    m.box("company", x1 - 2.2, x1, y0, y1, 0.8, 1.9)
    m.box("glass", x1 - 2.1, x1 - 0.06, y0 + 0.06, y1 - 0.06, 1.9, 2.75)
    m.box("company", x1 - 2.2, x1, y0, y1, 2.75, 2.95)
    m.box("company", x1 - 2.2, x1 - 1.9, y0, y1, 1.9, 2.75)  # back of the cab
    for y in (y0, y1 - 0.14):
        m.box("company", x1 - 0.14, x1, y, y + 0.14, 1.9, 2.75)
    m.box("dark", x1, x1 + 0.15, y0, y1, 0.7, 1.05)
    for y in (y0 + 0.2, y1 - 0.7):
        m.box("light", x1, x1 + 0.06, y, y + 0.5, 1.2, 1.5)
    # Load.
    m.box("cargo", x0, x1 - 2.5, y0, y1, 1.0, 3.3)
    m.box("cargo_dark", x0 - 0.04, x0, y0 + 0.2, y1 - 0.2, 1.2, 3.1)  # doors
    for x in (-3.0, -1.6, 3.0):
        for y in (y0 + 0.2, y1 - 0.2):
            m.wheel(x, y, 0.62, 0.45)
    m.save("lorry.glb")


# Rail vehicles of the usual length are 8 long, half a tile; the models are a little shorter so that
# there is a gap between them. The rails are about 2.4 apart, the floor of a carriage is at about 1.


def rail_wheels(m, xs, radius=0.5):
    for x in xs:
        for y in (-1.2, 1.2):
            m.wheel(x, y, radius, 0.25)


def bogie(m, x):
    m.box("dark", x - 1.1, x + 1.1, -1.05, 1.05, 0.35, 0.8)
    rail_wheels(m, (x - 0.6, x + 0.6), 0.42)


def buffers(m, x0, x1, z=1.05):
    for x, d in ((x0, -0.35), (x1, 0.35)):
        m.box("dark", min(x, x + d), max(x, x + d), -1.5, 1.5, z - 0.25, z + 0.25)
        for y in (-1.0, 1.0):
            m.box("metal", min(x + d, x + 1.6 * d), max(x + d, x + 1.6 * d), y - 0.18, y + 0.18, z - 0.18, z + 0.18)


def steam_engine():
    """A tank engine: boiler in front, cab at the back, three coupled driving wheels."""
    m = Model()
    x0, x1 = -3.6, 3.6
    m.box("dark", x0, x1, -1.45, 1.45, 0.9, 1.25)  # running board
    m.box("dark", x0 + 0.3, x1 - 0.3, -0.8, 0.8, 0.45, 0.9)  # frame
    m.cylinder("company", -0.4, 3.0, 0, 2.05, 0.95, caps="boiler")
    m.cylinder("boiler", 3.0, 3.6, 0, 2.05, 1.0)  # smokebox
    for x in (0.4, 1.6):
        m.cylinder("brass", x - 0.08, x + 0.08, 0, 2.05, 0.98)  # bands
    m.chimney("boiler", 3.15, 0, 2.6, 3.9, 0.32)
    m.chimney("brass", 1.3, 0, 2.6, 3.35, 0.38)  # dome
    # Side tanks along the boiler.
    for y0, y1 in ((-1.4, -0.75), (0.75, 1.4)):
        m.box("company_dark", 0.0, 2.4, y0, y1, 1.25, 2.4)
    # Cab and coal bunker.
    m.box("company", -2.6, -0.4, -1.45, 1.45, 1.25, 3.1)
    m.box("glass", -1.6, -0.6, -1.5, 1.5, 2.2, 2.9)
    m.box("glass", -0.45, -0.35, -1.0, -0.4, 2.3, 2.9)
    m.box("glass", -0.45, -0.35, 0.4, 1.0, 2.3, 2.9)
    m.box("roof", -2.8, -0.2, -1.55, 1.55, 3.1, 3.35)
    m.box("company_dark", x0, -2.6, -1.3, 1.3, 1.25, 2.4)
    m.box("boiler", x0 + 0.1, -2.7, -1.1, 1.1, 2.4, 2.65)  # coal
    m.box("light", x1, x1 + 0.08, -0.25, 0.25, 2.5, 2.9)
    rail_wheels(m, (-2.9,), 0.45)
    rail_wheels(m, (-1.5, 0.0, 1.5), 0.68)
    rail_wheels(m, (3.0,), 0.45)
    # Rods joining the driving wheels.
    for y in (-1.36, 1.36):
        m.box("metal", -1.5, 1.5, y - 0.04, y + 0.04, 0.6, 0.72)
    buffers(m, x0, x1)
    m.save("steam_engine.glb")


def diesel_engine(electric=False):
    """A diesel with a cab at each end; with electric, a pantograph on the roof."""
    m = Model()
    x0, x1 = -3.8, 3.8
    m.box("dark", x0, x1, -1.4, 1.4, 0.85, 1.15)  # frame
    m.box("company", x0 + 0.1, x1 - 0.1, -1.45, 1.45, 1.15, 3.2)
    m.box("company_dark", x0 + 0.1, x1 - 0.1, -1.47, 1.47, 1.15, 1.6)  # stripe at the bottom
    m.box("roof", x0 + 0.3, x1 - 0.3, -1.25, 1.25, 3.2, 3.5)
    for x, d in ((x0 + 0.1, -1), (x1 - 0.1, 1)):
        m.box("glass", min(x, x + 0.06 * d), max(x, x + 0.06 * d), -1.2, 1.2, 2.3, 2.95)  # windscreen
        m.box("glass", min(x, x - 0.9 * d), max(x, x - 0.9 * d), -1.5, 1.5, 2.3, 2.9)  # side windows of the cab
        m.box("light", min(x, x + 0.08 * d), max(x, x + 0.08 * d), -1.0, -0.6, 1.5, 1.8)
        m.box("light", min(x, x + 0.08 * d), max(x, x + 0.08 * d), 0.6, 1.0, 1.5, 1.8)
    # Grilles along the engine room.
    for i in range(5):
        x = -1.9 + i * 0.85
        m.box("dark", x, x + 0.5, -1.5, 1.5, 2.4, 2.9)
    if electric:
        m.box("dark", -0.6, 0.6, -0.6, 0.6, 3.5, 3.65)
        m.quad("metal", (-0.5, -0.5, 3.65), (0.5, -0.5, 3.65), (0.1, -0.5, 4.6), (-0.1, -0.5, 4.6))
        m.quad("metal", (0.5, 0.5, 3.65), (-0.5, 0.5, 3.65), (-0.1, 0.5, 4.6), (0.1, 0.5, 4.6))
        m.box("metal", -0.12, 0.12, -0.9, 0.9, 4.55, 4.7)
    else:
        m.chimney("dark", 0.5, 0, 3.5, 3.8, 0.2)  # exhaust
    bogie(m, -2.4)
    bogie(m, 2.4)
    buffers(m, x0, x1)
    m.save("electric_engine.glb" if electric else "diesel_engine.glb")


def carriage(m, x0, x1, cab=False):
    """The body of a passenger carriage, with a row of windows."""
    m.box("dark", x0 + 0.2, x1 - 0.2, -1.3, 1.3, 0.85, 1.1)
    m.box("company", x0, x1, -1.45, 1.45, 1.1, 2.1)
    m.box("glass", x0 + 0.05, x1 - 0.05, -1.43, 1.43, 2.1, 2.8)
    m.box("company", x0, x1, -1.45, 1.45, 2.8, 3.1)
    # Pillars between the windows.
    count = 7
    for i in range(count + 1):
        x = x0 + i * (x1 - x0 - 0.25) / count
        m.box("company", x, x + 0.25, -1.45, 1.45, 2.1, 2.8)
    m.prism_roof("roof", "roof", x0, x1, -1.45, 1.45, 3.1, 3.55)
    if cab:
        m.box("glass", x1, x1 + 0.06, -1.1, 1.1, 2.15, 2.75)
        m.box("light", x1, x1 + 0.08, -1.0, -0.6, 1.4, 1.7)
        m.box("light", x1, x1 + 0.08, 0.6, 1.0, 1.4, 1.7)


def passenger_carriage():
    m = Model()
    carriage(m, -3.7, 3.7)
    bogie(m, -2.5)
    bogie(m, 2.5)
    buffers(m, -3.7, 3.7)
    m.save("passenger_carriage.glb")


def railcar():
    """A diesel railcar: a carriage with a driving cab at the front."""
    m = Model()
    carriage(m, -3.7, 3.7, cab=True)
    m.box("dark", -1.2, 1.2, -1.0, 1.0, 0.45, 0.85)  # engine below the floor
    bogie(m, -2.5)
    bogie(m, 2.5)
    buffers(m, -3.7, 3.7)
    m.save("railcar.glb")


def van(material, filename, doors="company_dark", vents=False):
    """A covered goods van with a curved roof and sliding doors."""
    m = Model()
    x0, x1 = -3.6, 3.6
    m.box("dark", x0, x1, -1.3, 1.3, 0.85, 1.1)
    m.box(material, x0 + 0.1, x1 - 0.1, -1.4, 1.4, 1.1, 3.0)
    m.prism_roof("roof", material, x0, x1, -1.5, 1.5, 3.0, 3.4)
    m.box(doors, -0.8, 0.8, -1.46, 1.46, 1.2, 2.85)
    if vents:
        for x in (-2.6, -1.8, 1.8, 2.6):
            m.box("dark", x - 0.25, x + 0.25, -1.45, 1.45, 2.4, 2.8)
    # The company's colour as a stripe.
    m.box("company", x0 + 0.1, x1 - 0.1, -1.42, 1.42, 1.1, 1.3)
    rail_wheels(m, (-2.2, 2.2))
    buffers(m, x0, x1)
    m.save(filename)


def open_wagon():
    """An open wagon with low sides, for coal, wood and steel."""
    m = Model()
    x0, x1 = -3.6, 3.6
    m.box("dark", x0, x1, -1.3, 1.3, 0.85, 1.1)
    m.box("rust", x0 + 0.1, x1 - 0.1, -1.4, 1.4, 1.1, 1.3)  # floor
    for y0, y1 in ((-1.4, -1.25), (1.25, 1.4)):
        m.box("company_dark", x0 + 0.1, x1 - 0.1, y0, y1, 1.3, 2.3)
    for xa, xb in ((x0 + 0.1, x0 + 0.25), (x1 - 0.25, x1 - 0.1)):
        m.box("company_dark", xa, xb, -1.25, 1.25, 1.3, 2.3)
    for x in (-2.0, 0.0, 2.0):
        for y in (-1.45, 1.4):
            m.box("dark", x - 0.1, x + 0.1, y, y + 0.05, 1.3, 2.3)  # ribs
    rail_wheels(m, (-2.2, 2.2))
    buffers(m, x0, x1)
    m.save("open_wagon.glb")


def hopper():
    """A hopper wagon for grain and ore, with sloping ends and chutes below."""
    m = Model()
    x0, x1 = -3.6, 3.6
    m.box("dark", x0, x1, -1.2, 1.2, 0.85, 1.1)
    m.box("company_dark", x0 + 0.6, x1 - 0.6, -1.4, 1.4, 1.1, 2.9)
    # Sloping ends.
    for xa, xb in ((x0 + 0.1, x0 + 0.6), (x1 - 0.6, x1 - 0.1)):
        top_out, bottom_in = (xa, xb) if xa < 0 else (xb, xa)
        m.quad("company_dark", (top_out, -1.4, 2.9), (bottom_in, -1.4, 1.4), (bottom_in, 1.4, 1.4), (top_out, 1.4, 2.9))
        m.quad("company_dark", (top_out, 1.4, 2.9), (bottom_in, 1.4, 1.4), (bottom_in, -1.4, 1.4), (top_out, -1.4, 2.9))
    m.box("dark", x0 + 0.6, x1 - 0.6, -1.42, 1.42, 2.75, 2.95)  # top edge
    for x in (-1.0, 1.0):
        m.box("dark", x - 0.4, x + 0.4, -0.6, 0.6, 0.6, 1.1)  # chutes
    rail_wheels(m, (-2.6, 2.6))
    buffers(m, x0, x1)
    m.save("hopper.glb")


def tanker():
    """A tank wagon."""
    m = Model()
    x0, x1 = -3.6, 3.6
    m.box("dark", x0, x1, -1.2, 1.2, 0.85, 1.25)
    m.cylinder("boiler", x0 + 0.2, x1 - 0.2, 0, 2.2, 1.05, sides=16)
    m.cylinder("company", -0.15, 0.15, 0, 2.2, 1.08, sides=16)  # band in the company colour
    m.chimney("boiler", 0, 0, 3.0, 3.45, 0.4)  # filler
    for x in (-2.0, 2.0):
        m.box("dark", x - 0.1, x + 0.1, -1.15, 1.15, 1.2, 1.6)  # cradles
    rail_wheels(m, (-2.3, 2.3))
    buffers(m, x0, x1)
    m.save("tanker.glb")


# Buildings stand on a whole tile, 16 by 16, with the middle of the tile at the origin.
# Heights: one storey is about 3.3, which is how high the 2D game draws one floor.


def house():
    """A small house with a pitched roof; the walls take the colour of the house."""
    m = Model()
    m.box("company", -5, 5, -4, 4, 0, 4.6)
    m.box("concrete", -5.2, 5.2, -4.2, 4.2, 0, 0.4)
    m.prism_roof("tiles", "company", -5.6, 5.6, -4.7, 4.7, 4.6, 8.2)
    m.box("brick", 2.2, 3.2, -1.8, -0.8, 6.0, 9.0)  # chimney
    m.windows("glass", -5, 5, -4, 4, 0.6, 4.4, 2, 3, size=(1.1, 1.2))
    m.box("door", 4.98, 5.1, -0.6, 0.6, 0.3, 2.3)
    m.box("grass", -7, 7, -7, 7, 0, 0.05)
    m.save("house.glb")


def flats():
    """A block of flats of three storeys with a flat roof."""
    m = Model()
    m.box("company", -6, 6, -6, 6, 0, 10)
    m.box("concrete", -6.2, 6.2, -6.2, 6.2, 10, 10.6)
    m.box("metal", -2, 1, -1.5, 1.5, 10.6, 11.8)  # roof housing
    m.windows("glass", -6, 6, -6, 6, 0.4, 10, 3, 4, size=(1.6, 1.6))
    for z in (3.3, 6.6):
        m.box("concrete", -6.1, 6.1, -6.1, 6.1, z - 0.15, z + 0.15)
    m.save("flats.glb")


def office_tower():
    """A tall office tower with bands of windows."""
    m = Model()
    m.box("concrete", -5, 5, -5, 5, 0, 1.2)
    m.box("glass", -4.5, 4.5, -4.5, 4.5, 1.2, 26)
    for i in range(8):
        z = 1.2 + 3.1 * (i + 1)
        m.box("company", -4.7, 4.7, -4.7, 4.7, z - 0.5, z)
    for x in (-4.7, 4.1):
        for y in (-4.7, 4.1):
            m.box("company", x, x + 0.6, y, y + 0.6, 1.2, 26)
    m.box("concrete", -4.8, 4.8, -4.8, 4.8, 26, 26.6)
    m.box("metal", -1.5, 1.5, -1.5, 1.5, 26.6, 28.5)
    m.save("office_tower.glb")


def shops():
    """Shops on the ground floor with offices above, and an awning in the colour of the shop."""
    m = Model()
    m.box("brick", -6, 6, -5.5, 5.5, 0, 7)
    m.box("glass", -6.08, 6.08, -5.58, 5.58, 0.4, 2.8)  # shop windows
    m.box("brick", -6.1, 6.1, -5.6, 5.6, 2.8, 3.3)
    m.windows("glass", -6, 6, -5.5, 5.5, 3.3, 7, 1, 4, size=(1.3, 1.6))
    m.box("concrete", -6.2, 6.2, -5.7, 5.7, 7, 7.5)
    for (x0, x1, y0, y1) in ((6.1, 7.6, -5.5, 5.5), (-6, 6, -7.1, -5.6)):
        m.box("company", x0, x1, y0, y1, 2.9, 3.2)
    m.save("shops.glb")


def church():
    """A church with a nave and a tower with a spire."""
    m = Model()
    m.box("stone", -6, 4, -3.5, 3.5, 0, 6)
    m.prism_roof("slate", "stone", -6.3, 4.3, -4, 4, 6, 9.5)
    m.box("stone", 4, 7.5, -1.75, 1.75, 0, 14)
    m.pyramid("slate", 3.8, 7.7, -1.95, 1.95, 14, 21)
    for x in (-4.5, -2, 0.5, 3):
        for y in (-3.58, 3.5):
            m.box("glass", x - 0.4, x + 0.4, y, y + 0.08, 2, 5)
    m.box("door", 7.5, 7.6, -0.6, 0.6, 0, 2.6)
    m.box("grass", -7.5, 7.8, -7, 7, 0, 0.05)
    m.save("church.glb")


def factory_hall():
    """One tile of a factory hall with a sawtooth roof; several of them make the factory."""
    m = Model()
    m.box("brick", -8, 8, -8, 8, 0, 6)
    for i in range(4):
        y0 = -8 + i * 4
        m.quad("slate", (-8, y0, 6), (8, y0, 6), (8, y0 + 4, 8.5), (-8, y0 + 4, 8.5))
        m.quad("glass", (8, y0 + 4, 6), (-8, y0 + 4, 6), (-8, y0 + 4, 8.5), (8, y0 + 4, 8.5))
        m.triangle("brick", (8, y0, 6), (8, y0 + 4, 6), (8, y0 + 4, 8.5))
        m.triangle("brick", (-8, y0 + 4, 6), (-8, y0, 6), (-8, y0 + 4, 8.5))
    m.windows("glass", -8, 8, -8, 8, 1, 5, 1, 4, size=(2.2, 2.4))
    m.save("factory_hall.glb")


def factory_chimney():
    """A factory tile with a lower building and a tall chimney."""
    m = Model()
    m.box("brick", -8, 8, -8, 2, 0, 6)
    m.prism_roof("slate", "brick", -8, 8, -8, 2, 6, 8)
    m.box("concrete", -8, 8, 2, 8, 0, 0.2)
    m.box("brick", 3, 6, 3, 6, 0, 22)
    m.box("dark", 2.8, 6.2, 2.8, 6.2, 21, 22.2)
    m.box("company", 2.9, 6.1, 2.9, 6.1, 16, 17)
    m.windows("glass", -8, 8, -8, 2, 1, 5, 1, 4, size=(2.0, 2.4))
    m.save("factory_chimney.glb")


def platforms(m, building=False):
    """Two platforms along a track that runs front to back; the building side is on the right (negative y)."""
    m.box("platform", -8, 8, -8, -3, 0, 0.9)
    m.box("edge", -8, 8, -3.3, -3, 0.9, 0.95)
    m.box("platform", -8, 8, 3, 8, 0, 0.9)
    m.box("edge", -8, 8, 3, 3.3, 0.9, 0.95)
    if building:
        m.box("wall", -7, 7, -8, -4.4, 0.9, 5.4)
        m.box("company", -7.3, 7.3, -8.2, -4.1, 5.4, 6.0)
        m.box("glass", -6, 6, -4.48, -4.4, 1.6, 4.4)
        m.box("door", -0.8, 0.8, -4.45, -4.35, 0.9, 3.4)


def station_platform():
    m = Model()
    platforms(m)
    for x in (-5, 5):
        for y in (-5.5, 5.5):
            m.box("metal", x - 0.12, x + 0.12, y - 0.12, y + 0.12, 0.9, 2.8)
            m.box("company", x - 0.5, x + 0.5, y - 0.05, y + 0.05, 2.3, 2.8)
    m.save("station_platform.glb")


def station_building():
    m = Model()
    platforms(m, building=True)
    m.box("company", -6, 6, 6.8, 7.0, 0.9, 1.0)
    m.save("station_building.glb")


def station_roof():
    m = Model()
    platforms(m)
    for x in (-6, 0, 6):
        for y in (-5.5, 5.5):
            m.box("company", x - 0.2, x + 0.2, y - 0.2, y + 0.2, 0.9, 6.5)
    m.box("company", -8, 8, -8.2, 8.2, 6.5, 6.9)
    m.prism_roof("glass", "company", -8, 8, -8.2, 8.2, 6.9, 8.6)
    m.save("station_roof.glb")


def bus_stop(drive_through=False):
    """A bus shelter. A stop off the road has its front towards the road; one on the road has the road front to back."""
    m = Model()

    def shelter(x0, x1, y0, y1, open_side):
        m.box("concrete", x0, x1, y0, y1, 0, 0.3)
        m.box("company", x0, x1, y0, y1, 3.2, 3.5)
        for (px, py) in ((x0, y0), (x1 - 0.2, y0), (x0, y1 - 0.2), (x1 - 0.2, y1 - 0.2)):
            m.box("metal", px, px + 0.2, py, py + 0.2, 0.3, 3.2)
        if open_side != "back":
            m.box("glass", x0, x0 + 0.1, y0, y1, 0.6, 3.0)
        m.box("dark", (x0 + x1) / 2 - 0.15, (x0 + x1) / 2 + 0.15, y0 + 0.4, y1 - 0.4, 0.3, 1.0)
        m.box("company", (x0 + x1) / 2 - 0.1, (x0 + x1) / 2 + 0.1, y1 + 0.2, y1 + 0.4, 0, 4.4)

    if drive_through:
        shelter(-3, 0, -7.6, -6, "side")
        shelter(0, 3, 6, 7.6, "side")
    else:
        m.box("concrete", -8, -4, -8, 8, 0, 0.25)
        shelter(-7.6, -5.6, -5, 5, "front")
    m.save("bus_stop_drive_through.glb" if drive_through else "bus_stop.glb")


def lorry_stop(drive_through=False):
    """A loading bay with a canopy over the place where lorries stop."""
    m = Model()
    if drive_through:
        for y in (-7.4, 7.0):
            for x in (-6, 6):
                m.box("metal", x - 0.2, x + 0.2, y, y + 0.4, 0, 6)
        m.box("company", -7, 7, -7.6, 7.6, 6, 6.5)
    else:
        m.box("concrete", -8, -4.5, -8, 8, 0, 1.4)  # loading dock
        m.box("cargo", -8, -6, -7, 7, 1.4, 4.0)
        for y in (-7.4, 7.0):
            m.box("metal", 5.4, 5.8, y, y + 0.4, 0, 6)
        m.box("company", -8, 6.5, -7.6, 7.6, 6, 6.5)
    m.save("lorry_stop_drive_through.glb" if drive_through else "lorry_stop.glb")


if __name__ == "__main__":
    bus()
    lorry()
    steam_engine()
    diesel_engine()
    diesel_engine(electric=True)
    passenger_carriage()
    railcar()
    van("company_dark", "mail_van.glb", doors="dark")
    van("wood", "goods_van.glb", vents=True)
    open_wagon()
    hopper()
    tanker()
    house()
    flats()
    office_tower()
    shops()
    church()
    factory_hall()
    factory_chimney()
    station_platform()
    station_building()
    station_roof()
    bus_stop()
    bus_stop(drive_through=True)
    lorry_stop()
    lorry_stop(drive_through=True)
