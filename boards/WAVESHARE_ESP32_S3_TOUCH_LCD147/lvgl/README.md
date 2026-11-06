# Waveshare ESP32-S3-Touch-LCD-1.47 — firmware con LVGL

Variante del firmware que usa **LVGL** (interfaz grafica con touch) en lugar del `board.py` + `st7789/jd9853.py` del
firmware normal. Carpeta de la placa "normal": `../mp_board/` (compila con `make BOARD=WAVESHARE_ESP32_S3_TOUCH_LCD147`).

> **Estado (2026-11-03): compila y se probo en la placa.** Confirmado: arranque, pantalla, brillo, touch (con `MIRROR_X = True` en `touch_fix.py`),
> temperatura, WiFi, modulos propios congelados, REPL por UART y USB, `features.py` completo. **Sin resolver: SD** (`send_op_cond returned 0x107`,
> igual que en el firmware normal: probable falta de tarjeta/tarjeta no valida; probar otra FAT32). Bateria: sin bateria conectada no se probo.
> Lo marcado "verificar" abajo que no figure aqui sigue siendo hipotesis.

## 1. Hardware relevante (resumen)

ESP32-S3R8 (16 MB flash, 8 MB PSRAM octal). LCD IPS 1,47" 172x320 **JD9853** por SPI. Touch **AXS5106L** (I2C 0x63).
Sin IMU, sin RTC, sin camara. Mas detalles en `../docs/` y en `../tested_modules/`.

| Funcion | GPIO |
|---|---|
| LCD SCK / MOSI (sin MISO) | 38 / 39 |
| LCD CS / DC / RST / BL | 21 / 45 / 40 / 46 (BL por PWM) |
| Touch SDA / SCL / RST / INT | 42 / 41 / 47 / 48 |
| Bateria (ADC) | 12 (divisor 200K/100K, V = Vadc x 3) |
| SD (SDMMC 4 bits) CLK/CMD/D0..D3 | 16 / 15 / 17, 18, 13, 14 |
| BOOT | 0 |
| REPL UART0 (TX / RX) | 43 / 44 (`MICROPY_HW_ENABLE_UART_REPL` en `mpconfigboard.h`; ademas REPL por USB nativo) |

## 2. Como se compila: "su propio IDF"

`lvgl_micropython` (`~/lvgl_micropython`) **no usa tu ESP-IDF de `~/esp-idf`**. Trae su propia copia de todo:

| | Firmware normal | Firmware LVGL |
|---|---|---|
| ESP-IDF | `~/esp-idf` (v5.5.2), lo cargas tu con `export.sh` | `~/lvgl_micropython/lib/esp-idf` (v5.5.1) |
| MicroPython | `~/micropython` (v1.29.0) | `~/lvgl_micropython/lib/micropython` (su propio clon) |
| Comando | `cd ~/micropython/ports/esp32 && make BOARD=...` | `./build.sh` (llama a `python3 make.py esp32 ...`) |
| Entorno | tu shell con el IDF cargado | `make.py` lo prepara solo |

**Como conviven sin pisarse**
- ESP-IDF se localiza por la variable `IDF_PATH`. `make.py` la fija a *su* copia y ejecuta el `export.sh` de esa copia, solo dentro
  del proceso de compilacion.
- Si ya tienes un IDF cargado en la shell, `make.py` quita del `PATH` lo que contenga `espressif` o `esp-idf` antes de compilar
  (`builder/esp32.py`). Tu entorno no lo contamina y el suyo no contamina el tuyo.
- Comparten la carpeta de herramientas `~/.espressif` (compiladores, `python_env`; ~7 GB). Es una carpeta de instalacion comun:
  si las dos versiones de IDF piden herramientas distintas, `install.sh` las instala una al lado de la otra.
- Tu `~/esp-idf` y tu `~/micropython` **no se modifican**.
- Por que tiene su propia copia: fija la version de IDF y de MicroPython con las que probo sus parches y componentes. Usar la tuya
  (5.5.2) podria funcionar, pero seria terreno sin probar.

**Consecuencias**
- Se compila con `make.py`, **no** con `make BOARD=...` del puerto esp32 normal. No hace falta cargar tu IDF (ni conviene).
- `board.py`, `jd9853.py`, `axs5106.py` de `../tested_modules/` **no** entran en este firmware. Aqui la pantalla y el touch los dan los
  drivers de `lvgl_micropython`; el pegamento (SD, bateria, boton) hay que reescribirlo o subirlo como `.py`.

