# Touch AXS5106L (I2C 0x63, RST 47, INT 48): toca la pantalla durante 10 s. Dibuja un punto donde tocas.
import time, board, st7789
lcd = board.lcd()
board.backlight(80)
lcd.fill(st7789.BLACK)
i2c = board.i2c()
tp = board.touch(i2c)          # hace el reset del chip (200 ms + 300 ms)
print("I2C scan:", [hex(a) for a in i2c.scan()], "(esperado 0x63)")
try:
    print("ID:", tp.chip_id().hex(), "| raw:", tp.raw())
except OSError as e:
    print("sin respuesta del touch:", e)
t0 = time.ticks_ms()
n = 0
while time.ticks_diff(time.ticks_ms(), t0) < 10000:
    p = tp.read()
    if p:
        print("touch", p)
        n += 1
        x, y = p[0], p[1]
        lcd.fill_rect(max(0, x - 3), max(0, y - 3), 6, 6, st7789.GREEN)
    time.sleep_ms(30)
print("PASS" if n else "FAIL", "-", n, "lecturas")
