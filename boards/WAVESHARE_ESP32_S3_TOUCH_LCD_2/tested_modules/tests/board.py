# Helpers for the Waveshare ESP32-S3-Touch-LCD-2
import machine

LCD_SCK, LCD_MOSI, LCD_MISO = 39, 38, 40
LCD_CS, LCD_DC, LCD_BL = 45, 42, 1
SD_CS = 41
I2C_SDA, I2C_SCL = 48, 47
VBAT_PIN = 5
BOOT_PIN = 0


def spi(baudrate=20_000_000):
    return machine.SPI(1, baudrate=baudrate, sck=LCD_SCK, mosi=LCD_MOSI, miso=LCD_MISO)


def lcd(spi_bus=None):
    import st7789
    # ST7789T3 has no RST pin (software reset); IPS panel -> inverted colours
    return st7789.ST7789(spi_bus or spi(), cs=LCD_CS, dc=LCD_DC, rst=None, bl=None,
                         width=240, height=320, x_offset=0, y_offset=0, invert=True)


_bl = None


def backlight(percent=80):
    """Set LCD backlight brightness 0-100 (PWM on GPIO1, 5 kHz)."""
    global _bl
    if _bl is None:
        _bl = machine.PWM(machine.Pin(LCD_BL), freq=5000)
    _bl.duty(max(0, min(100, percent)) * 1023 // 100)


def button():
    """BOOT button (GPIO0, active low). button().value() == 0 when pressed."""
    return machine.Pin(BOOT_PIN, machine.Pin.IN, machine.Pin.PULL_UP)


def i2c(freq=400_000):
    return machine.I2C(0, scl=I2C_SCL, sda=I2C_SDA, freq=freq)


def touch(i2c_bus=None):
    import cst816
    return cst816.CST816(i2c_bus or i2c())


def imu(i2c_bus=None):
    import qmi8658
    return qmi8658.QMI8658(i2c_bus or i2c())


def sd_mount(path="/sd", spi_bus=None):
    """Mount the microSD (SPI mode) on the SPI bus shared with the LCD.
    Uses micropython-lib sdcard.py on the same machine.SPI as the LCD; the whole
    bus runs at 20 MHz after this call (machine.SDCard cannot share the bus)."""
    import os
    import sdcard
    # LCD CS must be high so it ignores SD traffic on the shared bus
    machine.Pin(LCD_CS, machine.Pin.OUT, value=1)
    sd = sdcard.SDCard(spi_bus or spi(), machine.Pin(SD_CS, machine.Pin.OUT), baudrate=20_000_000)
    os.mount(sd, path)
    return sd


def vbat():
    """Battery voltage in volts (GPIO5 through a 1/3 divider)."""
    adc = machine.ADC(machine.Pin(VBAT_PIN), atten=machine.ADC.ATTN_11DB)
    uv = sum(adc.read_uv() for _ in range(16)) / 16
    return uv * 3 / 1_000_000


def battery_percent():
    """Rough LiPo charge level 0-100 from vbat() (3.3 V empty, 4.2 V full)."""
    return max(0, min(100, int((vbat() - 3.3) / (4.2 - 3.3) * 100)))


def camera(**kwargs):
    """Camera using the pins baked into the firmware (needs the camera user C module)."""
    from camera import Camera
    return Camera(**kwargs)


def preview(lcd_dev, cam, frames=100):
    """Show camera frames on the LCD (UNTESTED). Camera must be RGB565 and
    frame_size must fit the LCD (e.g. QVGA 320x240 with lcd.rotation(1))."""
    for _ in range(frames):
        buf = cam.capture()
        if buf is None:
            continue
        # If colours look wrong, byte-swap the buffer (camera is little-endian,
        # ST7789 expects big-endian) before blitting.
        lcd_dev.blit_buffer(buf, 0, 0, cam.get_pixel_width(), cam.get_pixel_height())
