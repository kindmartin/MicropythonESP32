# CST816D/CST816S single-point capacitive touch (I2C addr 0x15)
import time

_ADDR = 0x15


class CST816:
    def __init__(self, i2c, addr=_ADDR, rst=None, width=240, height=320):
        self.i2c = i2c
        self.addr = addr
        self.width = width
        self.height = height
        if rst is not None:
            import machine
            p = machine.Pin(rst, machine.Pin.OUT, value=0)
            time.sleep_ms(10)
            p.value(1)
            time.sleep_ms(50)

    def read(self):
        """Return (x, y) of the touch point, or None if not touched."""
        try:
            d = self.i2c.readfrom_mem(self.addr, 0x01, 6)
        except OSError:      # el chip duerme y no hace ACK hasta que lo tocan
            return None
        if (d[1] & 0x0F) == 0:
            return None
        return (((d[2] & 0x0F) << 8) | d[3], ((d[4] & 0x0F) << 8) | d[5])

    def gesture(self):
        return self.i2c.readfrom_mem(self.addr, 0x01, 1)[0]
