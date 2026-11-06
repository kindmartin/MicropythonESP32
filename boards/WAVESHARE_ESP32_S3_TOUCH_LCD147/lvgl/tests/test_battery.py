# Bateria (BAT_ADC GPIO12, divisor x3): sin bateria ~0 V; con LiPo 3.3-4.2 V. Se muestra en pantalla y por serie.
import lvb, lvgl as lv
s = lvb.screen(0x000000)
lb = lvb.label(s, "")
for _ in range(10):
    v = lvb.vbat()
    txt = "%.2f V\n%d %%" % (v, lvb.battery_percent(v)) if v > 2.8 else "%.2f V\nsin bateria" % v
    lb.set_text(txt)
    print(txt.replace("\n", "  "))
    lvb.wait(500)
print("PASS si coincide con un multimetro (+-0.1 V)")
