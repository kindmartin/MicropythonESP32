# Temperatura: sensor interno del ESP32-S3 (esp32.mcu_temperature). Es la del chip, no la ambiente: sube con WiFi/CPU.
import time, board
for _ in range(10):
    print("%.1f C" % board.temp())
    time.sleep_ms(500)
print("PASS si esta entre 20 y 80 C")
