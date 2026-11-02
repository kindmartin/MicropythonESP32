# Overlay grafico sobre el frame de la camara (240x240 RGB565): bateria + horizonte tipo avion
# (o nivel de burbuja) con el IMU. Dibuja con framebuf directamente en el buffer que va al LCD.
# Sin texto (no hay fuente grande): todo es grafico.
#
# Colores: el LCD recibe RGB565 big-endian y framebuf escribe little-endian -> c565() ya los intercambia.
# Orientacion: VIEW_ROT dice como ves el panel respecto a su orientacion nativa (portrait); MIRROR_X compensa el
# espejo en x que aplica el driver del LCD (los dibujos van al mismo buffer que la camara, que ya lo compensa con hmirror):
#   0 = tal cual   90 = panel girado 90 grados contra reloj (franja de UI a tu derecha)   180 / 270
#
# Estilos (Overlay.style):
#   "horizon": placa VERTICAL (como una camara/telefono). Horizonte artificial + arco de alabeo +
#              flechas de giro (giroscopio).
#   "bubble" : placa PLANA. Nivel de burbuja.
#
# Mapeo del IMU a TU vista: 8 modos (Overlay.set_imu_mode), que se eligen con BOOT en video.py.
#   bit0: intercambia ejes (0: horizontal=y, vertical=x    1: horizontal=x, vertical=y)
#   bit1: invierte el signo horizontal     bit2: invierte el signo vertical
# Ajustes finos (signos que dependen de como esta montado el IMU): PITCH_SIGN y GZ_SIGN.
import framebuf
import math
from array import array


def c565(r, g, b):
    v = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
    return ((v & 0xFF) << 8) | (v >> 8)


WHITE = c565(255, 255, 255)
BLACK = c565(0, 0, 0)
GREY = c565(120, 120, 120)
GREEN = c565(0, 220, 0)
YELLOW = c565(255, 200, 0)
RED = c565(255, 40, 40)
CYAN = c565(0, 230, 230)
MAGENTA = c565(255, 0, 255)

MIRROR_X = True       # el driver del LCD usa MADCTL MX (espejo en x): se compensa al dibujar. La camara lo compensa con hmirror.
IMU_MODE_DEFAULT = 7     # modo IMU 8: dx = +ax, dy = +ay (ejes del IMU: +x=izquierda, +y=arriba, +z=hacia dentro de la pantalla)
PITCH_SIGN = 1       # +1: si inclinas la camara hacia arriba el horizonte debe BAJAR; si sube, pon -1
GZ_SIGN = -1         # +z apunta hacia dentro de la pantalla: gz>0 = giro HORARIO visto por ti. Si las flechas salen al reves, pon 1
PX_PER_DEG = 2.2     # desplazamiento del horizonte por grado de cabeceo
PITCH_MAX = 50       # grados maximos de cabeceo que se dibujan
GYRO_THRESHOLD = 12  # grados/s por debajo de los cuales no se muestran las flechas de giro


