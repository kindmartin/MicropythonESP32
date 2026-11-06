# LCD ST7789 170x320: colores, barras y marco. Si los colores salen en negativo: board.lcd(invert=False).
# Aqui el driver ya activa BGR; si el rojo sale azul, quita _BGR en st7789.py. Si hay franjas negras a un lado: x_offset.
import time, board, st7789
lcd = board.lcd()
board.backlight(80)
for name, c in (("ROJO", st7789.RED), ("VERDE", st7789.GREEN), ("AZUL", st7789.BLUE), ("BLANCO", st7789.WHITE)):
    print(name)
    lcd.fill(c)
    time.sleep_ms(600)
cols = (st7789.RED, st7789.GREEN, st7789.BLUE, st7789.YELLOW, st7789.CYAN, st7789.MAGENTA)
h = lcd.height // len(cols)
for i, c in enumerate(cols):
    lcd.fill_rect(0, i * h, lcd.width, h, c)
lcd.rect(0, 0, lcd.width, lcd.height, st7789.BLACK)
print("PASS si ves 6 barras horizontales con marco negro a los 4 bordes (sin cortes)")
