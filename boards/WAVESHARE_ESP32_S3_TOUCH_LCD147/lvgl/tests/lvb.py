# Ayudas comunes de los tests LVGL de la Waveshare ESP32-S3-Touch-LCD-1.47 (firmware LVGL: display, touch y TaskHandler ya los crea display.py).
# Pines confirmados con el esquematico: bateria GPIO12 (x3), SD SDMMC CLK16 CMD15 D0 17 D1 18 D2 13 D3 14, BOOT GPIO0.
import time, machine
import lvgl as lv
import display as _d                 # ejecuta el arranque generado (una sola vez; luego queda en cache)

disp = _d.display                    # jd9853.JD9853  (set_backlight, set_color_inversion, set_rotation...)
indev = _d.indev                     # axs5106.AXS5106
W, H = 172, 320
BOOT, VBAT = 0, 12


def screen(bg=0x000000):
    """Pantalla NUEVA y activa; la anterior se borra con sus callbacks (evita LvReferenceError si un ejemplo anterior se corto con Ctrl-C)."""
    old = lv.screen_active()
    s = lv.obj(None)
    s.set_style_bg_color(lv.color_hex(bg), 0)
    s.set_style_bg_opa(255, 0)
    lv.screen_load(s)
    try:
        old.delete()
    except Exception:
        pass
    return s


def label(parent, text, color=0xFFFFFF, y=None, x=None):
    lb = lv.label(parent)
    lb.set_text(text)
    lb.set_style_text_color(lv.color_hex(color), 0)
    if y is None:
        lb.center()
    else:
        lb.align(lv.ALIGN.TOP_LEFT, 4 if x is None else x, y)
    return lb


def button():
    return machine.Pin(BOOT, machine.Pin.IN, machine.Pin.PULL_UP)


def vbat():
    adc = machine.ADC(machine.Pin(VBAT), atten=machine.ADC.ATTN_11DB)
    return sum(adc.read_uv() for _ in range(16)) / 16 * 3 / 1_000_000


def battery_percent(v=None):
    v = vbat() if v is None else v
    return max(0, min(100, int((v - 3.3) / (4.2 - 3.3) * 100)))


def sd_mount(path="/sd"):
    import os
    sd = machine.SDCard(slot=1, width=4, clk=16, cmd=15, data_pins=(17, 18, 13, 14))
    os.mount(sd, path)
    return sd


def wait(ms):
    time.sleep_ms(ms)                # el TaskHandler corre por timer: la pantalla se refresca durante la espera


def touch_orient(mirror_x=True, mirror_y=False, swap=False):
    """Prueba la orientacion del touch SIN recompilar (se pierde al reiniciar). Cuando acierte, fijala en touch_fix.py y recompila."""
    class _C:
        pass
    c = _C()
    c.alphaX, c.betaX, c.alphaY, c.betaY = (0.0, 1.0, 1.0, 0.0) if swap else (1.0, 0.0, 0.0, 1.0)
    c.deltaX = c.deltaY = 0.0
    c.mirrorX, c.mirrorY = mirror_x, mirror_y
    c.save = lambda: None
    indev._cal = c
