#!/usr/bin/env python3
"""Make the ground textures of the OpenGFX3D package.

    python3 make_textures.py

Writes ground_*.png into this folder. make_models.py lists them in the index.
Needs numpy and Pillow.

Every texture is 512 x 512 pixels and repeats without a seam in both directions; the game
spreads one texture over a square of TILES x TILES tiles, so single tiles do not show.
All of them are computed from random numbers with a fixed seed: nothing is taken from
photographs or from other graphics.

The game matches the average colour of each texture to the ground sprites of the 2D game,
so the same textures serve all climates. Only the differences in colour within a texture
matter here, not its overall tint. ground_sand.png, the beach, is used as it is.
"""

import os

import numpy as np
from PIL import Image

SIZE = 512
TILES = 4

# Texture name, as in the index, to file name.
FILES = {
    "grass": "ground_grass.png",
    "soil": "ground_soil.png",
    "rough": "ground_rough.png",
    "rocks": "ground_rocks.png",
    "snow": "ground_snow.png",
    "desert": "ground_desert.png",
    "sand": "ground_sand.png",
    "water": "ground_water.png",
    "mask": "ground_mask.png",
}


def noise(rng, low, high, power=1.0, stretch=(1.0, 1.0)):
    """Random pattern that repeats at the edges, from -1 to 1.

    Made of waves with between `low` and `high` cycles across the texture; `power` says how
    quickly the short waves get weaker; `stretch` pulls the pattern out along x or y."""
    fy = np.fft.fftfreq(SIZE, 1.0 / SIZE)[:, None] * stretch[1]
    fx = np.fft.fftfreq(SIZE, 1.0 / SIZE)[None, :] * stretch[0]
    f = np.sqrt(fx * fx + fy * fy)
    spectrum = np.fft.fft2(rng.standard_normal((SIZE, SIZE)))
    keep = (f >= low) & (f <= high)
    spectrum = np.where(keep, spectrum / np.maximum(f, 1.0) ** power, 0.0)
    result = np.real(np.fft.ifft2(spectrum))
    result -= result.mean()
    return result / np.abs(result).max()


def level(pattern):
    """Spread the values of a pattern evenly from 0 to 1."""
    order = np.argsort(pattern, axis=None)
    result = np.empty(pattern.size)
    result[order] = np.linspace(0.0, 1.0, pattern.size)
    return result.reshape(pattern.shape)


