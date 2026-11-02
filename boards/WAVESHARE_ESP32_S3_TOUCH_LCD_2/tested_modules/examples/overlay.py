# Overlay grafico sobre el frame de la camara (240x240 RGB565): horizonte tipo avion + escala de cabeceo +
# bateria, con el IMU. Dibuja con framebuf directamente en el buffer que va al LCD. Sin texto.
#
# Elementos (todo en tu vista):
#   - Horizonte artificial: linea que se inclina con el alabeo y se desplaza con el cabeceo, marcas de suelo,
#     escala de cabeceo (+-10/20 grados) y simbolo fijo del avion en el centro. El horizonte se pone VERDE
#     cuando alabeo y cabeceo estan ambos dentro de +-LEVEL_DEG (cian el resto del tiempo).
#   - Arco de alabeo arriba con un puntero que apunta hacia el CIELO (verde nivelado, amarillo, rojo).
#   - Escala VERTICAL de cabeceo a la derecha con un triangulo: alineado con el cero (y verde) = nivelado.
#   - Flechas magenta a los lados SOLO mientras rotas (giroscopio): sentido horario / antihorario.
#   - Bateria arriba a la derecha.
#
# Cero (tare): Overlay.tare() toma el alabeo y cabeceo actuales como referencia (0 grados). Sirve si la pantalla
# no esta a 90 sino a 110: pasa a medir como si estuviera a 90. Se guarda en ZERO_FILE y se recarga al arrancar.
#
# Ejes del IMU en esta placa (medidos): +x = tu izquierda, +y = arriba, +z = hacia dentro de la pantalla
# (con la placa apaisada y el video derecho). Gravedad en tu vista: dx = +ax, dy = +ay.
# MIRROR_X: el driver del LCD aplica MADCTL MX (espejo en x) y la camara lo compensa con hmirror; el overlay
# se dibuja en el mismo buffer, asi que _p() tambien lo compensa.
# VIEW_ROT: como ves el panel respecto a su orientacion nativa (90 = franja de UI a tu derecha).
import framebuf
import math
import time
from array import array


def c565(r, g, b):
    # el LCD recibe RGB565 big-endian y framebuf escribe little-endian: se intercambian los bytes
    v = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
    return ((v & 0xFF) << 8) | (v >> 8)


WHITE = c565(255, 255, 255)
GREY = c565(120, 120, 120)
GREEN = c565(0, 220, 0)
YELLOW = c565(255, 200, 0)
RED = c565(255, 40, 40)
CYAN = c565(0, 230, 230)
MAGENTA = c565(255, 0, 255)

MIRROR_X = True
PITCH_SIGN = 1        # +1: az > 0 = la camara mira hacia arriba (el horizonte baja). Si sube, pon -1
GZ_SIGN = -1          # +z mira hacia dentro de la pantalla: gz > 0 = giro HORARIO para ti. Si va al reves, pon 1
PX_PER_DEG = 2.2      # desplazamiento del horizonte por grado de cabeceo
PITCH_MAX = 50        # grados maximos de cabeceo que se dibujan en el horizonte
LEVEL_DEG = 5         # el horizonte se pone verde si |alabeo| y |cabeceo| estan por debajo de esto
GYRO_THRESHOLD = 12   # grados/s por debajo de los cuales no se muestran las flechas de giro
SCALE_PX = 2.5        # px por grado en la escala vertical de cabeceo
SCALE_MAX = 33        # grados que caben en la escala (+-)
ZERO_FILE = "/imu_zero.txt"


