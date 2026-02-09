"""Hardware interface for Waveshare 2.7" e-Paper HAT (B) V1.

Uses gpiozero for GPIO and spidev for SPI.
Lazy initialization to avoid GPIO conflicts on import.
"""

import logging
import time

logger = logging.getLogger(__name__)

# Pin definition (BCM numbering)
RST_PIN = 17
DC_PIN = 25
CS_PIN = 8
BUSY_PIN = 24

# Lazily initialized
_rst = None
_dc = None
_busy = None
_spi = None


def _ensure_init():
    global _rst, _dc, _busy, _spi
    if _spi is not None:
        return

    import spidev
    import gpiozero

    _rst = gpiozero.LED(RST_PIN)
    _dc = gpiozero.LED(DC_PIN)
    _busy = gpiozero.Button(BUSY_PIN, pull_up=False)

    _spi = spidev.SpiDev(0, 0)
    _spi.max_speed_hz = 2000000
    _spi.mode = 0b00


def digital_write(pin, value):
    _ensure_init()
    if pin == RST_PIN:
        _rst.on() if value else _rst.off()
    elif pin == DC_PIN:
        _dc.on() if value else _dc.off()


def digital_read(pin):
    _ensure_init()
    if pin == BUSY_PIN:
        return _busy.value
    return 0


def delay_ms(delaytime):
    time.sleep(delaytime / 1000.0)


def spi_transfer(data):
    _ensure_init()
    _spi.writebytes(data)


def spi_writebyte2(data):
    _ensure_init()
    _spi.writebytes2(data)


def module_init():
    _ensure_init()
    return 0


def module_exit():
    global _rst, _dc, _busy, _spi
    logger.debug("spi end")
    if _spi is not None:
        _spi.close()
    if _rst is not None:
        _rst.off()
        _rst.close()
    if _dc is not None:
        _dc.off()
        _dc.close()
    if _busy is not None:
        _busy.close()
    _rst = _dc = _busy = _spi = None
