# Modulos propios que se congelan en el firmware LVGL (make.py lo suma a los drivers de LVGL).
# Fuente unica: ports/esp32/modules de ~/micropython (la misma carpeta que congela el firmware normal): wifiConnect, ftp*, fjs,
# netutils, fonts, drivers, lib, secrets.py, etc.
# Se SALTAN los archivos estandar de MicroPython (_boot, machine, flashbdev, inisetup, espnow, apa106): lvgl_micropython trae los suyos,
# de otra version, y pisarlos puede romper el arranque.
# OJO: incluye secrets.py y los webrepl_cfg.py -> el .bin contiene claves reales: NO publicar el .bin.
import os

_SRC = os.environ.get("MPY_USER_MODULES", os.path.expanduser("~/micropython/ports/esp32/modules"))
_STD = ("_boot.py", "machine.py", "flashbdev.py", "inisetup.py", "espnow.py", "apa106.py")

_files = []
for _root, _dirs, _names in os.walk(_SRC):
    _dirs[:] = sorted(d for d in _dirs if d != "__pycache__" and not d.startswith("."))
    for _n in sorted(_names):
        _rel = os.path.relpath(os.path.join(_root, _n), _SRC)
        if _n.endswith(".py") and _rel not in _STD:      # _STD: solo en la raiz
            _files.append(_rel)

# freeze() no expande carpetas dentro de la lista: se pasan los .py con su ruta relativa (conserva los paquetes: fjs/tlc.py, ...)
freeze(_SRC, tuple(_files))

# touch_fix.py (orientacion del touch) vive junto a este manifest; build.sh exporta su carpeta en LVGL_BOARD_DIR.
_HERE = os.environ.get("LVGL_BOARD_DIR")
if _HERE and os.path.exists(os.path.join(_HERE, "touch_fix.py")):
    freeze(_HERE, "touch_fix.py")

# Drivers directos de la placa (SIN LVGL), los mismos del firmware normal: board.py (detecta el firmware), st7789, lcd_jd9853, touch_axs5106.
# Nombres distintos a jd9853/axs5106 a proposito: esos son los modulos de LVGL. Sirven si NO se importa "display" (modos excluyentes).
if _HERE:
    _TM = os.path.join(_HERE, "..", "tested_modules")
    freeze(_TM, ("board.py", "st7789.py", "lcd_jd9853.py", "touch_axs5106.py"))
