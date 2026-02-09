"""Hardware interface for Waveshare 2.7" e-Paper HAT (B) V1.

Uses RPi.GPIO for GPIO and spidev for SPI — matches the original
Waveshare epdif.py that is proven to work.
"""

import time

import RPi.GPIO as GPIO
import spidev

# Pin definition (BCM numbering)
RST_PIN = 17
DC_PIN = 25
CS_PIN = 8
BUSY_PIN = 24

# Lazily initialized
SPI = None


def digital_write(pin, value):
    GPIO.output(pin, value)


def digital_read(pin):
    return GPIO.input(pin)


def delay_ms(delaytime):
    time.sleep(delaytime / 1000.0)


def spi_transfer(data):
    SPI.writebytes(data)


def spi_writebyte2(data):
    SPI.writebytes2(data)


def module_init():
    global SPI

    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(RST_PIN, GPIO.OUT)
    GPIO.setup(DC_PIN, GPIO.OUT)
    # CS_PIN (CE0) is managed by spidev — don't claim it via GPIO
    GPIO.setup(BUSY_PIN, GPIO.IN)

    SPI = spidev.SpiDev(0, 0)
    SPI.max_speed_hz = 2000000
    SPI.mode = 0b00
    return 0


def module_exit():
    global SPI
    if SPI is not None:
        SPI.close()
        SPI = None
    GPIO.output(RST_PIN, 0)
    GPIO.output(DC_PIN, 0)
    GPIO.cleanup([RST_PIN, DC_PIN, BUSY_PIN])
