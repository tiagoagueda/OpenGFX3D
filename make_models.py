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
