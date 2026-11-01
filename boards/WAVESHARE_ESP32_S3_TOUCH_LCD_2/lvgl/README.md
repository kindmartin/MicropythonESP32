# Waveshare ESP32-S3-Touch-LCD-2 — MicroPython board guide

Board definition: `ports/esp32/boards/WAVESHARE_ESP32_S3_TOUCH_LCD_2/`
Product: https://www.waveshare.com/esp32-s3-touch-lcd-2.htm
Pin data source: Waveshare official demo (`ESP32-S3-Touch-LCD-2-Demo.zip`, Arduino + ESP-IDF examples).

> Status: firmware builds. The drivers were written from the demo's pin/register
> info; unless marked **tested**, treat them as untested on hardware.

> **La unidad física que tenemos es el SKU "No Touch-No Camera"** (orden
> SpotPear Electronics, ref. 82049852809...; "ESP32-S3-LCD-2", sin touch ni
> cámara). Investigado en banco: `i2c.scan()` en I2C0 solo encuentra el IMU
> (`0x6B`), nunca el CST816D (`0x15`) -- confirmado contra el esquematico
> oficial (V1 y V2: `TP_RESET` no esta ruteado a ningun GPIO en ninguna de
> las dos versiones) y contra el driver del demo oficial de Waveshare
> (tambien usa `TP_RST=-1` y el mismo tipo de lectura I2C que ya probamos).
> No es un bug de wiring ni de `cst816.py`: esta placa concreta no tiene el
> sensor instalado. `board.touch()`/`cst816.py` quedan en el repo por si
> algun dia se usa una unidad con touch, pero no asumir que esta disponible.

## 1. Hardware

| Item | Detail |
|---|---|
| MCU | ESP32-S3R8, dual-core LX7 @ 240 MHz, WiFi + BLE |
| Flash / PSRAM | 16 MB flash, 8 MB octal PSRAM |
| Display | 2" IPS, 240x320, ST7789T3, SPI, no RST pin, PWM backlight |
| Touch | CST816D, I2C addr 0x15, single point, no INT/RST used by demo -- **no presente en nuestra unidad ("No Touch" SKU), ver nota arriba** |
| IMU | QMI8658 6-axis, I2C addr 0x6B |
| microSD | TF slot, **SPI mode**, shares the LCD bus |
| Battery | MX1.25 header, ETA6098 charger, voltage on ADC via 1/3 divider |
| Camera | 24-pin DVP, OV2640 / OV5640 |
| Buttons | BOOT (GPIO0), RST |
| USB | Type-C (native USB-JTAG/CDC) |

### Pin map

| Function | GPIO |
|---|---|
| LCD SCK / MOSI / MISO | 39 / 38 / 40 (SPI id 1, shared with SD) |
| LCD CS / DC / BL | 45 / 42 / 1 |
| LCD RST | not connected (software reset) |
| SD CS | 41 (same SCK/MOSI/MISO as LCD) |
| I2C0 SDA / SCL | 48 / 47 (touch + IMU) |
| Battery ADC | 5 (ADC1_CH4), voltage = Vadc * 3 |
| BOOT button | 0 |
| UART REPL | TX 43 / RX 44 |
| Camera XCLK / PCLK / VSYNC / HREF | 8 / 9 / 6 / 4 |
| Camera D0..D7 | 12, 13, 15, 11, 14, 10, 7, 2 |
| Camera SIOD / SIOC (own I2C) | 21 / 16 |
| Camera PWDN / RESET | 17 / none |

Notes:
- LCD and SD share one SPI bus; they are separated only by CS. `board.sd_mount()`
  forces LCD CS high first. Use a lower baudrate for SD (20 MHz) than the LCD (40 MHz+).
- Camera I2C (21/16) is separate from the touch/IMU I2C (48/47).
- Camera pins GPIO 2/4/6/7/8/9/10..15/16/17/21 are used, so they are not free GPIO.

## 2. Firmware build

