"""Entry point: render/poll loop for e-paper dashboard."""

import logging
import signal
import sys
import time

log = logging.getLogger("pi-eink-dashboard")

POLL_SLEEP = 0.2  # seconds between button polls
REFRESH_INTERVAL = 180.0  # seconds between auto-refreshes (3 min)
DEMO_SAVE_DIR = "demo_output"


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(name)s: %(message)s",
        stream=sys.stderr,
    )

    print("pi-eink-dashboard: starting...", flush=True)

    demo_mode = "--demo" in sys.argv

    from .composer import Composer

    if demo_mode:
        log.info("Demo mode — rendering to PNG files.")
        display = None
    else:
        from .display import Display, DisplayNotFoundError

        print("pi-eink-dashboard: initializing EPD...", flush=True)
        try:
            display = Display()
        except DisplayNotFoundError as e:
            log.info("e-Paper HAT not detected (%s) — exiting.", e)
            sys.exit(0)
        print("pi-eink-dashboard: EPD ready.", flush=True)

    from .input import InputHandler
    from .screens.dashboard import DashboardScreen
    from .screens.identity import IdentityScreen
    from .screens.network import NetworkScreen
    from .screens.health import HealthScreen
    from .screens.test_pattern import TestPatternScreen
    from .screens.art import ArtScreen

    inp = InputHandler()
    screens = [
        DashboardScreen(),
        IdentityScreen(),
        NetworkScreen(),
        HealthScreen(),
        TestPatternScreen(),
        ArtScreen(),
    ]
    total = len(screens)

    screen_idx = 0
    auto_cycle = False
    running = True

    def shutdown(_signum: int, _frame: object) -> None:
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    def render_current() -> None:
        """Render current screen and send to display (or save PNG in demo mode)."""
        composer = Composer()
        screen = screens[screen_idx]
        title = screen.title or "fullbleed"
        print(
            f"pi-eink-dashboard: rendering screen {screen_idx + 1}/{total}: {title}",
            flush=True,
        )
        screen.render(screen_idx, total, composer)
        black_img, red_img = composer.result()

        if display is not None:
            print("pi-eink-dashboard: sending to EPD...", flush=True)
            display.show(black_img, red_img)
            print("pi-eink-dashboard: display updated.", flush=True)
        else:
            _save_demo(screen_idx, screen, black_img, red_img)

    def _save_demo(
        idx: int, screen: object, black_img: object, red_img: object
    ) -> None:
        """Save rendered images as PNGs for headless development."""
        import os

        from PIL import Image

        os.makedirs(DEMO_SAVE_DIR, exist_ok=True)
        title = getattr(screen, "title", "") or "fullbleed"
        name = title.lower().replace(" ", "_")

        # Save individual layers
        black_img.save(f"{DEMO_SAVE_DIR}/{idx}_{name}_black.png")  # type: ignore[union-attr]
        red_img.save(f"{DEMO_SAVE_DIR}/{idx}_{name}_red.png")  # type: ignore[union-attr]

        # Create composite preview: white bg, black ink as black, red ink as red
        preview = Image.new("RGB", (264, 176), (255, 255, 255))
        for py in range(176):
            for px in range(264):
                r_pixel = red_img.getpixel((px, py))  # type: ignore[union-attr]
                b_pixel = black_img.getpixel((px, py))  # type: ignore[union-attr]
                if r_pixel == 0:
                    preview.putpixel((px, py), (200, 0, 0))
                elif b_pixel == 0:
                    preview.putpixel((px, py), (0, 0, 0))
        preview.save(f"{DEMO_SAVE_DIR}/{idx}_{name}_preview.png")
        log.info("Saved demo: %s/%d_%s_preview.png", DEMO_SAVE_DIR, idx, name)

    try:
        if demo_mode:
            # Demo: render all screens once and exit
            for i in range(total):
                screen_idx = i
                render_current()
            log.info(
                "Demo complete — %d screens rendered to %s/", total, DEMO_SAVE_DIR
            )
            return

        # === MAIN LOOP ===
        while running:
            # --- RENDER PHASE ---
            render_current()

            # --- POLL PHASE ---
            poll_start = time.monotonic()
            while running:
                elapsed = time.monotonic() - poll_start
                if elapsed >= REFRESH_INTERVAL:
                    # Auto-refresh timeout
                    if auto_cycle:
                        screen_idx = (screen_idx + 1) % total
                    break

                event = inp.poll()
                if event == "KEY1":
                    # Previous screen
                    screen_idx = (screen_idx - 1) % total
                    break
                elif event == "KEY2":
                    # Next screen
                    screen_idx = (screen_idx + 1) % total
                    break
                elif event == "KEY3":
                    # Force refresh current screen
                    break
                elif event == "KEY4":
                    # Toggle auto-cycle
                    auto_cycle = not auto_cycle
                    log.info("Auto-cycle: %s", "ON" if auto_cycle else "OFF")
                    # Don't break — just toggle, keep polling

                time.sleep(POLL_SLEEP)

    finally:
        if display is not None:
            display.close()


if __name__ == "__main__":
    main()
