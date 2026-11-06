# Elige el "modo" de los ejemplos en el firmware LVGL de la Touch-LCD-1.47 (copiar a la raiz de la placa: :use.py).
#   import use; use.raw()     # SIN LVGL: ejemplos en /raw  (board.py + st7789/lcd_jd9853/touch_axs5106, todo congelado)
#   import use; use.lvgl()    # CON LVGL: ejemplos en /lvgl (usa lvb.py; display/touch los crea LVGL)
# Los dos modos se excluyen (SPI host 1 e I2C 0): para cambiar de uno a otro haz machine.reset() antes.
import sys


def _set(d):
    for p in ("/raw", "/lvgl"):
        while p in sys.path:
            sys.path.remove(p)
    sys.path.insert(0, d)
    print("modo", d, "-> import test_all | features | ...")


def raw():
    _set("/raw")


def lvgl():
    _set("/lvgl")
