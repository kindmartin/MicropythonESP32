# Camara -> LCD con el overlay encima. Es la tarea critica: si muere, se para todo.
import gc
import time
import uasyncio as asyncio
import st7789
from camera import Camera, PixelFormat, FrameSize

VIDEO_Y = 0         # fila donde empieza el video; debajo queda una franja 240x80 libre para futuras UI


def setup(app):
    cfg = app.cfg
    lcd = app.lcd
    app.state.update(fps=0.0)
    app.add_mode("horizon")

    def tare():
        if app.mode == "horizon":
            ok = app.ov.tare()
            app.ov.flash(ok)
            print("[horizon] cero: %s" % ("alabeo %.1f, cabeceo %.1f" % (app.ov.roll0 * 57.2958, app.ov.pitch0)
                                          if ok else "no se pudo (placa casi plana)"))

    app.on("button_short", tare)

    def open_cam():
        cam = Camera(pixel_format=PixelFormat.RGB565, frame_size=FrameSize.R240X240, fb_count=2)
        cam.set_vflip(cfg["vflip"])
        cam.set_hmirror(cfg["hmirror"])
        for _ in range(3):
            cam.capture()
        return cam

    async def task(app):
        cam = None
        try:
            writable = True                         # el buffer de la camara admite dibujar encima?
            dst = None
            n = 0
            t0 = 0
            while True:
                if app.mode != "horizon":           # otro modo: soltar la camara y ceder
                    if cam:
                        cam.deinit()
                        cam = dst = None
                        gc.collect()
                    await asyncio.sleep_ms(100)
                    continue
                if cam is None:                     # (re)entrar al modo
                    cam = open_cam()
                    w, h = cam.get_pixel_width(), cam.get_pixel_height()
                    dst = bytearray(w * h * 2)
                    lcd.fill(st7789.BLACK)
                    lcd.hline(0, 240, 240, st7789.WHITE)
                    n = 0
                    t0 = time.ticks_ms()
                buf = cam.capture()
                if buf:
                    out = buf
                    if cfg["overlay"]:
                        s = app.state
                        if not writable:
                            dst[:] = buf
                            out = dst
                        try:
                            app.ov.draw(out, s.get("bat_pct", 0), s.get("bat_present", True))
                        except TypeError:           # buffer de solo lectura
                            writable = False
                            dst[:] = buf
                            out = dst
                            app.ov.draw(out, s.get("bat_pct", 0), s.get("bat_present", True))
                    lcd.blit_buffer(out, 0, VIDEO_Y, w, h)
                    n += 1
                    if n % 50 == 0:
                        app.state["fps"] = 50000 / time.ticks_diff(time.ticks_ms(), t0)
                        t0 = time.ticks_ms()
                        if cfg["verbose"]:
                            print("[horizon] fps %.1f bat %d%%" % (app.state["fps"], app.state.get("bat_pct", 0)))
                await asyncio.sleep_ms(0)           # cede al loop: IMU, boton, otros plugins
        finally:
            if cam:
                cam.deinit()
            gc.collect()

    app.add_task("video", task)
