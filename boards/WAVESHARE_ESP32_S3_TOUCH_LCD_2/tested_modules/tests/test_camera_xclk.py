# Compara el reloj de camara (XCLK): captura VGA a 20, 10 y 8 MHz con la misma escena.
# Fotos: /foto_xclk20.jpg, /foto_xclk10.jpg, /foto_xclk8.jpg  (bajarlas y comparar bandas/ruido)
import gc, time
from camera import Camera, PixelFormat, FrameSize

for mhz in (20, 10, 8):
    gc.collect()
    cam = Camera(xclk_freq=mhz * 1_000_000, pixel_format=PixelFormat.JPEG, frame_size=FrameSize.VGA)
    for _ in range(4):
        cam.capture()                  # estabiliza autoexposicion
    img = cam.capture()
    n = len(img) if img else 0
    if n:
        open("/foto_xclk%d.jpg" % mhz, "wb").write(img)
    print("PASS" if n > 1000 else "FAIL", "xclk", mhz, "MHz ->", n, "bytes")
    cam.deinit()
    time.sleep_ms(300)
