# test_board.py — Waveshare ESP32-S3-LCD-1.47B
# Pins from: waveshare.com/wiki/ESP32-S3-LCD-1.47B
# exec(open("test_board.py").read())

import machine, time, os, gc
import st7789, qmi8658

# ── Pin assignments ───────────────────────────────────────────────────────────
LCD_SCK  = 40
LCD_MOSI = 45
LCD_CS   = 42
LCD_DC   = 41
LCD_RST  = 39
LCD_BL   = 46

I2C_SCL  = 47   # schematic: IMU_SCL
I2C_SDA  = 48   # schematic: IMU_SDA

RGB_PIN  = 38   # WS2812, 1 LED

# SD via SDMMC (slot=1)
SD_CLK   = 14
SD_CMD   = 15
SD_D0    = 16
SD_D1    = 18
SD_D2    = 17
SD_D3    = 21

VBAT_PIN = 1    # schematic: BAT_ADC, divider 200K/100K (x3)

PASS = "[PASS]"
FAIL = "[FAIL]"
SKIP = "[SKIP]"
INFO = "[INFO]"


def section(title):
    print("\n" + "─" * 44)
    print(" " + title)
    print("─" * 44)


def scan_i2c_pins():
    section("I2C pin scanner")
    candidates = [(48,47),(47,48),(7,6),(6,7),(3,4),(4,3),(1,2),(2,1),(9,8),(8,9)]
    for scl, sda in candidates:
        try:
            i2c = machine.SoftI2C(scl=machine.Pin(scl), sda=machine.Pin(sda),
                                  freq=100_000, timeout=1000)
            devs = i2c.scan()
            if devs:
                print(INFO, f"SCL={scl} SDA={sda} → {[hex(d) for d in devs]}")
        except Exception:
            pass


# ── 1. LCD ─────────────────────────────────────────────────────────────────────
def test_lcd():
    section("LCD  ST7789  172×320")
    try:
        spi = machine.SPI(1, baudrate=40_000_000, sck=LCD_SCK, mosi=LCD_MOSI)
        lcd = st7789.ST7789(spi, cs=LCD_CS, dc=LCD_DC, rst=LCD_RST, bl=LCD_BL)
        lcd.rotation(1)
        print(INFO, f"Resolution: {lcd.width}×{lcd.height}")

        for name, col in [("RED", st7789.RED), ("GREEN", st7789.GREEN),
                          ("BLUE", st7789.BLUE), ("WHITE", st7789.WHITE)]:
            print(f"      {name}"); lcd.fill(col); time.sleep_ms(500)

        bar_colors = [st7789.RED, st7789.GREEN, st7789.BLUE,
                      st7789.YELLOW, st7789.CYAN, st7789.WHITE]
        bw = lcd.width // len(bar_colors)
        for i, c in enumerate(bar_colors):
            lcd.fill_rect(i * bw, 0, bw, lcd.height, c)
        lcd.rect(0, 0, lcd.width, lcd.height, st7789.BLACK)
        print(PASS, "LCD OK")
        lcd.backlight(False); time.sleep_ms(300); lcd.backlight(True)
        print(PASS, "Backlight OK")
        return lcd
    except Exception as e:
        print(FAIL, "LCD:", e)
        return None


# ── 2. IMU ─────────────────────────────────────────────────────────────────────
def test_imu():
    section("IMU  QMI8658")
    try:
        i2c = machine.I2C(0, scl=I2C_SCL, sda=I2C_SDA, freq=400_000)
        devs = i2c.scan()
        print(INFO, f"I2C devices: {[hex(d) for d in devs]}")
        if not devs:
            print(FAIL, "No devices — running pin scanner...")
            scan_i2c_pins(); return

        imu = qmi8658.QMI8658(i2c)
        for _ in range(20):
            if imu.data_ready: break
            time.sleep_ms(10)

        ax, ay, az, gx, gy, gz = imu.read_all()
        print(PASS, f"Accel (g):  ax={ax:.3f}  ay={ay:.3f}  az={az:.3f}")
        print(PASS, f"Gyro (°/s): gx={gx:.2f}  gy={gy:.2f}  gz={gz:.2f}")
        mag = (ax*ax + ay*ay + az*az) ** 0.5
        print(PASS if 0.8 < mag < 1.2 else FAIL, f"|a|={mag:.3f}g")
    except Exception as e:
        print(FAIL, "IMU:", e)
        scan_i2c_pins()


