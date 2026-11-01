# Touch CST816D: TOCA LA PANTALLA durante todo el test (el chip duerme y no
# aparece en el scan I2C hasta que lo tocan). Dura ~15 s.
import time, board
i2c = board.i2c()
print("Toca y mantene el dedo en la pantalla...")
found = False
for _ in range(100):
    s = i2c.scan()
    if 0x15 in s:
        found = True
        break
    time.sleep_ms(50)
print("I2C scan:", [hex(a) for a in s], "-> 0x15 (touch):", "OK" if found else "NO responde")
tp = board.touch()
t0 = time.ticks_ms()
n = 0
while time.ticks_diff(time.ticks_ms(), t0) < 15000:
    p = tp.read()
    if p:
        n += 1
        print("touch", p, "gesto", tp.gesture())
    time.sleep_ms(50)
print("PASS" if n else "FAIL", "-", n, "lecturas con toque")
