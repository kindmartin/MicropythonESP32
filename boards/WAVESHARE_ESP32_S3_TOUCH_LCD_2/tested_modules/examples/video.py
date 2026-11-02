# Video continuo camara -> LCD portrait 240x320, con overlay de horizonte tipo avion, escala de cabeceo,
# giro (giroscopio) y bateria (ver overlay.py).
#   - Video 240x240 (camara R240X240 RGB565) arriba; franja libre 240x80 debajo para la UI.
#   - La camara entrega RGB565 big-endian, tal cual lo espera el ST7789: el frame se envia
#     sin procesar. (El driver del LCD no usa el bit BGR; con BGR el rojo sale azul-turquesa.)
#   - El driver del LCD aplica MADCTL MX (espejo en x): la camara lo compensa con hmirror y el overlay con MIRROR_X.
#   - SPI del LCD a 40 MHz.
#
# USO (desde el REPL, se puede repetir sin reiniciar):
#     import video
#     video.run()                      # arranca; al salir vuelve al prompt
#     video.run(overlay_on=False)      # solo video
# Tras editar overlay.py / video.py:  import sys; [sys.modules.pop(m, None) for m in ("video","overlay")]
# Tambien arranca solo con:  mpremote run video.py
#
# BOOT corto : pone a CERO el alabeo y el cabeceo actuales (se guarda en /imu_zero.txt). Util si la pantalla
#              esta a 110 grados y no a 90: pasa a medir como si estuviera a 90. Marco verde = hecho; rojo =
#              placa casi plana, no se puede.
# BOOT largo : sale (1,5 s).   Tambien: tecla 'q' en la terminal, o Ctrl-C.
import gc, sys, time, select, board, st7789
import overlay
from camera import Camera, PixelFormat, FrameSize

# --- configuracion (confirmada en la placa) ---
VFLIP = False         # volteo vertical de la camara
HMIRROR = True        # espejo horizontal de la camara: compensa el MX del LCD y deja el video derecho
OVERLAY = True        # overlay sobre el video
VIEW_ROT = 90         # como ves el panel respecto a su orientacion nativa (90 = franja de UI a tu derecha)
VIDEO_Y = 0           # fila donde empieza el video (0 = arriba; 80 = franja de UI arriba)
UI_Y = 240 if VIDEO_Y == 0 else 0
LONG_MS = 1500        # BOOT sostenido para salir


def draw_ui(lcd):
    lcd.fill_rect(0, UI_Y, 240, 80, st7789.BLACK)
    lcd.hline(0, UI_Y if UI_Y else 79, 240, st7789.WHITE)


def run(overlay_on=None):
    """Arranca el video. Devuelve al salir (BOOT largo, 'q' o Ctrl-C)."""
    overlay_on = OVERLAY if overlay_on is None else overlay_on

    spi = board.spi(40_000_000)
    lcd = board.lcd(spi)          # portrait 240x320 (rotation 0)
    board.backlight(80)
    lcd.fill(st7789.BLACK)
    draw_ui(lcd)
    btn = board.button()
    stdin = select.poll()
    stdin.register(sys.stdin, select.POLLIN)

    ov = overlay.Overlay(240, VIEW_ROT)
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
        cam.set_vflip(VFLIP)
        cam.set_hmirror(HMIRROR)
        w, h = cam.get_pixel_width(), cam.get_pixel_height()    # 240 x 240
        dst = bytearray(w * h * 2)
        for _ in range(3):
            cam.capture()                                       # descarta frames iniciales
        n = 0
        t0 = time.ticks_ms()
        while True:
            buf = cam.capture()
            if buf:
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
                    if not writable:
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
                    ok = ov.tare()                    # pulsacion corta: cero del alabeo y cabeceo
                    ov.flash(ok)
                    print("cero: alabeo %.1f, cabeceo %.1f grados" % (ov.roll0 * 57.2958, ov.pitch0)
                          if ok else "cero: no se pudo (placa casi plana)")
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