## 3. Archivos de esta carpeta

| Archivo | Para que |
|---|---|
| `waveshare_s3_touch_lcd147.toml` | Bus SPI/I2C, display JD9853, touch AXS5106, brillo. Lo toma `make.py` solo (`--custom-board-path`) |
| `build.sh` | Compila: `./build.sh [dir_de_lvgl_micropython]` (exporta `GEN_SCRIPT=python`, `LV_PORT=esp32`) |
| `mpconfigboard.h` / `.cmake` | Nombre de la placa, I2C, `sdkconfig` (16 MB, QIO 80 MHz, PSRAM octal) |
| `sdkconfig.board`, `partitions.csv` | Config del IDF y particiones (app `factory` 6 MB + FAT ~10 MB) |
| `board.json` | Metadatos |

## 3b. Modulos propios congelados

`manifest_user.py` congela `~/micropython/ports/esp32/modules` (fjs, netutils, wifiConnect, ftp*, fonts, drivers, lib, secrets.py...), salvo los archivos estandar de MicroPython (`_boot`, `machine`, `flashbdev`, `inisetup`, `espnow`, `apa106`), que ya trae `lvgl_micropython` en otra version. Es la misma fuente que usa el firmware normal.

**El `.bin` resultante lleva las claves WiFi de `secrets.py` dentro: no publicarlo.** Comprobar tras compilar: `ls build-*/frozen_mpy | grep -E "fjs|wifiConnect"`.

## 3c. Drivers directos (sin LVGL) en este firmware

El firmware LVGL tambien lleva congelados `board.py`, `st7789.py`, `lcd_jd9853.py` y `touch_axs5106.py` (los mismos del firmware normal), asi que
los ejemplos y tests SIN LVGL (`../tested_modules/tests`, `../tested_modules/examples/features.py`) pueden correr aqui **si no importas `display`**.
- LVGL y los drivers directos se excluyen mutuamente (SPI host 1 e I2C 0): para cambiar de modo, `machine.reset()`.
- `board.py` detecta el firmware (`board.LVGL_FW`): en LVGL `machine.SPI` no tiene constructor clasico (solo `Bus`/`Device`), asi que `board.spi()` crea un
  `SPI.Bus(host=1)` + `SPI.Device(cs=-1)` (el CS lo mueve el driver), y `sd_mount()` usa `clk=`/`data_pins=` en lugar de `sck=`/`data=`.
- Los drivers se llaman `lcd_jd9853` / `touch_axs5106` y no `jd9853` / `axs5106` porque esos nombres son los modulos congelados de LVGL: un archivo propio con ese
  nombre (en el FS o congelado) los taparia y romperia el arranque de LVGL. Si venias del firmware normal, comprueba `os.listdir()` y borra `axs5106.py` / `jd9853.py` viejos.
- **Sin probar en la placa**: `board.spi()` en modo LVGL (¿acepta `cs=-1`?) y las escrituras grandes del LCD son hipotesis comprobadas solo contra el codigo y un `machine` simulado.

## 3d. Que va donde (mapa del firmware LVGL)

| Que | Donde | Como llega |
|---|---|---|
| Drivers **sin LVGL**: `board`, `st7789`, `lcd_jd9853`, `touch_axs5106` | congelados en el firmware | ya vienen; no se copian |
| Drivers **de LVGL**: `jd9853`, `axs5106`, `display`, `i2c`, `task_handler`, `touch_fix` | congelados en el firmware | ya vienen; no se copian |
| Tus modulos (`fjs`, `wifiConnect`, `ftp*`, ...) | congelados | ya vienen |
| Ejemplos y tests **sin LVGL** | `/raw` en la placa | `../deploy.sh` (desde `tested_modules/`) |
| Ejemplos y tests **con LVGL** (+ `lvb.py`) | `/lvgl` en la placa | `../deploy.sh` (desde `lvgl/tests` y `lvgl/examples`) |
| `use.py` (elige el modo) | raiz `/` | `../deploy.sh` |

Se usa asi (los modos se excluyen; para cambiar, `machine.reset()`):

