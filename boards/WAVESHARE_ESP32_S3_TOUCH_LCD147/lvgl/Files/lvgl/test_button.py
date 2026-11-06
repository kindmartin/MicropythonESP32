# Boton BOOT (GPIO0): pulsalo durante 10 s.
import time, lvb
b = lvb.button()
last, presses, t0 = 1, 0, time.ticks_ms()
while time.ticks_diff(time.ticks_ms(), t0) < 10000:
    v = b.value()
    if v != last:
        print("BOOT", "presionado" if v == 0 else "suelto")
        presses += v == 0
        last = v
    time.sleep_ms(20)
print("PASS" if presses else "FAIL", "-", presses, "pulsaciones")
