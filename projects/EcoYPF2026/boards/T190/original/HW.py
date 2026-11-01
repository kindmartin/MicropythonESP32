
# HW.py
# Pin map y helpers para Heltec Vision Master T190 (ESP32-S3R8) con MicroPython.
# Display TFT 170x320 integrado (N190-1732TBWPG01-C30), sin cellular, sin GPS.

import machine

# ── Display TFT integrado (SPI interno, NO en headers) ──────────────────────
# Controlador: ST7789 o GC9107 (170 RGB x 320, 4-wire SPI)
TFT_MOSI   = 48   # TFT_SDA
TFT_SCK    = 38   # TFT_SCL
TFT_CS     = 39   # TFT_CS
TFT_DC     = 47   # TFT_RS  (Data/Command)
TFT_RST    = 40   # TFT_RST
TFT_BL     = 17   # LEDK_EN (backlight enable via AW9364DNR)
TFT_PWR    = 7    # VTFT_Ctrl (P-MOSFET, LOW = display encendido)

TFT_WIDTH  = 170
TFT_HEIGHT = 320
TFT_SPI_ID = 1
TFT_BAUDRATE = 40_000_000

# ── UART para Phaserunner (Modbus RTU) ──────────────────────────────────────
# UART0 (GPIO43/44) está en J2 y es el puerto serie USB/debug.
# Usar UART1 con pines disponibles en J3 para el Phaserunner.
# GPIO4 y GPIO3 están libres en J3 (ADC1_CH3 y ADC1_CH2, sin función especial).
PR_UART_ID   = 1
PR_UART_TX   = 4    # J3 pin 8
PR_UART_RX   = 3    # J3 pin 9
PR_UART_BAUD = 115200

# ── ADC para acelerador y freno (0–3.3 V) ───────────────────────────────────
# GPIO8 y GPIO9 están ocupados por LoRa_NSS/SCK — usar GPIO4/3 u otros libres.
# Throttle y brake en J3: GPIO4 (ADC1_CH3) y GPIO2 (ADC1_CH1).
# NOTA: si no se usa LoRa, GPIO8/9/10/11 también quedan disponibles.
ADC_THROTTLE_PIN = 4    # J3 pin 8  — ADC1_CH3
ADC_BRAKE_PIN    = 2    # J3 pin 10 — ADC1_CH1

# ── DAC MCP4725 (I2C) ────────────────────────────────────────────────────────
# I2C externo: usar QuickLink I2C (GPIO1=SCL, GPIO2=SDA) o cualquier par libre.
# Si se usa GPIO2 para freno ADC, el I2C externo debe ir a otro par.
# Opción: usar GPIO3 (SDA) y GPIO4 (SCL) — pero chocan con UART PR.
# Solución práctica: I2C en GPIO1 (SCL) y GPIO2 (SDA) si el freno va a GPIO9.
# Ajustar según cableado final.
I2C_ID  = 0
I2C_SCL = 1    # QL_SCL — J3 pin 11
I2C_SDA = 2    # QL_SDA — J3 pin 10

DAC0_ADDR = 0x60   # Throttle DAC
DAC1_ADDR = 0x61   # Brake DAC

# ── Contador de pulsos de rueda ──────────────────────────────────────────────
TRIP_COUNTER_PIN       = 8    # J3 pin 7 (LoRa_NSS si hay LoRa; libre si no)
TRIP_COUNTER_ID        = 0
TRIP_COUNTER_FILTER_NS = 50_000
TRIP_COUNTER_EDGE      = "RISING"
TRIP_COUNTER_INTERVAL_MS = 1000

# ── Botonería ────────────────────────────────────────────────────────────────
# El T190 tiene UN botón de usuario: S3 en GPIO21 (pull-up 10K a 3.3V).
# Para UP/DOWN se puede usar un divisor resistivo en un ADC libre.
PAGE_BTN_PIN  = 21   # USER_KEY S3 — activo-bajo
UPDOWN_ADC_PIN = 9   # J3 pin 6 (LoRa_SCK si hay LoRa; libre si no)

# ── Batería del sistema (ADC interno) ───────────────────────────────────────
VBAT_ADC_PIN   = 6    # VBAT_Read (dividido R9/R11, habilitar Q3)
VBAT_ADC_CTRL  = 6    # mismo GPIO activa el circuito lector
VBAT_DIV_RATIO = (390 + 100) / 100.0   # R9=390K, R11=100K → ×4.9

# ── VEXT (salida 3.3V conmutable para sensores externos) ────────────────────
VEXT_CTRL_PIN = 5    # Ve_Ctrl — HIGH = VEXT habilitado

# ── Deep sleep wake ─────────────────────────────────────────────────────────
MAIN_WAKE_PIN = 21   # Botón usuario S3 (o cambiar a pin throttle si se desea)

# ── UART0 debug / REPL (J2 pines 9 y 10) ────────────────────────────────────
# GPIO43 = U0_TXD,  GPIO44 = U0_RXD  (también accesible via USB-JTAG/CDC)


# ── Utilidades ───────────────────────────────────────────────────────────────

def make_i2c(freq=400_000):
    return machine.I2C(I2C_ID,
                       scl=machine.Pin(I2C_SCL),
                       sda=machine.Pin(I2C_SDA),
                       freq=freq)


def make_adc(pin_num, atten=None, width=None):
    adc = machine.ADC(machine.Pin(pin_num))
    if atten is None:
        try:
            atten = machine.ADC.ATTN_11DB
        except AttributeError:
            atten = machine.ADC.ATTN_6DB
    if width is None:
        try:
            width = machine.ADC.WIDTH_12BIT
        except AttributeError:
            width = None
    try:
        adc.atten(atten)
    except Exception:
        pass
    if width is not None:
        try:
            adc.width(width)
        except Exception:
            pass
    return adc


def adc_read_volts(adc, vref=3.3):
    try:
        return (adc.read() * (float(vref) / 4095.0))
    except Exception:
        return 0.0


def make_input(pin_num, pull=None):
    if pull:
        return machine.Pin(pin_num, machine.Pin.IN, pull)
    return machine.Pin(pin_num, machine.Pin.IN)


def make_output(pin_num, *, value=1):
    pin = machine.Pin(pin_num, machine.Pin.OUT)
    pin.value(value)
    return pin


def display_power_on():
    """Enciende el display (VTFT_Ctrl LOW activa el P-MOSFET)."""
    make_output(TFT_PWR, value=0)


def display_power_off():
    make_output(TFT_PWR, value=1)


def backlight_on():
    make_output(TFT_BL, value=1)


def backlight_off():
    make_output(TFT_BL, value=0)


def vext_enable():
    make_output(VEXT_CTRL_PIN, value=1)


def vext_disable():
    make_output(VEXT_CTRL_PIN, value=0)


# ── DAC MCP4725 helpers (idénticos al proyecto original) ─────────────────────

def _dac_write_register(i2c, addr, code):
    code = max(0, min(4095, int(code)))
    hi = (code >> 4) & 0xFF
    lo = (code & 0x0F) << 4
    i2c.writeto(addr, bytes([0x40, hi, lo]))


def set_dac_volts(i2c, addr, volts, vref=3.3):
    v = max(0.0, min(float(volts), float(vref)))
    code = int(4095 * v / float(vref))
    _dac_write_register(i2c, addr, code)
    return code


def dacs_zero_both(i2c):
    _dac_write_register(i2c, DAC0_ADDR, 0)
    _dac_write_register(i2c, DAC1_ADDR, 0)
