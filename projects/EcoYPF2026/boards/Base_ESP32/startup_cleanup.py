"""Recuperacion: borra main.py si el boton BOOT esta presionado al arrancar.

Util cuando main.py bloquea el REPL (loop sin salida, crash en import).
Mantener BOOT (GPIO0) al dar reset/power-on; main.py se elimina y el
arranque cae en startup_fallback (WiFi + WebREPL + FTP) o en el REPL.
Si preferis conservar el archivo, usar d.py (lo renombra a mainBkp.py).
"""

BOOT_PIN = 0   # GPIO del boton BOOT (0 en casi todas las ESP32/S3)

try:
    import machine
except ImportError:
    machine = None

try:
    import uos
except ImportError:
    uos = None


def run():
    if machine is None or uos is None or not hasattr(machine, "Pin"):
        return
    try:
        button = machine.Pin(BOOT_PIN, machine.Pin.IN, machine.Pin.PULL_UP)
    except (TypeError, ValueError):
        button = machine.Pin(BOOT_PIN, machine.Pin.IN)
    try:
        pressed = button.value() == 0
    except AttributeError:
        pressed = False
    if not pressed:
        return
    try:
        uos.remove("main.py")
        print("[startup] BOOT held: main.py removed; recovery mode")
    except OSError as exc:
        print("[startup] main.py could not be removed:", exc)
