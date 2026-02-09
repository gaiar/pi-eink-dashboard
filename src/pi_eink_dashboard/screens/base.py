"""Base screen class with e-paper drawing helpers."""

from __future__ import annotations

from PIL import ImageFont

from ..composer import Composer, WIDTH, HEIGHT

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = FONT_BOLD_PATH if bold else FONT_PATH
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


# Font definitions
FONT_HERO = _load_font(40, bold=True)
FONT_LARGE = _load_font(24, bold=True)
FONT_TITLE = _load_font(18, bold=True)
FONT_SECTION = _load_font(14, bold=True)
FONT_BODY = _load_font(13)
FONT_LABEL = _load_font(11, bold=True)
FONT_SMALL = _load_font(10)

# Layout constants
HEADER_HEIGHT = 22
FOOTER_HEIGHT = 14
CONTENT_TOP = HEADER_HEIGHT + 2
CONTENT_BOTTOM = HEIGHT - FOOTER_HEIGHT - 2
MARGIN = 4


class BaseScreen:
    """Base class for e-paper dashboard screens."""

    title: str = ""
    fullbleed: bool = False

    def render(
        self,
        screen_index: int,
        total_screens: int,
        composer: Composer,
    ) -> None:
        """Render the screen into the composer buffers."""
        if self.fullbleed:
            self.draw(composer)
            return

        # Red header banner
        composer.rect((0, 0, WIDTH, HEADER_HEIGHT), color="red")
        # Title text in black on the red banner — creates black text on red bg
        composer.text_centered(3, self.title, FONT_TITLE, color="black")

        # Draw screen content
        self.draw(composer)

        # Footer with screen dots and timestamp
        self._draw_footer(composer, screen_index, total_screens)

    def draw(self, composer: Composer) -> None:
        """Override to draw screen content."""
        raise NotImplementedError

    @staticmethod
    def _draw_footer(
        composer: Composer,
        current: int,
        total: int,
    ) -> None:
        """Draw navigation dots and update time at the bottom."""
        import time

        y = HEIGHT - FOOTER_HEIGHT + 2

        # Screen indicator dots
        dot_r = 2
        spacing = 12
        start_x = 4

        for i in range(total):
            cx = start_x + i * spacing + dot_r
            if i == current:
                composer.ellipse(
                    (cx - dot_r, y - dot_r, cx + dot_r, y + dot_r),
                    color="black",
                )
            else:
                composer.ellipse(
                    (cx - dot_r, y - dot_r, cx + dot_r, y + dot_r),
                    color="black",
                    fill=False,
                )

        # Timestamp
        ts = time.strftime("Updated %H:%M")
        composer.text_right(y - 2, ts, FONT_SMALL, color="black")
