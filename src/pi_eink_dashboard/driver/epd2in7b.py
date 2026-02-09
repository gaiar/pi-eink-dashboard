"""Waveshare 2.7" e-Paper HAT (B) driver — V1 hardware.

Based on the original epd2in7b.py from Waveshare, adapted to use
the epdconfig module interface.

BUSY pin polarity: 0 = busy, 1 = idle (opposite of V2).
Data commands: 0x10 (black), 0x13 (red) (different from V2's 0x24/0x26).
"""

import logging
from . import epdconfig

# Display resolution
EPD_WIDTH = 176
EPD_HEIGHT = 264

# Commands
PANEL_SETTING = 0x00
POWER_SETTING = 0x01
POWER_OFF = 0x02
POWER_ON = 0x04
BOOSTER_SOFT_START = 0x06
DEEP_SLEEP = 0x07
DATA_START_TRANSMISSION_1 = 0x10
DATA_STOP = 0x11
DISPLAY_REFRESH = 0x12
DATA_START_TRANSMISSION_2 = 0x13
PARTIAL_DISPLAY_REFRESH = 0x16
LUT_FOR_VCOM = 0x20
LUT_WHITE_TO_WHITE = 0x21
LUT_BLACK_TO_WHITE = 0x22
LUT_WHITE_TO_BLACK = 0x23
LUT_BLACK_TO_BLACK = 0x24
PLL_CONTROL = 0x30
VCOM_AND_DATA_INTERVAL_SETTING = 0x50
TCON_RESOLUTION = 0x61
GET_STATUS = 0x71
VCM_DC_SETTING_REGISTER = 0x82

logger = logging.getLogger(__name__)


