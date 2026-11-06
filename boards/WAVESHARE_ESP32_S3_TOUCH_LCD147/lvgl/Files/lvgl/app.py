# App LVGL con 3 paginas que se cambian DESLIZANDO el dedo (tileview): 1 UI (brillo, bateria, temperatura, switch, boton),
# 2 FEATURES (chequeos de la placa + boton "Repetir"), 3 TOUCH (zona para probar el touch). Reune ui_demo.py y features.py.
# USO (REPL, con tests/lvb.py y touch_fix en la placa):  import app      # vuelve al prompt; app.stop() para parar los timers
# Desliza a izquierda/derecha para cambiar de pagina. Los chequeos de la pagina 2 no hacen esperas dentro de callbacks (no se bloquea LVGL).
import gc, os
import esp32
import lvgl as lv
import lvb

W, H = lvb.W, lvb.H
scr = lvb.screen(0x101820)
tv = lv.tileview(scr)
tv.set_size(W, H)
tv.set_style_bg_opa(0, 0)
t1 = tv.add_tile(0, 0, lv.DIR.RIGHT)
t2 = tv.add_tile(1, 0, lv.DIR.HOR)
t3 = tv.add_tile(2, 0, lv.DIR.LEFT)
NAMES = ("UI", "FEATURES", "TOUCH")
page = lvb.label(scr, "1/3", 0x808080, y=2, x=W - 30)


