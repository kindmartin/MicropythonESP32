
# main.py — Heltec T190  firmware inicial
# Funcionalidad: display ON + botón USER_KEY (GPIO21) cicla pantallas de prueba.

import machine
import uasyncio as asyncio
from machine import Pin, SPI

import HW
from drivers.tft170 import TFT170, rgb565

# ── Colores ──────────────────────────────────────────────────────────────────
BLACK  = 0x0000
WHITE  = 0xFFFF
RED    = rgb565(220,  40,  40)
GREEN  = rgb565( 40, 200,  40)
BLUE   = rgb565( 40, 100, 220)
YELLOW = rgb565(240, 220,   0)
CYAN   = rgb565(  0, 200, 220)

# ── Pantallas de demostración ────────────────────────────────────────────────
SCREENS = [
    {"bg": BLACK,  "fg": WHITE,  "title": "T190 OK",      "line2": "Heltec ESP32-S3"},
    {"bg": BLUE,   "fg": WHITE,  "title": "DISPLAY",      "line2": "170 x 320  TFT"},
    {"bg": RED,    "fg": WHITE,  "title": "BOTON S3",     "line2": "cicla pantallas"},
    {"bg": GREEN,  "fg": BLACK,  "title": "eBike2026",    "line2": "Firmware v0.1"},
    {"bg": YELLOW, "fg": BLACK,  "title": "GPIO OK",      "line2": "ESP32-S3R8"},
]

_screen_index = 0
_btn_pending  = False   # flag entre ISR y tarea asyncio


def _draw_screen(tft, idx):
    s = SCREENS[idx % len(SCREENS)]
    tft.fill(s["bg"])
    # Título centrado (fuente 8px del framebuf, scale x2 manual)
    _draw_text_big(tft, s["title"], s["fg"], y=100)
    _draw_text_big(tft, s["line2"], s["fg"], y=140)
    # Número de pantalla abajo
    tft.text("{}/{}".format(idx + 1, len(SCREENS)), 4, 305, s["fg"])
    tft.show()


def _draw_text_big(tft, text, color, y):
    """Escala 2x la fuente 8px integrada usando dos rect por bit."""
    # framebuf.text() usa fuente 8x8; la dibujamos en un buf temporal y luego
    # la escalamos manualmente para que sea legible en el display de 170px.
    x_start = max(0, (tft.width - len(text) * 16) // 2)
    # versión simple: texto normal x1 centrado (reemplazar con fuente mejor después)
    x_start8 = max(0, (tft.width - len(text) * 8) // 2)
    tft.text(text, x_start8, y, color)


# ── Tarea botón ───────────────────────────────────────────────────────────────

async def button_task(tft):
    global _screen_index, _btn_pending
    btn = Pin(HW.PAGE_BTN_PIN, Pin.IN, Pin.PULL_UP)
    was_pressed = False
    while True:
        pressed = (btn.value() == 0)   # activo-bajo
        if pressed and not was_pressed:
            _screen_index = (_screen_index + 1) % len(SCREENS)
            print("[BTN] pantalla ->", _screen_index)
            _draw_screen(tft, _screen_index)
        was_pressed = pressed
        await asyncio.sleep_ms(30)


# ── Arranque ──────────────────────────────────────────────────────────────────

def make_display():
    """Inicializa el display TFT integrado del T190."""
    # Encender alimentación del display (VTFT_Ctrl LOW = ON)
    HW.display_power_on()
    import time; time.sleep_ms(20)

    spi = SPI(
        HW.TFT_SPI_ID,
        baudrate=HW.TFT_BAUDRATE,
        polarity=0,
        phase=0,
        sck=machine.Pin(HW.TFT_SCK),
        mosi=machine.Pin(HW.TFT_MOSI),
        miso=None,
    )
    tft = TFT170(
        spi,
        dc=machine.Pin(HW.TFT_DC,  machine.Pin.OUT),
        rst=machine.Pin(HW.TFT_RST, machine.Pin.OUT),
        cs=machine.Pin(HW.TFT_CS,  machine.Pin.OUT),
        bl=machine.Pin(HW.TFT_BL,  machine.Pin.OUT),
        rotation=0,
    )
    return tft


async def main():
    print("[T190] arrancando...")
    tft = make_display()
    print("[T190] display OK  {}x{}".format(tft.width, tft.height))

    _draw_screen(tft, _screen_index)

    asyncio.create_task(button_task(tft))

    # Loop principal vacío — todo lo hace button_task
    while True:
        await asyncio.sleep_ms(500)


asyncio.run(main())
