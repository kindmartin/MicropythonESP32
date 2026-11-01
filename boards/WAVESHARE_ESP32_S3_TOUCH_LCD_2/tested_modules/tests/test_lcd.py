# LCD: colores, orientacion y offsets. Mirar la pantalla y confirmar a ojo.
import time, board, st7789

lcd = board.lcd()
board.backlight(80)
for name, c in (("ROJO", st7789.RED), ("VERDE", st7789.GREEN), ("AZUL", st7789.BLUE),
                ("BLANCO", st7789.WHITE), ("NEGRO", st7789.BLACK)):
    print("fill", name)           # si ROJO se ve azul -> orden BGR/RGB; si colores invertidos -> invert
    lcd.fill(c)
    time.sleep(1)

# Marco de 2 px en el borde: si falta algun lado, hay offset incorrecto
lcd.fill(st7789.BLACK)
lcd.rect(0, 0, lcd.width, lcd.height, st7789.WHITE)
lcd.rect(1, 1, lcd.width - 2, lcd.height - 2, st7789.WHITE)
lcd.fill_rect(0, 0, 40, 40, st7789.RED)                       # esquina sup-izq
lcd.fill_rect(lcd.width - 40, lcd.height - 40, 40, 40, st7789.GREEN)  # inf-der
print("Esperado (rotation 0): rojo arriba-izq, verde abajo-der, marco completo", lcd.width, "x", lcd.height)
time.sleep(3)

for r in (1, 2, 3, 0):
    lcd.rotation(r)
    lcd.fill(st7789.BLACK)
    lcd.fill_rect(0, 0, 40, 40, st7789.RED)
    lcd.rect(0, 0, lcd.width, lcd.height, st7789.WHITE)
    print("rotation", r, lcd.width, "x", lcd.height)
    time.sleep(2)