```python
import use; use.raw();  import test_all     # sin LVGL: board.lcd(), board.touch()...
import use; use.lvgl(); import app          # con LVGL: pantalla y touch los crea LVGL (import display)
```

Los nombres de tests/ejemplos se repiten entre los dos modos (`features`, `test_touch`, `test_sd`, `test_all`...): por eso van en carpetas distintas.

## 4. Compilar y flashear

> Trampa resuelta: `make.py` toma como nombre de board el **nombre de la carpeta** de `--custom-board-path` (aqui seria `lvgl`),
> y `mpconfigboard.cmake` / `sdkconfig.board` referencian `boards/WAVESHARE_ESP32_S3_TOUCH_LCD147_LVGL/...`. Sin coincidencia CMake falla con
> `file failed to open for reading ... sdkconfig.board`. `build.sh` compila desde una copia temporal con el nombre correcto.

```bash
cd ~/MicropythonESP32/boards/WAVESHARE_ESP32_S3_TOUCH_LCD147/lvgl && ./build.sh
```

El `.bin` queda en `~/lvgl_micropython/build/` (el nombre exacto lo imprime al final). **El flasheo lo hace el usuario**, imagen completa a offset 0:

```bash
~/.espressif/python_env/idf5.5_py3.12_env/bin/python -m esptool --chip esp32s3 -p /dev/ttyUSB0 -b 460800 write_flash 0x0 <firmware.bin>
```

## 5. Cosas a verificar en la primera prueba (heredadas de la Touch-LCD-2 y del demo)

1. **Drivers Python sin congelar** (CONFIRMADO en la 1a compilacion): `make.py` genera `build/manifest.py` pero no se lo pasa al `make`, y el firmware salio sin `jd9853`, `axs5106`,
   `i2c`, `task_handler` ni `display.py`. `build.sh` ahora exporta `FROZEN_MANIFEST=$LVGL_DIR/build/manifest.py`. Comprobar tras compilar: `strings firmware.bin | grep -c jd9853` debe ser > 0.
1b. **Touch sin congelar** (CONFIRMADO): `toml_reader` no registra `import axs5106` y no pide `INDEV=axs5106`; `build.sh` lo pasa a mano. Comprobar: `ls build-*/frozen_mpy | grep axs5106`.
1c. **Stack overflow en `mp_thread`** (visto en la placa): la pila de MicroPython era de 16 KB y LVGL dibuja dentro. `mpconfigboard.h` define ahora `MICROPY_TASK_STACK_SIZE (32 * 1024)`.
1d. **Touch espejado** (visto en la placa): el demo invierte x en vertical y el driver de LVGL no. `touch_fix.py` (congelado por `manifest_user.py`, enlazado desde el `.toml` con `touch_cal`) lo corrige con `MIRROR_X = True`. Para probar sin recompilar: `import lvb; lvb.touch_orient(mirror_x=True, mirror_y=False, swap=False)` y luego `import test_touch`.
1e. **`stack overflow in task mp_thread`** (visto en la placa, 2 veces; causa confirmada decodificando el backtrace con `xtensa-esp32s3-elf-addr2line` y el `micropython.elf`):
   `mp_thread` es un hilo de `_thread`. `boot.py` -> `startup_fallback` -> `wifiConnect` arranca el hilo FTP **al encender** (si no hay `main.py`), con la pila por
   defecto (~5 KB). Ese hilo se queda bloqueado en `socket_accept`, que llama a `mp_handle_pending()`: **ejecuta los callbacks programados, incluido el `TaskHandler` de LVGL**,
   es decir el refresco de LVGL (`lv_draw_label...`) corre dentro del hilo FTP y revienta su pila. Arreglo: `netutils/ftp_thread.py` (y `ftp_thread.py`) fijan
   `_thread.stack_size(24 * 1024)` antes de crear el hilo. El `_thread.stack_size(16384)` del `.toml` solo vale para hilos creados DESPUES de `import display`; el FTP nace antes.
   Ademas se corrigio un bug previo de `netutils/ftp_thread.py` (y `ftp_thread.py`): si `start_listen()` fallaba (sin red al arrancar), el `finally` de `dolisten` cerraba
   sockets que seguian en `None` -> `AttributeError` que se colaba en el REPL y rompia el handshake de `mpremote`. Ahora se comprueba cada socket antes de cerrarlo.
   Sin recompilar: crear un `main.py` (aunque sea vacio) evita el fallback y el hilo FTP.