Needs ESP-IDF >= 5.3 environment loaded (`. $IDF_PATH/export.sh`).
The camera is an external C module ([micropython-camera-API](https://github.com/cnadler86/micropython-camera-API),
cloned with its `esp32-camera` submodule to `~/micropython-camera-driver`).
It must also be registered as an IDF component:

```bash
cd ports/esp32
make BOARD=WAVESHARE_ESP32_S3_TOUCH_LCD_2 \
  CMAKE_ARGS="-DUSER_C_MODULES=$HOME/micropython-camera-driver/micropython.cmake -DEXTRA_COMPONENT_DIRS=$HOME/micropython-camera-driver"
```

(Passing `CMAKE_ARGS` on the command line replaces the Makefile value, so `USER_C_MODULES` is repeated inside it.)
Flash (offset 0 for the merged image):

```bash
idf.py -p /dev/ttyACM0 erase-flash      # optional full erase
esptool.py --chip esp32s3 -p /dev/ttyACM0 write_flash 0 build-WAVESHARE_ESP32_S3_TOUCH_LCD_2/firmware.bin
```

Board files: `mpconfigboard.h` (pins, camera defaults), `mpconfigboard.cmake`,
`sdkconfig.board` (16 MB, QIO 80 MHz, octal PSRAM), `partitions-16MB.csv`
(2x 3 MB OTA apps + ~10 MB FAT `vfs`), `manifest.py` (freezes `modules/`).

## 3. Software modules (frozen into the firmware)

| Module | What it does |
|---|---|
| `board.py` | Pins + one-line constructors for every peripheral (below) |
| `st7789.py` | LCD driver: `fill, fill_rect, pixel, hline, vline, rect, blit_buffer, invert, rotation`, `color565` and color constants |
| `cst816.py` | Touch: `read() -> (x, y) or None`, `gesture()` |
| `qmi8658.py` | IMU: `accel(), gyro(), read_all(), data_ready()` |
| `camera` (C module) | `Camera`, `PixelFormat`, `FrameSize`, ... |
| `acamera` | asyncio flavour of the camera |

Not implemented: text rendering/fonts (no font module is frozen), charging-status
detection (ETA6098 state not exposed by the demo), deep-sleep helpers, audio (board has none).

### board.py API

```python
import board
spi  = board.spi(baudrate=40_000_000)  # SPI(1) on 39/38/40
lcd  = board.lcd()                     # ST7789 240x320, invert=True, no backlight control
board.backlight(80)                    # PWM 0..100 on GPIO1 (call after lcd())
i2c  = board.i2c()                     # I2C(0) SDA48/SCL47 400 kHz
tp   = board.touch()                   # tp.read() -> (x, y) | None
imu  = board.imu()                     # imu.read_all() -> ax,ay,az,gx,gy,gz
board.sd_mount("/sd")                  # mounts microSD (SPI mode) on /sd
board.vbat()                           # battery volts
board.battery_percent()                # rough 0..100 (3.3 V..4.2 V)
btn  = board.button()                  # btn.value() == 0 when BOOT pressed
cam  = board.camera(**kw)              # camera.Camera(**kw), pins baked in firmware
board.preview(lcd, cam, frames=100)    # camera -> LCD (UNTESTED)
```

### Display

```python
import board, st7789
lcd = board.lcd(); board.backlight(80)
lcd.fill(st7789.BLACK)
lcd.fill_rect(10, 10, 100, 50, st7789.RED)
lcd.rotation(1)      # 0 portrait, 1 landscape, 2/3 flipped. No text API: draw bitmaps via blit_buffer
```

`blit_buffer(buf, x, y, w, h)` takes RGB565 big-endian bytes. Touch coordinates
are in the panel's native portrait frame and are **not** rotated by `lcd.rotation()`;
remap them yourself in landscape.

### Touch / IMU / battery / SD

```python
tp = board.touch()
p = tp.read()            # (x, y) or None

imu = board.imu()
ax, ay, az, gx, gy, gz = imu.read_all()

print(board.vbat(), board.battery_percent())

board.sd_mount("/sd")
import os; print(os.listdir("/sd"))
```

### Camera

The camera constructor needs no pins; defaults come from `mpconfigboard.h`
(XCLK 20 MHz, 2 frame buffers, JPEG quality 85, grab mode LATEST).

```python
from camera import Camera, PixelFormat, FrameSize
cam = Camera(pixel_format=PixelFormat.JPEG, frame_size=FrameSize.VGA)
print(cam.get_sensor_name())       # OV2640 / OV5640
img = cam.capture()                # memoryview with the JPEG bytes (None on failure)
open("/sd/photo.jpg", "wb").write(img)
cam.reconfigure(frame_size=FrameSize.QVGA, pixel_format=PixelFormat.RGB565)
cam.set_vflip(True); cam.set_hmirror(True); cam.set_quality(85)
cam.deinit()                       # release hardware
```

- Formats: `RGB565, RGB888, YUV422, GRAYSCALE, JPEG, RAW...` (OV2640 has no RGB888).
- Sizes: `QQVGA ... QVGA (320x240), VGA, SVGA, XGA, HD, FHD, UXGA, QXGA` (OV5640 goes higher).
- Use `Camera(init=False)` then `cam.init()` to delay initialization.
- Camera needs PSRAM; large frames at high sizes can exhaust memory with `fb_count=2`.
- Async version: `from acamera import Camera`.
- Full API typings: `~/micropython-camera-driver/typings/camera.pyi`.

Streaming/web examples live in `~/micropython-camera-driver/examples/` (e.g. `SimpleWebCam.py`).

## 4. Known issues / TODO

- `board.preview()` is untested; RGB565 byte order may need swapping.
- The ST7789 MADCTL/offset values were inherited from the LCD-1.9 driver; check
  orientation and color order (`invert`) on the real panel.
- No text/font rendering on the LCD.
- Charging state (ETA6098) and fuel gauge are not available; `battery_percent()` is voltage-based and approximate.
- Camera power (PWDN=GPIO17) is handled by the camera driver; keep GPIO17 free.
