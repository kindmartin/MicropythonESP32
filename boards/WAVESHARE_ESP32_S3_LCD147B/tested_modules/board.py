# Helpers for the Waveshare ESP32-S3-LCD-1.47B (pines del esquemático oficial)
import machine

LCD_SCK, LCD_MOSI = 40, 45
LCD_CS, LCD_DC, LCD_RST, LCD_BL = 42, 41, 39, 46
I2C_SCL, I2C_SDA = 47, 48          # IMU QMI8658 (0x6B)
IMU_INT1, IMU_INT2 = 13, 12
VBAT_PIN = 1                       # BAT_ADC, divisor 200K/100K -> V = Vadc x 3
BOOT_PIN = 0
RGB_PIN = 38                       # WS2812 (1 LED)
SD_CLK, SD_CMD, SD_D0, SD_D1, SD_D2, SD_D3 = 14, 15, 16, 18, 17, 21


def spi(baudrate=40_000_000):
    return machine.SPI(1, baudrate=baudrate, sck=LCD_SCK, mosi=LCD_MOSI)


def lcd(spi_bus=None, invert=True, x_offset=34):
    """ST7789 172x320 portrait (rotation 0). invert/x_offset: ajusta si los colores salen negativos o la imagen corrida."""
    import st7789
    return st7789.ST7789(spi_bus or spi(), cs=LCD_CS, dc=LCD_DC, rst=LCD_RST, bl=None,
                         width=172, height=320, x_offset=x_offset, y_offset=0, invert=invert)


_bl = None


def backlight(percent=80):
    """Brillo 0-100 (PWM 5 kHz en GPIO46)."""
    global _bl
    if _bl is None:
        _bl = machine.PWM(machine.Pin(LCD_BL), freq=5000)
    _bl.duty(max(0, min(100, percent)) * 1023 // 100)


def button():
    """BOOT (GPIO0, activo en bajo)."""
    return machine.Pin(BOOT_PIN, machine.Pin.IN, machine.Pin.PULL_UP)


def i2c(freq=400_000):
    return machine.I2C(0, scl=I2C_SCL, sda=I2C_SDA, freq=freq)


def imu(i2c_bus=None):
    import qmi8658
    return qmi8658.QMI8658(i2c_bus or i2c())


def rgb(r, g, b):
    """Pone el LED WS2812 (0-255 por canal)."""
    import neopixel
    np = neopixel.NeoPixel(machine.Pin(RGB_PIN), 1)
    np[0] = (r, g, b)
    np.write()


def sd_mount(path="/sd"):
    """Monta la microSD por SDMMC (slot 1, 4 bits)."""
    import os
    sd = machine.SDCard(slot=1, width=4, sck=SD_CLK, cmd=SD_CMD, data=(SD_D0, SD_D1, SD_D2, SD_D3))
    os.mount(sd, path)
    return sd


def vbat():
    """Tension de bateria en V (GPIO1, divisor x3)."""
    adc = machine.ADC(machine.Pin(VBAT_PIN), atten=machine.ADC.ATTN_11DB)
    uv = sum(adc.read_uv() for _ in range(16)) / 16
    return uv * 3 / 1_000_000


def battery_percent():
    return max(0, min(100, int((vbat() - 3.3) / (4.2 - 3.3) * 100)))