# ── 3. RGB LED ─────────────────────────────────────────────────────────────────
def test_rgb_led():
    section("WS2812 RGB LED  (GPIO38, 1 LED)")
    try:
        import neopixel
        np = neopixel.NeoPixel(machine.Pin(RGB_PIN), 1)
        for col in [(255,0,0),(0,255,0),(0,0,255),(255,255,0),(0,0,0)]:
            np[0] = col; np.write(); time.sleep_ms(350)
        print(PASS, "WS2812 OK")
    except Exception as e:
        print(FAIL, "WS2812:", e)


# ── 4. TF card (SDMMC 4-bit) ──────────────────────────────────────────────────
def test_sdcard():
    section("TF Card (SDMMC 4-bit)")
    try:
        sd  = machine.SDCard(slot=1, width=4,
                             clk=SD_CLK, cmd=SD_CMD,
                             d0=SD_D0, d1=SD_D1, d2=SD_D2, d3=SD_D3)
        vfs = os.VfsFat(sd)
        os.mount(vfs, "/sd")
        files = os.listdir("/sd")
        print(PASS, f"Mounted — {len(files)} entries: {files[:5]}")
        with open("/sd/_test.txt", "w") as f: f.write("lcd147b ok")
        with open("/sd/_test.txt") as f: data = f.read()
        os.remove("/sd/_test.txt")
        print(PASS, f"Write/read OK: '{data}'")
        os.umount("/sd")
    except Exception as e:
        print(SKIP, "TF card:", e)


# ── 5. Battery voltage ─────────────────────────────────────────────────────────
def test_vbat():
    section("Battery voltage  (GPIO4 — VERIFY)")
    try:
        adc = machine.ADC(machine.Pin(VBAT_PIN))
        adc.atten(machine.ADC.ATTN_11DB)
        raw = sum(adc.read() for _ in range(8)) // 8
        vbat = raw / 4095 * 3.3 * 2
        print(PASS, f"ADC raw={raw}  Vbat≈{vbat:.2f} V")
        if vbat < 3.0:
            print(INFO, "No battery or USB only")
    except Exception as e:
        print(SKIP, "VBAT:", e)


# ── 6. WiFi ────────────────────────────────────────────────────────────────────
def test_wifi():
    section("WiFi scan")
    try:
        import network
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        nets = wlan.scan()
        print(PASS, f"Found {len(nets)} networks")
        for n in sorted(nets, key=lambda x: -x[3])[:3]:
            try: ssid = n[0].decode()
            except: ssid = repr(n[0])
            print(f"       {ssid:24s}  RSSI={n[3]} dBm")
        wlan.active(False)
    except Exception as e:
        print(FAIL, "WiFi:", e)


# ── 7. Memory ──────────────────────────────────────────────────────────────────
def test_mem():
    section("Memory")
    gc.collect()
    free = gc.mem_free(); total = free + gc.mem_alloc()
    print(PASS, f"Heap: {free//1024} KB free / {total//1024} KB total")
    if total < 500:
        print(INFO, "Low heap — reflash firmware to activate 8MB PSRAM")
    import sys
    print(PASS, f"MicroPython: {sys.version}")


# ── Run ────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 44)
print(" Waveshare ESP32-S3-LCD-1.47B  board test")
print("=" * 44)

test_lcd()
test_imu()
test_rgb_led()
test_sdcard()
test_vbat()
test_wifi()
test_mem()

print("\n" + "=" * 44)
print(" Done")
print("=" * 44)
