#!/usr/bin/env python3
"""Draw 2D sprites of the power line models, for the 2D view of the game, and pack them into a base GRF.

    python3 make_sprites.py path/to/src/table/palettes.h -o power.grf [--png sheet.png]

The models are drawn the way the 2D game sees the world: from the south, with x to the lower left,
y to the lower right and z up, 64 pixels to a tile at normal zoom. Every sprite gets an 8 bpp version
at normal zoom (for the 8 bpp blitters) and 32 bpp versions at normal, 2x and 4x zoom.

The order of the sprites must match SPR_POWER_* in the game (src/table/sprites.h):
  0-3   pylon, the line along x, along y, along the N-S diagonal, along the E-W diagonal
  4-5   overhead substation, gantry taking wires along x, along y
  6     underground substation
  7-10  transition pylon, in the same four directions as the pylon
  11-14 wires over one tile: along x, along y, along the N-S diagonal, along the E-W diagonal
  15-22 wires from the middle of a tile to its edge, towards N, NE, E, SE, S, SW, W, NW
  23    cable marker post, in the middle of the tile
  24-31 underground cable as the power network view shows it, from the middle of a tile to its edge,
        towards N, NE, E, SE, S, SW, W, NW
  32-39 industry tiles 175 to 182 of the power plants (models_power_plants.py), without their ground plate:
        oil turbine hall, oil tanks, solar panels, solar inverter house, wind turbine (rotor standing still),
        dam across a river along x, dam across a river along y, hydro powerhouse
  40-46 toolbar icons: build line, pylon, overhead substation, transition pylon, underground cable,
        underground substation, power network view (drawn small, with their top left corner as origin)
  47-52 mouse cursors for the same tools as 40-45 (origin at the middle of their foot)
  53-55 status lights over substations and plant connections: green (energy flows), yellow (on a
        network, but nothing flows), red (not joined to any plant or consumer)

Sprites are drawn relative to the north corner of their tile at the height of its foot (the game
draws them with that point as their origin). Wires are drawn with their conductors at height 0;
the game draws them at the height of the line.
"""

import argparse
import math
import re
import struct

import numpy as np

import models_power
from preview import read_glb

SUN = np.array([-0.4683, 0.5620, 0.6817])
Z_PER_PIXEL = 0.40824829  # world units per pixel of height in the 2D game
WIRE_Z = models_power.WIRE_Z
PHASE = models_power.PHASE
EARTH_Z = models_power.TOP


def rotated(triangles, heading, at):
    """Turn the triangles so x points along heading (an angle in radians on the map) and move them to at."""
    c, s = math.cos(heading), math.sin(heading)
    out = []
    for tri, colour in triangles:
        out.append((tuple((at[0] + p[0] * c - p[1] * s, at[1] + p[0] * s + p[1] * c, at[2] + p[2]) for p in tri), colour))
    return out


def wire_triangles(direction, half=False):
    """Wires along a direction given as (dx, dy) per tile; conductors at height 0, the earth wire above.
    Over the whole tile, through its middle; or with half, from the middle of the tile to its edge."""
    dx, dy = direction
    length = math.hypot(dx, dy) * 16
    ux, uy = dx * 16 / length, dy * 16 / length
    start, end = (0.0, length / 2) if half else (-length / 2, length / 2)
    tris = []
    colour = (0.30, 0.29, 0.27)
    r = 0.12
    for offset, z in ((-PHASE, 0.0), (0.0, 0.0), (PHASE, 0.0), (0.0, EARTH_Z - WIRE_Z)):
        cx, cy = 8 - uy * offset, 8 + ux * offset
        a = (cx + ux * start, cy + uy * start)
        b = (cx + ux * end, cy + uy * end)
        # A thin square tube.
        px, py = -uy * r, ux * r
        corners = []
        for p in (a, b):
            corners.append([(p[0] + sx * px, p[1] + sx * py, z + sz * r) for sx, sz in ((1, 1), (-1, 1), (-1, -1), (1, -1))])
        for k in range(4):
            q = [corners[0][k], corners[0][(k + 1) % 4], corners[1][(k + 1) % 4], corners[1][k]]
            tris.append(((q[0], q[1], q[2]), colour))
            tris.append(((q[0], q[2], q[3]), colour))
    return tris


