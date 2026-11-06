# (archivo touch_axs5106.py: NO se llama axs5106.py porque chocaria con el driver congelado de lvgl_micropython)
# AXS5106L touch (I2C 0x63). Protocolo del demo oficial de Waveshare (libraries/esp_lcd_touch_axs5106l):
# reset 200 ms bajo + 300 ms alto; ID en reg 0x08 (3 bytes); toques en reg 0x01 (14 bytes):
#   d[1] = n toques; punto i: x = (d[2+6i]&0xF)<<8|d[3+6i], y = (d[4+6i]&0xF)<<8|d[5+6i].
# En vertical (rotation 0) el demo invierte x: x = width-1-xraw.
import time

_ADDR = 0x63
_ID_REG = 0x08
_DATA_REG = 0x01


class AXS5106:
    def __init__(self, i2c, addr=_ADDR, rst=None, width=172, height=320, int_pin=None):
        self.i2c = i2c
        self.int = None
        if int_pin is not None:
            import machine
            self.int = machine.Pin(int_pin, machine.Pin.IN, machine.Pin.PULL_UP)
        self.addr = addr
        self.width = width
        self.height = height
        if rst is not None:
            import machine
            p = machine.Pin(rst, machine.Pin.OUT, value=0)
            time.sleep_ms(200)
            p.value(1)
            time.sleep_ms(300)

    def _rd(self, reg, n):
        # Como Arduino Wire: escribir el registro CON STOP y leer en otra transaccion (no repeated start)
        self.i2c.writeto(self.addr, bytes([reg]), True)
        return self.i2c.readfrom(self.addr, n)

    def chip_id(self):
        return self._rd(_ID_REG, 3)

    def raw(self):
        return self._rd(_DATA_REG, 14)

    def read(self):
        """(x, y) del primer toque en pantalla vertical, o None."""
        try:
            d = self.raw()
        except OSError:
            return None
        if d[1] == 0:
            return None
        x = ((d[2] & 0x0F) << 8) | d[3]
        y = ((d[4] & 0x0F) << 8) | d[5]
        return (self.width - 1 - x, y)
