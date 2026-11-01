# font_demo_40.py -- Demo con fuente seven-segment_40 en Heltec T190
#
# Subir al ESP32:
#   seven_segment_40.py  (nombre con guion bajo, sin guion)
#   font_demo_40.py
#   st7789py.py

import time
from machine import SoftSPI, Pin
import st7789py as st7789

import seven_segment_40 as seg40

# --- Config T190 --------------------------------------------------------
W, H = 170, 320
ROTATIONS = ((0x00, 170, 320, 35, 0, False),
             (0x60, 320, 170,  0, 35, False),
             (0xC0, 170, 320, 35,  0, False),
             (0xA0, 320, 170,  0, 35, False))

BLACK  = st7789.BLACK
WHITE  = st7789.WHITE
CYAN   = st7789.CYAN
YELLOW = st7789.YELLOW
GREEN  = st7789.GREEN
RED    = st7789.RED
ORANGE = st7789.color565(255, 140, 0)
GRAY   = st7789.color565(50, 50, 50)

def make_tft():
    Pin(7, Pin.OUT).value(0)
    time.sleep_ms(120)
    spi = SoftSPI(baudrate=20_000_000, polarity=0, phase=0,
                  sck=Pin(38), mosi=Pin(48), miso=Pin(46))
    return st7789.ST7789(spi, W, H,
        cs=Pin(39, Pin.OUT), dc=Pin(47, Pin.OUT),
        reset=Pin(40, Pin.OUT), backlight=Pin(17, Pin.OUT),
        custom_rotations=ROTATIONS, rotation=0,
        color_order=st7789.BGR)


# --- Renderizador font_to_py (hmap=True, reverse=False) -----------------

