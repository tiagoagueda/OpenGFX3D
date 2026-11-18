#!/usr/bin/env python3
"""Make the NewGRF of the fork's built-in trams and trolleybuses (OG3T) from the models of models_trams.py.

    python3 make_models.py          # first, so the .glb files are up to date
    python3 make_trams_grf.py       # writes newgrf/opengfx3d_trams.grf, needs nmlc (pip install nml)

The 2D sprites are drawn from the same models the 3D view shows, the way the 2D game sees the world (from the
south, 64 pixels to a tile), in the eight directions of a road vehicle, as 8 bpp sprites at normal zoom. Company
colour parts use the company colour entries of the palette. The vehicles run on the road types of the fork by
label: ELRL (street tram), RAIL (horse tram), ELRR (reserved tram track) and ELRD (electrified road).

The NML source, the sprite sheets and the language file are written to newgrf/ too, so the NewGRF can be
inspected or rebuilt with nmlc alone.
"""

import json
import math
import os
import struct
import subprocess
import sys

import numpy as np
from PIL import Image

from models_trams import GRFID

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "newgrf")
NAME = "opengfx3d_trams"

SUN = np.array([-0.4683, 0.5620, 0.6817])
Z_PER_PIXEL = 0.40824829  # world units per pixel of height in the 2D game

# The game's Direction order (N, NE, E, SE, S, SW, W, NW) as the heading of the vehicle's front on the map,
# with x towards the lower left of the screen and y towards the lower right.
HEADINGS = [5 * math.pi / 4, math.pi, 3 * math.pi / 4, math.pi / 2, math.pi / 4, 0.0, -math.pi / 4, -math.pi / 2]

TEMPERATE_ARCTIC_TROPIC = "bitmask(CLIMATE_TEMPERATE, CLIMATE_ARCTIC, CLIMATE_TROPICAL)"
TOYLAND = "bitmask(CLIMATE_TOYLAND)"

# The vehicles. Parts of articulated vehicles follow their front part and are not sold on their own.
# Speeds in km/h, power in hp, weight in tonnes, capacity in passengers or bags of mail.
VEHICLES = [
    dict(id=100, item="horse_tram", name="Hackney Horse Tram", model="tram_horse.glb", tram="RAIL", year=1860,
         life_years=45, speed=12, power=4, weight=4, capacity=30, cost=6, running=6, vehicle_life=20),
    dict(id=101, item="albion_tram", name="Albion Tram", model="tram_albion.glb", tram="ELRL", year=1890,
         life_years=45, speed=32, power=50, weight=10, capacity=34, cost=12, running=10, vehicle_life=30),
    dict(id=102, item="corridor_tram", name="Corridor Bogie Tram", model="tram_corridor.glb", tram="ELRL", year=1925,
         life_years=45, speed=56, power=160, weight=17, capacity=46, cost=16, running=13, vehicle_life=35),
    dict(id=103, item="meridian_tram", name="Meridian Articulated Tram", model="tram_meridian_front.glb", tram="ELRL",
         year=1960, life_years=45, speed=72, power=300, weight=18, capacity=42, cost=24, running=18, vehicle_life=35,
         parts=[104]),
    dict(id=104, item="meridian_tram_rear", model="tram_meridian_rear.glb", tram="ELRL", weight=14, capacity=42, part=True),
    dict(id=105, item="vela_tram", name="Vela Low-Floor Tram", model="tram_vela_front.glb", tram="ELRL", year=1995,
         life_years=50, speed=80, power=560, weight=14, capacity=36, cost=34, running=22, vehicle_life=35,
         parts=[106, 107]),
    dict(id=106, item="vela_tram_middle", model="tram_vela_middle.glb", tram="ELRL", weight=12, capacity=40, part=True),
    dict(id=107, item="vela_tram_rear", model="tram_vela_rear.glb", tram="ELRL", weight=14, capacity=36, part=True),
    dict(id=108, item="works_mail_tram", name="Works Mail Tram", model="tram_works_mail.glb", tram="ELRL", year=1900,
         life_years=60, speed=40, power=90, weight=12, capacity=30, cargo="MAIL", cost=12, running=10, vehicle_life=30),
    dict(id=109, item="penrose_trolleybus", name="Penrose Trolleybus", model="trolleybus_penrose.glb", road="ELRD",
         year=1930, life_years=40, speed=50, power=80, weight=8, capacity=36, cost=11, running=9, vehicle_life=18),
    dict(id=110, item="castor_trolleybus", name="Castor Trolleybus", model="trolleybus_castor.glb", road="ELRD",
         year=1965, life_years=40, speed=70, power=150, weight=10, capacity=40, cost=14, running=11, vehicle_life=18),
    dict(id=111, item="lyra_trolleybus", name="Lyra Articulated Trolleybus", model="trolleybus_lyra_front.glb",
         road="ELRD", year=1990, life_years=45, speed=80, power=240, weight=10, capacity=40, cost=22, running=16,
         vehicle_life=18, parts=[112]),
    dict(id=112, item="lyra_trolleybus_rear", model="trolleybus_lyra_rear.glb", road="ELRD", weight=7, capacity=36,
         part=True),
    dict(id=113, item="toy_tram", name="Ploddyphut Wobble Tram", model="tram_toy.glb", tram="ELRL", year=1900,
         life_years=100, speed=56, power=120, weight=10, capacity=40, cost=14, running=10, vehicle_life=30,
         climates=TOYLAND),
    dict(id=114, item="toy_trolleybus", name="Ploddyphut Bumble Trolleybus", model="trolleybus_toy.glb", road="ELRD",
         year=1930, life_years=100, speed=56, power=100, weight=8, capacity=36, cost=12, running=9, vehicle_life=18,
         climates=TOYLAND),
]


