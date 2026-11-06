# horizon: video de camara + horizonte artificial, en un hilo con asyncio. El REPL queda libre.
#
#   import horizon
#   horizon.start()                  # arranca en segundo plano; start(mode='ball') arranca en la bola
#   horizon.mode('ball')             # cambia de modo (BOOT doble hace lo mismo, alternando)
#   horizon.stop()                   # para (tambien BOOT largo)
#   horizon.status()                 # dict: running, fps, bat_pct, ...
#   horizon.enable_autostart()       # arranca solo al encender (escribe main.py); disable_autostart() lo quita
#   horizon.config(overlay=False)    # cambia un ajuste y lo guarda (efectivo en el proximo start)
#   horizon.start(reload=True)       # recarga los plugins (tras editarlos)
# BOOT corto = cero (horizonte) / reiniciar nivel (bola); doble = cambiar de modo; largo = parar.
# Arquitectura y como anadir un plugin: ver app.py.
from horizon.app import App, DEFAULT, save_cfg

app = App()
_MARK = "# horizon-autostart"
_MAIN = "main.py"


def start(reload=False, mode=None):
    return app.start(reload, mode)


def mode(name=None):
    """Sin argumento: modo actual. Con nombre ('horizon' / 'ball'): cambia de modo."""
    if name:
        app.set_mode(name)
    return app.mode


def stop(wait=True):
    app.stop()
    if wait:
        import time
        for _ in range(60):
            if not app.running:
                break
            time.sleep_ms(50)
    return not app.running


def status():
    d = dict(app.state)
    d["running"] = app.running
    return d


def config(**kw):
    for k, v in kw.items():
        if k not in DEFAULT:
            raise KeyError(k)
        app.cfg[k] = v
    save_cfg(app.cfg)
    return app.cfg


def _ours():
    try:
        with open(_MAIN) as f:
            txt = f.read()
        return _MARK in txt or not txt.strip()      # un main.py vacio (el que evita el hilo FTP) tambien vale
    except OSError:
        return None             # no existe


def enable_autostart():
    own = _ours()
    if own is False:
        print("main.py existe y no es de horizon: anade 'import horizon; horizon.boot()' a mano")
    else:
        with open(_MAIN, "w") as f:
            f.write("%s\nimport horizon\nhorizon.boot()\n" % _MARK)
    config(autostart=True)


def disable_autostart():
    if _ours():
        open(_MAIN, "w").close()        # vacio, no borrado: sin main.py arranca el fallback/FTP del firmware
    config(autostart=False)


def boot():
    """Llamar desde main.py: arranca si autostart esta activo."""
    if app.cfg["autostart"]:
        start()
