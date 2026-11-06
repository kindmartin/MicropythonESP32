# Helpers for the Waveshare ESP32-S3-Touch-LCD-1.47 (pines confirmados con el esquematico oficial)
# Funciona en los DOS firmwares: el normal y el de lvgl_micropython (donde machine.SPI no tiene constructor clasico, solo Bus/Device,
# y machine.SDCard usa otros nombres de parametros). En el firmware LVGL NO hagas "import display" si usas estos drivers directos:
# LVGL se queda con el SPI/I2C y los dos modos son excluyentes (reinicia con machine.reset() para cambiar de modo).
import machine

LVGL_FW = hasattr(machine.SPI, "Bus")      # True en lvgl_micropython

LCD_SCK, LCD_MOSI = 38, 39
LCD_CS, LCD_DC, LCD_RST, LCD_BL = 21, 45, 40, 46
I2C_SDA, I2C_SCL = 42, 41          # touch AXS5106L (0x63); la placa NO trae IMU
TP_RST, TP_INT = 47, 48
SD_CLK, SD_CMD, SD_D0, SD_D1, SD_D2, SD_D3 = 16, 15, 17, 18, 13, 14
BOOT_PIN = 0
VBAT_PIN = 12                      # BAT_ADC (esquematico), divisor 200K/100K
VBAT_DIV = 3                       # V = Vadc x 3


_bus = None
_dev = {}


def spi(baudrate=40_000_000):
    if not LVGL_FW:
        return machine.SPI(1, baudrate=baudrate, sck=LCD_SCK, mosi=LCD_MOSI)
    global _bus
    try:
        if _bus is None:
            _bus = machine.SPI.Bus(host=1, sck=LCD_SCK, mosi=LCD_MOSI)
        if baudrate not in _dev:
            _dev[baudrate] = machine.SPI.Device(spi_bus=_bus, freq=baudrate, cs=-1)   # el CS lo mueve el driver (st7789.py)
        return _dev[baudrate]
    except Exception as e:
        raise RuntimeError("SPI ocupado: en el firmware LVGL no importes 'display' si usas los drivers directos (reinicia) -> %r" % (e,))


def lcd(spi_bus=None, invert=True, x_offset=34):
    """JD9853 (ST7789-compatible) 172x320 portrait. invert/x_offset: ajusta si los colores salen negativos o la imagen corrida."""
    import lcd_jd9853
    return lcd_jd9853.JD9853(spi_bus or spi(), cs=LCD_CS, dc=LCD_DC, rst=LCD_RST, bl=None,
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
    # el touch puede dormir hasta que lo tocas: escanea tocando la pantalla
    return machine.I2C(0, scl=I2C_SCL, sda=I2C_SDA, freq=freq)


def touch(i2c_bus=None):
    import touch_axs5106
    return touch_axs5106.AXS5106(i2c_bus or i2c(), rst=TP_RST, int_pin=TP_INT)


def temp():
    """Temperatura del chip ESP32-S3 en C (sensor interno; no hay sensor de temperatura dedicado)."""
    import esp32
    return esp32.mcu_temperature()


def sd_mount(path="/sd"):
    """Monta la microSD por SDMMC (slot 1, 4 bits). Nombres de parametros distintos segun el firmware."""
    import os
    if LVGL_FW:
        sd = machine.SDCard(slot=1, width=4, clk=SD_CLK, cmd=SD_CMD, data_pins=(SD_D0, SD_D1, SD_D2, SD_D3))
    else:
        sd = machine.SDCard(slot=1, width=4, sck=SD_CLK, cmd=SD_CMD, data=(SD_D0, SD_D1, SD_D2, SD_D3))
    os.mount(sd, path)
    return sd


def vbat():
    """Tension de bateria en V, o None si VBAT_PIN no esta definido."""
    if VBAT_PIN is None:
        return None
    adc = machine.ADC(machine.Pin(VBAT_PIN), atten=machine.ADC.ATTN_11DB)
    uv = sum(adc.read_uv() for _ in range(16)) / 16
    return uv * VBAT_DIV / 1_000_000


def battery_percent():
    v = vbat()
    return None if v is None else max(0, min(100, int((v - 3.3) / (4.2 - 3.3) * 100)))
