# Nucleo de horizon: hilo + asyncio + plugins. No sabe nada de camara, IMU ni botones: eso son plugins.
#
# Un plugin es un modulo horizon/plugins/<nombre>.py con `def setup(app)`. En setup puede:
#     app.add_task(nombre, corutina)      corutina(app) corre en el loop asyncio del hilo (debe hacer await a menudo)
#     app.add_layer(fn)                   fn(ov, fb): dibuja encima del frame (coordenadas de tu vista: ov.line/rect/...)
#     app.on("evento", fn)                suscribirse a eventos (button_short, button_long, ...); app.emit("evento", ...)
#     app.on_stop(fn)                     limpieza al parar
#     app.state[...]                      datos compartidos (bat_pct, fps, ...)
#     app.add_mode(nombre)                registra una "pantalla" (horizon, ball...); solo la tarea del modo activo dibuja:
#                                         comprueba `app.mode == nombre` en su bucle y suelta sus recursos si no es la suya
#     app.set_mode(n) / app.next_mode()   cambia de modo (evento "mode"); el boton doble hace next_mode()
# El orden de cfg["plugins"] es el orden de setup(): los que dibujan o leen van despues de los que crean el hardware.
import sys
import time
import json
import gc
import _thread
import uasyncio as asyncio

CFG_FILE = "/horizon.json"
DEFAULT = {
    "autostart": False,
    "plugins": ["display", "imu", "battery", "button", "video", "ball"],
    "mode": "horizon",          # modo inicial: "horizon" o "ball"
    "ball": {"swap_xy": True, "sign_x": -1, "sign_y": 1},   # ejes del IMU para la bola (portrait)
    "buttons": {},              # tiempos del boton (ver buttons.PAGE_DEFAULTS): SHORT_MS, LONG_MS, EXTRA_MS, DOUBLE_MS
    "critical": ["video"],      # si una de estas tareas muere, se para todo
    "view_rot": 90,             # como ves el panel respecto a su orientacion nativa
    "hmirror": True,            # espejo de la camara (compensa el MX del LCD)
    "vflip": False,
    "overlay": True,
    "backlight": 80,
    "spi_hz": 40_000_000,
    "verbose": False,           # imprime fps/bateria en el REPL cada 100 frames
}


def load_cfg():
    cfg = dict(DEFAULT)
    try:
        with open(CFG_FILE) as f:
            cfg.update(json.load(f))
    except (OSError, ValueError):
        pass
    return cfg


def save_cfg(cfg):
    diff = {k: v for k, v in cfg.items() if DEFAULT.get(k) != v}
    with open(CFG_FILE, "w") as f:
        json.dump(diff, f)


class App:
    def __init__(self):
        self.cfg = load_cfg()
        self.running = False
        self.state = {}
        self._reset()

    def _reset(self):
        self.ov = None
        self.mode = None
        self.modes = []
        self.layers = []
        self._events = {}
        self._tasks = []        # (nombre, corutina)
        self._stops = []
        self._hw = {}
        self._stop = False

    # ---- API para plugins
    def add_task(self, name, coro):
        self._tasks.append((name, coro))

    def add_layer(self, fn):
        self.layers.append(fn)

    def on(self, event, fn):
        self._events.setdefault(event, []).append(fn)

    def emit(self, event, *args):
        for fn in self._events.get(event, ()):
            try:
                fn(*args)
            except Exception as e:
                print("[horizon] error en handler", event)
                sys.print_exception(e)

    def on_stop(self, fn):
        self._stops.append(fn)

    def hw(self, name, factory):
        """Recurso de hardware compartido (p.ej. el bus I2C): se crea una vez."""
        if name not in self._hw:
            self._hw[name] = factory()
        return self._hw[name]

    def add_mode(self, name):
        self.modes.append(name)

    def set_mode(self, name):
        if name in self.modes and name != self.mode:
            self.mode = name
            print("[horizon] modo:", name)
            self.emit("mode", name)

    def next_mode(self):
        if self.modes:
            i = self.modes.index(self.mode) if self.mode in self.modes else -1
            self.set_mode(self.modes[(i + 1) % len(self.modes)])

    def stop(self):
        self._stop = True

    # ---- ciclo de vida
    def start(self, reload=False, mode=None):
        if self.running:
            print("[horizon] ya esta en marcha")
            return False
        if reload:
            for m in [m for m in sys.modules if m == "horizon.plugins" or m.startswith("horizon.plugins.")
                      or m in ("horizon.overlay",)]:
                del sys.modules[m]
        self.cfg = load_cfg()
        self._reset()
        self._mode0 = mode or self.cfg["mode"]
        self.running = True
        gc.collect()
        _thread.stack_size(20 * 1024)
        _thread.start_new_thread(self._thread_main, ())
        return True

    def _thread_main(self):
        try:
            asyncio.run(self._main())
        except Exception as e:
            print("[horizon] error fatal")
            sys.print_exception(e)
        finally:
            self.running = False
            gc.collect()
            print("[horizon] parado")

    async def _guard(self, name, coro):
        try:
            await coro(self)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            print("[horizon] tarea '%s' murio" % name)
            sys.print_exception(e)
            if name in self.cfg["critical"]:
                self.stop()

    async def _main(self):
        from horizon.overlay import Overlay
        self.ov = Overlay(240, self.cfg["view_rot"])
        self.ov.layers = self.layers
        for name in self.cfg["plugins"]:
            try:
                mod = __import__("horizon.plugins." + name, None, None, ["setup"])
                mod.setup(self)
            except Exception as e:
                print("[horizon] plugin '%s' no cargo" % name)
                sys.print_exception(e)
                if name in self.cfg["critical"]:
                    self._stop = True
        self.mode = self._mode0 if self._mode0 in self.modes else (self.modes[0] if self.modes else None)
        tasks = [asyncio.create_task(self._guard(n, c)) for n, c in self._tasks] if not self._stop else []
        while not self._stop:                   # supervisor: stop() puede llamarse desde cualquier hilo
            await asyncio.sleep_ms(50)
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        for fn in self._stops:
            try:
                fn()
            except Exception as e:
                sys.print_exception(e)