def rasterise(triangles, scale, aa):
    """Draw triangles in the projection of the 2D game; returns an RGBA image (float) and the offset of its top left pixel."""
    f = scale * aa
    pts = []
    for tri, colour in triangles:
        for p in tri:
            pts.append(p)
    pts = np.array(pts)
    sx = 2 * (pts[:, 1] - pts[:, 0]) * f
    sy = (pts[:, 0] + pts[:, 1] - pts[:, 2] / Z_PER_PIXEL) * f
    x0 = math.floor(sx.min() / f) * f - aa
    y0 = math.floor(sy.min() / f) * f - aa
    w = int(math.ceil((sx.max() - x0) / aa)) * aa + 2 * aa
    h = int(math.ceil((sy.max() - y0) / aa)) * aa + 2 * aa
    colour_buf = np.zeros((h, w, 3))
    alpha = np.zeros((h, w))
    depth = np.full((h, w), -1e30)

    for i, (tri, colour) in enumerate(triangles):
        P = np.array(tri)
        X = 2 * (P[:, 1] - P[:, 0]) * f - x0
        Y = (P[:, 0] + P[:, 1] - P[:, 2] / Z_PER_PIXEL) * f - y0
        D = P[:, 0] + P[:, 1] + 2 * P[:, 2] / Z_PER_PIXEL
        area = (X[1] - X[0]) * (Y[2] - Y[0]) - (X[2] - X[0]) * (Y[1] - Y[0])
        if abs(area) < 1e-9:
            continue
        n = np.cross(P[1] - P[0], P[2] - P[0])
        ln = np.linalg.norm(n)
        if ln == 0:
            continue
        n = n / ln
        # Towards the viewer is (1, 1, 2 / Z_PER_PIXEL) in world units; draw both sides, lit by the side that faces us.
        view = np.array([1, 1, 2 / Z_PER_PIXEL])
        if n.dot(view) < 0:
            n = -n
        light = 0.50 + 0.65 * max(0.0, float(n.dot(SUN)))
        col = np.clip(np.array(colour) * light, 0, 1)
        bx0, bx1 = max(int(math.floor(X.min())), 0), min(int(math.ceil(X.max())) + 1, w)
        by0, by1 = max(int(math.floor(Y.min())), 0), min(int(math.ceil(Y.max())) + 1, h)
        if bx0 >= bx1 or by0 >= by1:
            continue
        gx, gy = np.meshgrid(np.arange(bx0, bx1) + 0.5, np.arange(by0, by1) + 0.5)
        w0 = ((X[1] - gx) * (Y[2] - gy) - (X[2] - gx) * (Y[1] - gy)) / area
        w1 = ((X[2] - gx) * (Y[0] - gy) - (X[0] - gx) * (Y[2] - gy)) / area
        w2 = 1 - w0 - w1
        inside = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
        d = w0 * D[0] + w1 * D[1] + w2 * D[2]
        region = depth[by0:by1, bx0:bx1]
        nearer = inside & (d > region)
        region[nearer] = d[nearer]
        colour_buf[by0:by1, bx0:bx1][nearer] = col
        alpha[by0:by1, bx0:bx1][nearer] = 1.0

    # Average blocks of aa x aa pixels, weighting colour by coverage.
    h2, w2 = h // aa, w // aa
    a = alpha.reshape(h2, aa, w2, aa).mean(axis=(1, 3))
    c = (colour_buf * alpha[..., None]).reshape(h2, aa, w2, aa, 3).sum(axis=(1, 3))
    cover = alpha.reshape(h2, aa, w2, aa).sum(axis=(1, 3))
    with np.errstate(invalid="ignore", divide="ignore"):
        c = np.where(cover[..., None] > 0, c / cover[..., None], 0)
    rgba = np.concatenate([c, a[..., None]], axis=2)
    return rgba, int(round(x0 / aa)), int(round(y0 / aa))