class EPD:
    def __init__(self):
        self.reset_pin = epdconfig.RST_PIN
        self.dc_pin = epdconfig.DC_PIN
        self.busy_pin = epdconfig.BUSY_PIN
        self.width = EPD_WIDTH
        self.height = EPD_HEIGHT

    # LUT tables for V1 hardware
    lut_vcom_dc = [
        0x00,
        0x00,
        0x00,
        0x1A,
        0x1A,
        0x00,
        0x00,
        0x01,
        0x00,
        0x0A,
        0x0A,
        0x00,
        0x00,
        0x08,
        0x00,
        0x0E,
        0x01,
        0x0E,
        0x01,
        0x10,
        0x00,
        0x0A,
        0x0A,
        0x00,
        0x00,
        0x08,
        0x00,
        0x04,
        0x10,
        0x00,
        0x00,
        0x05,
        0x00,
        0x03,
        0x0E,
        0x00,
        0x00,
        0x0A,
        0x00,
        0x23,
        0x00,
        0x00,
        0x00,
        0x01,
    ]

    lut_ww = [
        0x90,
        0x1A,
        0x1A,
        0x00,
        0x00,
        0x01,
        0x40,
        0x0A,
        0x0A,
        0x00,
        0x00,
        0x08,
        0x84,
        0x0E,
        0x01,
        0x0E,
        0x01,
        0x10,
        0x80,
        0x0A,
        0x0A,
        0x00,
        0x00,
        0x08,
        0x00,
        0x04,
        0x10,
        0x00,
        0x00,
        0x05,
        0x00,
        0x03,
        0x0E,
        0x00,
        0x00,
        0x0A,
        0x00,
        0x23,
        0x00,
        0x00,
        0x00,
        0x01,
    ]

    lut_bw = [
        0xA0,
        0x1A,
        0x1A,
        0x00,
        0x00,
        0x01,
        0x00,
        0x0A,
        0x0A,
        0x00,
        0x00,
        0x08,
        0x84,
        0x0E,
        0x01,
        0x0E,
        0x01,
        0x10,
        0x90,
        0x0A,
        0x0A,
        0x00,
        0x00,
        0x08,
        0xB0,
        0x04,
        0x10,
        0x00,
        0x00,
        0x05,
        0xB0,
        0x03,
        0x0E,
        0x00,
        0x00,
        0x0A,
        0xC0,
        0x23,
        0x00,
        0x00,
        0x00,
        0x01,
    ]

    lut_bb = [
        0x90,
        0x1A,
        0x1A,
        0x00,
        0x00,
        0x01,
        0x40,
        0x0A,
        0x0A,
        0x00,
        0x00,
        0x08,
        0x84,
        0x0E,
        0x01,
        0x0E,
        0x01,
        0x10,
        0x80,
        0x0A,
        0x0A,
        0x00,
        0x00,
        0x08,
        0x00,
        0x04,
        0x10,
        0x00,
        0x00,
        0x05,
        0x00,
        0x03,
        0x0E,
        0x00,
        0x00,
        0x0A,
        0x00,
        0x23,
        0x00,
        0x00,
        0x00,
        0x01,
    ]

    lut_wb = [
        0x90,
        0x1A,
        0x1A,
        0x00,
        0x00,
        0x01,
        0x20,
        0x0A,
        0x0A,
        0x00,
        0x00,
        0x08,
        0x84,
        0x0E,
        0x01,
        0x0E,
        0x01,
        0x10,
        0x10,
        0x0A,
        0x0A,
        0x00,
        0x00,
        0x08,
        0x00,
        0x04,
        0x10,
        0x00,
        0x00,
        0x05,
        0x00,
        0x03,
        0x0E,
        0x00,
        0x00,
        0x0A,
        0x00,
        0x23,
        0x00,
        0x00,
        0x00,
        0x01,
    ]

    def reset(self):
        epdconfig.digital_write(self.reset_pin, 1)
        epdconfig.delay_ms(200)
        epdconfig.digital_write(self.reset_pin, 0)
        epdconfig.delay_ms(2)
        epdconfig.digital_write(self.reset_pin, 1)
        epdconfig.delay_ms(200)

    def send_command(self, command):
        epdconfig.digital_write(self.dc_pin, 0)
        epdconfig.spi_transfer([command])

    def send_data(self, data):
        epdconfig.digital_write(self.dc_pin, 1)
        epdconfig.spi_transfer([data])

    def send_data2(self, data):
        epdconfig.digital_write(self.dc_pin, 1)
        epdconfig.spi_writebyte2(data)

    def wait_until_idle(self, timeout_ms=30000):
        """Wait until BUSY pin goes HIGH (idle). V1: 0=busy, 1=idle."""
        logger.debug("e-Paper busy")
        elapsed = 0
        while epdconfig.digital_read(self.busy_pin) == 0:
            epdconfig.delay_ms(100)
            elapsed += 100
            if elapsed >= timeout_ms:
                logger.warning("e-Paper busy timeout after %d ms", timeout_ms)
                break
        logger.debug("e-Paper busy release")

    def set_lut(self):
        self.send_command(LUT_FOR_VCOM)
        for b in self.lut_vcom_dc:
            self.send_data(b)

        self.send_command(LUT_WHITE_TO_WHITE)
        for b in self.lut_ww:
            self.send_data(b)

        self.send_command(LUT_BLACK_TO_WHITE)
        for b in self.lut_bw:
            self.send_data(b)

        self.send_command(LUT_WHITE_TO_BLACK)
        for b in self.lut_bb:
            self.send_data(b)

        self.send_command(LUT_BLACK_TO_BLACK)
        for b in self.lut_wb:
            self.send_data(b)

    def init(self):
        if epdconfig.module_init() != 0:
            return -1

        self.reset()

        self.send_command(POWER_ON)
        self.wait_until_idle()

        self.send_command(PANEL_SETTING)
        self.send_data(0xAF)  # KWR-AF

        self.send_command(PLL_CONTROL)
        self.send_data(0x3A)  # 100Hz

        self.send_command(POWER_SETTING)
        self.send_data(0x03)
        self.send_data(0x00)
        self.send_data(0x2B)
        self.send_data(0x2B)
        self.send_data(0x09)

        self.send_command(BOOSTER_SOFT_START)
        self.send_data(0x07)
        self.send_data(0x07)
        self.send_data(0x17)

        # Power optimization
        self.send_command(0xF8)
        self.send_data(0x60)
        self.send_data(0xA5)

        self.send_command(0xF8)
        self.send_data(0x89)
        self.send_data(0xA5)

        self.send_command(0xF8)
        self.send_data(0x90)
        self.send_data(0x00)

        self.send_command(0xF8)
        self.send_data(0x93)
        self.send_data(0x2A)

        self.send_command(0xF8)
        self.send_data(0x73)
        self.send_data(0x41)

        self.send_command(VCM_DC_SETTING_REGISTER)
        self.send_data(0x12)

        self.send_command(VCOM_AND_DATA_INTERVAL_SETTING)
        self.send_data(0x87)

        self.set_lut()

        self.send_command(PARTIAL_DISPLAY_REFRESH)
        self.send_data(0x00)

        return 0

    def getbuffer(self, image):
        """Convert a 1-bit PIL image to the EPD buffer format."""
        buf = [0xFF] * (self.width * self.height // 8)
        image_monocolor = image.convert("1")
        imwidth, imheight = image_monocolor.size
        pixels = image_monocolor.load()

        if imwidth == self.width and imheight == self.height:
            for y in range(imheight):
                for x in range(imwidth):
                    if pixels[x, y] != 0:
                        buf[(x + y * self.width) // 8] &= ~(0x80 >> (x % 8))
        elif imwidth == self.height and imheight == self.width:
            for y in range(imheight):
                for x in range(imwidth):
                    newx = y
                    newy = self.height - x - 1
                    if pixels[x, y] != 0:
                        buf[(newx + newy * self.width) // 8] &= ~(0x80 >> (y % 8))
        return buf

    def display(self, imageblack, imagered):
        """Send black and red image buffers to the display and refresh.

        V1 protocol: command 0x10 for black, 0x13 for red.
        Sends data byte-by-byte matching original Waveshare driver.
        """
        self.send_command(TCON_RESOLUTION)
        self.send_data(EPD_WIDTH >> 8)
        self.send_data(EPD_WIDTH & 0xFF)
        self.send_data(EPD_HEIGHT >> 8)
        self.send_data(EPD_HEIGHT & 0xFF)

        if imageblack is not None:
            self.send_command(DATA_START_TRANSMISSION_1)
            epdconfig.delay_ms(2)
            for i in range(0, self.width * self.height // 8):
                self.send_data(imageblack[i])
            self.send_command(DATA_STOP)

        if imagered is not None:
            self.send_command(DATA_START_TRANSMISSION_2)
            epdconfig.delay_ms(2)
            for i in range(0, self.width * self.height // 8):
                self.send_data(imagered[i])
            self.send_command(DATA_STOP)

        self.send_command(DISPLAY_REFRESH)
        self.wait_until_idle()

    def Clear(self):
        """Clear the display to white."""
        buf_size = self.width * self.height // 8

        self.send_command(TCON_RESOLUTION)
        self.send_data(EPD_WIDTH >> 8)
        self.send_data(EPD_WIDTH & 0xFF)
        self.send_data(EPD_HEIGHT >> 8)
        self.send_data(EPD_HEIGHT & 0xFF)

        # V1 polarity: bit=1 means ink, bit=0 means no ink (white)
        self.send_command(DATA_START_TRANSMISSION_1)
        epdconfig.delay_ms(2)
        for i in range(buf_size):
            self.send_data(0x00)
        self.send_command(DATA_STOP)

        self.send_command(DATA_START_TRANSMISSION_2)
        epdconfig.delay_ms(2)
        for i in range(buf_size):
            self.send_data(0x00)
        self.send_command(DATA_STOP)

        self.send_command(DISPLAY_REFRESH)
        self.wait_until_idle()

    def sleep(self):
        self.send_command(VCOM_AND_DATA_INTERVAL_SETTING)
        self.send_data(0xF7)

        self.send_command(POWER_OFF)
        self.wait_until_idle()

        self.send_command(DEEP_SLEEP)
        self.send_data(0xA5)
        epdconfig.delay_ms(2000)
        epdconfig.module_exit()