def read_model(path):
    """Read a .glb of gfx3d.Model: a list of ((p0, p1, p2), colour, company) in the game frame (front, left, up)."""
    data = open(path, "rb").read()
    length = struct.unpack_from("<I", data, 12)[0]
    scene = json.loads(data[20:20 + length])
    pos = 20 + length
    blen = struct.unpack_from("<I", data, pos)[0]
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
            q = [(v[2], v[0], v[1]) for v in p]
            for k in range(0, len(idx) - 2, 3):
                triangles.append(((q[idx[k]], q[idx[k + 1]], q[idx[k + 2]]), c, name.startswith("company")))
    return triangles


def rotated(triangles, heading):
    c, s = math.cos(heading), math.sin(heading)
    return [(tuple((p[0] * c - p[1] * s, p[0] * s + p[1] * c, p[2]) for p in tri), colour, company)
            for tri, colour, company in triangles]


def rasterise(triangles, aa=4):
    """Draw in the projection of the 2D game at normal zoom. Returns (rgb, alpha, company) images at 1x and the
    offset of the top left pixel from the vehicle's position."""
    pts = np.array([p for tri, _, _ in triangles for p in tri])
    sx = 2 * (pts[:, 1] - pts[:, 0]) * aa
    sy = (pts[:, 0] + pts[:, 1] - pts[:, 2] / Z_PER_PIXEL) * aa
    x0 = math.floor(sx.min() / aa) * aa - aa
    y0 = math.floor(sy.min() / aa) * aa - aa
    w = int(math.ceil((sx.max() - x0) / aa)) * aa + 2 * aa
    h = int(math.ceil((sy.max() - y0) / aa)) * aa + 2 * aa
    colour_buf = np.zeros((h, w, 3))
    company_buf = np.zeros((h, w))
    alpha = np.zeros((h, w))
    depth = np.full((h, w), -1e30)
    view = np.array([1, 1, 2 / Z_PER_PIXEL])

    for tri, colour, company in triangles:
        P = np.array(tri)
        X = 2 * (P[:, 1] - P[:, 0]) * aa - x0
        Y = (P[:, 0] + P[:, 1] - P[:, 2] / Z_PER_PIXEL) * aa - y0
        D = P[:, 0] + P[:, 1] + 2 * P[:, 2] / Z_PER_PIXEL
        area = (X[1] - X[0]) * (Y[2] - Y[0]) - (X[2] - X[0]) * (Y[1] - Y[0])
        if abs(area) < 1e-9:
            continue
        n = np.cross(P[1] - P[0], P[2] - P[0])
        ln = np.linalg.norm(n)
        if ln == 0:
            continue
        n = n / ln
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
        company_buf[by0:by1, bx0:bx1][nearer] = 1.0 if company else 0.0
        alpha[by0:by1, bx0:bx1][nearer] = 1.0

    h2, w2 = h // aa, w // aa
    cover = alpha.reshape(h2, aa, w2, aa).sum(axis=(1, 3))
    c = (colour_buf * alpha[..., None]).reshape(h2, aa, w2, aa, 3).sum(axis=(1, 3))
    k = (company_buf * alpha).reshape(h2, aa, w2, aa).sum(axis=(1, 3))
    with np.errstate(invalid="ignore", divide="ignore"):
        c = np.where(cover[..., None] > 0, c / cover[..., None], 0)
        k = np.where(cover > 0, k / cover, 0)
    a = cover / (aa * aa)
    return c, a, k, x0 // aa, y0 // aa


