# Horizonte artificial para la Waveshare ESP32-S3-LCD-1.9 (170x320, sin touch), SIN camara: cielo/suelo simulados
# con el IMU QMI8658 + alabeo, cabeceo y bateria. Mismo estilo que examples/overlay.py de la Touch-LCD-2.
#
# USO (REPL):   import horizon; horizon.start()        # en un HILO: el REPL queda libre. Parar: horizon.stop() o BOOT > 3 s
#               horizon.run()                          # bloqueante (salir: BOOT > 3 s o tecla 'q')
#               horizon.start(sim=True) / run(sim=True)  # horizonte simulado (sin mover la placa)
#               Ojo: los print() del hilo salen en el REPL; no importa el modulo desde otro hilo bloqueado.
#
# BOTON (BOOT, GPIO0), 4 gestos (el LED RGB se pone verde al llegar a "largo" y rojo al llegar a "extra"):
#   corto  : RUN = pone el CERO (alabeo/cabeceo actuales = 0).  En configuracion = cambia el valor del ajuste mostrado.
#   doble  : en RUN alterna HORIZONTE / NIVEL de burbuja (en NIVEL, corto = cero del nivel sobre una superficie plana).
#            En configuracion, pasa al siguiente ajuste.
#   largo  : (0,7-3 s) entra a configuracion; estando dentro, vuelve a RUN.
#   extra  : (> 3 s) sale al REPL.
# Ajustes (modo configuracion), el banner de abajo muestra "n/total AJUSTE valor":
#   VISTA gira la imagen 90 grados | EJES gira 90 grados los ejes del IMU | CABEC invierte el cabeceo | ALAB invierte el alabeo
#   GIRO invierte las flechas de giro | BURB-X / BURB-Y invierten un eje de la burbuja | CIELO intercambia los colores de cielo y suelo | ESPEJO espejo horizontal | COLOR intercambia rojo/azul | INV invierte los colores del panel
#   SIM activa/desactiva el horizonte simulado
# Todo se guarda en /horizon_cfg.json y se recarga al arrancar. Calibracion tipica:
#   SIM para ver la imagen -> COLOR/INV/ESPEJO/VISTA hasta que se vea bien -> desactiva SIM ->
#   EJES/ALAB/CABEC hasta que el horizonte reaccione correctamente al inclinar la placa -> RUN y CERO.
# Valores por defecto SIN medir en la 1.9 (copiados de la 1.47B; swap_rb=True porque este driver activa BGR). Ejes del IMU: sin medir. Convencion (como en la Touch-LCD-2): el acelerometro lee +1 g
# en el eje que apunta hacia arriba; EJES/ALAB/CABEC existen para ajustar eso en 30 segundos.
import framebuf, math, time, sys, select, json
from array import array
import board, st7789

CFG_FILE = "/horizon_cfg.json"
LONG_MS = 700                   # BOOT sostenido >= LONG_MS: "largo" (LED verde)
EXTRA_MS = 3000                 # BOOT sostenido >= EXTRA_MS: "extra" (LED rojo)
DOUBLE_MS = 300                 # ventana para el segundo clic del "doble"
W, H = 170, 320                 # buffer nativo (portrait)
PX_PER_DEG = 2.2
PITCH_MAX = 60
LEVEL_DEG = 5
MODES = ("RUN", "VISTA", "EJES", "CABEC", "ALAB", "GIRO", "BURB-X", "BURB-Y", "CIELO", "ESPEJO", "COLOR", "INV", "SIM")
GYRO_THRESHOLD = 12     # grados/s por debajo de los cuales no se muestran las flechas de giro
SCALE_PX = 2.5          # px por grado en la escala vertical de cabeceo
SCALE_MAX = 33          # grados que caben en la escala (+-)

