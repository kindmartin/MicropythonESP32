# Preview de camara en el LCD (SIN PROBAR). Camara RGB565 QVGA (320x240) en landscape.
# Si los colores salen raros, prueba SWAP = True (intercambia bytes del frame).
import gc, board
from camera import Camera, PixelFormat, FrameSize

SWAP = False
FRAMES = 150

spi = board.spi()
lcd = board.lcd(spi)
board.backlight(80)
lcd.rotation(1)

cam = Camera(pixel_format=PixelFormat.RGB565, frame_size=FrameSize.QVGA)
print("sensor:", cam.get_sensor_name(), cam.get_pixel_width(), "x", cam.get_pixel_height())
w, h = cam.get_pixel_width(), cam.get_pixel_height()
for i in range(FRAMES):
    buf = cam.capture()
    if buf is None:
        continue
    if SWAP:
        b = bytearray(buf)
        b[0::2], b[1::2] = b[1::2], b[0::2]
        buf = b
    lcd.blit_buffer(buf, 0, 0, w, h)
cam.deinit()
gc.collect()
print("fin preview")
