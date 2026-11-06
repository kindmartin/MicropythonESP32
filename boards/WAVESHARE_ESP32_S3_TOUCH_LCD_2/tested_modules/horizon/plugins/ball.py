# Modo "ball": bola rodante con el IMU + obstaculos con el touch. Pantalla completa portrait 240x320.
#   corto  : reiniciar nivel (bola al centro, sin obstaculos)
#   tocar  : coloca un obstaculo (maximo MAX_OBS)
#   deslizar el dedo arriba/abajo : bola mas pesada / mas ligera (3 niveles; tambien app.state["mass"])
# Ejes del IMU: cfg["ball"] = {swap_xy, sign_x, sign_y} (valores confirmados en portrait).
import framebuf
import gc
import time
import uasyncio as asyncio
import board

W, H = 240, 320
MIRROR_X = True        # el driver del LCD aplica MADCTL MX (espejo en x): se compensa al dibujar
G_PX = 1400.0          # px/s^2 por 1 g de inclinacion
R_OBS = 18
MAX_OBS = 8
SWIPE_PX = 50
# nivel de peso: (radio, rebote, rozamiento, ganancia de inclinacion)
MASSES = ((9, 0.80, 0.4, 1.0), (12, 0.65, 0.6, 1.0), (17, 0.30, 1.2, 0.8))


def c565(r, g, b):
    # el LCD recibe RGB565 big-endian y framebuf escribe little-endian: se intercambian los bytes
    v = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
    return ((v & 0xFF) << 8) | (v >> 8)


BG = c565(10, 10, 30)
WHITE = c565(255, 255, 255)
GREY = c565(90, 90, 110)
BLUE = c565(60, 120, 255)


def setup(app):
    app.add_mode("ball")
    bc = app.cfg["ball"]
    swap, sx, sy = bc["swap_xy"], bc["sign_x"], bc["sign_y"]
    app.state["mass"] = 1
    try:
        tp = board.touch(app.hw("i2c", board.i2c))
    except Exception as e:
        print("[horizon] touch no disponible:", e)
        tp = None
    g = {"x": W / 2, "y": H / 2, "vx": 0.0, "vy": 0.0, "obs": []}

    def reset():
        if app.mode == "ball":
            g.update(x=W / 2, y=H / 2, vx=0.0, vy=0.0, obs=[])

    app.on("button_short", reset)

    async def task(app):
        buf = fb = None
        lcd = app.lcd
        start = last = None             # touch: primer y ultimo punto del toque en curso
        t_prev = time.ticks_ms()

        def mx(x):
            return W - 1 - x if MIRROR_X else x

        def disc(x, y, r, c):
            fb.ellipse(mx(int(x)), int(y), r, r, c, True)

        while True:
            if app.mode != "ball":
                if buf:
                    buf = fb = None
                    gc.collect()
                await asyncio.sleep_ms(100)
                continue
            if buf is None:             # (re)entrar al modo
                buf = bytearray(W * H * 2)
                fb = framebuf.FrameBuffer(buf, W, H, framebuf.RGB565)
                g.update(vx=0.0, vy=0.0)
                t_prev = time.ticks_ms()
            now = time.ticks_ms()
            dt = min(0.05, time.ticks_diff(now, t_prev) / 1000)
            t_prev = now
            r_ball, bounce, drag, gain = MASSES[app.state["mass"]]
            obs = g["obs"]

            # --- touch: toque = obstaculo, deslizar vertical = peso
            if tp:
                p = tp.read()
                if p:
                    if start is None:
                        start = p
                    last = p
                elif start is not None:
                    dy = last[1] - start[1]
                    if abs(dy) >= SWIPE_PX:
                        m = app.state["mass"] + (1 if dy < 0 else -1)         # arriba = mas pesada
                        app.state["mass"] = max(0, min(len(MASSES) - 1, m))
                    else:
                        obs.append(start)
                        if len(obs) > MAX_OBS:
                            obs.pop(0)
                    start = last = None

            # --- fisica
            ax, ay, _az = app.state["acc"]
            if swap:
                ax, ay = ay, ax
            x, y, vx, vy = g["x"], g["y"], g["vx"], g["vy"]
            vx += sx * ax * G_PX * gain * dt
            vy += sy * ay * G_PX * gain * dt
            k = max(0.0, 1 - drag * dt)
            vx *= k
            vy *= k
            x += vx * dt
            y += vy * dt
            if x < r_ball:
                x, vx = r_ball, -vx * bounce
            elif x > W - 1 - r_ball:
                x, vx = W - 1 - r_ball, -vx * bounce
            if y < r_ball:
                y, vy = r_ball, -vy * bounce
            elif y > H - 1 - r_ball:
                y, vy = H - 1 - r_ball, -vy * bounce
            for ox, oy in obs:
                dx, dy2 = x - ox, y - oy
                d2 = dx * dx + dy2 * dy2
                rr = r_ball + R_OBS
                if 0 < d2 < rr * rr:
                    d = d2 ** 0.5
                    nx, ny = dx / d, dy2 / d
                    x, y = ox + nx * rr, oy + ny * rr
                    vn = vx * nx + vy * ny
                    if vn < 0:
                        vx -= (1 + bounce) * vn * nx
                        vy -= (1 + bounce) * vn * ny
            g["x"], g["y"], g["vx"], g["vy"] = x, y, vx, vy

            # --- dibujo
            fb.fill(BG)
            for gx in range(0, W, 40):
                fb.vline(mx(gx), 0, H, GREY)
            for gy in range(0, H, 40):
                fb.hline(0, gy, W, GREY)
            for ox, oy in obs:
                disc(ox, oy, R_OBS, BLUE)
            sp = min(1.0, (vx * vx + vy * vy) ** 0.5 / 400)
            disc(x, y, r_ball, c565(int(40 + 215 * sp), int(255 - 215 * sp), 60))
            for i in range(app.state["mass"] + 1):          # puntos arriba a la izquierda = nivel de peso
                disc(10 + i * 10, 10, 3, WHITE)
            lcd.blit_buffer(buf, 0, 0, W, H)
            await asyncio.sleep_ms(0)

    app.add_task("ball", task)
