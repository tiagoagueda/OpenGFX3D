#!/usr/bin/env python3
"""Draw pictures of models, to check them without starting the game.

    python3 preview.py house.glb church.glb -o preview.png

Each model is drawn twice: from the angle of the 2D game (looking from the south, 30 degrees down)
and from the opposite side. A grid shows the tile (16 by 16) under the model; company colour parts
are drawn in blue and loads are drawn as if the vehicle is full.
"""

import argparse
import json
import math
import struct

from PIL import Image, ImageDraw

SUN = (-0.4683, 0.5620, 0.6817)


def read_glb(path):
    data = open(path, "rb").read()
    length, kind = struct.unpack_from("<II", data, 12)
    scene = json.loads(data[20:20 + length])
    pos = 20 + length
    blen, _ = struct.unpack_from("<II", data, pos)
    binary = data[pos + 8:pos + 8 + blen]

    def accessor(i):
        a = scene["accessors"][i]
        v = scene["bufferViews"][a["bufferView"]]
        off = v.get("byteOffset", 0) + a.get("byteOffset", 0)
        n = a["count"]
        if a["type"] == "VEC3":
            return [struct.unpack_from("<3f", binary, off + 12 * k) for k in range(n)]
        fmt = {5121: "B", 5123: "H", 5125: "I"}[a["componentType"]]
        size = struct.calcsize(fmt)
        return [struct.unpack_from("<" + fmt, binary, off + size * k)[0] for k in range(n)]

    triangles = []
    for mesh in scene["meshes"]:
        for prim in mesh["primitives"]:
            p = accessor(prim["attributes"]["POSITION"])
            idx = accessor(prim["indices"]) if "indices" in prim else list(range(len(p)))
            mat = scene["materials"][prim["material"]] if "material" in prim else {}
            name = mat.get("name", "")
            c = mat.get("pbrMetallicRoughness", {}).get("baseColorFactor", [0.8, 0.8, 0.8, 1])
            c = [x ** (1 / 2.2) for x in c[:3]]
            if name.startswith("company"):
                c = [c[0] * 0.25, c[1] * 0.45, c[2] * 0.95]
            # glTF (x left, y up, z front) to the game frame (front, left, up).
            q = [(v[2], v[0], v[1]) for v in p]
            for k in range(0, len(idx) - 2, 3):
                triangles.append(((q[idx[k]], q[idx[k + 1]], q[idx[k + 2]]), c))
    return triangles


def draw(triangles, yaw, size, scale):
    img = Image.new("RGB", (size, size), (70, 110, 60))
    d = ImageDraw.Draw(img)
    pitch = math.radians(30)
    cy, sy = math.cos(yaw), math.sin(yaw)

    def project(p):
        # Camera looks along (cos yaw, sin yaw) on the map, tilted down by the pitch.
        x, y, z = p
        right = x * sy - y * cy
        depth = x * cy + y * sy
        up = z * math.cos(pitch) + depth * math.sin(pitch)
        dist = depth * math.cos(pitch) - z * math.sin(pitch)
        return (size / 2 + right * scale, size * 0.62 - up * scale, dist)

    for i in range(-8, 9, 4):
        for a, b in (((i, -8, 0), (i, 8, 0)), ((-8, i, 0), (8, i, 0))):
            pa, pb = project(a), project(b)
            d.line([pa[:2], pb[:2]], fill=(95, 140, 80))
    faces = []
    for (a, b, c), colour in triangles:
        u = [b[i] - a[i] for i in range(3)]
        v = [c[i] - a[i] for i in range(3)]
        n = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]]
        ln = math.sqrt(sum(x * x for x in n)) or 1
        n = [x / ln for x in n]
        pa, pb, pc = project(a), project(b), project(c)
        # Back faces point away from the camera.
        area = (pb[0] - pa[0]) * (pc[1] - pa[1]) - (pb[1] - pa[1]) * (pc[0] - pa[0])
        if area >= 0:
            continue
        light = 0.45 + 0.8 * max(0.0, sum(n[i] * SUN[i] for i in range(3)))
        col = tuple(int(max(0, min(255, ch * light * 255))) for ch in colour)
        faces.append(((pa[2] + pb[2] + pc[2]) / 3, [pa[:2], pb[:2], pc[:2]], col))
    faces.sort(key=lambda f: -f[0])
    for _, poly, col in faces:
        d.polygon(poly, fill=col)
    return img


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("models", nargs="+")
    parser.add_argument("-o", "--output", default="preview.png")
    parser.add_argument("--size", type=int, default=320)
    parser.add_argument("--scale", type=float, default=0, help="pixels per world unit; 0 fits a tile")
    args = parser.parse_args()
    scale = args.scale or args.size / 30
    sheet = Image.new("RGB", (args.size * 2, args.size * len(args.models)), (0, 0, 0))
    for row, path in enumerate(args.models):
        triangles = read_glb(path)
        for col, yaw in enumerate((math.radians(225), math.radians(45))):
            img = draw(triangles, yaw, args.size, scale)
            ImageDraw.Draw(img).text((4, 4), path + (" (2D angle)" if col == 0 else " (back)"), fill=(255, 255, 255))
            sheet.paste(img, (col * args.size, row * args.size))
    sheet.save(args.output)


if __name__ == "__main__":
    main()
