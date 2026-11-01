# Mide FPS del video camara -> LCD, separando captura y envio al LCD.
import gc, time, board
from camera import Camera, PixelFormat, FrameSize

N = 60
for spi_mhz in (20, 40, 80):
    spi = board.spi(spi_mhz * 1_000_000)
    lcd = board.lcd(spi)
    board.backlight(80)
    lcd.rotation(1)
    cam = Camera(pixel_format=PixelFormat.RGB565, frame_size=FrameSize.QVGA, fb_count=2)
    w, h = cam.get_pixel_width(), cam.get_pixel_height()
    for _ in range(3):
        cam.capture()
    tc = tb = 0
    t_all = time.ticks_ms()
    for _ in range(N):
        t0 = time.ticks_ms()
        buf = cam.capture()
        t1 = time.ticks_ms()
        lcd.blit_buffer(buf, 0, 0, w, h)
        t2 = time.ticks_ms()
        tc += time.ticks_diff(t1, t0)
        tb += time.ticks_diff(t2, t1)
    dt = time.ticks_diff(time.ticks_ms(), t_all)
    print("SPI %d MHz: %.1f fps | captura %d ms | LCD %d ms por frame (%dx%d)" % (
        spi_mhz, N * 1000 / dt, tc // N, tb // N, w, h))
    cam.deinit()
    gc.collect()
