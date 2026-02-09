"""EPD display driver wrapper for Waveshare 2.7" e-Paper HAT (B) V1."""

import logging
import os

from PIL import Image

log = logging.getLogger("pi-eink-dashboard")

# Display dimensions (landscape orientation: 264 wide x 176 tall)
WIDTH = 264
HEIGHT = 176


class DisplayNotFoundError(Exception):
    """Raised when the e-Paper HAT hardware is not detected."""


class Display:
    """Wrap the Waveshare EPD V1 driver with init/show/clear/close."""

    def __init__(self) -> None:
        if not os.path.exists("/dev/spidev0.0"):
            raise DisplayNotFoundError("SPI device /dev/spidev0.0 not found")

        try:
            from .driver.epd2in7b import EPD

            self._epd = EPD()
        except Exception as e:
            raise DisplayNotFoundError(f"Cannot initialize EPD: {e}") from e

        if self._epd.init() != 0:
            raise DisplayNotFoundError("EPD init() returned non-zero")

        self._epd.Clear()
        log.info("EPD initialized and cleared.")

    def show(self, black_image: Image.Image, red_image: Image.Image) -> None:
        """Display two 1-bit PIL Images (black layer and red layer).

        Images should be 264x176 mode '1'. White=255 (no ink), Black=0 (ink).
        Rotates from landscape (264x176) to portrait (176x264) for the EPD.
        """
        # EPD native resolution is 176x264 (portrait). Composer draws 264x176
        # (landscape). Rotate 90 CCW to match.
        black_rot = black_image.transpose(Image.ROTATE_90)
        red_rot = red_image.transpose(Image.ROTATE_90)
        black_buf = self._epd.getbuffer(black_rot)
        red_buf = self._epd.getbuffer(red_rot)
        self._epd.display(black_buf, red_buf)

    def clear(self) -> None:
        """Clear the display to white."""
        self._epd.Clear()

    def close(self) -> None:
        """Clear display and enter sleep mode."""
        try:
            self._epd.Clear()
            self._epd.sleep()
        except Exception:
            log.exception("Error during display close")
