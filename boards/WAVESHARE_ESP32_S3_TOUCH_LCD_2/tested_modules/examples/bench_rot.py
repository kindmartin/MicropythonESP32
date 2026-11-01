# Benchmark de rotacion 90 de un frame 320x240 RGB565 (viper). Imprime ms por frame.
import time, micropython


@micropython.viper
def rot_cw_naive(src: ptr16, dst: ptr16, w: int, h: int):
    for y in range(h):
        sy = y * w
        for x in range(w):
            dst[x * h + (h - 1 - y)] = src[sy + x]


@micropython.viper
def rot_cw_32(src: ptr32, dst: ptr32, w: int, h: int):
    # Bloques 2x2 con accesos de 32 bits (w y h pares). Giro 90 a favor del reloj.
    w2 = w >> 1
    h2 = h >> 1
    for ye in range(0, h, 2):
        a = ye * w2           # fila ye  (palabras de 2 px)
        b = a + w2            # fila ye+1
        for xi in range(w2):
            A = src[a + xi]   # lo = (ye, x)   hi = (ye, x+1)
            B = src[b + xi]   # lo = (ye+1, x) hi = (ye+1, x+1)
            x = xi << 1
            # destino fila x: indice de pixel x*h + (h-2-ye) -> palabra (x*h + h-2-ye)/2
            d0 = (x * h + h - 2 - ye) >> 1
            dst[d0] = (B & 0xFFFF) | (A << 16)
            dst[d0 + h2] = ((B >> 16) & 0xFFFF) | ((A >> 16) << 16)


@micropython.viper
def rot_ccw_32(src: ptr32, dst: ptr32, w: int, h: int):
    # Giro 90 contra reloj: dst[(w-1-x)*h + y] = src[y*w + x]
    w2 = w >> 1
    h2 = h >> 1
    for ye in range(0, h, 2):
        a = ye * w2
        b = a + w2
        for xi in range(w2):
            A = src[a + xi]
            B = src[b + xi]
            x = xi << 1
            d0 = ((w - 1 - x) * h + ye) >> 1          # fila (w-1-x)
            dst[d0] = (A & 0xFFFF) | (B << 16)
            dst[d0 - h2] = ((A >> 16) & 0xFFFF) | ((B >> 16) << 16)   # fila (w-2-x)


w, h = 320, 240
src = bytearray(w * h * 2)
for i in range(0, len(src), 2):
    src[i] = (i >> 1) & 0xFF
    src[i + 1] = (i >> 9) & 0xFF
dst = bytearray(w * h * 2)
ref = bytearray(w * h * 2)
rot_cw_naive(src, ref, w, h)
for name, f in (("cw naive 16bit", rot_cw_naive), ("cw 2x2 32bit", rot_cw_32)):
    f(src, dst, w, h)
    t0 = time.ticks_ms()
    for _ in range(10):
        f(src, dst, w, h)
    print(name, time.ticks_diff(time.ticks_ms(), t0) / 10, "ms/frame")
rot_cw_32(src, dst, w, h)
print("cw 32bit == naive:", ref == dst)

# CCW: la referencia es el cw girado 180 = cw sobre la imagen con vflip+hflip; se compara por formula
refc = bytearray(w * h * 2)
for y in range(0, h, 7):
    for x in range(0, w, 5):
        pass
rot_ccw_32(src, dst, w, h)
ok = True
s16 = memoryview(src).cast("H")
d16 = memoryview(dst).cast("H")
for y in range(h):
    for x in range(0, w, 13):
        if d16[(w - 1 - x) * h + y] != s16[y * w + x]:
            ok = False
print("ccw 32bit ok:", ok)
