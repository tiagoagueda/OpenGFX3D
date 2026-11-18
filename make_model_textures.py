#!/usr/bin/env python3
"""Make the surface textures of the models of the OpenGFX3D package.

    python3 make_model_textures.py

Writes tex_*.png into this folder; gfx3d.py lists which material gets which texture (TEXTURE_RULES),
and Model.save() puts them on the models. Run make_models.py afterwards. Needs numpy and Pillow.

Every texture is 256 x 256 pixels, repeats without a seam in both directions, and shows a surface
(brickwork, roof tiles, planks, ...) in shades of grey around MEAN. The game multiplies the
texture with the colour of the material, so one texture of brickwork serves red, yellow and pink
brick alike, and company colours stay company colours. The textures are spread over the model by
size (TEXTURES in gfx3d.py says how many world units one repeat covers), not stretched to fit.

All of them are computed from random numbers with a fixed seed: nothing is taken from
photographs or from other graphics.
"""

import numpy as np
from PIL import Image

from gfx3d import TEXTURES, TEXTURE_MEAN

SIZE = 256


def noise(rng, low, high, power=1.0, stretch=(1.0, 1.0)):
    """Random pattern that repeats at the edges, from -1 to 1 (see make_textures.py)."""
    fy = np.fft.fftfreq(SIZE, 1.0 / SIZE)[:, None] * stretch[1]
    fx = np.fft.fftfreq(SIZE, 1.0 / SIZE)[None, :] * stretch[0]
    f = np.sqrt(fx * fx + fy * fy)
    spectrum = np.fft.fft2(rng.standard_normal((SIZE, SIZE)))
    keep = (f >= low) & (f <= high)
    spectrum = np.where(keep, spectrum / np.maximum(f, 1.0) ** power, 0.0)
    result = np.real(np.fft.ifft2(spectrum))
    result -= result.mean()
    return result / np.abs(result).max()