def crop(rgba, xoff, yoff):
    ys, xs = np.nonzero(rgba[..., 3] > 0.02)
    if len(xs) == 0:
        return rgba[:1, :1], xoff, yoff
    return rgba[ys.min():ys.max() + 1, xs.min():xs.max() + 1], xoff + xs.min(), yoff + ys.min()


def read_palette(path):
    text = open(path).read()
    start = text.index("_palette = {")
    body = text[start:text.index("};", start)]
    colours = [(0, 0, 0)] + [tuple(int(v) for v in m) for m in re.findall(r"M\(\s*(\d+),\s*(\d+),\s*(\d+)\)", body)]
    return np.array(colours[:256], dtype=float)


def usable_indices():
    """Palette entries a sprite may use: not transparent, not company colours, not the animated ones at the end."""
    bad = set(range(0xC6, 0xCE)) | set(range(0xD7, 0x100)) | {0}
    return [i for i in range(256) if i not in bad]


def to_8bpp(rgba, palette):
    idx = usable_indices()
    pal = palette[idx]
    rgb = rgba[..., :3] * 255
    flat = rgb.reshape(-1, 3)
    d = ((flat[:, None, :] - pal[None, :, :]) ** 2).sum(axis=2)
    chosen = np.array(idx)[d.argmin(axis=1)].reshape(rgba.shape[:2])
    chosen[rgba[..., 3] < 0.5] = 0
    return chosen.astype(np.uint8)


def literal_stream(data):
    """The GRF sprite compression with only runs of plain bytes."""
    out = bytearray()
    for i in range(0, len(data), 0x80):
        chunk = data[i:i + 0x80]
        out.append(0 if len(chunk) == 0x80 else len(chunk))
        out += chunk
    return bytes(out)


def sprite_entry(sprite_id, colour, zoom, pixels, width, height, xoff, yoff):
    body = struct.pack("<BBHHhh", colour, zoom, height, width, xoff, yoff) + literal_stream(pixels)
    return struct.pack("<II", sprite_id, len(body)) + body


def write_grf(path, sprites):
    """sprites: a list of lists of (colour, zoom, pixels, width, height, xoff, yoff), one list per sprite."""
    data = bytearray()
    graphics = bytearray()
    for n, versions in enumerate(sprites):
        sprite_id = n + 1
        data += struct.pack("<IBI", 4, 0xFD, sprite_id)
        for v in versions:
            graphics += sprite_entry(sprite_id, *v)
    data += struct.pack("<I", 0)
    graphics += struct.pack("<I", 0)
    header = b"\x00\x00GRF\x82\x0d\x0a\x1a\x0a"
    with open(path, "wb") as f:
        f.write(header + struct.pack("<I", 1 + len(data)) + b"\x00" + bytes(data) + bytes(graphics))


