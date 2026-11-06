# Diagnostico del touch: imprime los 14 bytes crudos y el nivel de INT (GPIO48) mientras tocas durante 10 s.
# Sin tocar: raw[1] = 0 e INT = 1. Tocando: raw[1] = n toques, INT baja a 0.
import time, board
tp = board.touch()
print("scan:", [hex(a) for a in tp.i2c.scan()], "| id:", tp.chip_id().hex())
last = None
t0 = time.ticks_ms()
while time.ticks_diff(time.ticks_ms(), t0) < 10000:
    r = bytes(tp.raw())
    i = tp.int.value()
    if (r, i) != last:
        print("INT=%d raw=%s" % (i, r.hex()))
        last = (r, i)
    time.sleep_ms(20)