def smoothstep(lo, hi, x):
    t = np.clip((x - lo) / (hi - lo if hi != lo else 1e-9), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def grid():
    """Position of each pixel, from 0 to 1: across (u) and from the top down (v)."""
    c = (np.arange(SIZE) + 0.5) / SIZE
    return np.meshgrid(c, c)


def blocks(rng, rows, columns, shift=0.5, joint=0.06, vary=0.1, jitter=0.0):
    """Rows of blocks, each row shifted against the one above: bricks, slabs, slates.

    Returns how light each block is (around 1), how far each pixel is into its block from the top (0 to 1),
    and the joints (1 in a joint, 0 elsewhere). `joint` is the width of a joint as a share of the height of a row."""
    u, v = grid()
    row = np.floor(v * rows).astype(int)
    offsets = (np.arange(rows) * shift + jitter * rng.random(rows)) % 1.0
    x = u * columns + offsets[row]
    column = np.floor(x).astype(int) % columns
    tone = 1.0 + vary * (rng.random((rows, columns)) * 2.0 - 1.0)
    fy = v * rows - row
    fx = x - np.floor(x)
    width = joint * columns / rows
    in_joint = np.maximum(1.0 - smoothstep(0.0, joint, np.minimum(fy, 1.0 - fy)), 1.0 - smoothstep(0.0, width, np.minimum(fx, 1.0 - fx)))
    return tone[row, column], fy, in_joint


def cells(rng, count, edge=0.08):
    """Cells around random points (stones, leaves). Returns how light each cell is (0 to 1),
    and how close each pixel is to the edge of its cell (1 on the edge, 0 inside)."""
    points = rng.random((count, 2))
    tones = rng.random(count)
    u, v = grid()
    best = np.full((SIZE, SIZE), 9.0)
    second = np.full((SIZE, SIZE), 9.0)
    which = np.zeros((SIZE, SIZE), dtype=int)
    for i, (px, py) in enumerate(points):
        dx = np.abs(u - px)
        dy = np.abs(v - py)
        d = np.hypot(np.minimum(dx, 1.0 - dx), np.minimum(dy, 1.0 - dy))
        nearer = d < best
        second = np.where(nearer, best, np.minimum(second, d))
        which = np.where(nearer, i, which)
        best = np.where(nearer, d, best)
    size = 1.0 / np.sqrt(count)
    return tones[which], 1.0 - smoothstep(0.0, edge * size, second - best)


def brick(rng):
    tone, _, joint = blocks(rng, 8, 4, vary=0.12, joint=0.14)
    return tone * (1.0 - 0.30 * joint) * (1.0 + 0.05 * noise(rng, 30, 120, 0.0) + 0.05 * noise(rng, 1, 5, 1.0))


def stone(rng):
    tone, _, joint = blocks(rng, 6, 3, shift=0.37, vary=0.09, joint=0.08, jitter=0.4)
    return tone * (1.0 - 0.28 * joint) * (1.0 + 0.07 * noise(rng, 8, 100, 0.6) + 0.05 * noise(rng, 1, 5, 1.0))


def rubble(rng):
    tone, edge = cells(rng, 70, 0.22)
    return (0.86 + 0.28 * tone) * (1.0 - 0.38 * edge) * (1.0 + 0.06 * noise(rng, 20, 120, 0.3))


def rooftiles(rng):
    """Rows of tiles that overlap: each row is lightest at its lower edge and lies in the shadow of the row above."""
    tone, fy, _ = blocks(rng, 6, 8, vary=0.10, joint=0.0)
    u, _ = grid()
    row = np.floor(grid()[1] * 6)
    ridge = 0.5 + 0.5 * np.cos((u * 8 + 0.5 * row) * 2.0 * np.pi)
    return tone * (0.78 + 0.26 * fy) * (1.0 - 0.35 * smoothstep(0.12, 0.0, fy)) * (0.92 + 0.10 * ridge) * (1.0 + 0.04 * noise(rng, 1, 6, 1.0))


def slate(rng):
    tone, fy, joint = blocks(rng, 8, 6, vary=0.10, joint=0.08)
    return tone * (0.90 + 0.12 * fy) * (1.0 - 0.22 * joint) * (1.0 + 0.04 * noise(rng, 20, 100, 0.2))


def thatch(rng):
    _, v = grid()
    layers = (v * 4) % 1.0
    return (0.86 + 0.16 * layers) * (1.0 - 0.25 * smoothstep(0.10, 0.0, layers)) * (1.0 + 0.16 * noise(rng, 10, 120, 0.3, (1.0, 0.12)) + 0.05 * noise(rng, 1, 6, 1.0))


def planks(rng):
    """Boards lying along u, with their grain, and here and there the end of a board."""
    tone, _, joint = blocks(rng, 8, 1, shift=0.37, vary=0.10, joint=0.10)
    return tone * (1.0 - 0.34 * joint) * (1.0 + 0.10 * noise(rng, 4, 120, 0.5, (0.08, 1.0)) + 0.03 * noise(rng, 40, 120, 0.0))


def bark(rng):
    return 1.0 + 0.22 * noise(rng, 6, 100, 0.5, (1.0, 0.15)) + 0.08 * noise(rng, 2, 10, 1.0)


def concrete(rng):
    """Cast in panels: faint seams, stains that run down, and the grain of the surface."""
    u, v = grid()
    seams = np.maximum(1.0 - smoothstep(0.0, 0.006, np.minimum(u % 0.5, 0.5 - u % 0.5)), 1.0 - smoothstep(0.0, 0.006, np.minimum(v % 0.5, 0.5 - v % 0.5)))
    return (1.0 - 0.16 * seams) * (1.0 + 0.05 * noise(rng, 1, 6, 1.0) + 0.05 * noise(rng, 3, 40, 0.8, (1.0, 0.2)) + 0.04 * noise(rng, 40, 120, 0.0))


def plaster(rng):
    return 1.0 + 0.06 * noise(rng, 1, 8, 1.0) + 0.04 * noise(rng, 3, 30, 0.8, (1.0, 0.25)) + 0.035 * noise(rng, 40, 120, 0.0)


def panel(rng):
    """Painted sheet metal: seams between the sheets, a row of rivets along them, and a soft sheen."""
    u, v = grid()

    def line(x, at, width):
        d = np.abs(x - at)
        return 1.0 - smoothstep(0.0, width, np.minimum(d, 1.0 - d))

    seams = np.maximum(line(u, 0.0, 0.007), np.maximum(line(u, 0.5, 0.007), line(v, 0.0, 0.007)))
    rivets = np.zeros((SIZE, SIZE))
    for at in (0.035, 0.465, 0.535, 0.965):
        for k in range(8):
            rivets = np.maximum(rivets, 1.0 - smoothstep(0.004, 0.012, np.hypot(u - at, v - (k + 0.5) / 8)))
    for k in range(16):
        rivets = np.maximum(rivets, 1.0 - smoothstep(0.004, 0.012, np.hypot(u - (k + 0.5) / 16, v - 0.035)))
    return (1.0 - 0.20 * seams) * (1.0 - 0.14 * rivets) * (1.0 + 0.035 * noise(rng, 1, 5, 1.0) + 0.02 * noise(rng, 4, 60, 0.6, (0.15, 1.0)))


def metal(rng):
    """Bare metal: brushed along u, with seams and a little dirt."""
    u, v = grid()
    seams = np.maximum(1.0 - smoothstep(0.0, 0.006, np.minimum(u % 0.5, 0.5 - u % 0.5)), 1.0 - smoothstep(0.0, 0.006, np.minimum(v, 1.0 - v)))
    return (1.0 - 0.20 * seams) * (1.0 + 0.07 * noise(rng, 3, 120, 0.4, (0.06, 1.0)) + 0.06 * noise(rng, 1, 6, 1.0))


def corrugated(rng):
    u, _ = grid()
    return (0.86 + 0.18 * np.cos(u * 8 * 2.0 * np.pi)) * (1.0 + 0.05 * noise(rng, 1, 6, 1.0) + 0.04 * noise(rng, 3, 40, 0.8, (1.0, 0.2)))


def paving(rng):
    tone, _, joint = blocks(rng, 4, 4, vary=0.07, joint=0.05)
    return tone * (1.0 - 0.30 * joint) * (1.0 + 0.05 * noise(rng, 20, 120, 0.2))


def asphalt(rng):
    return 1.0 + 0.09 * noise(rng, 40, 128, 0.0) + 0.05 * noise(rng, 1, 8, 1.0)


def gravel(rng):
    tone, edge = cells(rng, 600, 0.3)
    return (0.80 + 0.40 * tone) * (1.0 - 0.30 * edge)


def foliage(rng):
    """Leaves in clumps: light on top of each clump, dark in the gaps between them."""
    tone, edge = cells(rng, 110, 0.5)
    small, small_edge = cells(rng, 700, 0.5)
    return (0.80 + 0.30 * tone) * (1.0 - 0.36 * edge) * (0.92 + 0.14 * small) * (1.0 - 0.14 * small_edge)


def grass(rng):
    return 1.0 + 0.10 * noise(rng, 30, 128, 0.2, (1.0, 0.45)) + 0.08 * noise(rng, 2, 12, 1.0)


def soil(rng):
    tone, edge = cells(rng, 420, 0.5)
    return (0.90 + 0.18 * tone) * (1.0 - 0.10 * edge) * (1.0 + 0.08 * noise(rng, 2, 14, 0.8) + 0.05 * noise(rng, 50, 128, 0.0))


def crops(rng):
    """Rows of plants."""
    u, _ = grid()
    rows = 0.5 + 0.5 * np.cos(u * 8 * 2.0 * np.pi)
    return (0.74 + 0.30 * rows) * (1.0 + 0.16 * noise(rng, 20, 128, 0.2) + 0.06 * noise(rng, 2, 10, 1.0))


def glass(rng):
    """A window pane: the sky mirrored in streaks, lighter towards the top."""
    u, v = grid()
    streaks = 0.5 + 0.5 * np.cos((u + v) * 2 * 2.0 * np.pi)
    return 0.88 + 0.34 * smoothstep(0.55, 1.0, streaks) + 0.10 * np.cos(v * 2.0 * np.pi) + 0.03 * noise(rng, 1, 6, 1.0)


def glass_grid(rng):
    """A glazed front: panes in a frame, each mirroring a little more or less of the sky."""
    tone, fy, joint = blocks(rng, 2, 3, shift=0.0, vary=0.16, joint=0.07)
    return np.where(joint > 0.5, 0.62, tone * (1.12 - 0.26 * fy))


def water(rng):
    return 1.0 + 0.12 * noise(rng, 3, 40, 0.6, (0.35, 1.0)) + 0.05 * noise(rng, 1, 5, 1.0)


def snow(rng):
    return 1.0 + 0.035 * noise(rng, 2, 14, 1.0) + 0.02 * noise(rng, 50, 128, 0.0)


def fabric(rng):
    u, v = grid()
    weave = np.cos(u * 64 * 2.0 * np.pi) * np.cos(v * 64 * 2.0 * np.pi)
    return 1.0 + 0.05 * weave + 0.06 * noise(rng, 1, 8, 1.0) + 0.05 * noise(rng, 3, 30, 0.8, (1.0, 0.3))


def rust(rng):
    return 1.0 + 0.14 * noise(rng, 2, 20, 0.8) + 0.08 * noise(rng, 3, 60, 0.6, (1.0, 0.15)) + 0.05 * noise(rng, 50, 128, 0.0)


def main():
    for index, name in enumerate(TEXTURES):
        rng = np.random.default_rng(7000 + index)
        image = globals()[name](rng)
        # Bring the average to the same value for all, so that Model.save() can make up for it.
        for _ in range(4):
            image = np.clip(image * TEXTURE_MEAN / image.mean(), 0.0, 1.0)
        data = (image * 255.0 + 0.5).astype(np.uint8)
        Image.fromarray(np.stack([data] * 3, axis=-1), "RGB").save(f"tex_{name}.png", optimize=True)


if __name__ == "__main__":
    main()