2. **Bucle de reinicios** (`rst:0x1 POWERON`) visto una vez con la otra placa al iniciar el panel: recuperar con BOOT+RST y reflashear.
3. **Touch**: el driver de `lvgl_micropython` lee como el demo (escribe el registro con STOP y lee aparte), pero resetea 10 ms; el demo usa
   200 ms bajo + 300 ms alto. Si no responde, alargar `hw_reset`. El demo invierte x en vertical (`x = 171 - xraw`): el driver de LVGL no lo hace,
   asi que el touch puede salir **espejado en x** -> ajustar con `touch_cal` o rotacion.
4. **Colores / recorte**: `offset_x = 34` y `rgb565_byte_swap = true` por analogia con el firmware normal; si salen cortes, rojo/azul cambiados o
   negativo: probar `jd9853.BYTE_ORDER_BGR`, `rgb565_byte_swap = false` o quitar `set_color_inversion`.
5. **MADCTL**: el demo deja `0x36 = 0x00`; el init de `lvgl_micropython` no lo escribe, lo deja a la rotacion del framework. Verificar orientacion.
6. **SPI sin MISO**: se pone `miso = -1`. Si `make.py` lo rechaza, quitar la linea o poner un GPIO libre.
7. **Brillo**: PWM en GPIO46 via `STATE_PWM`; `display.set_backlight(0..100)`.
8. Bateria (GPIO12) y SD no vienen en este firmware: usar `machine.ADC(Pin(12), atten=ADC.ATTN_11DB)` (V = uV x 3) y `machine.SDCard(slot=1, width=4, sck=16, cmd=15, data=(17,18,13,14))`.

## 5b. Tests y ejemplos (LVGL)

`tests/` y `examples/` usan LVGL (no `board.py`): `tests/lvb.py` es el ayudante comun (importa `display`, que ejecuta el arranque generado y expone
`display.display` y `display.indev`) y hay que subirlo junto con lo que pruebes. Sin probar en la placa: la API de LVGL se contrasto con `lvgl.pyi`.

| Archivo | Que prueba |
|---|---|
| `tests/test_display.py` | colores a pantalla completa, 6 barras y marco (colores, offset, recorte) |
| `tests/test_backlight.py` | brillo PWM (GPIO46) |
| `tests/test_touch.py` | punto verde que sigue al dedo + coordenadas (aqui se ve si el touch sale espejado) |
| `tests/test_battery.py` | GPIO12, divisor x3 |
| `tests/test_temp.py` | temperatura del chip |
| `tests/test_sd.py` | microSD (`machine.SDCard(slot=1, width=4, clk=16, cmd=15, data_pins=(17,18,13,14))`; en este arbol los nombres son `clk`/`data_pins`) |
| `tests/test_button.py` | BOOT (GPIO0) |
| `tests/test_all.py` | los corre en orden |
| `examples/features.py` | todo lo anterior en una pantalla de estado + touch interactivo (BOOT sale) |
| `examples/app.py` | **app de 3 paginas que se cambian deslizando** (tileview): UI, FEATURES (chequeos + boton Repetir) y TOUCH (zona de prueba) |
| `examples/ui_demo.py` | UI: slider de brillo, barra de bateria, temperatura, switch de inversion, boton |

Subir y correr (con `screen` cerrado):

```bash
M="python3 ~/micropython/tools/mpremote/mpremote.py connect /dev/ttyUSB0"; cd ~/MicropythonESP32/boards/WAVESHARE_ESP32_S3_TOUCH_LCD147/lvgl && for f in tests/*.py examples/*.py; do $M fs cp $f :$(basename $f); done; $M exec "import features"
```

## 6. Primer script de prueba (tras flashear)

```python
import lcd_bus, lvgl as lv   # los nombres reales los define el firmware generado por make.py
import task_handler
scr = lv.screen_active()
lbl = lv.label(scr); lbl.set_text("Hola LVGL 1.47"); lbl.center()
```

Si `display`/`indev` ya se crearon al arrancar (por el `.toml`), basta con `import lvgl as lv` y `lv.screen_active()`.
