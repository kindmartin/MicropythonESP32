> **Ubicacion en este repo:** `boards/WAVESHARE_ESP32_S3_LCD147B/` — `mp_board/` (carpeta para compilar),
> `tested_modules/` (drivers + `tests/` + `examples/`), `docs/`. Compilar: `scripts/install_board.sh WAVESHARE_ESP32_S3_LCD147B <micropython> --force`.

# Waveshare ESP32-S3-LCD-1.47B — guia MicroPython

Producto: https://www.waveshare.com/product/esp32-related/displays/lcd-spi-qspi/esp32-s3-lcd-1.47b.htm
Wiki: https://www.waveshare.com/wiki/ESP32-S3-LCD-1.47B — Esquematico: `.../ESP32-S3-LCD-1.47B_schematic_diagram.pdf`
Fuente de los pines: tabla GPIO del esquematico oficial (la pagina web solo los muestra como imagen).

> **Estado (2026-11-02):** definicion de placa y drivers escritos; **nada probado en la placa todavia**.
> Compila segun lo previsto pero no se ha compilado ni flasheado. Los scripts pasan `mpy-cross`; el dibujo del
> horizonte se verifico en una simulacion en CPython (4 orientaciones), no en el panel.

## 1. Hardware

| Item | Detalle |
|---|---|
| MCU | ESP32-S3R8, LX7 doble nucleo 240 MHz, WiFi + BLE 5 |
| Flash / PSRAM | 16 MB / 8 MB octal |
| Pantalla | IPS 1,47" 172x320, ST7789, SPI (3 hilos + DC), backlight por MOSFET |
| IMU | QMI8658 (acel. + giroscopio), I2C 0x6B |
| Otros | LED RGB WS2812, microSD (SDMMC), cargador LiPo, BOOT y RST, USB-C nativo, header de 18 pines |
| **Sin** | camara, touch |

## 2. Mapa de pines

| Funcion | GPIO |
|---|---|
| LCD SCK / MOSI | 40 / 45 (SPI id 1, sin MISO) |
| LCD CS / DC / RST / BL | 42 / 41 / 39 / 46 (BL con PWM) |
| I2C0 SCL / SDA (IMU) | 47 / 48 |
| IMU INT1 / INT2 | 13 / 12 |
| Bateria (BAT_ADC) | 1, divisor 200K/100K: V = Vadc x 3 |
| BOOT | 0 |
| LED RGB WS2812 | 38 |
| SD (SDMMC) CLK / CMD / D0 / D1 / D2 / D3 | 14 / 15 / 16 / 18 / 17 / 21 |
| UART0 TX / RX | 43 / 44 (en el header) |
| USB nativo D- / D+ | 19 / 20 |

Header de 18 pines (segun el diagrama): 5V, GND, 3V3, GP0, GP2..GP6 (izquierda); TX, RX, VBAT, GND, GP7..GP11 (derecha).
El `C3` serigrafiado junto al conector es solo un rotulo de la placa, no el chip.

## 3. Compilar y flashear

```bash
~/MicropythonESP32/scripts/install_board.sh WAVESHARE_ESP32_S3_LCD147B ~/micropython --force
cd ~/micropython/ports/esp32 && make BOARD=WAVESHARE_ESP32_S3_LCD147B
```
Congela `board.py`, `st7789.py` y `qmi8658.py` (ver `frozen_modules.txt`). `MICROPY_HW_ENABLE_UART_REPL=1`: REPL por UART0 (43/44) y por USB CDC.
**Flasheo** (con el USB nativo no hay auto-reset): mantener BOOT, pulsar RST, soltar BOOT; luego
`python -m esptool --chip esp32s3 -p <puerto> -b 460800 write_flash 0x0 build-WAVESHARE_ESP32_S3_LCD147B/firmware.bin`.

## 4. Tests (`tested_modules/tests/`)

`test_lcd`, `test_backlight`, `test_imu` (incluye `i2c.scan()`, esperado 0x6b), `test_vbat`, `test_rgb`, `test_sd`, `test_button`, `test_all`.
Copiar con mpremote y ejecutar con `import test_xxx`. `test_board_legacy.py` es el test antiguo de una sola pieza.

