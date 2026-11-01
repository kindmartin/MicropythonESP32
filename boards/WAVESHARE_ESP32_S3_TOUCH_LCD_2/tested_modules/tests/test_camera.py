# Camara: detecta el sensor y captura JPEG. Baja la foto con:
#   mpremote cp :_foto.jpg .
import gc, time, board
from camera import Camera, PixelFormat, FrameSize

print("mem libre antes:", gc.mem_free())
cam = Camera(pixel_format=PixelFormat.JPEG, frame_size=FrameSize.VGA)
print("sensor:", cam.get_sensor_name(), cam.get_pixel_width(), "x", cam.get_pixel_height())

for size_name in ("QVGA", "VGA", "SVGA"):
    cam.reconfigure(frame_size=getattr(FrameSize, size_name))
    cam.capture(); cam.capture()       # descarta 2 frames (tras reconfigure el 1ro es del tamano anterior)
    t0 = time.ticks_ms()
    img = cam.capture()
    dt = time.ticks_diff(time.ticks_ms(), t0)
    n = len(img) if img else 0
    print("PASS" if n > 1000 else "FAIL", size_name, n, "bytes", dt, "ms")
    if size_name == "VGA" and img:
        open("/_foto.jpg", "wb").write(img)
        print("guardada /_foto.jpg")

cam.deinit()
gc.collect()
print("mem libre despues:", gc.mem_free())
