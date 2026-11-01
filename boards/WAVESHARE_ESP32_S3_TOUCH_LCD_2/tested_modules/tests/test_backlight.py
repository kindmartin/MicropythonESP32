# Backlight PWM: debe subir y bajar el brillo suavemente.
import time, board
board.lcd().fill(0xFFFF)
for p in list(range(0, 101, 10)) + list(range(100, -1, -10)):
    print("brillo", p, "%")
    board.backlight(p)
    time.sleep_ms(300)
board.backlight(80)
print("OK si el brillo cambio visiblemente (no solo on/off)")
