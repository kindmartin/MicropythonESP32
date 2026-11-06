# (archivo lcd_jd9853.py: NO se llama jd9853.py porque chocaria con el driver congelado de lvgl_micropython)
# JD9853 (1.47" IPS 172x320) sobre la API de st7789.ST7789. Secuencia de init copiada del demo oficial de Waveshare
# (Arduino/examples/01_gfx_helloworld, lcd_reg_init). Es ST7789-compatible salvo el init: MADCTL=0x00 en vertical (sin MX).
import time
import st7789

_INIT = (
    (0xDF, b"\x98\x53"),
    (0xB2, b"\x23"),
    (0xB7, b"\x00\x47\x00\x6F"),
    (0xBB, b"\x1C\x1A\x55\x73\x63\xF0"),
    (0xC0, b"\x44\xA4"),
    (0xC1, b"\x16"),
    (0xC3, b"\x7D\x07\x14\x06\xCF\x71\x72\x77"),
    (0xC4, b"\x00\x00\xA0\x79\x0B\x0A\x16\x79\x0B\x0A\x16\x82"),
    (0xC8, b"\x3F\x32\x29\x29\x27\x2B\x27\x28\x28\x26\x25\x17\x12\x0D\x04\x00"
           b"\x3F\x32\x29\x29\x27\x2B\x27\x28\x28\x26\x25\x17\x12\x0D\x04\x00"),
    (0xD0, b"\x04\x06\x6B\x0F\x00"),
    (0xD7, b"\x00\x30"),
    (0xE6, b"\x14"),
    (0xDE, b"\x01"),
    (0xB7, b"\x03\x13\xEF\x35\x35"),
    (0xC1, b"\x14\x15\xC0"),
    (0xC2, b"\x06\x3A"),
    (0xC4, b"\x72\x12"),
    (0xBE, b"\x00"),
    (0xDE, b"\x02"),
    (0xE5, b"\x00\x02\x00"),
    (0xE5, b"\x01\x02\x00"),
    (0xDE, b"\x00"),
    (0x35, b"\x00"),
    (0x3A, b"\x05"),
    (0x2A, b"\x00\x22\x00\xCD"),
    (0x2B, b"\x00\x00\x01\x3F"),
    (0xDE, b"\x02"),
    (0xE5, b"\x00\x02\x00"),
    (0xDE, b"\x00"),
    (0x36, b"\x00"),
)


class JD9853(st7789.ST7789):
    def __init__(self, spi, cs, dc, rst, bl=None, width=172, height=320,
                 x_offset=34, y_offset=0, invert=True, bgr=False):
        super().__init__(spi, cs, dc, rst, bl, width, height, x_offset, y_offset, invert, bgr)

    def _init(self):
        if self._rst is not None:
            self._rst.value(0); time.sleep_ms(10)
            self._rst.value(1); time.sleep_ms(120)
        self._write(0x01); time.sleep_ms(150)       # SWRESET
        self._write(0x11); time.sleep_ms(120)       # SLPOUT
        for cmd, data in _INIT:
            self._write(cmd, data)
        self._write(0x21)                           # INVON (el demo lo deja encendido: panel IPS)
        time.sleep_ms(10)
        if not self._invert:
            self._write(0x20)
        self._write(0x29)                           # DISPON
        time.sleep_ms(10)

    def rotation(self, r):
        """0=vertical 1,2,3 = giros (r != 0 sin verificar en el panel)."""
        madctl = (0x00, 0x60, 0xC0, 0xA0)[r % 4] | self._bgr
        self._write(0x36, bytes([madctl]))
        if r % 2:
            self.width, self.height = self.height, self.width
            self._xoff, self._yoff = self._yoff, self._xoff
