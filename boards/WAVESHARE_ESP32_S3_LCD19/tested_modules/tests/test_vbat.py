# Bateria (GPIO4, divisor x3): sin bateria ~0 V o ruido; con LiPo 3.3-4.2 V.
import time, board
for _ in range(10):
    print("%.3f V  %d %%" % (board.vbat(), board.battery_percent()))
    time.sleep_ms(500)
print("PASS si coincide con un multimetro (+-0.1 V)")
