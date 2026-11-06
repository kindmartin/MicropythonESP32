# Backlight por PWM (GPIO46): debe subir y bajar el brillo.
import lvb
s = lvb.screen(0xFFFFFF)
lvb.label(s, "BRILLO", 0x000000)
for p in (100, 60, 30, 10, 0, 30, 60, 100, 80):
    lvb.disp.set_backlight(p)
    print("brillo", p)
    lvb.wait(500)