class Overlay:
    def __init__(self, size=240, view_rot=90, style="horizon", mirror_x=MIRROR_X):
        self.n = size
        self.mx = mirror_x
        self.vr = view_rot
        self.style = style
        self.ax = self.ay = 0.0     # aceleracion filtrada (g) en los ejes del IMU
        self.az = 1.0
        self.gz = 0.0               # velocidad de giro filtrada alrededor de z (grados/s)
        self.set_imu_mode(IMU_MODE_DEFAULT)

    def set_imu_mode(self, m):
        self.imu_mode = m & 7
        self.ix, self.iy = (0, 1) if m & 1 else (1, 0)
        self.sx = 1 if m & 2 else -1
        self.sy = 1 if m & 4 else -1

    # ---- mapa vista (x der, y abajo, como lo ves) -> panel nativo
    def _p(self, x, y):
        """Coordenadas de tu vista -> coordenadas del BUFFER (no del panel fisico).
        1) tu vista -> panel nativo segun VIEW_ROT.  2) el LCD espeja x (MADCTL MX): se invierte aqui."""
        n = self.n - 1
        if self.vr == 90:
            px, py = n - y, x
        elif self.vr == 180:
            px, py = n - x, n - y
        elif self.vr == 270:
            px, py = y, n - x
        else:
            px, py = x, y
        if self.mx:
            px = n - px
        return px, py

    def rect(self, fb, x, y, w, h, c, fill=False):
        x0, y0 = self._p(x, y)
        x1, y1 = self._p(x + w - 1, y + h - 1)
        fb.rect(min(x0, x1), min(y0, y1), abs(x1 - x0) + 1, abs(y1 - y0) + 1, c, fill)

    def line(self, fb, x0, y0, x1, y1, c):
        a, b = self._p(int(x0), int(y0))
        d, e = self._p(int(x1), int(y1))
        fb.line(a, b, d, e, c)

    def circle(self, fb, cx, cy, r, c, fill=False):
        a, b = self._p(int(cx), int(cy))
        fb.ellipse(a, b, r, r, c, fill)

    def tri(self, fb, p0, p1, p2, c):
        """Triangulo relleno con vertices en coordenadas de tu vista."""
        pts = [self._p(int(x), int(y)) for x, y in (p0, p1, p2)]
        if hasattr(fb, "poly"):
            fb.poly(0, 0, array("h", [pts[0][0], pts[0][1], pts[1][0], pts[1][1], pts[2][0], pts[2][1]]), c, True)
        else:                                   # sin poly: solo el contorno
            for i in range(3):
                a, b = pts[i], pts[(i + 1) % 3]
                fb.line(a[0], a[1], b[0], b[1], c)

    # ---- datos del IMU
    def update_imu(self, acc, gyro=None, alpha=0.25):
        self.ax += alpha * (acc[0] - self.ax)
        self.ay += alpha * (acc[1] - self.ay)
        self.az += alpha * (acc[2] - self.az)
        if gyro is not None:
            self.gz += 0.4 * (gyro[2] - self.gz)

    def _gravity(self):
        """Proyeccion de la gravedad en TU pantalla (dx der, dy abajo), en g."""
        a = (self.ax, self.ay, self.az)
        return self.sx * a[self.ix], self.sy * a[self.iy]

    # ---- bateria
    def battery(self, fb, pct, present=True):
        x, y = 196, 8                       # arriba a la derecha (en tu vista)
        self.rect(fb, x, y, 34, 16, WHITE)
        self.rect(fb, x + 34, y + 4, 3, 8, WHITE, True)       # polo
        if not present:                      # sin bateria: tachado gris
            self.line(fb, x + 2, y + 2, x + 31, y + 13, GREY)
            self.line(fb, x + 2, y + 13, x + 31, y + 2, GREY)
            return
        col = GREEN if pct > 50 else (YELLOW if pct > 20 else RED)
        w = (30 * max(0, min(100, pct))) // 100
        if w > 0:
            self.rect(fb, x + 2, y + 2, w, 12, col, True)

    # ---- estilo "bubble" (placa plana)
    def bubble(self, fb):
        cx, cy, r = 36, 204, 28              # abajo a la izquierda (en tu vista)
        dx, dy = self._gravity()
        px, py = dx * r, dy * r              # 1 g = radio completo
        m = (px * px + py * py) ** 0.5
        lim = r - 5
        if m > lim:
            px, py = px * lim / m, py * lim / m
        tilt = min(1.0, (dx * dx + dy * dy) ** 0.5)
        col = GREEN if tilt < 0.05 else (YELLOW if tilt < 0.3 else RED)
        self.circle(fb, cx, cy, r, WHITE)
        self.circle(fb, cx, cy, r // 2, GREY)
        self.line(fb, cx - r, cy, cx + r, cy, GREY)
        self.line(fb, cx, cy - r, cx, cy + r, GREY)
        self.circle(fb, cx + px, cy + py, 5, col, True)

    # ---- estilo "horizon" (placa vertical): horizonte artificial tipo avion
    def horizon(self, fb):
        c0 = self.n // 2
        dx, dy = self._gravity()
        m = math.sqrt(dx * dx + dy * dy)
        # alabeo (theta, horario +): angulo de la gravedad respecto a "abajo de la pantalla".
        # Placa casi plana (m pequeno): el alabeo no esta definido -> horizonte nivelado.
        theta = math.atan2(dx, dy) if m > 0.2 else 0.0
        pitch = math.degrees(math.atan2(self.az * PITCH_SIGN, m if m > 0.05 else 0.05))
        pitch = max(-PITCH_MAX, min(PITCH_MAX, pitch))   # limita el desplazamiento: el horizonte no se pierde
        s, c = math.sin(theta), math.cos(theta)
        # vectores unitarios en tu vista: h = a lo largo del horizonte (c, -s); g = hacia el suelo (s, c)
        off = pitch * PX_PER_DEG                      # camara hacia arriba -> horizonte baja (hacia el suelo)
        hx, hy = c0 + s * off, c0 + c * off
        # horizonte: dos segmentos con hueco en el centro
        for sg in (-1, 1):
            self.line(fb, hx + sg * c * 24, hy - sg * s * 24, hx + sg * c * 110, hy - sg * s * 110, CYAN)
        # marcas de suelo (hacia donde cae la gravedad)
        for t in (-80, -45, 45, 80):
            bx, by = hx + t * c, hy - t * s
            self.line(fb, bx, by, bx + s * 9, by + c * 9, CYAN)
        # escala de cabeceo: lineas a +-10 y +-20 grados (arriba = hacia el cielo)
        for ang in (-20, -10, 10, 20):
            px = hx - s * ang * PX_PER_DEG
            py = hy - c * ang * PX_PER_DEG
            ln = 22 if ang % 20 == 0 else 14
            self.line(fb, px - c * ln, py + s * ln, px + c * ln, py - s * ln, WHITE)
        # simbolo fijo del avion (centro de la pantalla)
        self.line(fb, c0 - 40, c0, c0 - 14, c0, YELLOW)
        self.line(fb, c0 + 14, c0, c0 + 40, c0, YELLOW)
        self.line(fb, c0 - 14, c0, c0 - 14, c0 + 6, YELLOW)
        self.line(fb, c0 + 14, c0, c0 + 14, c0 + 6, YELLOW)
        self.circle(fb, c0, c0, 2, YELLOW, True)
        # arco de alabeo arriba: marcas cada 15 grados y puntero que apunta al CIELO
        R = 104
        for a in range(-60, 61, 15):
            r = math.radians(a)
            ln = 10 if a % 30 == 0 else 5
            self.line(fb, c0 + R * math.sin(r), c0 - R * math.cos(r),
                      c0 + (R - ln) * math.sin(r), c0 - (R - ln) * math.cos(r), WHITE)
        roll_deg = math.degrees(theta)
        col = GREEN if abs(roll_deg) < 10 else (YELLOW if abs(roll_deg) < 30 else RED)
        sk = max(-math.radians(75), min(math.radians(75), -theta))     # el cielo se ve girado al reves
        tip = (c0 + (R - 12) * math.sin(sk), c0 - (R - 12) * math.cos(sk))
        b1 = (c0 + (R + 2) * math.sin(sk - 0.07), c0 - (R + 2) * math.cos(sk - 0.07))
        b2 = (c0 + (R + 2) * math.sin(sk + 0.07), c0 - (R + 2) * math.cos(sk + 0.07))
        self.tri(fb, tip, b1, b2, col)
        # flechas de giro (solo mientras rotas): sentido horario/antihorario segun el giroscopio
        rate_cw = -self.gz * GZ_SIGN
        if abs(rate_cw) > GYRO_THRESHOLD:
            k = int(min(14, 6 + abs(rate_cw) / 14))
            cw = rate_cw > 0
            # lado derecho: horario baja, antihorario sube; lado izquierdo: al reves
            for side, up in ((c0 + 100, not cw), (c0 - 100, cw)):
                if up:
                    self.tri(fb, (side - k, c0 + k), (side + k, c0 + k), (side, c0 - k), MAGENTA)
                else:
                    self.tri(fb, (side - k, c0 - k), (side + k, c0 - k), (side, c0 + k), MAGENTA)

    def draw(self, buf, pct, present=True):
        """Dibuja bateria + horizonte (o burbuja) sobre buf (bytearray/memoryview escribible 240x240 RGB565)."""
        fb = framebuf.FrameBuffer(buf, self.n, self.n, framebuf.RGB565)
        if self.style == "bubble":
            self.bubble(fb)
        else:
            self.horizon(fb)
        self.battery(fb, pct, present)
