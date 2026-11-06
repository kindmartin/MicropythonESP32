# LED RGB WS2812 (GPIO38): rojo, verde, azul, apagado.
import time, board
for c in ((40, 0, 0), (0, 40, 0), (0, 0, 40), (0, 0, 0)):
    board.rgb(*c)
    print(c)
    time.sleep_ms(600)