def default_palette():
    from nml import palette
    return np.frombuffer(palette.palette_data[0], dtype=np.uint8).reshape(256, 3).astype(float)


def to_8bpp(rgb, alpha, company, pal):
    """Pick palette entries: company colour parts get the eight company colour shades by brightness."""
    usable = [i for i in range(1, 256) if not (0xC6 <= i <= 0xCD or i >= 0xD7)]
    flat = (rgb * 255).reshape(-1, 3)
    d = ((flat[:, None, :] - pal[usable][None, :, :]) ** 2).sum(axis=2)
    out = np.array(usable)[d.argmin(axis=1)].reshape(rgb.shape[:2])
    lum = rgb.mean(axis=2)
    shade = np.clip(np.round((lum - 0.45) / (1.15 - 0.45) * 7), 0, 7).astype(int)
    out = np.where(company > 0.5, 0xC6 + shade, out)
    out[alpha < 0.5] = 0
    return out.astype(np.uint8)


def draw_sheet(vehicle, pal):
    """Draw the eight directions of one vehicle part side by side; returns the image and the NML sprite lines."""
    model = read_model(os.path.join(HERE, vehicle["model"]))
    sprites = []
    for heading in HEADINGS:
        rgb, a, k, xoff, yoff = rasterise(rotated(model, heading))
        img = to_8bpp(rgb, a, k, pal)
        ys, xs = np.nonzero(img)
        img = img[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
        sprites.append((img, int(xoff + xs.min()), int(yoff + ys.min())))
    width = sum(s[0].shape[1] + 1 for s in sprites) + 1
    height = max(s[0].shape[0] for s in sprites) + 2
    sheet = np.zeros((height, width), dtype=np.uint8)
    lines = []
    x = 1
    for img, xoff, yoff in sprites:
        h, w = img.shape
        sheet[1:1 + h, x:x + w] = img
        lines.append(f"    [{x}, 1, {w}, {h}, {xoff}, {yoff}]")
        x += w + 1
    image = Image.fromarray(sheet, "P")
    image.putpalette(pal.astype(np.uint8).flatten().tolist())
    return image, lines


def nml_item(v):
    lines = [f"item(FEAT_ROADVEHS, {v['item']}, {v['id']}) {{", "    property {"]
    if "tram" in v:
        lines.append(f"        tram_type: {v['tram']};")
        lines.append("        misc_flags: bitmask(ROADVEH_FLAG_TRAM);")
    else:
        lines.append(f"        road_type: {v['road']};")
    cargo = v.get("cargo", "PASS")
    if v.get("part"):
        lines += [
            "        climates_available: NO_CLIMATE;",
            "        introduction_date: date(1850, 1, 1);",
            "        model_life: VEHICLE_NEVER_EXPIRES;",
            "        vehicle_life: 30;",
        ]
    else:
        lines += [
            f"        name: string(STR_NAME_{v['item'].upper()});",
            f"        climates_available: {v.get('climates', TEMPERATE_ARCTIC_TROPIC)};",
            f"        introduction_date: date({v['year']}, 1, 1);",
            f"        model_life: {v['life_years']};",
            f"        vehicle_life: {v['vehicle_life']};",
            "        reliability_decay: 20;",
            f"        speed: {v['speed']} km/h;",
            f"        power: {v['power']} hp;",
            f"        cost_factor: {v['cost']};",
            f"        running_cost_factor: {v['running']};",
            "        running_cost_base: RUNNING_COST_ROADVEH;",
            "        loading_speed: 8;",
            "        sound_effect: SOUND_BUS_START_PULL_AWAY;" if "road" in v else "        sound_effect: SOUND_TRAIN_HORN;",
            "        visual_effect: VISUAL_EFFECT_DISABLE;" if v["id"] != 100 else "        visual_effect: VISUAL_EFFECT_DISABLE;",
        ]
    lines += [
        f"        weight: {v['weight']} ton;",
        f"        cargo_capacity: {v['capacity']};",
        f"        default_cargo_type: {cargo};",
        f"        refittable_cargo_classes: bitmask({'CC_MAIL' if cargo == 'MAIL' else 'CC_PASSENGERS'});",
        "        non_refittable_cargo_classes: bitmask();",
        "        refit_cost: 0;",
        "        length: 8;",
        "    }",
        "    graphics {",
    ]
    if v.get("parts"):
        lines.append(f"        articulated_part: sw_{v['item']}_parts;")
    lines += [f"        default: set_{v['item']};", "    }", "}", ""]
    return lines


def main():
    os.makedirs(os.path.join(OUT, "gfx"), exist_ok=True)
    os.makedirs(os.path.join(OUT, "lang"), exist_ok=True)
    pal = default_palette()

    nml = [
        "/* Made by make_trams_grf.py from the OpenGFX3D models; edit that script, not this file. */",
        "",
        "grf {",
        f"    grfid: \"\\{GRFID[0:2]}\\{GRFID[2:4]}\\{GRFID[4:6]}\\{GRFID[6:8]}\";",
        "    name: string(STR_GRF_NAME);",
        "    desc: string(STR_GRF_DESC);",
        "    version: 1;",
        "    min_compatible_version: 1;",
        "}",
        "",
        "roadtypetable { ROAD, ELRD }",
        "tramtypetable { ELRL, RAIL, ELRR }",
        "cargotable { PASS, MAIL }",
        "",
    ]
    for v in VEHICLES:
        image, lines = draw_sheet(v, pal)
        image.save(os.path.join(OUT, "gfx", f"{v['item']}.png"), optimize=True)
        nml.append(f"spriteset(set_{v['item']}, \"gfx/{v['item']}.png\") {{")
        nml.append("\n".join(lines))
        nml.append("}")
        nml.append("")
        print(v["item"], image.size)
    for v in VEHICLES:
        if v.get("parts"):
            nml.append(f"switch(FEAT_ROADVEHS, SELF, sw_{v['item']}_parts, extra_callback_info1) {{")
            for i, part in enumerate(v["parts"]):
                nml.append(f"    {i + 1}: return {part};")
            nml.append("    return CB_RESULT_NO_MORE_ARTICULATED_PARTS;")
            nml.append("}")
            nml.append("")
    for v in VEHICLES:
        nml += nml_item(v)
    with open(os.path.join(OUT, f"{NAME}.nml"), "w") as f:
        f.write("\n".join(nml))

    lang = [
        "##grflangid 0x01",
        "STR_GRF_NAME :OpenGFX3D Trams and Trolleybuses",
        "STR_GRF_DESC :Trams and trolleybuses of the OpenTTD 3D fork, drawn from its 3D models. Trams run on street "
        "tramway, horse tramway and reserved tramway; trolleybuses need electrified road.",
    ]
    for v in VEHICLES:
        if not v.get("part"):
            lang.append(f"STR_NAME_{v['item'].upper()} :{v['name']}")
    with open(os.path.join(OUT, "lang", "english.lng"), "w") as f:
        f.write("\n".join(lang) + "\n")

    result = subprocess.run(["nmlc", "-c", "--quiet", f"--grf={NAME}.grf", f"{NAME}.nml"], cwd=OUT)
    if result.returncode != 0:
        sys.exit(result.returncode)
    for junk in (".nmlcache",):
        path = os.path.join(OUT, junk)
        if os.path.isdir(path):
            import shutil
            shutil.rmtree(path)


if __name__ == "__main__":
    main()
