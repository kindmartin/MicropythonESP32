# Bola rodante: IMU (inclinacion) + touch + LCD, sin camara. Pantalla completa portrait 240x320.
#   - Inclina la placa: la bola rueda hacia donde "cae" (acelerometro QMI8658) y rebota en los bordes.
#   - Toca la pantalla (CST816D): se coloca un obstaculo redondo donde tocas (maximo MAX_OBS, el mas viejo se pierde).
#   - Color: la bola pasa de verde a rojo segun la velocidad.
#   - BOOT corto: borra los obstaculos.  BOOT largo (1,5 s), tecla 'q' o Ctrl-C: sale.
#
# USO (desde el REPL, se puede repetir sin reiniciar):
#     import bola_tactil
#     bola_tactil.run()
# Copia antes board.py, st7789.py, cst816.py y qmi8658.py (de tested_modules/) a la placa.
#
# SIN PROBAR EN HARDWARE: ejes y signos son configurables abajo. Si la bola rueda al reves, cambia SIGN_X / SIGN_Y;
# si rueda de lado, pon SWAP_XY = True. Con la placa apaisada el IMU da +x = izquierda, +y = arriba (ver README).
import framebuf
import gc
import select
import sys
import time
import board

W, H = 240, 320
MIRROR_X = True        # el driver del LCD aplica MADCTL MX (espejo en x): se compensa al dibujar
SWAP_XY = True         # placa en portrait: el IMU tiene los ejes girados 90 grados respecto a la pantalla
SIGN_X = -1            # tras el swap; si la bola va al lado contrario en horizontal, pon 1
SIGN_Y = 1             # si va al lado contrario en vertical, pon -1
G_PX = 1400.0          # aceleracion en px/s^2 por 1 g de inclinacion
BOUNCE = 0.65          # fraccion de velocidad que se conserva al rebotar
DRAG = 0.6             # rozamiento (1/s)
R_BALL = 12
R_OBS = 18
MAX_OBS = 8
LONG_MS = 1500


def c565(r, g, b):
    # el LCD recibe RGB565 big-endian y framebuf escribe little-endian: se intercambian los bytes
    v = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
    return ((v & 0xFF) << 8) | (v >> 8)


BG = c565(10, 10, 30)
GREY = c565(90, 90, 110)
BLUE = c565(60, 120, 255)


def run():
    spi = board.spi(40_000_000)
    lcd = board.lcd(spi)                       # portrait 240x320
    board.backlight(80)
    imu = board.imu()
    try:
        tp = board.touch()
    except Exception as e:
        print("touch no disponible:", e)
        tp = None
    btn = board.button()
    stdin = select.poll()
    stdin.register(sys.stdin, select.POLLIN)

    buf = bytearray(W * H * 2)
    fb = framebuf.FrameBuffer(buf, W, H, framebuf.RGB565)

    def mx(x):
        return W - 1 - x if MIRROR_X else x

    def disc(x, y, r, c):
        fb.ellipse(mx(int(x)), int(y), r, r, c, True)

    x, y, vx, vy = W / 2, H / 2, 0.0, 0.0
    obs = []                                   # obstaculos (x, y) en coordenadas de tu vista
    was_touch = False
    t_press = None
    t_prev = time.ticks_ms()
    fps_t, fps_n = t_prev, 0
    try:
        while True:
            now = time.ticks_ms()
            dt = min(0.05, time.ticks_diff(now, t_prev) / 1000)
            t_prev = now

            # --- entrada
            if stdin.poll(0) and sys.stdin.read(1) in ("q", "Q"):
                break
            if btn.value() == 0:
                if t_press is None:
                    t_press = now
                elif time.ticks_diff(now, t_press) > LONG_MS:
                    break
            elif t_press is not None:
                if time.ticks_diff(now, t_press) < LONG_MS:
                    obs.clear()
                t_press = None
            if tp:
                p = tp.read()
                if p and not was_touch:        # un obstaculo por toque
                    obs.append(p)
                    if len(obs) > MAX_OBS:
                        obs.pop(0)
                was_touch = p is not None

            # --- fisica
            ax, ay, _az = imu.accel()
            if SWAP_XY:
                ax, ay = ay, ax
            vx += SIGN_X * ax * G_PX * dt
            vy += SIGN_Y * ay * G_PX * dt
            k = max(0.0, 1 - DRAG * dt)
            vx *= k
            vy *= k
            x += vx * dt
            y += vy * dt
            if x < R_BALL:
                x, vx = R_BALL, -vx * BOUNCE
            elif x > W - 1 - R_BALL:
                x, vx = W - 1 - R_BALL, -vx * BOUNCE
            if y < R_BALL:
                y, vy = R_BALL, -vy * BOUNCE
            elif y > H - 1 - R_BALL:
                y, vy = H - 1 - R_BALL, -vy * BOUNCE
            for ox, oy in obs:                 # rebote circulo-circulo
                dx, dy = x - ox, y - oy
                d2 = dx * dx + dy * dy
                rr = R_BALL + R_OBS
                if 0 < d2 < rr * rr:
                    d = d2 ** 0.5
                    nx, ny = dx / d, dy / d
                    x, y = ox + nx * rr, oy + ny * rr
                    vn = vx * nx + vy * ny
                    if vn < 0:                 # solo si se acerca al obstaculo
                        vx -= (1 + BOUNCE) * vn * nx
                        vy -= (1 + BOUNCE) * vn * ny

            # --- dibujo
            fb.fill(BG)
            for gx in range(0, W, 40):
                fb.vline(mx(gx), 0, H, GREY)
            for gy in range(0, H, 40):
                fb.hline(0, gy, W, GREY)
            for ox, oy in obs:
                disc(ox, oy, R_OBS, BLUE)
            sp = min(1.0, (vx * vx + vy * vy) ** 0.5 / 400)
            disc(x, y, R_BALL, c565(int(40 + 215 * sp), int(255 - 215 * sp), 60))
            lcd.blit_buffer(buf, 0, 0, W, H)

            fps_n += 1
            if time.ticks_diff(now, fps_t) >= 1000:
                print(fps_n, "fps")           # fb.text saldria espejado por el MX del LCD: fps por consola
                fps_n, fps_t = 0, now
                gc.collect()
    except KeyboardInterrupt:
        pass
    finally:
        lcd.fill(0)
        board.backlight(0)


if __name__ == "__main__":
    run()