def render_char(font, ch, fg, bg):
    """Convierte un caracter a buffer RGB565. Retorna (buf, w, h)."""
    data, ch_h, ch_w = font.get_ch(ch)
    bpr = (ch_w - 1) // 8 + 1   # bytes por fila
    fh, fl = fg >> 8, fg & 0xFF
    bh, bl = bg >> 8, bg & 0xFF
    buf = bytearray(ch_w * ch_h * 2)
    for row in range(ch_h):
        for col in range(ch_w):
            byte = data[row * bpr + col // 8]
            bit  = (byte >> (7 - (col % 8))) & 1
            i = (row * ch_w + col) * 2
            if bit:
                buf[i], buf[i+1] = fh, fl
            else:
                buf[i], buf[i+1] = bh, bl
    return buf, ch_w, ch_h

def str_width(font, text):
    """Ancho total en px de un string."""
    total = 0
    for ch in text:
        _, _, w = font.get_ch(ch)
        total += w
    return total

def txt_font(tft, font, text, x, y, fg, bg=BLACK):
    """Dibuja text con font en (x,y). Retorna x final."""
    cx = x
    for ch in text:
        buf, cw, ch_h = render_char(font, ch, fg, bg)
        if cx + cw > W:
            break
        tft.blit_buffer(buf, cx, y, cw, ch_h)
        cx += cw
    return cx

def txt_centered(tft, font, text, y, fg, bg=BLACK):
    """Dibuja text centrado horizontalmente."""
    tw = str_width(font, text)
    cx = max(0, (W - tw) // 2)
    txt_font(tft, font, text, cx, y, fg, bg)


# --- Helper texto 8x8 built-in ------------------------------------------

import framebuf as _fb

def t8(tft, x, y, s, fg, bg=BLACK):
    if not s: return
    w, h = len(s) * 8, 8
    stride = (w + 7) // 8
    mono = bytearray(stride * h)
    _fb.FrameBuffer(mono, w, h, _fb.MONO_HLSB).text(s, 0, 0, 1)
    fh, fl = fg >> 8, fg & 0xFF
    bh, bl = bg >> 8, bg & 0xFF
    buf = bytearray(w * h * 2)
    for r in range(h):
        rb = r * stride
        for c in range(w):
            i = (r * w + c) * 2
            if (mono[rb + c // 8] >> (7 - (c % 8))) & 1:
                buf[i], buf[i+1] = fh, fl
            else:
                buf[i], buf[i+1] = bh, bl
    tft.blit_buffer(buf, x, y, w, h)


# --- Pantallas demo ------------------------------------------------------

def screen_info(tft):
    """Pantalla 1: info de la fuente y muestra de digitos."""
    tft.fill(BLACK)
    # Cabecera
    tft.fill_rect(0, 0, W, 16, st7789.color565(0, 80, 80))
    t8(tft, 2, 4, "seven-segment_40", WHITE, st7789.color565(0, 80, 80))

    # Datos de la fuente
    t8(tft, 0, 22, "h=" + str(seg40.height()) +
                   " bsln=" + str(seg40.baseline()) +
                   " maxW=" + str(seg40.max_width()), CYAN)

    # Digitos 0-4 en fila (pueden ser anchos)
    t8(tft, 0, 38, "0  1  2  3  4", GRAY)
    x = 0
    for ch in "01234":
        buf, cw, ch_h = render_char(seg40, ch, GREEN, BLACK)
        if x + cw <= W:
            tft.blit_buffer(buf, x, 48, cw, ch_h)
            x += cw + 2

    # Digitos 5-9
    t8(tft, 0, 96, "5  6  7  8  9", GRAY)
    x = 0
    for ch in "56789":
        buf, cw, ch_h = render_char(seg40, ch, YELLOW, BLACK)
        if x + cw <= W:
            tft.blit_buffer(buf, x, 106, cw, ch_h)
            x += cw + 2

    # Separadores y letras utiles
    t8(tft, 0, 154, "Separadores: . : - /", GRAY)
    x = 4
    for ch in ".:- /":
        buf, cw, ch_h = render_char(seg40, ch, RED, BLACK)
        if x + cw <= W:
            tft.blit_buffer(buf, x, 164, cw, ch_h)
            x += cw + 6

    time.sleep_ms(3000)


def screen_clock(tft):
    """Pantalla 2: reloj simulado HH:MM centrado."""
    tft.fill(BLACK)
    t8(tft, 0, 4, "Reloj HH:MM", WHITE)
    tft.hline(0, 14, W, GRAY)

    # Simula HH:MM de 12:00 a 12:10
    for m in range(11):
        s = "12:{:02d}".format(m)
        # Fondo de zona de texto
        tft.fill_rect(0, 20, W, seg40.height() + 4, BLACK)
        txt_centered(tft, seg40, s, 22, CYAN)
        time.sleep_ms(400)

    time.sleep_ms(1000)


def screen_counter(tft):
    """Pantalla 3: contador 00 -> 99 animado."""
    tft.fill(BLACK)
    t8(tft, 0, 4, "Contador 00-99", WHITE)
    tft.hline(0, 14, W, GRAY)

    FG_COLORS = [GREEN, CYAN, YELLOW, ORANGE, RED, WHITE]
    for i in range(100):
        s = "{:02d}".format(i)
        fg = FG_COLORS[i % len(FG_COLORS)]
        tft.fill_rect(0, 18, W, seg40.height() + 4, BLACK)
        txt_centered(tft, seg40, s, 20, fg)
        time.sleep_ms(100)

    time.sleep_ms(500)


def screen_value(tft):
    """Pantalla 4: valor con unidad — util para sensores."""
    tft.fill(BLACK)
    t8(tft, 0, 4, "Temperatura:", WHITE)

    valores = [("23.5", "C"), ("24.1", "C"), ("24.8", "C"), ("25.0", "C")]
    for val, unidad in valores:
        tft.fill_rect(0, 18, W, seg40.height() + 4, BLACK)
        tw = str_width(seg40, val)
        # Valor a la izquierda, unidad en texto 8x8
        txt_font(tft, seg40, val, 0, 20, ORANGE)
        t8(tft, tw + 4, 20 + seg40.height() - 8, unidad, ORANGE)
        time.sleep_ms(700)

    time.sleep_ms(1000)


# --- Main ----------------------------------------------------------------

def main():
    tft = make_tft()
    screen_info(tft)
    screen_clock(tft)
    screen_counter(tft)
    screen_value(tft)
    tft.fill(BLACK)
    t8(tft, 0, 10, "Demo terminado", WHITE)

main()
