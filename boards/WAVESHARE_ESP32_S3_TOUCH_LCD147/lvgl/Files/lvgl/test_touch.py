# Touch AXS5106L con LVGL: toca la pantalla durante 10 s. Un punto verde sigue al dedo y se imprimen las coordenadas.
# Comprueba que el punto queda DEBAJO del dedo: si sale espejado en x (hipotesis del README), usar touch_cal o invertir x.
import lvb, lvgl as lv, time
s = lvb.screen(0x000000)
info = lvb.label(s, "toca la pantalla", 0xFFFFFF, y=4)
dot = lv.obj(s)
dot.set_size(18, 18)
dot.set_style_radius(lv.RADIUS_CIRCLE, 0)
dot.set_style_bg_color(lv.color_hex(0x00FF00), 0)
dot.set_style_border_width(0, 0)
dot.add_flag(lv.obj.FLAG.HIDDEN)
n = [0]


def cb(e):
    p = lv.point_t()
    lv.indev_active().get_point(p)
    n[0] += 1
    dot.remove_flag(lv.obj.FLAG.HIDDEN)
    dot.set_pos(p.x - 9, p.y - 9)
    info.set_text("x=%d y=%d n=%d" % (p.x, p.y, n[0]))
    print("touch", p.x, p.y)


s.add_event_cb(cb, lv.EVENT.PRESSING, None)
t0 = time.ticks_ms()
try:
    while time.ticks_diff(time.ticks_ms(), t0) < 10000:
        lvb.wait(50)
finally:
    s.remove_event_cb(cb)
print("PASS" if n[0] else "FAIL", "-", n[0], "eventos de touch")