class Overlay:
    def __init__(self, size=240, view_rot=90, mirror_x=MIRROR_X):
        self.n = size
        self.vr = view_rot
        self.mx = mirror_x
        self.ax = self.ay = 0.0     # aceleracion filtrada (g) en los ejes del IMU
        self.az = 1.0
        self.gz = 0.0               # velocidad de giro filtrada alrededor de z (grados/s)
        self._seeded = False        # el filtro arranca con la primera lectura (no desde 'placa plana')
        self.roll0 = 0.0            # referencia de cero: alabeo (rad) y cabeceo (grados)
        self.pitch0 = 0.0
        self._flash_until = 0
        self._flash_col = GREEN
        self.load_zero()

    # ---- cero (tare)
    def load_zero(self):
        try:
            with open(ZERO_FILE) as f:
                a, b = f.read().split()
            self.roll0, self.pitch0 = float(a), float(b)
        except (OSError, ValueError):
            pass

    def save_zero(self):
        try:
            with open(ZERO_FILE, "w") as f:
                f.write("%f %f" % (self.roll0, self.pitch0))
        except OSError:
            pass

    def tare(self):
        """Toma el alabeo/cabeceo actuales como cero. False si la placa esta casi plana (alabeo indefinido)."""
        theta, pitch, m = self._attitude()
        if m < 0.5:
            return False
        self.roll0, self.pitch0 = theta, pitch
        self.save_zero()
        return True

    def reset_zero(self):
        self.roll0 = self.pitch0 = 0.0
        self.save_zero()

    def flash(self, ok=True, ms=600):
        """Marco verde (o rojo) un momento: confirmacion visual del boton."""
        self._flash_until = time.ticks_add(time.ticks_ms(), ms)
        self._flash_col = GREEN if ok else RED

    # ---- mapa vista (x der, y abajo, como lo ves) -> coordenadas del BUFFER
    def _p(self, x, y):
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
        if not self._seeded:
            self.ax, self.ay, self.az = acc[0], acc[1], acc[2]
            self._seeded = True
            return
        self.ax += alpha * (acc[0] - self.ax)
        self.ay += alpha * (acc[1] - self.ay)
        self.az += alpha * (acc[2] - self.az)
        if gyro is not None:
            self.gz += 0.4 * (gyro[2] - self.gz)

    def _attitude(self):
        """(alabeo horario en rad, cabeceo en grados, modulo de la gravedad en el plano). Sin restar el cero."""
        dx, dy = self.ax, self.ay                 # gravedad en tu vista
        m = math.sqrt(dx * dx + dy * dy)
        theta = math.atan2(dx, dy) if m > 0.2 else 0.0      # placa casi plana: alabeo indefinido -> 0
        pitch = math.degrees(math.atan2(self.az * PITCH_SIGN, m if m > 0.05 else 0.05))
        return theta, pitch, m

    def _relative(self):
        """Alabeo (rad) y cabeceo (grados) respecto al cero."""
        theta, pitch, m = self._attitude()
        if m > 0.2:
            d = theta - self.roll0
            theta = (d + math.pi) % (2 * math.pi) - math.pi      # envuelve a (-pi, pi]
        return theta, pitch - self.pitch0

    # ---- elementos
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

    def horizon(self, fb, theta, pitch):
        c0 = self.n // 2
        roll_deg = math.degrees(theta)
        level = abs(roll_deg) < LEVEL_DEG and abs(pitch) < LEVEL_DEG
        hcol = GREEN if level else CYAN                 # verde: alabeo y cabeceo dentro de +-LEVEL_DEG
        pitch_c = max(-PITCH_MAX, min(PITCH_MAX, pitch))     # el horizonte no se sale de la pantalla
        s, c = math.sin(theta), math.cos(theta)
        # vectores unitarios en tu vista: h = a lo largo del horizonte (c, -s); g = hacia el suelo (s, c)
        off = pitch_c * PX_PER_DEG                    # camara hacia arriba -> horizonte baja (hacia el suelo)
        hx, hy = c0 + s * off, c0 + c * off
        for sg in (-1, 1):                             # horizonte: dos segmentos con hueco central
            self.line(fb, hx + sg * c * 24, hy - sg * s * 24, hx + sg * c * 110, hy - sg * s * 110, hcol)
        for t in (-80, -45, 45, 80):                   # marcas de suelo
            bx, by = hx + t * c, hy - t * s
            self.line(fb, bx, by, bx + s * 9, by + c * 9, hcol)
        for ang in (-20, -10, 10, 20):                 # escala de cabeceo (arriba = cielo)
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
        col = GREEN if abs(roll_deg) < 10 else (YELLOW if abs(roll_deg) < 30 else RED)
        sk = max(-math.radians(75), min(math.radians(75), -theta))     # el cielo se ve girado al reves
        tip = (c0 + (R - 12) * math.sin(sk), c0 - (R - 12) * math.cos(sk))
        b1 = (c0 + (R + 2) * math.sin(sk - 0.07), c0 - (R + 2) * math.cos(sk - 0.07))
        b2 = (c0 + (R + 2) * math.sin(sk + 0.07), c0 - (R + 2) * math.cos(sk + 0.07))
        self.tri(fb, tip, b1, b2, col)

    def pitch_scale(self, fb, pitch):
        """Escala vertical a la derecha: el triangulo marca el cabeceo; alineado con el cero (amarillo) = nivelado."""
        x, z = 226, self.n // 2
        self.line(fb, x, z - int(SCALE_MAX * SCALE_PX), x, z + int(SCALE_MAX * SCALE_PX), GREY)
        for deg in range(-30, 31, 5):
            y = z - deg * SCALE_PX
            if deg == 0:
                self.line(fb, x - 14, y, x + 3, y, YELLOW)
            else:
                self.line(fb, x - (8 if deg % 10 == 0 else 4), y, x, y, WHITE)
        p = max(-SCALE_MAX, min(SCALE_MAX, pitch))
        y = z - p * SCALE_PX
        col = GREEN if abs(pitch) < 2 else (YELLOW if abs(pitch) < 10 else RED)
        self.tri(fb, (x - 7, y), (x - 21, y - 8), (x - 21, y + 8), col)

    def turn_arrows(self, fb):
        """Flechas magenta mientras rotas (giroscopio): derecha baja + izquierda sube = horario."""
        rate_cw = -self.gz * GZ_SIGN
        if abs(rate_cw) <= GYRO_THRESHOLD:
            return
        c0 = self.n // 2
        k = int(min(13, 6 + abs(rate_cw) / 14))
        cw = rate_cw > 0
        for side, up in ((c0 + 70, not cw), (c0 - 70, cw)):
            if up:
                self.tri(fb, (side - k, c0 + k), (side + k, c0 + k), (side, c0 - k), MAGENTA)
            else:
                self.tri(fb, (side - k, c0 - k), (side + k, c0 - k), (side, c0 + k), MAGENTA)

    def draw(self, buf, pct, present=True):
        """Dibuja el overlay sobre buf (bytearray/memoryview escribible 240x240 RGB565)."""
        fb = framebuf.FrameBuffer(buf, self.n, self.n, framebuf.RGB565)
        theta, pitch = self._relative()
        self.horizon(fb, theta, pitch)
        self.pitch_scale(fb, pitch)
        self.turn_arrows(fb)
        self.battery(fb, pct, present)
        if time.ticks_diff(self._flash_until, time.ticks_ms()) > 0:      # confirmacion del boton
            self.rect(fb, 0, 0, self.n, self.n, self._flash_col)
            self.rect(fb, 1, 1, self.n - 2, self.n - 2, self._flash_col)
            self.rect(fb, 2, 2, self.n - 4, self.n - 4, self._flash_col)
