"""Dual-buffer rendering engine for tri-color e-paper (black/white/red)."""

from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont

# Display dimensions (landscape)
WIDTH = 264
HEIGHT = 176

# Ink colors for 1-bit images
INK = 0  # black pixel (ink applied)
NO_INK = 255  # white pixel (no ink)


class Composer:
    """Manage two 1-bit image buffers: one for black, one for red.

    All drawing operations accept a color parameter ("black" or "red")
    to route to the correct layer. When both layers have ink at the
    same pixel, red overrides black on the physical display.
    """

    def __init__(self) -> None:
        self._black = Image.new("1", (WIDTH, HEIGHT), NO_INK)
        self._red = Image.new("1", (WIDTH, HEIGHT), NO_INK)
        self._draw_black = ImageDraw.Draw(self._black)
        self._draw_red = ImageDraw.Draw(self._red)

    def _draw(self, color: str) -> ImageDraw.ImageDraw:
        if color == "red":
            return self._draw_red
        return self._draw_black

    def result(self) -> tuple[Image.Image, Image.Image]:
        """Return (black_image, red_image) for display."""
        return self._black, self._red

    def text(
        self,
        xy: tuple[int, int],
        text: str,
        font: ImageFont.FreeTypeFont,
        color: str = "black",
    ) -> None:
        """Draw text on the specified layer."""
        self._draw(color).text(xy, text, fill=INK, font=font)

    def text_centered(
        self,
        y: int,
        text: str,
        font: ImageFont.FreeTypeFont,
        color: str = "black",
    ) -> None:
        """Draw horizontally centered text."""
        draw = self._draw(color)
        tw = draw.textlength(text, font=font)
        x = (WIDTH - int(tw)) // 2
        draw.text((x, y), text, fill=INK, font=font)

    def text_right(
        self,
        y: int,
        text: str,
        font: ImageFont.FreeTypeFont,
        color: str = "black",
        margin: int = 4,
    ) -> None:
        """Draw right-aligned text."""
        draw = self._draw(color)
        tw = draw.textlength(text, font=font)
        x = WIDTH - int(tw) - margin
        draw.text((x, y), text, fill=INK, font=font)

    def textlength(self, text: str, font: ImageFont.FreeTypeFont) -> int:
        """Return pixel width of text (layer-independent)."""
        return int(self._draw_black.textlength(text, font=font))

    def rect(
        self,
        xy: tuple[int, int, int, int],
        color: str = "black",
        fill: bool = True,
    ) -> None:
        """Draw a filled or outlined rectangle."""
        x0, y0, x1, y1 = xy
        if fill:
            self._draw(color).rectangle([(x0, y0), (x1, y1)], fill=INK)
        else:
            self._draw(color).rectangle([(x0, y0), (x1, y1)], outline=INK)

    def line(
        self,
        xy: tuple[int, int, int, int],
        color: str = "black",
        width: int = 1,
    ) -> None:
        """Draw a line."""
        x0, y0, x1, y1 = xy
        self._draw(color).line([(x0, y0), (x1, y1)], fill=INK, width=width)

    def hline(self, y: int, color: str = "black", x0: int = 4, x1: int = WIDTH - 4) -> None:
        """Draw a horizontal divider line."""
        self.line((x0, y, x1, y), color=color)

    def ellipse(
        self,
        xy: tuple[int, int, int, int],
        color: str = "black",
        fill: bool = True,
    ) -> None:
        """Draw a filled or outlined ellipse."""
        x0, y0, x1, y1 = xy
        if fill:
            self._draw(color).ellipse([(x0, y0), (x1, y1)], fill=INK)
        else:
            self._draw(color).ellipse([(x0, y0), (x1, y1)], outline=INK)

    def progress_bar(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        percent: float,
        color: str = "black",
        critical_threshold: float = 85.0,
    ) -> None:
        """Draw a progress bar. Switches to red if percent >= critical_threshold."""
        bar_color = "red" if percent >= critical_threshold else color

        # Outline
        self._draw_black.rectangle(
            [(x, y), (x + width, y + height)], outline=INK
        )
        # Fill
        fill_w = max(0, int((width - 2) * min(percent, 100) / 100))
        if fill_w > 0:
            self._draw(bar_color).rectangle(
                [(x + 1, y + 1), (x + 1 + fill_w, y + height - 1)], fill=INK
            )

    def label_value(
        self,
        x: int,
        y: int,
        label: str,
        value: str,
        label_font: ImageFont.FreeTypeFont,
        value_font: ImageFont.FreeTypeFont,
        label_color: str = "red",
        value_color: str = "black",
        gap: int = 3,
    ) -> None:
        """Draw a label: value pair with label in one color and value in another."""
        self.text((x, y), label, font=label_font, color=label_color)
        lw = self.textlength(label, label_font)
        self.text((x + lw + gap, y), value, font=value_font, color=value_color)

    def paste_image(
        self,
        black_layer: Image.Image,
        red_layer: Image.Image,
    ) -> None:
        """Paste pre-rendered 1-bit layers (e.g. from dithering)."""
        self._black.paste(black_layer, (0, 0))
        self._red.paste(red_layer, (0, 0))
