# Video continuo camara -> LCD portrait 240x320, con overlay de bateria + nivel de burbuja (IMU).
#   - Video 240x240 (camara R240X240 RGB565) arriba; franja libre 240x80 debajo para la UI.
#   - La camara entrega RGB565 big-endian, tal cual lo espera el ST7789: el frame se envia
#     sin procesar. (El driver del LCD no usa el bit BGR; con BGR el rojo sale azul-turquesa.)
#   - SPI del LCD a 40 MHz.
#
# USO (desde el REPL, se puede repetir sin reiniciar):
#     import video
#     video.run()                      # arranca; al salir vuelve al prompt
#     video.run(boot_action="video")   # BOOT recorre las orientaciones del video en vez del IMU
#     video.run(imu_mode=3, overlay_on=False)
#     video.run(style="bubble")        # nivel de burbuja (placa plana) en vez del horizonte
# Tras editar overlay.py / video.py:  import sys; [sys.modules.pop(m, None) for m in ("video","overlay")]
# Tambien arranca solo con:  mpremote run video.py
#
# Salir: pulsacion LARGA de BOOT (1,5 s), tecla 'q' en la terminal, o Ctrl-C.
# Pulsacion corta de BOOT: siguiente modo (mapeo del IMU por defecto, u orientacion del video).
import gc, sys, time, select, micropython, board, st7789
import overlay
from camera import Camera, PixelFormat, FrameSize

# --- configuracion por defecto (run() acepta overrides) ---
# Orientacion del video: 8 modos (0..7)
#   bit0: volteo vertical (camara)   bit1: espejo horizontal (camara)
#   bit2: girar 90 a favor del reloj en software (mas lento)
MODE = 2              # 2 = espejo horizontal (modo 3, confirmado: se ve derecho)
BOOT_ACTION = "imu"   # que recorre BOOT: "imu" (8 mapeos de la burbuja) o "video" (8 orientaciones)
IMU_MODE = 3          # mapeo del IMU confirmado en la placa: "modo IMU 4" (horizontal=eje x +, vertical=eje y -)
OVERLAY = True        # bateria + horizonte/burbuja dibujados SOBRE el video (ver overlay.py)
STYLE = "horizon"     # "horizon" (placa vertical, tipo avion) o "bubble" (placa plana)
VIEW_ROT = 90         # como ves el panel respecto a su orientacion nativa (90 = franja de UI a tu derecha)
VIDEO_Y = 0           # fila donde empieza el video (0 = arriba; 80 = franja de UI arriba)
UI_Y = 240 if VIDEO_Y == 0 else 0
BAT_BAR = False       # barra de bateria en la franja de UI (el overlay ya dibuja la bateria sobre el video)
LONG_MS = 1500        # BOOT sostenido para salir


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


def run(mode=None, imu_mode=None, boot_action=None, overlay_on=None, style=None):
    """Arranca el video. Devuelve al salir (BOOT largo, 'q' o Ctrl-C)."""
    mode = MODE if mode is None else mode
    imu_mode = IMU_MODE if imu_mode is None else imu_mode
    boot_action = BOOT_ACTION if boot_action is None else boot_action
    overlay_on = OVERLAY if overlay_on is None else overlay_on
    style = STYLE if style is None else style

    spi = board.spi(40_000_000)
    lcd = board.lcd(spi)          # portrait 240x320 (rotation 0)
    board.backlight(80)
    lcd.fill(st7789.BLACK)
    try:
        pct = board.battery_percent()
    except Exception:
        pct = 0
    draw_ui(lcd, pct, imu_mode if boot_action == "imu" else mode)
    btn = board.button()
    stdin = select.poll()
    stdin.register(sys.stdin, select.POLLIN)

    ov = overlay.Overlay(240, VIEW_ROT, style)
    ov.set_imu_mode(imu_mode)
    imu = None
    if overlay_on:
        try:
            imu = board.imu()
        except Exception as e:                  # sin IMU: solo bateria
            print("IMU no disponible:", e)
    bat_pct, bat_present, t_bat = 0, True, -10000
    writable = True                             # el buffer de la camara admite dibujar encima?

    cam = None
    dst = None
    try:
        cam = Camera(pixel_format=PixelFormat.RGB565, frame_size=FrameSize.R240X240, fb_count=2)

        def apply_mode(m):
            cam.set_vflip(bool(m & 1))
            cam.set_hmirror(bool(m & 2))
            print("modo", m + 1, "-> vflip=%d, hmirror=%d, giro90=%d" % (m & 1, (m >> 1) & 1, (m >> 2) & 1))

        apply_mode(mode)
        w, h = cam.get_pixel_width(), cam.get_pixel_height()    # 240 x 240
        dst = bytearray(w * h * 2)
        for _ in range(3):
            cam.capture()                                       # descarta frames iniciales
        n = 0
        t0 = time.ticks_ms()
        while True:
            buf = cam.capture()
            if buf:
                if mode & 4:
                    rot_cw(buf, dst, w, h)
                    out = dst
                else:
                    out = buf
                if overlay_on:
                    if imu:
                        try:
                            d = imu.read_all()                  # ax ay az gx gy gz
                            ov.update_imu(d[:3], d[3:])
                        except OSError:
                            pass
                    if time.ticks_diff(time.ticks_ms(), t_bat) > 2000:      # bateria cada 2 s
                        v = board.vbat()
                        bat_present = v > 2.8
                        bat_pct = max(0, min(100, int((v - 3.3) / (4.2 - 3.3) * 100)))
                        t_bat = time.ticks_ms()
                    if out is buf and not writable:
                        dst[:] = buf
                        out = dst
                    try:
                        ov.draw(out, bat_pct, bat_present)
                    except TypeError:                   # buffer de la camara de solo lectura
                        writable = False
                        dst[:] = buf
                        out = dst
                        ov.draw(out, bat_pct, bat_present)
                lcd.blit_buffer(out, 0, VIDEO_Y, w, h)
                n += 1
                if btn.value() == 0:                  # BOOT
                    t_press = time.ticks_ms()
                    while btn.value() == 0 and time.ticks_diff(time.ticks_ms(), t_press) < LONG_MS:
                        time.sleep_ms(20)
                    if btn.value() == 0:              # pulsacion larga: salir
                        print("salir (BOOT largo)")
                        break
                    if boot_action == "imu":          # pulsacion corta: siguiente mapeo del IMU
                        imu_mode = (imu_mode + 1) % 8
                        ov.set_imu_mode(imu_mode)
                        print("modo IMU %d  (horizontal=eje %s %s, vertical=eje %s %s)" % (
                            imu_mode + 1, "xyz"[ov.ix], "+" if ov.sx > 0 else "-",
                            "xyz"[ov.iy], "+" if ov.sy > 0 else "-"))
                        draw_ui(lcd, pct, imu_mode)
                    else:                             # siguiente orientacion del video
                        mode = (mode + 1) % 8
                        apply_mode(mode)
                        draw_ui(lcd, pct, mode)
                if stdin.poll(0):                     # tecla 'q' (o Ctrl-C si llega como dato)
                    if sys.stdin.read(1) in ("q", "Q", "\x03"):
                        print("salir (tecla)")
                        break
                if n % 100 == 0:
                    print("fps: %.1f  bat: %d%% %s" % (
                        100000 / time.ticks_diff(time.ticks_ms(), t0), bat_pct,
                        "" if bat_present else "(sin bateria)"))
                    t0 = time.ticks_ms()
    finally:
        if cam:
            cam.deinit()
        dst = None
        gc.collect()


if __name__ == "__main__":      # mpremote run video.py  /  exec(open('video.py').read())
    run()
