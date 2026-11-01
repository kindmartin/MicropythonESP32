# Video continuo camara -> LCD portrait 240x320.
#   - Video 240x240 (camara R240X240 RGB565) arriba; franja libre 240x80 debajo para la UI.
#   - La camara entrega RGB565 big-endian, tal cual lo espera el ST7789: el frame se envia
#     sin procesar. (El driver del LCD no usa el bit BGR; con BGR el rojo sale azul-turquesa.)
#   - Sin rotacion por defecto (el sensor ya esta orientado para la placa en horizontal).
# SPI 40 MHz. Ctrl-C para salir.
import gc, time, micropython, board, st7789
from camera import Camera, PixelFormat, FrameSize

# Orientacion: 8 modos (0..7). Pulsa BOOT para pasar al siguiente (los cuadritos = modo+1).
#   bit0: volteo vertical (camara)   bit1: espejo horizontal (camara)
#   bit2: girar 90 a favor del reloj en software (mas lento)
MODE = 2          # 2 = espejo horizontal (confirmado con la hoja BONFIM)
VIDEO_Y = 0       # fila donde empieza el video (0 = arriba; 80 = franja de UI arriba)
UI_Y = 240 if VIDEO_Y == 0 else 0
BAT_BAR = True    # barra de bateria de ejemplo en la franja de UI


@micropython.viper
def rot_cw(src: ptr32, dst: ptr32, w: int, h: int):
    # Giro 90 a favor del reloj. Bloques 2x2, accesos de 32 bit (w y h pares).
    # Equivale a dst[x*h + (h-1-y)] = src[y*w + x]
    w2 = w >> 1
    h2 = h >> 1
    for ye in range(0, h, 2):
        a = ye * w2
        b = a + w2
        for xi in range(w2):
            A = src[a + xi]
            B = src[b + xi]
            x = xi << 1
            d0 = (x * h + h - 2 - ye) >> 1
            dst[d0] = (B & 0xFFFF) | (A << 16)
            dst[d0 + h2] = ((B >> 16) & 0xFFFF) | ((A >> 16) << 16)


def draw_ui(lcd, pct, mode):
    lcd.fill_rect(0, UI_Y, 240, 80, st7789.BLACK)
    lcd.hline(0, UI_Y if UI_Y else 79, 240, st7789.WHITE)
    if BAT_BAR:
        lcd.rect(10, UI_Y + 50, 100, 20, st7789.WHITE)
        lcd.fill_rect(12, UI_Y + 52, max(0, min(96, pct)), 16, st7789.GREEN)
    # modo = (mode + 1) cuadritos amarillos (1..8)
    for i in range(mode + 1):
        lcd.fill_rect(10 + i * 28, UI_Y + 10, 22, 22, st7789.YELLOW)


spi = board.spi(40_000_000)
lcd = board.lcd(spi)          # portrait 240x320 (rotation 0)
board.backlight(80)
lcd.fill(st7789.BLACK)
try:
    pct = board.battery_percent()
except Exception:
    pct = 0
draw_ui(lcd, pct, MODE)
btn = board.button()

cam = Camera(pixel_format=PixelFormat.RGB565, frame_size=FrameSize.R240X240, fb_count=2)


def apply_mode(m):
    cam.set_vflip(bool(m & 1))
    cam.set_hmirror(bool(m & 2))
    print("modo", m + 1, "-> vflip=%d, hmirror=%d, giro90=%d" % (m & 1, (m >> 1) & 1, (m >> 2) & 1))


apply_mode(MODE)
w, h = cam.get_pixel_width(), cam.get_pixel_height()    # 240 x 240
dst = bytearray(w * h * 2)
for _ in range(3):
    cam.capture()                                       # descarta frames iniciales
n = 0
t0 = time.ticks_ms()
try:
    while True:
        buf = cam.capture()
        if buf:
            if MODE & 4:
                rot_cw(buf, dst, w, h)
                lcd.blit_buffer(dst, 0, VIDEO_Y, h, w)
            else:
                lcd.blit_buffer(buf, 0, VIDEO_Y, w, h)
            n += 1
            if btn.value() == 0:                  # BOOT: siguiente orientacion
                MODE = (MODE + 1) % 8
                apply_mode(MODE)
                draw_ui(lcd, pct, MODE)
                while btn.value() == 0:
                    time.sleep_ms(20)
            if n % 100 == 0:
                print("fps: %.1f" % (100000 / time.ticks_diff(time.ticks_ms(), t0)))
                t0 = time.ticks_ms()
finally:
    cam.deinit()
    gc.collect()
