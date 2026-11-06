# Demo de interfaz LVGL para la Waveshare ESP32-S3-Touch-LCD-1.47 (172x320 vertical): brillo, bateria, temperatura, switch y botones.
# USO (REPL, con tests/lvb.py en la placa):  import ui_demo      # vuelve al prompt; la UI sigue viva (timers)
#   ui_demo.stop()  para parar el refresco.   Controles: slider = brillo | switch = invertir colores | boton = contador
import lvgl as lv
import esp32
import lvb

scr = lvb.screen(0x101820)
title = lvb.label(scr, "LVGL 1.47", 0x00DCDC, y=6, x=46)

lvb.label(scr, "Brillo", 0xFFFFFF, y=36)
sl = lv.slider(scr)
sl.set_size(140, 14)
sl.align(lv.ALIGN.TOP_MID, 0, 62)
sl.set_range(5, 100)
sl.set_value(80, 0)


def on_slider(e):
    lvb.disp.set_backlight(sl.get_value())


sl.add_event_cb(on_slider, lv.EVENT.VALUE_CHANGED, None)

lvb.label(scr, "Bateria", 0xFFFFFF, y=92)
bar = lv.bar(scr)
bar.set_size(140, 14)
bar.align(lv.ALIGN.TOP_MID, 0, 118)
bar.set_range(0, 100)
vlbl = lvb.label(scr, "", 0xFFC800, y=138)
tlbl = lvb.label(scr, "", 0xFFC800, y=158)

lvb.label(scr, "Invertir color", 0xFFFFFF, y=190)
sw = lv.switch(scr)
sw.align(lv.ALIGN.TOP_RIGHT, -8, 184)
sw.add_state(lv.STATE.CHECKED)               # el panel arranca invertido (set_color_inversion(True) en el .toml)


def on_switch(e):
    lvb.disp.set_color_inversion(sw.has_state(lv.STATE.CHECKED))


sw.add_event_cb(on_switch, lv.EVENT.VALUE_CHANGED, None)

count = [0]
btn = lv.button(scr)
btn.set_size(140, 44)
btn.align(lv.ALIGN.TOP_MID, 0, 230)
blbl = lv.label(btn)
blbl.set_text("Toca: 0")
blbl.center()


def on_btn(e):
    count[0] += 1
    blbl.set_text("Toca: %d" % count[0])


btn.add_event_cb(on_btn, lv.EVENT.CLICKED, None)


def refresh(t):
    v = lvb.vbat()
    if v > 2.8:
        bar.set_value(lvb.battery_percent(v), 0)
        vlbl.set_text("%.2f V  %d %%" % (v, lvb.battery_percent(v)))
    else:
        bar.set_value(0, 0)
        vlbl.set_text("%.2f V sin bateria" % v)
    tlbl.set_text("Chip: %.1f C" % esp32.mcu_temperature())


refresh(None)
_timer = lv.timer_create(refresh, 2000, None)


def stop():
    _timer.delete()
