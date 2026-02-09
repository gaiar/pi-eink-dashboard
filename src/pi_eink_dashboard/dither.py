"""Tri-color Floyd-Steinberg dithering for e-paper display.

CIELAB color space with serpentine scanning and gamma-correct processing.
Palette colors tuned to actual Waveshare 2.7" tri-color e-ink pigments.
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance

log = logging.getLogger("pi-eink-dashboard")

WIDTH = 264
HEIGHT = 176

# Actual e-ink panel sRGB values (Waveshare 2.7" B, measured approximation).
# Pure #FF0000 is wrong — e-ink red pigment is desaturated and warm.
PALETTE_SRGB = np.array([
    [0, 0, 0],        # black
    [192, 48, 43],     # red (typical e-ink red pigment, ~#C0302B)
    [255, 255, 255],   # white
], dtype=np.float64)

_IDX_BLACK = 0
_IDX_RED = 1
_IDX_WHITE = 2

# Floyd-Steinberg error diffusion weights:
#       * 7/16
# 3/16 5/16 1/16
_FS_KERNEL = [(1, 0, 7 / 16), (-1, 1, 3 / 16), (0, 1, 5 / 16), (1, 1, 1 / 16)]


# --- sRGB → CIELAB pipeline (gamma-correct) ---

def _srgb_to_linear(srgb: np.ndarray) -> np.ndarray:
    """Convert sRGB [0,255] to linear RGB [0,1]."""
    v = srgb / 255.0
    return np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)


def _linear_to_xyz(rgb: np.ndarray) -> np.ndarray:
    """Convert linear RGB to CIE XYZ (D65 illuminant)."""
    m = np.array([
        [0.4124564, 0.3575761, 0.1804375],
        [0.2126729, 0.7151522, 0.0721750],
        [0.0193339, 0.1191920, 0.9503041],
    ])
    return rgb @ m.T


def _xyz_to_lab(xyz: np.ndarray) -> np.ndarray:
    """Convert CIE XYZ to CIELAB."""
    white = np.array([0.95047, 1.00000, 1.08883])
    xyz_n = xyz / white

    delta = 6.0 / 29.0
    f = np.where(
        xyz_n > delta ** 3,
        np.cbrt(xyz_n),
        xyz_n / (3 * delta ** 2) + 4.0 / 29.0,
    )

    L = 116.0 * f[..., 1] - 16.0
    a = 500.0 * (f[..., 0] - f[..., 1])
    b = 200.0 * (f[..., 1] - f[..., 2])
    return np.stack([L, a, b], axis=-1)


def _srgb_to_lab(srgb: np.ndarray) -> np.ndarray:
    """Convert sRGB [0,255] to CIELAB."""
    return _xyz_to_lab(_linear_to_xyz(_srgb_to_linear(srgb)))


# Pre-compute palette in CIELAB (module-level, done once)
_PALETTE_LAB = _srgb_to_lab(PALETTE_SRGB)


def dither_image(
    source: str | Path | Image.Image,
    saturation_boost: float = 2.5,
    contrast_boost: float = 1.3,
) -> tuple[Image.Image, Image.Image]:
    """Dither an image to tri-color and return (black_layer, red_layer).

    Uses Floyd-Steinberg error diffusion with serpentine scanning in CIELAB
    color space for perceptually accurate color matching.

    Return two mode '1' images:
    - black_layer: 0 where black pixels should appear, 255 elsewhere
    - red_layer: 0 where red pixels should appear, 255 elsewhere
    """
    if isinstance(source, Image.Image):
        img = source.convert("RGB")
    else:
        img = Image.open(source).convert("RGB")

    img = img.resize((WIDTH, HEIGHT), Image.LANCZOS)
    img = ImageEnhance.Color(img).enhance(saturation_boost)
    img = ImageEnhance.Contrast(img).enhance(contrast_boost)

    # Convert entire image sRGB → CIELAB (vectorized, fast)
    pixels = _srgb_to_lab(np.array(img, dtype=np.float64))

    result = np.zeros((HEIGHT, WIDTH), dtype=np.uint8)

    # Floyd-Steinberg with serpentine scanning
    for y in range(HEIGHT):
        if y % 2 == 0:
            x_range = range(WIDTH)
            direction = 1
        else:
            x_range = range(WIDTH - 1, -1, -1)
            direction = -1

        for x in x_range:
            old = pixels[y, x]

            # Nearest palette color in CIELAB (Euclidean distance)
            diff = _PALETTE_LAB - old
            nearest = int(np.argmin(np.sum(diff * diff, axis=1)))
            result[y, x] = nearest

            # Distribute quantization error to neighbors
            error = old - _PALETTE_LAB[nearest]
            for dx, dy, weight in _FS_KERNEL:
                nx = x + dx * direction
                ny = y + dy
                if 0 <= nx < WIDTH and 0 <= ny < HEIGHT:
                    pixels[ny, nx] += error * weight

    # Extract layers: 0=ink, 255=no ink
    black_data = np.where(result == _IDX_BLACK, 0, 255).astype(np.uint8)
    red_data = np.where(result == _IDX_RED, 0, 255).astype(np.uint8)

    black_layer = Image.fromarray(black_data, mode="L").convert(
        "1", dither=Image.Dither.NONE
    )
    red_layer = Image.fromarray(red_data, mode="L").convert(
        "1", dither=Image.Dither.NONE
    )

    label = source if isinstance(source, (str, Path)) else "PIL.Image"
    log.info("Dithered %s to %dx%d tri-color (CIELAB+serpentine).", label, WIDTH, HEIGHT)
    return black_layer, red_layer
