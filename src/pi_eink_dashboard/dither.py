"""Tri-color Atkinson dithering for e-paper display."""

from __future__ import annotations

import logging
from pathlib import Path

from PIL import Image, ImageEnhance

log = logging.getLogger("pi-eink-dashboard")

WIDTH = 264
HEIGHT = 176

# Target palette: white, black, red
PALETTE = [(255, 255, 255), (0, 0, 0), (255, 0, 0)]

# Atkinson diffusion kernel: distributes 6/8 of error (discards 25%)
# Offsets: (dx, dy, weight)  — all weights are 1/8
_ATKINSON_KERNEL = [
    (1, 0),
    (2, 0),
    (-1, 1),
    (0, 1),
    (1, 1),
    (0, 2),
]


def _closest_color(r: int, g: int, b: int) -> tuple[int, int, int]:
    """Find the closest palette color by Euclidean distance."""
    best = PALETTE[0]
    best_dist = float("inf")
    for pr, pg, pb in PALETTE:
        dist = (r - pr) ** 2 + (g - pg) ** 2 + (b - pb) ** 2
        if dist < best_dist:
            best_dist = dist
            best = (pr, pg, pb)
    return best


def dither_image(
    image_path: str | Path,
    saturation_boost: float = 2.5,
    contrast_boost: float = 1.3,
) -> tuple[Image.Image, Image.Image]:
    """Dither an image to tri-color and return (black_layer, red_layer).

    Returns two mode '1' images:
    - black_layer: 0 where black pixels should appear, 255 elsewhere
    - red_layer: 0 where red pixels should appear, 255 elsewhere
    """
    img = Image.open(image_path).convert("RGB")

    # Resize to display dimensions
    img = img.resize((WIDTH, HEIGHT), Image.LANCZOS)

    # Boost saturation to make reds pop
    img = ImageEnhance.Color(img).enhance(saturation_boost)

    # Boost contrast for cleaner dithering
    img = ImageEnhance.Contrast(img).enhance(contrast_boost)

    # Atkinson error diffusion
    pixels = list(img.getdata())
    w, h = img.size
    # Work with float arrays for error accumulation
    errors = [[0.0, 0.0, 0.0] for _ in range(w * h)]

    result = [(255, 255, 255)] * (w * h)

    for y in range(h):
        for x in range(w):
            idx = y * w + x
            or_, og, ob = pixels[idx]
            # Add accumulated error
            r = max(0, min(255, int(or_ + errors[idx][0])))
            g = max(0, min(255, int(og + errors[idx][1])))
            b = max(0, min(255, int(ob + errors[idx][2])))

            # Find closest palette color
            nr, ng, nb = _closest_color(r, g, b)
            result[idx] = (nr, ng, nb)

            # Compute error
            er = r - nr
            eg = g - ng
            eb = b - nb

            # Distribute error (Atkinson: 1/8 each, 6 neighbors)
            for dx, dy in _ATKINSON_KERNEL:
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h:
                    nidx = ny * w + nx
                    errors[nidx][0] += er / 8.0
                    errors[nidx][1] += eg / 8.0
                    errors[nidx][2] += eb / 8.0

    # Split into two 1-bit layers
    black_layer = Image.new("1", (w, h), 255)
    red_layer = Image.new("1", (w, h), 255)

    black_pixels = black_layer.load()
    red_pixels = red_layer.load()

    for y in range(h):
        for x in range(w):
            r, g, b = result[y * w + x]
            if r == 0 and g == 0 and b == 0:
                black_pixels[x, y] = 0  # type: ignore[index]
            elif r == 255 and g == 0 and b == 0:
                red_pixels[x, y] = 0  # type: ignore[index]
            # White pixels: both layers stay 255

    log.info("Dithered %s to %dx%d tri-color.", image_path, w, h)
    return black_layer, red_layer
