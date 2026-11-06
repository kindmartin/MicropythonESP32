# Helpers para la Waveshare ESP32-S3-LCD-1.9 (version SIN touch, SKU 30995).
# Pines tomados de ports/esp32/boards/WAVESHARE_ESP32_S3_LCD19 (test_board.py); NO contrastados con el esquematico oficial.
import machine

LCD_SCK, LCD_MOSI = 10, 13
LCD_CS, LCD_DC, LCD_RST, LCD_BL = 12, 11, 9, 14
I2C_SCL, I2C_SDA = 48, 47          # IMU QMI8658 (0x6B)
IMU_INT1, IMU_INT2 = 8, 7
VBAT_PIN = 4                       # BAT_ADC, se asume divisor x3 (sin medir)
BOOT_PIN = 0
RGB_PIN = 15                       # WS2812
RGB_COUNT = 2                      # test_board.py asume 2 LEDs (sin confirmar)
SD_CLK, SD_CMD, SD_D0 = 41, 39, 40  # SDMMC 1 bit


def spi(baudrate=40_000_000):
    return machine.SPI(1, baudrate=baudrate, sck=LCD_SCK, mosi=LCD_MOSI)


def lcd(spi_bus=None, invert=True, x_offset=35):
    """ST7789V2 170x320 portrait. invert/x_offset: ajusta si los colores salen negativos o la imagen corrida.
    Este st7789.py activa el bit BGR de MADCTL (a diferencia del de la 1.47)."""
    import st7789
    return st7789.ST7789(spi_bus or spi(), cs=LCD_CS, dc=LCD_DC, rst=LCD_RST, bl=None,
                         width=170, height=320, x_offset=x_offset, y_offset=0, invert=invert)


_bl = None


def backlight(percent=80):
    """Brillo 0-100 (PWM 5 kHz en GPIO14)."""
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
    """Pone todos los LED WS2812 (0-255 por canal)."""
    import neopixel
    np = neopixel.NeoPixel(machine.Pin(RGB_PIN), RGB_COUNT)
    for i in range(RGB_COUNT):
        np[i] = (r, g, b)
    np.write()


def sd_mount(path="/sd"):
    """Monta la microSD por SDMMC (slot 1, 1 bit)."""
    import os
    sd = machine.SDCard(slot=1, width=1, sck=SD_CLK, cmd=SD_CMD, data=(SD_D0,))
    os.mount(sd, path)
    return sd


def vbat():
    """Tension de bateria en V (GPIO4, divisor x3 asumido)."""
    adc = machine.ADC(machine.Pin(VBAT_PIN), atten=machine.ADC.ATTN_11DB)
    uv = sum(adc.read_uv() for _ in range(16)) / 16
    return uv * 3 / 1_000_000


def battery_percent():
    return max(0, min(100, int((vbat() - 3.3) / (4.2 - 3.3) * 100)))
