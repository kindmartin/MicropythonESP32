# Pantalla JD9853 172x320 con LVGL: colores a pantalla completa y marco. Si los colores salen cambiados (rojo<->azul) o en negativo:
# display.set_color_inversion(False) / rgb565_byte_swap / BYTE_ORDER en el .toml. Si hay franja negra a un lado: offset_x.
import lvb, lvgl as lv
for name, c in (("ROJO", 0xFF0000), ("VERDE", 0x00FF00), ("AZUL", 0x0000FF), ("BLANCO", 0xFFFFFF)):
    s = lvb.screen(c)
    lvb.label(s, name, 0x000000 if name == "BLANCO" else 0xFFFFFF)
    print(name)
    lvb.wait(700)
s = lvb.screen(0x000000)
cols = (0xFF0000, 0x00FF00, 0x0000FF, 0xFFFF00, 0x00FFFF, 0xFF00FF)
h = lvb.H // len(cols)
for i, c in enumerate(cols):
    o = lv.obj(s)
    o.set_size(lvb.W, h)
    o.set_pos(0, i * h)
    o.set_style_bg_color(lv.color_hex(c), 0)
    o.set_style_radius(0, 0)
    o.set_style_border_width(0, 0)
fr = lv.obj(s)
fr.set_size(lvb.W, lvb.H)
fr.set_pos(0, 0)
fr.set_style_bg_opa(0, 0)
fr.set_style_radius(0, 0)
fr.set_style_border_color(lv.color_hex(0xFFFFFF), 0)
fr.set_style_border_width(2, 0)
print("PASS si ves 6 barras (R G B Y C M, de arriba a abajo) con marco blanco a los 4 bordes, sin cortes")
