# Test integrado (LVGL) de la Waveshare ESP32-S3-Touch-LCD-1.47: pantalla, brillo, touch, bateria, temperatura, SD, WiFi y memoria.
# USO (REPL, con tests/lvb.py en la placa):  import features     # BOOT (GPIO0) = salir
#   repetir:  import sys; sys.modules.pop("features"); import features
# Fase 1: chequeos automaticos, resultado en pantalla y por serie. Fase 2: toca la pantalla, un punto verde sigue al dedo.
import time, gc, os
import lvgl as lv
import lvb

GREEN, RED, YELLOW, CYAN, WHITE = 0x00DC00, 0xFF3232, 0xFFC800, 0x00DCDC, 0xFFFFFF
scr = lvb.screen(0x000000)
lvb.label(scr, "TOUCH-LCD-1.47", CYAN, y=2, x=22)
row = [24]


def report(name, ok, info=""):
    lvb.label(scr, ("OK   " if ok else "FAIL ") + name + " " + info, GREEN if ok else RED, y=row[0])
    row[0] += 18
    print("[%s] %s %s" % ("PASS" if ok else "FAIL", name, info))
    lvb.wait(30)


def check(name, fn):
    try:
        report(name, True, fn() or "")
    except Exception as e:
        report(name, False, repr(e)[:16])


def t_display():
    for c in (0xFF0000, 0x00FF00, 0x0000FF):
        lv.screen_active().set_style_bg_color(lv.color_hex(c), 0)
        lvb.wait(250)
    lv.screen_active().set_style_bg_color(lv.color_hex(0), 0)
    return "%dx%d" % (lvb.W, lvb.H)


def t_backlight():
    for p in (100, 40, 10, 40, 100, 80):
        lvb.disp.set_backlight(p)
        lvb.wait(200)


def t_touch():
    d = lvb.indev
    return "init ok (probar abajo)"


def t_battery():
    v = lvb.vbat()
    return "%.2fV %d%%" % (v, lvb.battery_percent(v)) if v > 2.8 else "%.2fV sin bat" % v


def t_temp():
    import esp32
    t = esp32.mcu_temperature()
    if not 10 < t < 90:
        raise ValueError("%.0fC" % t)
    return "%.1fC chip" % t


def t_sd():
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


def t_wifi():
    import network
    w = network.WLAN(network.STA_IF)
    w.active(True)
    n = w.scan()
    w.active(False)
    return "%d redes" % len(n)


def t_mem():
    gc.collect()
    return "%dKB libres" % (gc.mem_free() // 1024)


check("Pantalla", t_display)
check("Brillo", t_backlight)
check("Touch", t_touch)
check("Bateria", t_battery)
check("Temp", t_temp)
check("SD", t_sd)
check("WiFi", t_wifi)
check("Memoria", t_mem)

lvb.label(scr, "TOCA LA PANTALLA", YELLOW, y=row[0] + 10)
lvb.label(scr, "BOOT = salir", YELLOW, y=row[0] + 28)
dot = lv.obj(scr)
dot.set_size(16, 16)
dot.set_style_radius(lv.RADIUS_CIRCLE, 0)
dot.set_style_bg_color(lv.color_hex(GREEN), 0)
dot.set_style_border_width(0, 0)
dot.add_flag(lv.obj.FLAG.HIDDEN)
pos = lvb.label(scr, "", WHITE, y=lvb.H - 20)
n = [0]


def on_touch(e):
    p = lv.point_t()
    lv.indev_active().get_point(p)
    n[0] += 1
    dot.remove_flag(lv.obj.FLAG.HIDDEN)
    dot.set_pos(p.x - 8, p.y - 8)
    pos.set_text("x=%d y=%d n=%d" % (p.x, p.y, n[0]))


scr.add_event_cb(on_touch, lv.EVENT.PRESSING, None)
btn = lvb.button()
try:
    while btn.value():
        lvb.wait(30)
finally:                                    # tambien si se corta con Ctrl-C
    scr.remove_event_cb(on_touch)
print("[%s] Touch - %d eventos" % ("PASS" if n[0] else "FAIL", n[0]))
print("fin")
