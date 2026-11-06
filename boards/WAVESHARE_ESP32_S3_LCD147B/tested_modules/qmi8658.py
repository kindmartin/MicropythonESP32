import machine
import time
import struct

_ADDR = 0x6B

_WHO_AM_I  = 0x00
_CTRL1     = 0x02
_CTRL2     = 0x03
_CTRL3     = 0x04
_CTRL7     = 0x08
_STATUS1   = 0x2E
_AX_L      = 0x35
_GX_L      = 0x3B

_EN_ACC = 0x01
_EN_GYR = 0x02

_ACC_SCALE = {2: 16384, 4: 8192, 8: 4096, 16: 2048}
_GYR_SCALE = {16: 2048, 32: 1024, 64: 512, 128: 256,
              256: 128, 512: 64, 1024: 32, 2048: 16}


class QMI8658:
    """
    Driver for QMI8658 6-axis IMU (accelerometer + gyroscope).

    Usage:
        i2c = machine.I2C(0, scl=47, sda=48, freq=400_000)
        imu = QMI8658(i2c)
        ax, ay, az, gx, gy, gz = imu.read_all()
    """

    def __init__(self, i2c, addr=_ADDR, acc_scale=8, gyro_scale=512):
        self._i2c   = i2c
        self._addr  = addr
        self._buf6  = bytearray(6)
        self._buf12 = bytearray(12)

        who = self._r1(_WHO_AM_I)
        if who not in (0x05, 0x06, 0x07):
            raise RuntimeError("QMI8658 not found (WHO_AM_I=0x{:02X})".format(who))

        self._w(_CTRL1, 0x40)

        acc_bits = {2: 0, 4: 1, 8: 2, 16: 3}[acc_scale]
        self._w(_CTRL2, (acc_bits << 4) | 0x03)
        self._acc_lsb = _ACC_SCALE[acc_scale]

        gyr_bits = {16: 0, 32: 1, 64: 2, 128: 3, 256: 4,
                    512: 5, 1024: 6, 2048: 7}[gyro_scale]
        self._w(_CTRL3, (gyr_bits << 4) | 0x03)
        self._gyr_lsb = _GYR_SCALE[gyro_scale]

        self._w(_CTRL7, _EN_ACC | _EN_GYR)
        time.sleep_ms(10)

    def _w(self, reg, val):
        self._i2c.writeto_mem(self._addr, reg, bytes([val]))

    def _r1(self, reg):
        return self._i2c.readfrom_mem(self._addr, reg, 1)[0]

    def _ri(self, reg, buf):
        self._i2c.readfrom_mem_into(self._addr, reg, buf)

    def accel(self):
        """Return (ax, ay, az) in g."""
        self._ri(_AX_L, self._buf6)
        ax, ay, az = struct.unpack_from('<hhh', self._buf6)
        k = self._acc_lsb
        return ax / k, ay / k, az / k

    def gyro(self):
        """Return (gx, gy, gz) in degrees/s."""
        self._ri(_GX_L, self._buf6)
        gx, gy, gz = struct.unpack_from('<hhh', self._buf6)
        k = self._gyr_lsb
        return gx / k, gy / k, gz / k

    def read_all(self):
        """Return (ax, ay, az, gx, gy, gz) in one I2C burst."""
        self._ri(_AX_L, self._buf12)
        ax, ay, az, gx, gy, gz = struct.unpack_from('<hhhhhh', self._buf12)
        al, gl = self._acc_lsb, self._gyr_lsb
        return ax/al, ay/al, az/al, gx/gl, gy/gl, gz/gl

    @property
    def data_ready(self):
        return bool(self._r1(_STATUS1) & 0x03)
