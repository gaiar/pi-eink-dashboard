"""Screen 5: Programmatic BWR color test pattern.

Validates display hardware and dithering quality with:
- Solid color blocks (black, white, red)
- Dithered gradients (black-to-white, red-to-white, black-to-red)
- Fine line test (1px, 2px in both colors)
- Text rendering at multiple sizes in both colors
"""

from ..composer import Composer, WIDTH
from .base import BaseScreen, FONT_LARGE, FONT_BODY, FONT_SMALL


class TestPatternScreen(BaseScreen):
    title = ""
    fullbleed = True

    def draw(self, composer: Composer) -> None:
        y = 0

        # === Section 1: Solid color blocks ===
        block_h = 30
        third = WIDTH // 3

        # Black block
        composer.rect((0, y, third - 1, y + block_h), color="black")
        # White block (leave empty — white is default)
        # Red block
        composer.rect((third * 2, y, WIDTH - 1, y + block_h), color="red")

        # Labels (drawn in opposite color for visibility)
        composer.text_centered(y + 8, "BLACK          WHITE            RED", FONT_SMALL, color="red")
        # Overwrite middle label in black
        mid_x = (WIDTH - composer.textlength("WHITE", FONT_SMALL)) // 2
        composer.text((mid_x, y + 8), "WHITE", FONT_SMALL, color="black")
        y += block_h + 2

        # === Section 2: Dithered gradients ===
        grad_h = 28
        grad_w = WIDTH - 8
        gx = 4

        # Black-to-white gradient (checkerboard dithering at various densities)
        self._draw_gradient(composer, gx, y, grad_w, grad_h // 3, "black")
        y += grad_h // 3

        # Red-to-white gradient
        self._draw_gradient(composer, gx, y, grad_w, grad_h // 3, "red")
        y += grad_h // 3

        # Black-to-red gradient (alternating dots)
        self._draw_mixed_gradient(composer, gx, y, grad_w, grad_h // 3)
        y += grad_h // 3 + 4

        # === Section 3: Fine line test ===
        composer.text((4, y), "Lines:", FONT_SMALL, color="black")
        y += 12

        # 1px lines
        for i in range(10):
            x = 4 + i * 12
            composer.line((x, y, x, y + 14), color="black", width=1)
        for i in range(10):
            x = 130 + i * 12
            composer.line((x, y, x, y + 14), color="red", width=1)
        y += 16

        # 2px lines
        for i in range(10):
            x = 4 + i * 12
            composer.line((x, y, x, y + 14), color="black", width=2)
        for i in range(10):
            x = 130 + i * 12
            composer.line((x, y, x, y + 14), color="red", width=2)
        y += 18

        # === Section 4: Text rendering at multiple sizes ===
        composer.text((4, y), "Abc123", FONT_LARGE, color="black")
        composer.text((130, y), "Abc123", FONT_LARGE, color="red")
        y += 28

        composer.text((4, y), "Quick brown fox", FONT_BODY, color="black")
        y += 16
        composer.text((4, y), "Quick brown fox", FONT_BODY, color="red")
        y += 16

        composer.text((4, y), "TINY TEXT 0123456789", FONT_SMALL, color="black")
        composer.text_right(y, "RED TINY TEXT", FONT_SMALL, color="red")

    def _draw_gradient(
        self,
        composer: Composer,
        x: int,
        y: int,
        width: int,
        height: int,
        color: str,
    ) -> None:
        """Draw a gradient from full color to white using dithered patterns."""
        steps = 8
        step_w = width // steps

        for i in range(steps):
            sx = x + i * step_w
            density = 1.0 - (i / (steps - 1))  # 1.0 = solid, 0.0 = empty

            if density >= 0.9:
                composer.rect((sx, y, sx + step_w - 1, y + height - 1), color=color)
            elif density >= 0.7:
                # Dense checkerboard
                for py in range(y, y + height):
                    for px in range(sx, sx + step_w):
                        if (px + py) % 2 == 0:
                            composer.rect((px, py, px, py), color=color)
            elif density >= 0.5:
                # Medium checkerboard (every other pixel in every other row)
                for py in range(y, y + height, 2):
                    for px in range(sx, sx + step_w, 2):
                        composer.rect((px, py, px, py), color=color)
            elif density >= 0.3:
                # Sparse dots
                for py in range(y, y + height, 3):
                    for px in range(sx, sx + step_w, 3):
                        composer.rect((px, py, px, py), color=color)
            elif density >= 0.1:
                # Very sparse dots
                for py in range(y, y + height, 4):
                    for px in range(sx, sx + step_w, 4):
                        composer.rect((px, py, px, py), color=color)
            # density < 0.1: leave white

    def _draw_mixed_gradient(
        self,
        composer: Composer,
        x: int,
        y: int,
        width: int,
        height: int,
    ) -> None:
        """Draw a gradient from black to red using alternating pixels."""
        steps = 8
        step_w = width // steps

        for i in range(steps):
            sx = x + i * step_w
            # 0 = all black, 7 = all red
            red_ratio = i / (steps - 1)

            for py in range(y, y + height):
                for px in range(sx, sx + step_w):
                    # Use position hash to determine color
                    pixel_hash = (px * 7 + py * 13) % steps
                    threshold = int(red_ratio * steps)
                    if pixel_hash < threshold:
                        composer.rect((px, py, px, py), color="red")
                    else:
                        composer.rect((px, py, px, py), color="black")
