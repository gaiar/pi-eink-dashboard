"""Fullbleed photo slideshow screen using pre-dithered Unsplash images."""

from __future__ import annotations

from ..composer import Composer, WIDTH, HEIGHT
from ..photos import PhotoCache
from .base import BaseScreen, FONT_HERO, FONT_BODY, FONT_SMALL


class PhotoScreen(BaseScreen):
    """Display pre-dithered photos fullbleed."""

    title = ""
    fullbleed = True

    def __init__(self, cache: PhotoCache) -> None:
        self._cache = cache

    def advance(self) -> None:
        self._cache.advance()

    def retreat(self) -> None:
        self._cache.retreat()

    def draw(self, composer: Composer) -> None:
        layers = self._cache.get_dithered()
        if layers is None:
            composer.text_centered(70, "No photos cached", FONT_BODY, color="black")
            composer.text_centered(90, "Press KEY3 to fetch", FONT_SMALL, color="red")
            return

        black_layer, red_layer = layers
        composer.paste_image(black_layer, red_layer)

    def draw_loading(self, composer: Composer) -> None:
        """Draw a loading screen shown while photos are being fetched."""
        cx = WIDTH // 2
        cy = HEIGHT // 2

        # --- Decorative red border (double-line frame) ---
        composer.rect((0, 0, WIDTH - 1, HEIGHT - 1), color="red", fill=False)
        composer.rect((3, 3, WIDTH - 4, HEIGHT - 4), color="red", fill=False)

        # --- Camera icon (centered, above text) ---
        # Camera body: rounded rectangle approximated with rect
        cam_w, cam_h = 44, 30
        cam_x = cx - cam_w // 2
        cam_y = cy - 42
        composer.rect(
            (cam_x, cam_y, cam_x + cam_w, cam_y + cam_h),
            color="black",
            fill=False,
        )
        # Lens circle
        lens_r = 9
        composer.ellipse(
            (cx - lens_r, cam_y + cam_h // 2 - lens_r,
             cx + lens_r, cam_y + cam_h // 2 + lens_r),
            color="red",
            fill=False,
        )
        # Inner lens dot
        composer.ellipse(
            (cx - 3, cam_y + cam_h // 2 - 3,
             cx + 3, cam_y + cam_h // 2 + 3),
            color="red",
        )
        # Viewfinder bump on top
        vf_w = 14
        composer.rect(
            (cx - vf_w // 2, cam_y - 6, cx + vf_w // 2, cam_y),
            color="black",
        )
        # Flash dot
        composer.ellipse(
            (cam_x + cam_w - 10, cam_y + 4,
             cam_x + cam_w - 5, cam_y + 9),
            color="black",
        )

        # --- "LOADING" text ---
        composer.text_centered(cy + 2, "LOADING", FONT_HERO, color="black")

        # --- Animated-style dots bar (static on e-ink, but decorative) ---
        dot_y = cy + 48
        dot_r = 3
        dot_spacing = 16
        n_dots = 5
        start_x = cx - (n_dots - 1) * dot_spacing // 2

        for i in range(n_dots):
            dx = start_x + i * dot_spacing
            # Alternate filled/outline for visual rhythm
            if i % 2 == 0:
                composer.ellipse(
                    (dx - dot_r, dot_y - dot_r, dx + dot_r, dot_y + dot_r),
                    color="red",
                )
            else:
                composer.ellipse(
                    (dx - dot_r, dot_y - dot_r, dx + dot_r, dot_y + dot_r),
                    color="red",
                    fill=False,
                )

        # --- Subtitle ---
        composer.text_centered(
            dot_y + 12, "Fetching photos...", FONT_SMALL, color="black"
        )
