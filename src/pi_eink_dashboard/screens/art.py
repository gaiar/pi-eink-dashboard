"""Screen 6: Generative tri-color art (fullbleed)."""

from __future__ import annotations

import random

from ..composer import Composer, WIDTH, HEIGHT
from .base import BaseScreen


class ArtScreen(BaseScreen):
    title = ""
    fullbleed = True

    def __init__(self) -> None:
        self._algorithm_idx = 0

    def draw(self, composer: Composer) -> None:
        algorithms = [
            self._voronoi_mosaic,
            self._concentric_geometry,
            self._tile_grid,
        ]
        algo = algorithms[self._algorithm_idx % len(algorithms)]
        algo(composer)
        self._algorithm_idx += 1

    def _voronoi_mosaic(self, composer: Composer) -> None:
        """Generate a Voronoi-like mosaic pattern using random seed points."""
        n_points = random.randint(12, 20)
        seeds = [
            (random.randint(0, WIDTH), random.randint(0, HEIGHT))
            for _ in range(n_points)
        ]
        colors = [random.choice(["black", "red", "white"]) for _ in range(n_points)]

        # For each pixel, find nearest seed and assign its color
        # Use a coarser grid for performance (4x4 blocks)
        block = 4
        for by in range(0, HEIGHT, block):
            for bx in range(0, WIDTH, block):
                cx, cy = bx + block // 2, by + block // 2
                best_dist = float("inf")
                best_idx = 0
                for i, (sx, sy) in enumerate(seeds):
                    dist = (cx - sx) ** 2 + (cy - sy) ** 2
                    if dist < best_dist:
                        best_dist = dist
                        best_idx = i

                c = colors[best_idx]
                if c != "white":
                    composer.rect(
                        (
                            bx,
                            by,
                            min(bx + block, WIDTH) - 1,
                            min(by + block, HEIGHT) - 1,
                        ),
                        color=c,
                    )

        # Draw cell borders by finding pixels where nearest seed changes
        for by in range(0, HEIGHT, block):
            for bx in range(0, WIDTH - block, block):
                cx1, cy1 = bx + block // 2, by + block // 2
                cx2 = cx1 + block

                best1 = min(
                    range(n_points),
                    key=lambda i: (cx1 - seeds[i][0]) ** 2
                    + (cy1 - seeds[i][1]) ** 2,
                )
                best2 = min(
                    range(n_points),
                    key=lambda i: (cx2 - seeds[i][0]) ** 2
                    + (cy1 - seeds[i][1]) ** 2,
                )

                if best1 != best2:
                    composer.line(
                        (bx + block, by, bx + block, min(by + block, HEIGHT) - 1),
                        color="black",
                    )

    def _concentric_geometry(self, composer: Composer) -> None:
        """Generate concentric geometric shapes."""
        cx, cy = WIDTH // 2, HEIGHT // 2
        max_r = min(WIDTH, HEIGHT) // 2

        shape = random.choice(["circles", "diamonds", "mixed"])
        n_rings = random.randint(6, 12)

        for i in range(n_rings, 0, -1):
            r = int(max_r * i / n_rings)
            color = "red" if i % 3 == 0 else "black"
            fill = i % 2 == 0

            if shape == "circles" or (shape == "mixed" and i % 2 == 0):
                composer.ellipse(
                    (cx - r, cy - r, cx + r, cy + r),
                    color=color,
                    fill=fill,
                )
            else:
                self._draw_diamond(composer, cx, cy, r, color, fill)

        # Add some random dots
        for _ in range(random.randint(5, 15)):
            x = random.randint(10, WIDTH - 10)
            y = random.randint(10, HEIGHT - 10)
            r = random.randint(2, 6)
            c = random.choice(["black", "red"])
            composer.ellipse((x - r, y - r, x + r, y + r), color=c)

    def _draw_diamond(
        self,
        composer: Composer,
        cx: int,
        cy: int,
        r: int,
        color: str,
        fill: bool,
    ) -> None:
        """Draw a diamond shape as 4 lines."""
        composer.line((cx, cy - r, cx + r, cy), color=color)
        composer.line((cx + r, cy, cx, cy + r), color=color)
        composer.line((cx, cy + r, cx - r, cy), color=color)
        composer.line((cx - r, cy, cx, cy - r), color=color)

        if fill:
            for dy in range(-r + 1, r):
                half_w = r - abs(dy)
                if half_w > 0:
                    composer.line(
                        (cx - half_w, cy + dy, cx + half_w, cy + dy),
                        color=color,
                    )

    def _tile_grid(self, composer: Composer) -> None:
        """Generate a random tile grid pattern."""
        tile_size = random.choice([16, 22, 32])
        cols = WIDTH // tile_size + 1
        rows = HEIGHT // tile_size + 1

        patterns = ["solid", "cross", "diagonal", "dots", "empty"]

        for row in range(rows):
            for col in range(cols):
                x = col * tile_size
                y = row * tile_size
                x1 = min(x + tile_size - 1, WIDTH - 1)
                y1 = min(y + tile_size - 1, HEIGHT - 1)

                pattern = random.choice(patterns)
                color = random.choice(["black", "red"])

                if pattern == "solid":
                    composer.rect((x, y, x1, y1), color=color)
                elif pattern == "cross":
                    mid_x = x + tile_size // 2
                    mid_y = y + tile_size // 2
                    composer.line((x, mid_y, x1, mid_y), color=color)
                    composer.line((mid_x, y, mid_x, y1), color=color)
                elif pattern == "diagonal":
                    composer.line((x, y, x1, y1), color=color)
                    composer.line((x1, y, x, y1), color=color)
                elif pattern == "dots":
                    mid_x = x + tile_size // 2
                    mid_y = y + tile_size // 2
                    r = max(2, tile_size // 6)
                    composer.ellipse(
                        (mid_x - r, mid_y - r, mid_x + r, mid_y + r),
                        color=color,
                    )
                # "empty" = white, nothing to draw