def subjects():
    """The sprites, in order: (name, triangles relative to the north corner of the tile)."""
    pylon = read_glb("power_pylon.glb")
    overhead = read_glb("power_substation_overhead.glb")
    underground = read_glb("power_substation_underground.glb")
    transition = read_glb("power_pylon_transition.glb")
    # Directions on the map, as angles: x, y, the N-S diagonal (x and y growing together), the E-W diagonal.
    headings = [0.0, math.pi / 2, math.pi / 4, -math.pi / 4]
    centre = (8.0, 8.0, 0.0)
    out = []
    for i, h in enumerate(headings):
        out.append((f"pylon_{i}", rotated(pylon, h, centre)))
    out.append(("substation_x", rotated(overhead, 0.0, centre)))
    out.append(("substation_y", rotated(overhead, math.pi / 2, centre)))
    out.append(("substation_underground", rotated(underground, 0.0, centre)))
    for i, h in enumerate(headings):
        out.append((f"transition_{i}", rotated(transition, h, centre)))
    for i, d in enumerate(((1, 0), (0, 1), (1, 1), (1, -1))):
        out.append((f"wire_{i}", wire_triangles(d)))
    # Half wires from the middle of a pylon tile to its edge, in the order of the game's Direction: N, NE, E, SE, S, SW, W, NW.
    for i, d in enumerate(((-1, -1), (-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1))):
        out.append((f"half_wire_{i}", wire_triangles(d, half=True)))
    marker = read_glb("power_cable_marker.glb")
    out.append(("cable_marker", rotated(marker, 0.0, (8.0, 8.0, 0.0))))
    cable = read_glb("power_cable_view.glb")
    for i, d in enumerate(((-1, -1), (-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1))):
        # The piece is 16 long and centred; scale it to reach from the middle of the tile to its edge or corner.
        length = math.hypot(*d) * 8
        heading = math.atan2(d[1], d[0])
        scaled = [(tuple((p[0] * length / 16 + length / 2, p[1], p[2]) for p in tri), colour) for tri, colour in cable]
        out.append((f"cable_{i}", rotated(scaled, heading, (8.0, 8.0, 0.0))))
    # Industry tiles of the power plants; the game draws their ground with a ground sprite of its own.
    import models_power_plants as plants

    def without_ground(tris):
        return [(tri, colour) for tri, colour in tris if max(p[2] for p in tri) > 0.07 or min(p[2] for p in tri) < -0.01]

    for name in ("oil_hall", "oil_tanks", "solar_panels", "solar_inverter", "wind_tower", "dam_x", "dam_y", "powerhouse"):
        tris = without_ground(read_glb(plants.fname(name)))
        if name == "wind_tower":
            hub = plants.WIND_HUB
            rotor = [(tuple((p[0] + hub[0], p[1] + hub[1], p[2] + hub[2]) for p in tri), colour) for tri, colour in read_glb(plants.fname("wind_rotor"))]
            tris = tris + rotor
        out.append((f"plant_{name}", rotated(tris, 0.0, (8.0, 8.0, 0.0))))

    # Toolbar icons and cursors: the models seen the same way, drawn small.
    line = rotated(pylon, math.pi / 2, centre) + wire_at(wire_triangles((0, 1)), models_power.WIRE_Z)
    cable_icon = rotated(marker, 0.0, (8.0, 8.0, 0.0))
    for d in ((-1, 0), (1, 0)):
        length = 8
        heading = math.atan2(d[1], d[0])
        scaled = [(tuple((p[0] * length / 16 + length / 2, p[1], p[2]) for p in tri), colour) for tri, colour in cable]
        cable_icon += rotated(scaled, heading, (8.0, 8.0, 0.0))
    tools = [
        ("line", line),
        ("pylon", rotated(pylon, math.pi / 2, centre)),
        ("substation", rotated(overhead, math.pi / 2, centre)),
        ("transition", rotated(transition, math.pi / 2, centre)),
        ("cable", cable_icon),
        ("substation_underground", rotated(underground, 0.0, centre)),
    ]
    view_icon = rotated(pylon, math.pi / 2, centre) + wire_at(wire_triangles((0, 1)), models_power.WIRE_Z) + lamp((8.0, 8.0, models_power.TOP + 2.0), (0.25, 0.85, 0.30), 1.6)
    for name, tris in tools:
        out.append((f"icon_{name}", tris))
    out.append(("icon_network_view", view_icon))
    for name, tris in tools:
        out.append((f"cursor_{name}", tris))
    for name, colour in (("green", (0.25, 0.95, 0.30)), ("yellow", (1.0, 0.85, 0.15)), ("red", (1.0, 0.20, 0.15))):
        out.append((f"light_{name}", lamp((8.0, 8.0, 0.0), colour, 0.9)))
    return out


