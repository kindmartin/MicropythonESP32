# Bateria: BAT_ADC = GPIO12 (esquematico), divisor 200K/100K (x3). Sin bateria ~0 V o ruido; con LiPo 3.3-4.2 V.
import time, board
if board.VBAT_PIN is None:
    print("SKIP: board.VBAT_PIN sin definir (mira el esquematico)")
else:
    for _ in range(10):
        print("%.3f V  %d %%" % (board.vbat(), board.battery_percent()))
        time.sleep_ms(500)
    print("PASS si coincide con un multimetro (+-0.1 V)")
