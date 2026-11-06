# boot.py -- plantilla base ESP32
# Orden: cleanup (recuperacion) -> fallback (sin main.py) -> hostname.
# Cada paso es opcional: si el modulo no existe se ignora, asi boot.py
# nunca impide llegar al REPL.
import network
import machine

HOSTNAME_PREFIX = "ESP32"   # cambiar por proyecto, p.ej. "T190", "PaddockS3"

try:
    import startup_cleanup
    startup_cleanup.run()
except ImportError:
    pass

try:
    import startup_fallback
    startup_fallback.run()
except ImportError:
    pass

if hasattr(network, "hostname"):
    try:
        uid = machine.unique_id()
        suffix = "{:02X}{:02X}".format(uid[-2], uid[-1])
    except Exception:
        suffix = "0000"
    network.hostname("{}-{}".format(HOSTNAME_PREFIX, suffix))
