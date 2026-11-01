"""Fallback: si no hay main.py, levanta WiFi (+ WebREPL + FTP) para
poder subir codigo por red.

Depende del modulo congelado `wifiConnect` del FW (ver
CATALOGO_MODULOS_FW.md); lee wifi_config.py e ipaddress.cfg.
"""

try:
    import uos
except ImportError:
    uos = None


def run():
    if uos is not None:
        try:
            uos.stat("main.py")
            return
        except OSError:
            pass
    try:
        import wifiConnect
    except ImportError:
        print("[startup] main.py absent; wifiConnect fallback unavailable")