def on_scroll_end(e):
    i = (tv.get_scroll_x() + W // 2) // W
    page.set_text("%d/3" % (i + 1))


tv.add_event_cb(on_scroll_end, lv.EVENT.SCROLL_END, None)

# ---------------------------------------------------------------- pagina 1: UI
lvb.label(t1, "LVGL 1.47", 0x00DCDC, y=6, x=46)
lvb.label(t1, "Brillo", 0xFFFFFF, y=36)
sl = lv.slider(t1)
sl.set_size(120, 14)
sl.align(lv.ALIGN.TOP_MID, 0, 62)
sl.set_range(5, 100)
sl.set_value(80, 0)
sl.add_event_cb(lambda e: lvb.disp.set_backlight(sl.get_value()), lv.EVENT.VALUE_CHANGED, None)

lvb.label(t1, "Bateria", 0xFFFFFF, y=92)
bar = lv.bar(t1)
bar.set_size(120, 14)
bar.align(lv.ALIGN.TOP_MID, 0, 118)
bar.set_range(0, 100)
vlbl = lvb.label(t1, "", 0xFFC800, y=138)
tlbl = lvb.label(t1, "", 0xFFC800, y=158)

lvb.label(t1, "Invertir color", 0xFFFFFF, y=190)
sw = lv.switch(t1)
sw.align(lv.ALIGN.TOP_RIGHT, -8, 184)
sw.add_state(lv.STATE.CHECKED)            # el panel arranca invertido (set_color_inversion(True) en el .toml)
sw.add_event_cb(lambda e: lvb.disp.set_color_inversion(sw.has_state(lv.STATE.CHECKED)), lv.EVENT.VALUE_CHANGED, None)

count = [0]
btn = lv.button(t1)
btn.set_size(120, 44)
btn.align(lv.ALIGN.TOP_MID, 0, 230)
blbl = lv.label(btn)
blbl.set_text("Toca: 0")
blbl.center()


def on_btn(e):
    count[0] += 1
    blbl.set_text("Toca: %d" % count[0])


btn.add_event_cb(on_btn, lv.EVENT.CLICKED, None)
lvb.label(t1, "desliza >>", 0x808080, y=H - 18, x=W - 80)


def refresh(t=None):
    v = lvb.vbat()
    if v > 2.8:
        bar.set_value(lvb.battery_percent(v), 0)
        vlbl.set_text("%.2f V  %d %%" % (v, lvb.battery_percent(v)))
    else:
        bar.set_value(0, 0)
        vlbl.set_text("%.2f V sin bateria" % v)
    tlbl.set_text("Chip: %.1f C" % esp32.mcu_temperature())


# ---------------------------------------------------------------- pagina 2: FEATURES
lvb.label(t2, "FEATURES", 0x00DCDC, y=6, x=44)
rows = []
for i in range(7):
    rows.append(lvb.label(t2, "", 0xFFFFFF, y=30 + i * 20))
rbtn = lv.button(t2)
rbtn.set_size(120, 40)
rbtn.align(lv.ALIGN.TOP_MID, 0, 190)
rl = lv.label(rbtn)
rl.set_text("Repetir")
rl.center()
note = lvb.label(t2, "SD: pon una microSD FAT32", 0x808080, y=240)


def _sd():
    sd = lvb.sd_mount()
    try:
        with open("/sd/_t.txt", "w") as f:
            f.write("ok")
        ok = open("/sd/_t.txt").read() == "ok"
        os.remove("/sd/_t.txt")
        if not ok:
            raise OSError("lectura")
        return "%d arch." % len(os.listdir("/sd"))
    finally:
        os.umount("/sd")
        sd.deinit()


def _wifi():
    import network
    w = network.WLAN(network.STA_IF)
    w.active(True)
    n = w.scan()
    w.active(False)
    return "%d redes" % len(n)


def _bat():
    v = lvb.vbat()
    return "%.2fV %d%%" % (v, lvb.battery_percent(v)) if v > 2.8 else "%.2fV sin bat" % v


def _temp():
    t = esp32.mcu_temperature()
    if not 10 < t < 90:
        raise ValueError("%.0fC" % t)
    return "%.1fC" % t


def _mem():
    gc.collect()
    return "%dKB libres" % (gc.mem_free() // 1024)


CHECKS = (("Pantalla", lambda: "%dx%d" % (W, H)), ("Touch", lambda: "ver pag. 3"), ("Bateria", _bat),
          ("Temp", _temp), ("SD", _sd), ("WiFi", _wifi), ("Memoria", _mem))


def run_checks(e=None):
    for lb, (name, fn) in zip(rows, CHECKS):
        try:
            lb.set_text("OK   %s %s" % (name, fn() or ""))
            lb.set_style_text_color(lv.color_hex(0x00DC00), 0)
        except Exception as ex:
            lb.set_text("FAIL %s %s" % (name, repr(ex)[:12]))
            lb.set_style_text_color(lv.color_hex(0xFF3232), 0)
        print(lb.get_text())


rbtn.add_event_cb(run_checks, lv.EVENT.CLICKED, None)

# ---------------------------------------------------------------- pagina 3: TOUCH
lvb.label(t3, "TOUCH", 0x00DCDC, y=6, x=56)
pos = lvb.label(t3, "toca aqui", 0xFFFFFF, y=30, x=44)
pad = lv.obj(t3)
pad.set_size(W - 16, H - 90)
pad.align(lv.ALIGN.TOP_MID, 0, 56)
pad.set_style_bg_color(lv.color_hex(0x203040), 0)
pad.set_style_border_color(lv.color_hex(0x00DCDC), 0)
pad.set_style_border_width(1, 0)
dot = lv.obj(t3)
dot.set_size(16, 16)
dot.set_style_radius(lv.RADIUS_CIRCLE, 0)
dot.set_style_bg_color(lv.color_hex(0x00FF00), 0)
dot.set_style_border_width(0, 0)
dot.add_flag(lv.obj.FLAG.HIDDEN)
dot.remove_flag(lv.obj.FLAG.CLICKABLE)
n = [0]


def on_touch(e):
    p = lv.point_t()
    lv.indev_active().get_point(p)
    n[0] += 1
    dot.remove_flag(lv.obj.FLAG.HIDDEN)
    dot.set_pos(p.x - 8, p.y - 8)
    pos.set_text("x=%d y=%d n=%d" % (p.x, p.y, n[0]))


pad.add_event_cb(on_touch, lv.EVENT.PRESSING, None)
lvb.label(t3, "<< desliza", 0x808080, y=H - 18, x=4)

# ---------------------------------------------------------------- arranque
refresh()
run_checks()
_timer = lv.timer_create(refresh, 2000, None)


def stop():
    _timer.delete()