# Valores de la 1.47B (confirmados alli, NO en la 1.9): vista a 270 grados, ejes del IMU girados 270 (imu_rot=3), sin espejo.
# swap_rb=False: el driver st7789 NO activa el bit BGR. sky_swap=True: el driver aplica MADCTL MX (espejo en x del buffer),
# que deja cielo y suelo intercambiados; lvl_sx=1 y lvl_sy=-1: la burbuja depende solo de imu_rot (imu_rot=3 invierte ambos ejes frente a imu_rot=1).
DEFAULT = {"view": 270, "imu_rot": 3, "pitch_sign": 1, "roll_sign": 1, "gyro_sign": -1, "mirror": False, "swap_rb": True,
           "invert": True, "roll0": 0.0, "pitch0": 0.0, "lvl_x0": 0.0, "lvl_y0": 0.0, "lvl_sx": 1, "lvl_sy": -1, "sky_swap": True}


def c565(r, g, b, swap_rb=False):
    if swap_rb:
        r, b = b, r
    v = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
    return ((v & 0xFF) << 8) | (v >> 8)       # framebuf little-endian -> LCD big-endian


class Horizon:
    def __init__(self, cfg):
        self.cfg = cfg
        self.ax = self.ay = 0.0
        self.az = 1.0
        self.gz = 0.0
        self._seeded = False
        self._g = bytearray(8)
        self._gfb = framebuf.FrameBuffer(self._g, 8, 8, framebuf.MONO_HLSB)
        self.buf = bytearray(W * H * 2)
        self.fb = framebuf.FrameBuffer(self.buf, W, H, framebuf.RGB565)
        self.set_palette()
        if self.fold_zero():
            print("ajuste: giro de 90 grados del cero pasado a imu_rot (el nivel usa los mismos ejes)")

    def set_palette(self):
        s = self.cfg["swap_rb"]
        self.SKY = c565(40, 110, 200, s)
        self.GROUND = c565(130, 80, 30, s)
        if self.cfg["sky_swap"]:                       # cielo y suelo intercambiados
            self.SKY, self.GROUND = self.GROUND, self.SKY
        self.WHITE = c565(255, 255, 255, s)
        self.BLACK = 0
        self.GREY = c565(120, 120, 120, s)
        self.GREEN = c565(0, 220, 0, s)
        self.YELLOW = c565(255, 200, 0, s)
        self.RED = c565(255, 40, 40, s)
        self.MAGENTA = c565(255, 0, 255, s)

    # ---- geometria: la "vista" es como miras la placa (x der, y abajo)
    def size(self):
        return (W, H) if self.cfg["view"] in (0, 180) else (H, W)

    def _p(self, x, y):
        x, y = int(x), int(y)
        v = self.cfg["view"]
        if v == 90:
            px, py = W - 1 - y, x
        elif v == 180:
            px, py = W - 1 - x, H - 1 - y
        elif v == 270:
            px, py = y, H - 1 - x
        else:
            px, py = x, y
        if self.cfg["mirror"]:
            px = W - 1 - px
        return px, py

    def line(self, x0, y0, x1, y1, c):
        a, b = self._p(x0, y0)
        d, e = self._p(x1, y1)
        self.fb.line(a, b, d, e, c)

    def circle(self, cx, cy, r, c, fill=False):
        a, b = self._p(cx, cy)
        self.fb.ellipse(a, b, int(r), int(r), c, fill)

    def rect(self, x, y, w, h, c, fill=False):
        x0, y0 = self._p(x, y)
        x1, y1 = self._p(x + w - 1, y + h - 1)
        self.fb.rect(min(x0, x1), min(y0, y1), abs(x1 - x0) + 1, abs(y1 - y0) + 1, c, fill)

    def poly(self, pts, c):
        q = []
        for x, y in pts:
            a, b = self._p(x, y)
            q.append(a)
            q.append(b)
        self.fb.poly(0, 0, array("h", q), c, True)

    def text(self, s, x, y, c, k=1):
        """Texto 8x8 (ampliado k veces) en tu vista; se dibuja pixel a pixel para respetar la rotacion.
        El driver del LCD aplica MADCTL MX (espejo en x del buffer): si mirror=False cada letra se invierte
        a proposito (en x en vista 0/180, en y en 90/270) para que el texto se lea bien en el panel."""
        flip = not self.cfg["mirror"]
        horiz = self.cfg["view"] in (0, 180)          # eje de la vista que cae sobre el x del buffer
        n = len(s) * 8 * k
        for i, ch in enumerate(s):
            self._gfb.fill(0)
            self._gfb.text(ch, 0, 0, 1)
            for yy in range(8):
                row = self._g[yy]
                if row:
                    for xx in range(8):
                        if row & (0x80 >> xx):
                            ux, uy = (i * 8 + xx) * k, yy * k
                            if flip:
                                if horiz:
                                    ux = n - k - ux
                                else:
                                    uy = 8 * k - k - uy
                            if k == 1:
                                a, b = self._p(x + ux, y + uy)
                                self.fb.pixel(a, b, c)
                            else:
                                self.rect(x + ux, y + uy, k, k, c, True)

    # ---- IMU
    def update_imu(self, acc, gz=0.0, alpha=0.25):
        if not self._seeded:
            self.ax, self.ay, self.az = acc
            self._seeded = True
            return
        self.ax += alpha * (acc[0] - self.ax)
        self.ay += alpha * (acc[1] - self.ay)
        self.az += alpha * (acc[2] - self.az)
        self.gz += 0.4 * (gz - self.gz)

    def _attitude(self):
        """(alabeo horario rad, cabeceo grados, modulo de la gravedad en el plano) sin restar el cero."""
        x, y = self.ax, self.ay
        for _ in range(self.cfg["imu_rot"]):          # gira el sistema de ejes del IMU 90 grados
            x, y = y, -x
        x *= self.cfg["roll_sign"]
        m = math.sqrt(x * x + y * y)
        theta = math.atan2(x, y) if m > 0.2 else 0.0
        pitch = math.degrees(math.atan2(self.az * self.cfg["pitch_sign"], m if m > 0.05 else 0.05))
        return theta, pitch, m

    def fold_zero(self):
        """Pasa a imu_rot los giros de 90 grados que el cero de alabeo haya absorbido (|roll0| > 45 grados).
        El horizonte se ve igual, pero el nivel (que no usa roll0) queda en los mismos ejes."""
        cfg = self.cfg
        q = int(round(cfg["roll0"] / (math.pi / 2)))
        if q:
            cfg["imu_rot"] = (cfg["imu_rot"] - q) % 4
            cfg["roll0"] -= q * math.pi / 2
            cfg["lvl_x0"] = cfg["lvl_y0"] = 0.0         # medidos con los ejes anteriores
        return q

    def tare(self):
        theta, pitch, m = self._attitude()
        if m < 0.5:
            return False
        self.cfg["roll0"], self.cfg["pitch0"] = theta, pitch
        self.fold_zero()
        return True

    def relative(self, sim_t=None):
        if sim_t is not None:                          # horizonte simulado
            t = sim_t / 1000
            return math.radians(35 * math.sin(t * 0.9)), 18 * math.sin(t * 0.6 + 1)
        theta, pitch, m = self._attitude()
        if m > 0.2:
            d = theta - self.cfg["roll0"]
            theta = (d + math.pi) % (2 * math.pi) - math.pi
        return theta, pitch - self.cfg["pitch0"]

    # ---- dibujo
    def draw_scene(self, theta, pitch, pct, present):
        vw, vh = self.size()
        cx, cy = vw // 2, vh // 2
        self.fb.fill(self.SKY)
        s, c = math.sin(theta), math.cos(theta)
        p = max(-PITCH_MAX, min(PITCH_MAX, pitch))
        off = p * PX_PER_DEG                          # camara hacia arriba -> el horizonte baja
        hx, hy = cx + s * off, cy + c * off
        L = 500
        self.poly(((hx - c * L, hy + s * L), (hx + c * L, hy - s * L),
                   (hx + c * L + s * L, hy - s * L + c * L), (hx - c * L + s * L, hy + s * L + c * L)), self.GROUND)
        level = abs(math.degrees(theta)) < LEVEL_DEG and abs(pitch) < LEVEL_DEG
        hcol = self.GREEN if level else self.WHITE
        self.line(hx - c * L, hy + s * L, hx + c * L, hy - s * L, hcol)
        for ang in (-20, -10, 10, 20):                # escala de cabeceo
            px, py = hx - s * ang * PX_PER_DEG, hy - c * ang * PX_PER_DEG
            ln = 22 if ang % 20 == 0 else 14
            self.line(px - c * ln, py + s * ln, px + c * ln, py - s * ln, self.WHITE)
        # simbolo fijo
        Y = self.YELLOW
        self.line(cx - 36, cy, cx - 12, cy, Y)
        self.line(cx + 12, cy, cx + 36, cy, Y)
        self.line(cx - 12, cy, cx - 12, cy + 6, Y)
        self.line(cx + 12, cy, cx + 12, cy + 6, Y)
        self.rect(cx - 1, cy - 1, 3, 3, Y, True)
        # arco de alabeo con puntero al cielo
        R = min(vw, vh) // 2 - 4
        for a in range(-60, 61, 15):
            r = math.radians(a)
            ln = 10 if a % 30 == 0 else 5
            self.line(cx + R * math.sin(r), cy - R * math.cos(r),
                      cx + (R - ln) * math.sin(r), cy - (R - ln) * math.cos(r), self.WHITE)
        rd = abs(math.degrees(theta))
        col = self.GREEN if rd < 10 else (self.YELLOW if rd < 30 else self.RED)
        sk = max(-1.3, min(1.3, -theta))
        self.poly(((cx + (R - 12) * math.sin(sk), cy - (R - 12) * math.cos(sk)),
                   (cx + (R + 2) * math.sin(sk - 0.07), cy - (R + 2) * math.cos(sk - 0.07)),
                   (cx + (R + 2) * math.sin(sk + 0.07), cy - (R + 2) * math.cos(sk + 0.07))), col)
        self.pitch_scale(pitch)
        self.turn_arrows()
        # bateria arriba a la izquierda
        bx, by = 6, 6
        self.rect(bx, by, 30, 14, self.WHITE)
        self.rect(bx + 30, by + 4, 3, 6, self.WHITE, True)
        if not present:
            self.line(bx + 2, by + 2, bx + 27, by + 11, self.GREY)
            self.line(bx + 2, by + 11, bx + 27, by + 2, self.GREY)
        elif pct > 0:
            bc = self.GREEN if pct > 50 else (self.YELLOW if pct > 20 else self.RED)
            self.rect(bx + 2, by + 2, (26 * pct) // 100, 10, bc, True)

    def pitch_scale(self, pitch):
        """Escala vertical a la derecha: el triangulo marca el cabeceo; alineado con el cero (amarillo) = nivelado."""
        vw, vh = self.size()
        x, z = vw - 8, vh // 2
        self.line(x, z - int(SCALE_MAX * SCALE_PX), x, z + int(SCALE_MAX * SCALE_PX), self.GREY)
        for deg in range(-30, 31, 5):
            y = z - deg * SCALE_PX
            if deg == 0:
                self.line(x - 12, y, x + 3, y, self.YELLOW)
            else:
                self.line(x - (7 if deg % 10 == 0 else 4), y, x, y, self.WHITE)
        p = max(-SCALE_MAX, min(SCALE_MAX, pitch))
        y = z - p * SCALE_PX
        a = abs(pitch)
        col = self.GREEN if a < 2 else (self.YELLOW if a < 10 else self.RED)
        self.poly(((x - 6, y), (x - 18, y - 7), (x - 18, y + 7)), col)

    def turn_arrows(self):
        """Triangulos magenta a los lados SOLO mientras rotas (giroscopio): derecha baja + izquierda sube = horario."""
        rate_cw = -self.gz * self.cfg["gyro_sign"]
        if abs(rate_cw) <= GYRO_THRESHOLD:
            return
        vw, vh = self.size()
        cx, cy = vw // 2, vh // 2
        k = int(min(12, 6 + abs(rate_cw) / 14))
        d = min(55, vw // 2 - 28)
        M = self.MAGENTA
        cw = rate_cw > 0
        for side, up in ((cx + d, not cw), (cx - d, cw)):
            if up:
                self.poly(((side - k, cy + k), (side + k, cy + k), (side, cy - k)), M)
            else:
                self.poly(((side - k, cy - k), (side + k, cy - k), (side, cy + k)), M)

    # ---- nivel de burbuja: inclinacion de la placa en los dos ejes del plano de la pantalla
    def tilts(self, sim_t=None):
        """(tx, ty) en grados, sin cero de nivel. tx>0: el lado derecho de tu vista esta mas alto; ty>0: el lado de arriba."""
        if sim_t is not None:
            t = sim_t / 1000
            return 6 * math.sin(t * 0.8) * self.cfg["lvl_sx"], 4 * math.sin(t * 0.55 + 1) * self.cfg["lvl_sy"]
        x, y = self.ax, self.ay
        for _ in range(self.cfg["imu_rot"]):
            x, y = y, -x
        x *= self.cfg["roll_sign"]
        z = self.az
        return (self.cfg["lvl_sx"] * math.degrees(math.atan2(x, math.sqrt(y * y + z * z))),
                self.cfg["lvl_sy"] * math.degrees(math.atan2(y, math.sqrt(x * x + z * z))))

    def level_zero(self, sim_t=None):
        self.cfg["lvl_x0"], self.cfg["lvl_y0"] = self.tilts(sim_t)

    def draw_level(self, sim_t=None):
        """Burbuja: se mueve hacia el lado MAS ALTO. Verde < 0,5 grados en ambos ejes, amarillo < 2, rojo el resto."""
        vw, vh = self.size()
        R = min(vw, vh) // 2 - 10
        land = vw > vh
        cx, cy = (R + 10, vh // 2) if land else (vw // 2, R + 14)
        tx, ty = self.tilts(sim_t)
        tx -= self.cfg["lvl_x0"]
        ty -= self.cfg["lvl_y0"]
        self.fb.fill(self.BLACK)
        self.circle(cx, cy, R, self.WHITE)
        self.circle(cx, cy, R // 3, self.GREY)
        self.line(cx - R, cy, cx + R, cy, self.GREY)
        self.line(cx, cy - R, cx, cy + R, self.GREY)
        for k in range(-10, 11, 5):                    # marcas de 5 grados en los ejes (escala R/12 por grado)
            d = k * (R - 12) / 12
            self.line(cx + d, cy - 3, cx + d, cy + 3, self.WHITE)
            self.line(cx - 3, cy + d, cx + 3, cy + d, self.WHITE)
        bx, by = tx * (R - 12) / 12, -ty * (R - 12) / 12
        m = math.sqrt(bx * bx + by * by)
        if m > R - 12:
            bx, by = bx * (R - 12) / m, by * (R - 12) / m
        a = max(abs(tx), abs(ty))
        col = self.GREEN if a < 0.5 else (self.YELLOW if a < 2 else self.RED)
        self.circle(cx + bx, cy + by, 9, col, True)
        self.circle(cx + bx, cy + by, 9, self.WHITE)
        # lecturas: grados y pendiente en % (100 x tan) por eje
        tot = math.degrees(math.acos(max(-1, min(1, math.cos(math.radians(tx)) * math.cos(math.radians(ty))))))
        lines = ("X %+.1fd" % tx, "  %+.1f%%" % (100 * math.tan(math.radians(tx))),
                 "Y %+.1fd" % ty, "  %+.1f%%" % (100 * math.tan(math.radians(ty))),
                 "TOT %.1fd" % tot)
        x0, y0 = (cx + R + 8, cy - 50) if land else (8, cy + R + 12)
        for i, ln in enumerate(lines):                 # letra 2x (16 px): 7-9 caracteres por linea
            self.text(ln, x0, y0 + i * 20, col if i == 4 else self.WHITE, 2)

    def banner(self, mi, sim, lvl=False):
        cfg = self.cfg
        val = {"RUN": "cero %+.0f/%+.0f" % (math.degrees(cfg["roll0"]), cfg["pitch0"]),
               "VISTA": "%d" % cfg["view"], "EJES": "%d" % (cfg["imu_rot"] * 90),
               "CABEC": "%+d" % cfg["pitch_sign"], "ALAB": "%+d" % cfg["roll_sign"], "GIRO": "%+d" % cfg["gyro_sign"],
               "BURB-X": "%+d" % cfg["lvl_sx"], "BURB-Y": "%+d" % cfg["lvl_sy"], "CIELO": "swap" if cfg["sky_swap"] else "normal",
               "ESPEJO": "si" if cfg["mirror"] else "no", "COLOR": "RB" if cfg["swap_rb"] else "RGB",
               "INV": "si" if cfg["invert"] else "no", "SIM": "on" if sim else "off"}[MODES[mi]]
        s = "%d/%d %s %s" % (mi + 1, len(MODES), MODES[mi], val)
        if mi == 0 and lvl:
            s = "NIVEL cero %+.1f/%+.1f" % (cfg["lvl_x0"], cfg["lvl_y0"])
        vw, vh = self.size()
        self.rect(0, vh - 12, min(vw, len(s) * 8 + 4), 12, self.BLACK, True)
        self.text(s, 2, vh - 10, self.WHITE)


def load_cfg():
    cfg = dict(DEFAULT)
    try:
        with open(CFG_FILE) as f:
            cfg.update(json.load(f))
    except (OSError, ValueError):
        pass
    return cfg


def save_cfg(cfg):
    try:
        with open(CFG_FILE, "w") as f:
            json.dump(cfg, f)
    except OSError:
        pass


LED_ZONE = ((0, 0, 0), (0, 40, 0), (40, 0, 0))     # corto / largo / extra


def led(rgb):
    """LED RGB de feedback (GPIO38). Sin LED o sin neopixel, no pasa nada."""
    try:
        board.rgb(*rgb)
    except Exception:
        pass


def gesture(btn):
    """Lee un gesto de BOOT: 'corto', 'doble', 'largo' o 'extra' (None si no hay pulsacion). Bloquea mientras se pulsa."""
    if btn.value():
        return None
    t = time.ticks_ms()
    zone = 0
    while btn.value() == 0:
        held = time.ticks_diff(time.ticks_ms(), t)
        z = 2 if held >= EXTRA_MS else (1 if held >= LONG_MS else 0)
        if z != zone:
            zone = z
            led(LED_ZONE[zone])
        time.sleep_ms(20)
    led(LED_ZONE[0])
    if zone == 2:
        return "extra"
    if zone == 1:
        return "largo"
    t = time.ticks_ms()                            # corto: esperar un segundo clic corto
    while time.ticks_diff(time.ticks_ms(), t) < DOUBLE_MS:
        if btn.value() == 0:
            while btn.value() == 0:
                time.sleep_ms(20)
            return "doble"
        time.sleep_ms(10)
    return "corto"


def show_cfg(cfg, sim, mode=""):
    """Imprime todos los ajustes: copia esta linea para dejarlos como valores por defecto."""
    print("[%s] view=%d imu_rot=%d pitch_sign=%+d roll_sign=%+d gyro_sign=%+d mirror=%s swap_rb=%s invert=%s sim=%s lvl_sx=%+d lvl_sy=%+d sky_swap=%s roll0=%.3f pitch0=%.1f"
          % (mode, cfg["view"], cfg["imu_rot"], cfg["pitch_sign"], cfg["roll_sign"], cfg["gyro_sign"],
             cfg["mirror"], cfg["swap_rb"], cfg["invert"], sim, cfg["lvl_sx"], cfg["lvl_sy"], cfg["sky_swap"], cfg["roll0"], cfg["pitch0"]))


_stop = False
_bg = False                     # True: corre en un hilo y NO lee stdin (deja el REPL libre)


def run(sim=False):
    global _stop
    _stop = False
    cfg = load_cfg()
    spi = board.spi(40_000_000)
    lcd = board.lcd(spi, invert=cfg["invert"])
    board.backlight(80)
    btn = board.button()
    imu = None
    try:
        imu = board.imu()
    except Exception as e:
        print("IMU no disponible (usa SIM):", e)
        sim = True
    stdin = None
    if not _bg:
        stdin = select.poll()
        stdin.register(sys.stdin, select.POLLIN)
    hz = Horizon(cfg)
    mi = 0
    lvl = False                                # RUN: False = horizonte, True = nivel de burbuja
    show_until = time.ticks_add(time.ticks_ms(), 3000)
    bat_pct, present, t_bat = 0, True, -10000
    show_cfg(cfg, sim, "inicio")
    while True:
        now = time.ticks_ms()
        if imu:
            try:
                d = imu.read_all()
                hz.update_imu(d[:3], d[5])
            except OSError:
                pass
        if time.ticks_diff(now, t_bat) > 2000:
            v = board.vbat()
            present = v > 2.8
            bat_pct = max(0, min(100, int((v - 3.3) / (4.2 - 3.3) * 100)))
            t_bat = now
        if lvl and mi == 0:
            hz.draw_level(now if sim else None)
        else:
            theta, pitch = hz.relative(now if sim else None)
            hz.draw_scene(theta, pitch, bat_pct, present)
        if mi or time.ticks_diff(show_until, now) > 0:
            hz.banner(mi, sim, lvl)
        lcd.blit_buffer(hz.buf, 0, 0, W, H)
        g = gesture(btn)
        if g == "extra":                               # > 3 s: salir al REPL
            print("salir (BOOT extra)")
            break
        if g == "largo":                               # entrar / salir de configuracion
            mi = 0 if mi else 1
            print("config:", MODES[mi])
            show_until = time.ticks_add(time.ticks_ms(), 3000)
        elif g == "doble" and mi == 0:                 # RUN: alterna horizonte / nivel de burbuja
            lvl = not lvl
            print("vista:", "NIVEL" if lvl else "HORIZONTE")
            show_until = time.ticks_add(time.ticks_ms(), 3000)
        elif g == "doble":                             # siguiente ajuste
            mi = mi % (len(MODES) - 1) + 1
            print("ajuste ->", MODES[mi])
            show_until = time.ticks_add(time.ticks_ms(), 3000)
        elif g == "corto":                             # RUN: cero; config: cambia el valor del ajuste
            m = MODES[mi]
            if m == "RUN" and lvl:
                hz.level_zero(now if sim else None)
                print("cero del nivel: x=%.2f y=%.2f grados" % (cfg["lvl_x0"], cfg["lvl_y0"]))
            elif m == "RUN":
                print("cero:", "ok" if hz.tare() else "placa casi plana, no se puede")
            elif m == "VISTA":
                cfg["view"] = (cfg["view"] + 90) % 360
            elif m == "EJES":
                cfg["imu_rot"] = (cfg["imu_rot"] + 1) % 4
            elif m == "CABEC":
                cfg["pitch_sign"] = -cfg["pitch_sign"]
            elif m == "ALAB":
                cfg["roll_sign"] = -cfg["roll_sign"]
            elif m == "GIRO":
                cfg["gyro_sign"] = -cfg["gyro_sign"]
            elif m == "BURB-X":                        # invierte solo el eje X de la burbuja (no toca el horizonte)
                cfg["lvl_sx"] = -cfg["lvl_sx"]
                cfg["lvl_x0"] = 0.0
            elif m == "BURB-Y":
                cfg["lvl_sy"] = -cfg["lvl_sy"]
                cfg["lvl_y0"] = 0.0
            elif m == "CIELO":                         # intercambia los colores de cielo y suelo
                cfg["sky_swap"] = not cfg["sky_swap"]
                hz.set_palette()
            elif m == "ESPEJO":
                cfg["mirror"] = not cfg["mirror"]
            elif m == "COLOR":
                cfg["swap_rb"] = not cfg["swap_rb"]
                hz.set_palette()
            elif m == "INV":
                cfg["invert"] = not cfg["invert"]
                lcd.invert(cfg["invert"])
            elif m == "SIM":
                sim = not sim
                if sim is False and imu is None:
                    sim = True
            save_cfg(cfg)
            show_cfg(cfg, sim, MODES[mi])
            show_until = time.ticks_add(time.ticks_ms(), 3000)
        if _stop:
            print("salir (stop)")
            break
        if stdin and stdin.poll(0) and sys.stdin.read(1) in ("q", "Q", "\x03"):
            print("salir")
            break


def start(sim=False):
    """Arranca en un hilo y devuelve al REPL. Parar: horizon.stop() o BOOT > 3 s."""
    global _bg
    import _thread
    _bg = True
    _thread.stack_size(12 * 1024)
    _thread.start_new_thread(run, (sim,))


def stop():
    global _stop
    _stop = True
