# Temperatura del chip ESP32-S3 (no hay sensor de temperatura dedicado; sube con WiFi/CPU).
import esp32, lvb
s = lvb.screen(0x000000)
lb = lvb.label(s, "")
for _ in range(10):
    t = esp32.mcu_temperature()
    lb.set_text("%.1f C\n(chip)" % t)
    print("%.1f C" % t)
    lvb.wait(500)
print("PASS si esta entre 20 y 80 C")
