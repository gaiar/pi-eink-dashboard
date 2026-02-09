"""4-button input handler for Waveshare 2.7" e-Paper HAT (B) V1."""

import logging
import time

log = logging.getLogger("pi-eink-dashboard")

# Button GPIO pin mapping for the 2.7" e-Paper HAT
PINS = {
    "KEY1": 5,
    "KEY2": 6,
    "KEY3": 13,
    "KEY4": 19,
}

DEBOUNCE_MS = 200


class InputHandler:
    """Read button events with debouncing via gpiozero."""

    def __init__(self) -> None:
        self._buttons: dict[str, object] = {}
        self._last_event_time: dict[str, float] = {}
        self._available = False

        try:
            import gpiozero

            for name, pin in PINS.items():
                self._buttons[name] = gpiozero.Button(pin, pull_up=True)
                self._last_event_time[name] = 0.0
            self._available = True
            log.info("Buttons initialized: %s", list(PINS.keys()))
        except Exception as e:
            log.warning("Button input unavailable: %s", e)

    def poll(self) -> str | None:
        """Return the name of a pressed button, or None."""
        if not self._available:
            return None

        now = time.monotonic()
        for name, button in self._buttons.items():
            if button.is_pressed:  # type: ignore[union-attr]
                if (now - self._last_event_time[name]) > (DEBOUNCE_MS / 1000):
                    self._last_event_time[name] = now
                    return name
        return None
