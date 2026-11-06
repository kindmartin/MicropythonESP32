import machine
import time

_SWRESET = 0x01
_SLPOUT  = 0x11
_INVOFF  = 0x20
_INVON   = 0x21
_DISPON  = 0x29
_CASET   = 0x2A
_RASET   = 0x2B
_RAMWR   = 0x2C
_MADCTL  = 0x36
_COLMOD  = 0x3A

_MX  = 0x40
_MY  = 0x80
_MV  = 0x20
_BGR = 0x08

def color565(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)

BLACK   = 0x0000
WHITE   = 0xFFFF
RED     = color565(255,   0,   0)
GREEN   = color565(  0, 255,   0)
BLUE    = color565(  0,   0, 255)
YELLOW  = color565(255, 255,   0)
CYAN    = color565(  0, 255, 255)
MAGENTA = color565(255,   0, 255)


class ST7789:
    """
    Driver for ST7789V displays.
    Default config: Waveshare ESP32-S3-LCD-1.9 (170x320, x_offset=35).
    The 1.9\" board has a 90° hardware rotation, so the display is
    physically in landscape — call rotation(1) if needed.

    Usage:
        spi = machine.SPI(1, baudrate=40_000_000, sck=10, mosi=11)
        lcd = ST7789(spi, cs=9, dc=8, rst=12, bl=2)
        lcd.fill(BLACK)
    """

    def __init__(self, spi, cs, dc, rst, bl=None,
                 width=170, height=320,
                 x_offset=35, y_offset=0,
                 invert=False, bgr=False):
        self._spi    = spi
        self._cs     = machine.Pin(cs,  machine.Pin.OUT, value=1)
        self._dc     = machine.Pin(dc,  machine.Pin.OUT, value=0)
        self._rst    = machine.Pin(rst, machine.Pin.OUT, value=1) if rst is not None else None
        self._bl     = machine.Pin(bl,  machine.Pin.OUT, value=0) if bl is not None else None
        self.width   = width
        self.height  = height
        self._xoff   = x_offset
        self._yoff   = y_offset
        self._invert = invert
        self._bgr    = _BGR if bgr else 0   # bit BGR de MADCTL (orden R/B del panel)
        self._init()
        if self._bl:
            self._bl.value(1)

    def _cmd(self, cmd):
        self._dc.value(0); self._cs.value(0)
        self._spi.write(bytes([cmd]))
        self._cs.value(1)

    def _data(self, data):
        self._dc.value(1); self._cs.value(0)
        self._spi.write(data if isinstance(data, (bytes, bytearray, memoryview)) else bytes(data))
        self._cs.value(1)

    def _write(self, cmd, data=None):
        self._cmd(cmd)
        if data is not None:
            self._data(data)

    def _init(self):
        if self._rst is not None:
            self._rst.value(0); time.sleep_ms(10)
            self._rst.value(1); time.sleep_ms(120)
        self._write(_SWRESET); time.sleep_ms(150)
        self._write(_SLPOUT);  time.sleep_ms(10)
        self._write(_COLMOD, b'\x55')
        self._write(_MADCTL,  bytes([_MX | self._bgr]))
        if self._invert:
            self._write(_INVON)
        self._write(_DISPON);  time.sleep_ms(10)

    def _win(self, x0, y0, x1, y1):
        x0 += self._xoff; x1 += self._xoff
        y0 += self._yoff; y1 += self._yoff
        self._write(_CASET, bytearray([x0>>8, x0&0xFF, x1>>8, x1&0xFF]))
        self._write(_RASET, bytearray([y0>>8, y0&0xFF, y1>>8, y1&0xFF]))
        self._cmd(_RAMWR)

    def _flood(self, color, n):
        hi, lo = color >> 8, color & 0xFF
        chunk = bytearray([hi, lo] * 256)
        self._dc.value(1); self._cs.value(0)
        for _ in range(n // 256):
            self._spi.write(chunk)
        rem = n % 256
        if rem:
            self._spi.write(chunk[:rem * 2])
        self._cs.value(1)

    def fill(self, color):
        self._win(0, 0, self.width - 1, self.height - 1)
        self._flood(color, self.width * self.height)

    def fill_rect(self, x, y, w, h, color):
        self._win(x, y, x + w - 1, y + h - 1)
        self._flood(color, w * h)

    def pixel(self, x, y, color):
        if 0 <= x < self.width and 0 <= y < self.height:
            self._win(x, y, x, y)
            self._data(bytearray([color >> 8, color & 0xFF]))

    def hline(self, x, y, w, color):   self.fill_rect(x, y, w, 1, color)
    def vline(self, x, y, h, color):   self.fill_rect(x, y, 1, h, color)

    def rect(self, x, y, w, h, color):
        self.hline(x, y, w, color);           self.hline(x, y+h-1, w, color)
        self.vline(x, y, h, color);           self.vline(x+w-1, y, h, color)

    def blit_buffer(self, buf, x, y, w, h):
        self._win(x, y, x + w - 1, y + h - 1)
        self._data(buf)

    def backlight(self, on):
        if self._bl:
            self._bl.value(1 if on else 0)

    def invert(self, on):
        self._write(_INVON if on else _INVOFF)

    def rotation(self, r):
        """0=portrait  1=landscape  2=portrait-flip  3=landscape-flip"""
        madctl = (_MX, _MV, _MY, _MX|_MY|_MV)[r % 4] | self._bgr
        self._write(_MADCTL, bytes([madctl]))
        if r % 2:
            self.width, self.height = self.height, self.width
            self._xoff, self._yoff  = self._yoff, self._xoff