def smoothstep(lo, hi, x):
    t = np.clip((x - lo) / (hi - lo), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def colour(*rgb):
    return np.array(rgb, dtype=float) / 255.0


def mix(a, b, t):
    """Blend two colours or images; `t` is one number per pixel."""
    return a + (b - a) * t[..., None]


def shade(image, amount):
    """Lighten and darken an image; `amount` is around 0."""
    return image * (1.0 + amount[..., None])


def save(name, image):
    data = (np.clip(image, 0.0, 1.0) * 255.0 + 0.5).astype(np.uint8)
    Image.fromarray(data, "RGB" if data.ndim == 3 else "L").save(FILES[name], optimize=True)


def grass(rng):
    """A meadow: patches of lighter and darker green, with the grain of the blades on top."""
    patches = level(noise(rng, 1, 6, 1.2))
    clumps = noise(rng, 6, 40, 0.8)
    blades = noise(rng, 30, 200, 0.2, (1.0, 0.45))
    dry = smoothstep(0.72, 0.95, level(noise(rng, 2, 10, 1.0)))
    image = mix(colour(52, 104, 30), colour(86, 140, 42), patches)
    image = mix(image, colour(128, 146, 58), dry * 0.45)
    image = shade(image, 0.16 * clumps + 0.14 * blades)
    return image


def soil(rng):
    """Bare earth: brown, with clods and a few small stones."""
    patches = level(noise(rng, 1, 6, 1.2))
    clods = noise(rng, 10, 70, 0.6)
    grain = noise(rng, 60, 240, 0.0)
    stones = smoothstep(0.985, 0.995, level(noise(rng, 40, 120, 0.3)))
    image = mix(colour(98, 70, 42), colour(130, 96, 60), patches)
    image = shade(image, 0.18 * clods + 0.10 * grain)
    image = mix(image, colour(168, 160, 148), stones * 0.7)
    return image


def rough(rng):
    """Rough land: grass with dark tufts and worn, brownish spots."""
    base = grass(rng)
    tufts = smoothstep(0.62, 0.80, level(noise(rng, 8, 30, 0.6)))
    worn = smoothstep(0.70, 0.92, level(noise(rng, 3, 14, 1.0)))
    grain = noise(rng, 40, 200, 0.2)
    image = mix(base, colour(110, 100, 52), worn * 0.6)
    image = mix(image, colour(34, 76, 24), tufts * 0.55)
    return shade(image, 0.10 * grain)


def rocks(rng):
    """Stony ground: gravel and thin grass between the rocks."""
    base = grass(rng)
    gravel = smoothstep(0.35, 0.70, level(noise(rng, 3, 16, 0.9)))
    pebbles = noise(rng, 30, 140, 0.3)
    grain = noise(rng, 80, 250, 0.0)
    stone = mix(colour(120, 114, 102), colour(160, 154, 142), level(pebbles))
    image = mix(base, stone, gravel * 0.5)
    return shade(image, 0.08 * grain)


def snow(rng):
    """Snow: nearly white, with soft bluish drifts and a little sparkle."""
    drifts = noise(rng, 1, 8, 1.4, (1.0, 0.6))
    ripples = noise(rng, 8, 40, 1.0, (1.0, 0.5))
    grain = noise(rng, 100, 250, 0.0)
    image = mix(colour(214, 224, 238), colour(250, 252, 255), level(drifts))
    return shade(image, 0.03 * ripples + 0.015 * grain)


def sandy(rng, dark, light, ripple):
    """Sand: fine grain, with wind ripples."""
    patches = level(noise(rng, 1, 6, 1.3))
    waves = noise(rng, 14, 50, 0.8, (0.35, 1.0))
    grain = noise(rng, 80, 250, 0.0)
    speckle = smoothstep(0.97, 0.995, level(noise(rng, 60, 200, 0.2)))
    image = mix(dark, light, patches)
    image = shade(image, ripple * waves + 0.07 * grain)
    return mix(image, dark * 0.75, speckle * 0.5)


def water(rng):
    """Water seen from above: darker and lighter blue, with the lines of small waves."""
    swell = level(noise(rng, 1, 5, 1.3))
    waves = noise(rng, 6, 30, 1.0, (0.5, 1.0))
    # Ridges: bright thin lines where a wavy pattern crosses zero.
    ridges = 1.0 - np.abs(noise(rng, 5, 24, 1.1, (0.6, 1.0))) * 4.0
    ridges = np.clip(ridges, 0.0, 1.0) ** 3
    image = mix(colour(30, 74, 124), colour(48, 100, 152), swell)
    image = shade(image, 0.10 * waves)
    return mix(image, colour(120, 164, 200), ridges * 0.22)


def mask(rng):
    """Where one kind of ground takes over from another: every value from black to white is as common as the next.
    The game puts the second kind where the mask is below how far the change has gone."""
    blobs = noise(rng, 3, 20, 1.1)
    edge = noise(rng, 20, 120, 0.5)
    return level(blobs + 0.25 * edge)


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    makers = {
        "grass": grass,
        "soil": soil,
        "rough": rough,
        "rocks": rocks,
        "snow": snow,
        "desert": lambda rng: sandy(rng, colour(196, 158, 92), colour(226, 192, 124), 0.10),
        "sand": lambda rng: sandy(rng, colour(206, 180, 132), colour(234, 214, 170), 0.05),
        "water": water,
        "mask": mask,
    }
    for seed, (name, maker) in enumerate(makers.items()):
        save(name, maker(np.random.default_rng(1000 + seed)))


if __name__ == "__main__":
    main()