## 5. Ejemplo: horizonte sin camara (`examples/horizon.py`)

`import horizon` (o `horizon.run(sim=True)`). Cielo/suelo dibujados con framebuf, alabeo con puntero al cielo, escala de cabeceo,
simbolo fijo y bateria; verde cuando |alabeo| y |cabeceo| < 5 grados. BOOT con 4 gestos (el LED RGB se pone verde al llegar a "largo" y rojo al llegar a "extra"):

| Gesto | En RUN | En configuracion |
|---|---|---|
| corto | CERO (alabeo/cabeceo actuales = 0; en NIVEL, cero del nivel) | cambia el valor del ajuste mostrado |
| doble | alterna HORIZONTE / NIVEL de burbuja | siguiente ajuste |
| largo (0,7-3 s) | entra a configuracion | vuelve a RUN |
| extra (> 3 s) | sale al REPL | sale al REPL |

**Vista NIVEL (burbuja):** para usar la placa apoyada en una superficie. La burbuja va hacia el lado mas alto; verde < 0,5 grados en ambos ejes,
amarillo < 2, rojo el resto. Muestra por cada eje del plano de la pantalla (X = derecha, Y = arriba) los grados y la pendiente en %
(100 x tan) y el angulo total respecto a la vertical. En NIVEL, un clic corto toma la superficie actual como cero (`lvl_x0`/`lvl_y0`).
Si un eje de la burbuja va al reves, en configuracion usa BURB-X o BURB-Y (invierten solo la burbuja; el horizonte no cambia). Tras invertir uno, repite el cero del nivel.

Ajustes: VISTA (gira la imagen 90 grados), EJES (gira 90 grados los ejes del IMU), CABEC (invierte el cabeceo), ALAB (invierte el alabeo),
GIRO (invierte las flechas de giro), BURB-X y BURB-Y (invierten un eje de la burbuja), ESPEJO, COLOR (intercambia rojo/azul), INV (invierte colores del panel), SIM (horizonte simulado).
El modulo corre al importarlo (`import horizon`). Se guarda en `/horizon_cfg.json`. Orden de calibracion: SIM (comprobar imagen) -> COLOR/INV/ESPEJO/VISTA -> SIM off ->
EJES/ALAB/CABEC -> RUN + CERO. Salir: tecla `q` o Ctrl-C.

## 6. Calibracion confirmada en la placa (2026-11-03)

Valores que dieron un horizonte y una burbuja correctos (son los `DEFAULT` de `horizon.py`):
`view=270 imu_rot=3 pitch_sign=+1 roll_sign=+1 gyro_sign=-1 mirror=False swap_rb=False invert=True lvl_sx=+1 lvl_sy=-1 sky_swap=True`.

- La placa se mira girada 270 grados y los ejes del IMU van girados 270 (`imu_rot=3`). El cero de alabeo no debe absorber esos giros: se pasan a `imu_rot` solos (`fold_zero`).
- `st7789.py` no activa el bit BGR (`swap_rb=False`), pero si aplica `MADCTL MX` (espejo en x del buffer): por eso el texto se dibuja con cada letra invertida
  a proposito (con `mirror=False`) y cielo/suelo salen intercambiados (`sky_swap=True`). Quitar MX del driver evitaria ambos parches, pero obliga a recalibrar.
- La burbuja lleva su propia inversion de ejes (`lvl_sx=+1`, `lvl_sy=-1`), independiente del horizonte, y solo depende de `imu_rot`: con `imu_rot=3` los dos ejes quedan invertidos respecto a `imu_rot=1`.

## 7. Pendiente / por confirmar en la placa

- `x_offset=34`: la imagen del horizonte se ve bien. Falta correr `test_lcd` con el firmware nuevo (driver sin bit BGR).
- fps del horizonte: ~22 medidos (110 KB por cuadro a 40 MHz de SPI).
- `machine.SDCard(slot=1, width=4, ...)` y `neopixel` en el LED de GPIO38.
- GPIO de los pines del header (GP0, GP2..GP11) no se probaron.