def outlined(rgba, zoom):
    """Give an icon a dark outline, as the game's own icons have, so thin lattice work reads on any button."""
    width = {0: 1, 2: 2, 1: 3}[zoom]
    rgba = np.pad(rgba, ((width, width), (width, width), (0, 0)))
    mask = rgba[..., 3] > 0.35
    grown = mask.copy()
    for dy in range(-width, width + 1):
        for dx in range(-width, width + 1):
            grown |= np.roll(np.roll(mask, dy, axis=0), dx, axis=1)
    edge = grown & ~mask
    rgba[edge] = (0.06, 0.06, 0.06, 1.0)
    # Brighten the inside a little: the models are grey steel, which looks dull at this size.
    rgba[mask, :3] = np.clip(rgba[mask, :3] * 1.25, 0, 1)
    rgba[mask, 3] = 1.0
    return rgba


def wire_at(tris, z):
    """Lift wire triangles (conductors at height 0) to height z."""
    return [(tuple((p[0], p[1], p[2] + z) for p in tri), colour) for tri, colour in tris]


def lamp(at, colour, r):
    """A small octahedron of one colour: a status light."""
    x, y, z = at
    top, bottom = (x, y, z + 2 * r), (x, y, z)
    ring = [(x + r, y, z + r), (x, y + r, z + r), (x - r, y, z + r), (x, y - r, z + r)]
    tris = []
    for k in range(4):
        a, b = ring[k], ring[(k + 1) % 4]
        tris.append(((top, a, b), colour))
        tris.append(((bottom, b, a), colour))
    return tris


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("palette", help="src/table/palettes.h of the game")
    parser.add_argument("-o", "--output", default="power.grf")
    parser.add_argument("--png", help="also write a sheet of the normal zoom sprites")
    args = parser.parse_args()
    palette = read_palette(args.palette)

    # GRF zoom numbers: 0 normal, 1 four times, 2 twice.
    zooms = ((0, 1, 4), (2, 2, 3), (1, 4, 2))
    sprites = []
    sheet = []
    ICON_SIZE = 20  # pixels at normal zoom, the size of the game's own toolbar icons
    CURSOR_SIZE = 26
    for name, tris in subjects():
        versions = []
        fit = 1.0
        if name.startswith("icon_") or name.startswith("cursor_"):
            size = ICON_SIZE if name.startswith("icon_") else CURSOR_SIZE
            rgba, _, _ = crop(*rasterise(tris, 1, 1))
            fit = min(1.0, (size - 1) / max(rgba.shape[0], rgba.shape[1]))
        for zoom, scale, aa in zooms:
            rgba, xoff, yoff = rasterise(tris, scale * fit, aa)
            rgba, xoff, yoff = crop(rgba, xoff, yoff)
            if name.startswith("icon_") or name.startswith("cursor_"):
                rgba = outlined(rgba, zoom)
            h, w = rgba.shape[:2]
            if name.startswith("icon_"):
                xoff, yoff = 0, 0
            elif name.startswith("cursor_"):
                xoff, yoff = -(w // 2), -h
            elif name.startswith("light_"):
                xoff, yoff = -(w // 2), -h
            if zoom == 0:
                pal = to_8bpp(rgba, palette)
                versions.append((0x04, 0, pal.tobytes(), w, h, xoff, yoff))
                sheet.append(rgba)
            px = np.clip(np.round(rgba * 255), 0, 255).astype(np.uint8)
            versions.append((0x03, zoom, px.tobytes(), w, h, xoff, yoff))
        sprites.append(versions)
        print(name, [(v[1], v[3], v[4], v[5], v[6]) for v in versions])
    write_grf(args.output, sprites)

    if args.png:
        from PIL import Image
        width = sum(s.shape[1] + 4 for s in sheet)
        height = max(s.shape[0] for s in sheet)
        img = Image.new("RGBA", (width, height), (90, 130, 70, 255))
        x = 0
        for s in sheet:
            img.alpha_composite(Image.fromarray(np.clip(np.round(s * 255), 0, 255).astype(np.uint8), "RGBA"), (x, height - s.shape[0]))
            x += s.shape[1] + 4
        img.save(args.png)


if __name__ == "__main__":
    main()
