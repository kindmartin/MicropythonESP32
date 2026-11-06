# Test integrado de la Waveshare ESP32-S3-Touch-LCD-1.47: LCD, brillo, SD, bateria, temperatura, WiFi, memoria y touch.
# USO (REPL):  import features        # corre al importar; BOOT (GPIO0) = salir del modo touch
#              para repetir:  import sys; sys.modules.pop("features"); import features
# Fase 1: chequeos automaticos (resultado en pantalla y por serie). Fase 2: toca la pantalla, dibuja un punto por toque.
import framebuf, time, gc, os
import board, st7789

W, H = 172, 320


def c565(r, g, b):
    v = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
    return ((v & 0xFF) << 8) | (v >> 8)       # framebuf little-endian -> LCD big-endian


BLACK, WHITE = 0, c565(255, 255, 255)
GREEN, RED, YELLOW, CYAN = c565(0, 220, 0), c565(255, 50, 50), c565(255, 200, 0), c565(0, 220, 220)

buf = bytearray(W * H * 2)
fb = framebuf.FrameBuffer(buf, W, H, framebuf.RGB565)
lcd = None
lines = []


def show():
    fb.fill(BLACK)
    fb.text("TOUCH-LCD-1.47", 14, 4, CYAN)
    for i, (txt, col) in enumerate(lines):
        fb.text(txt[:21], 2, 22 + i * 12, col)
    lcd.blit_buffer(buf, 0, 0, W, H)


def report(name, ok, info=""):
    lines.append(("%s %s %s" % ("OK " if ok else "FAIL", name, info), GREEN if ok else RED))
    print("[%s] %s %s" % ("PASS" if ok else "FAIL", name, info))
    show()


def check(name, fn):
    try:
        info = fn()
        report(name, True, info or "")
    except Exception as e:
        report(name, False, repr(e)[:18])


def t_lcd():
    for c in (st7789.RED, st7789.GREEN, st7789.BLUE, st7789.WHITE):
        lcd.fill(c)
        time.sleep_ms(300)
    cols = (st7789.RED, st7789.GREEN, st7789.BLUE, st7789.YELLOW, st7789.CYAN, st7789.MAGENTA)
    for i, c in enumerate(cols):
        lcd.fill_rect(0, i * (H // 6), W, H // 6, c)
    lcd.rect(0, 0, W, H, st7789.BLACK)
    time.sleep_ms(1200)
    return "%dx%d" % (W, H)


def t_backlight():
    for p in (100, 40, 10, 40, 100):
        board.backlight(p)
        time.sleep_ms(250)
    board.backlight(80)


def t_vbat():
    v = board.vbat()
    if v < 2.8:
        return "%.2fV sin bat" % v
    return "%.2fV %d%%" % (v, board.battery_percent())


def t_temp():
    t = board.temp()
    if not 10 < t < 90:
        raise ValueError("%.0fC" % t)
    return "%.1fC chip" % t


def t_sd():
    sd = board.sd_mount()
    try:
        with open("/sd/_t.txt", "w") as f:
            f.write("ok")
        ok = open("/sd/_t.txt").read() == "ok"
        os.remove("/sd/_t.txt")
        if not ok:
            raise OSError("lectura distinta")
        return "%d arch." % len(os.listdir("/sd"))
    finally:
        os.umount("/sd")
        sd.deinit()


def t_wifi():
    import network
    w = network.WLAN(network.STA_IF)
    w.active(True)
    n = w.scan()
    w.active(False)
    return "%d redes" % len(n)


def t_mem():
    gc.collect()
    free = gc.mem_free()
    return "%dKB libres" % (free // 1024)


def t_touch_id():
    global tp
    tp = board.touch()
    return "id " + tp.chip_id().hex()


tp = None


def run():
    global lcd
    lcd = board.lcd()
    board.backlight(80)
    lines.clear()
    check("LCD", t_lcd)
    check("Brillo", t_backlight)
    check("Touch", t_touch_id)
    check("Bateria", t_vbat)
    check("Temp", t_temp)
    check("SD", t_sd)
    check("WiFi", t_wifi)
    check("Memoria", t_mem)
    lines.append(("", WHITE))
    lines.append(("TOCA LA PANTALLA", YELLOW))
    lines.append(("BOOT = salir", YELLOW))
    show()
    btn = board.button()
    n = 0
    while btn.value():
        p = tp.read() if tp else None
        if p:
            n += 1
            x, y = p
            fb.fill_rect(max(0, x - 3), max(0, y - 3), 7, 7, GREEN)
            fb.fill_rect(0, H - 12, W, 12, BLACK)
            fb.text("x=%3d y=%3d n=%d" % (x, y, n), 2, H - 10, WHITE)
            lcd.blit_buffer(buf, 0, 0, W, H)
        time.sleep_ms(20)
    print("[%s] Touch - %d lecturas" % ("PASS" if n else "FAIL", n))
    print("fin")


run()
