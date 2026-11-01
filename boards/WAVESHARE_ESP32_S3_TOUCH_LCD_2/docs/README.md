> **Ubicacion en este repo:** `boards/WAVESHARE_ESP32_S3_TOUCH_LCD_2/` — `mp_board/` (carpeta para compilar),
> `tested_modules/` (drivers + `tests/` + `examples/`), `lvgl/`, `docs/`. Para compilar usa
> `scripts/install_board.sh WAVESHARE_ESP32_S3_TOUCH_LCD_2 <micropython>`; las rutas `ports/esp32/boards/...`
> y `modules/`, `tests/` de abajo se refieren a la copia ya instalada en MicroPython.

# Waveshare ESP32-S3-Touch-LCD-2 — MicroPython board guide

Board definition: `ports/esp32/boards/WAVESHARE_ESP32_S3_TOUCH_LCD_2/`
Product: https://www.waveshare.com/esp32-s3-touch-lcd-2.htm
Pin data source: Waveshare official demo (`ESP32-S3-Touch-LCD-2-Demo.zip`, Arduino + ESP-IDF examples).

> Status: firmware builds. The drivers were written from the demo's pin/register
> info; unless marked **tested**, treat them as untested on hardware.

## 1. Hardware

| Item | Detail |
|---|---|
| MCU | ESP32-S3R8, dual-core LX7 @ 240 MHz, WiFi + BLE |
| Flash / PSRAM | 16 MB flash, 8 MB octal PSRAM |
| Display | 2" IPS, 240x320, ST7789T3, SPI, no RST pin, PWM backlight |
| Touch | CST816D, I2C addr 0x15, single point, no INT/RST used by demo |
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
- Camera pins GPIO 2/4/6/7/8/9/10..15/16/17/21 are also on the 28-pin header:
  free for general use only if the camera is not used.

### 28-pin header (per Waveshare pin definition)

Right side (1-14): 3V3, GND, TX(43), RX(44), 47, 48, 15, 13, 11, 12, 14, 9, GND, VBAT.
Left side (15-28): 5V, GND, 19, 20, 10, 7, 8, 21, 18, 17, 16, 6, 4, 2.

- 47/48 = I2C0 (touch + IMU): external I2C devices can share it (avoid 0x15, 0x6B).
- 43/44 = UART0 REPL. 19/20 = native USB D-/D+ (do not use if USB is needed).
- 18 is the only header GPIO not used by any on-board peripheral.
- LCD, SD, backlight, vbat and BOOT pins are not on the header.

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

- Camera -> LCD video: measured ~25 fps at QVGA RGB565 with the LCD SPI at 40 MHz (camera-limited; `tests/test_camera_fps.py`). `board.preview()` colours/orientation still need visual confirmation (RGB565 byte order may need swapping). `blit_buffer` accepts the camera's memoryview without copying.
- The ST7789 MADCTL/offset values were inherited from the LCD-1.9 driver; check
  orientation and color order (`invert`) on the real panel.
- No text/font rendering on the LCD.
- Charging state (ETA6098) and fuel gauge are not available; `battery_percent()` is voltage-based and approximate.
- Camera power (PWDN=GPIO17) is handled by the camera driver; keep GPIO17 free.

## 5. Video camara -> LCD (probado, funciona)

`tests/video.py`: video 240x240 (camara `R240X240`, RGB565) arriba y franja libre 240x80 abajo para la UI,
SPI del LCD a 40 MHz, ~24 fps (limite de la camara). Resultados de la puesta a punto:

- **Colores:** la camara entrega RGB565 *big-endian*, tal cual lo espera el ST7789: el frame se envia sin
  procesar (`lcd.blit_buffer(buf, ...)`). `st7789.py` ya **no** activa el bit BGR de MADCTL (parametro
  `bgr=False`); con BGR el rojo salia azul-turquesa. Cuidado: el orden little-endian da un mosaico psicodelico.
- **Orientacion:** con la placa en horizontal (franja de UI a la derecha) la imagen queda derecha con el
  **espejo horizontal** de la camara (`cam.set_hmirror(True)`), sin rotacion por software. Si cambia el montaje,
  el boton BOOT recorre las 8 orientaciones (volteo V, espejo H, giro 90 en software); los cuadritos amarillos
  indican el modo (modo 3 = el correcto aqui).
- **Rendimiento:** sin rotar, ~24 fps. Rotar 90 en software (viper, bloques 2x2 de 32 bit) cuesta ~16 ms para
  240x240 (~28 ms con la version simple), bajando a ~16 fps. `blit_buffer` acepta el `memoryview` de la camara sin copiar.
- Frames de la camara: tras `reconfigure()` hay que descartar 2 frames (el primero es del tamano anterior).
- `fs cp` de `mpremote` falla con algunos binarios en este firmware (`SyntaxError ... invalid \x escape`); el
  volcado de frames crudos por serie pierde datos. Para analizar un frame: volcar un muestreo reducido con CRC por linea.
- El hilo FTP (`netutils/ftp_thread.py`) se cae en bucle y llena el REPL de errores: un `main.py` vacio +
  `import r` (reinicio) evita que arranque y deja `mpremote` usable.
