# Backlight por PWM (GPIO14): debe subir y bajar el brillo.
import time, board, st7789
lcd = board.lcd()
lcd.fill(st7789.WHITE)
for p in (100, 60, 30, 10, 0, 30, 60, 100):
    board.backlight(p)
    print("brillo", p)
    time.sleep_ms(500)
