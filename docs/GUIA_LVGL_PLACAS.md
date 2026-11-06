# Guía: firmware MicroPython + LVGL para placas ESP32-S3 (referencia)

Referencia para compilar un firmware con **LVGL** (`lvgl_micropython`) para placas parecidas a las Waveshare ESP32-S3 con pantalla SPI y touch I2C.
Sale de la **Waveshare ESP32-S3-Touch-LCD-1.47** (JD9853 172x320 + AXS5106L, sin IMU), trabajada el 2026-11-03. Los ejemplos de código y rutas son de esa
placa: sustituye `<PLACA>`, `<DISPLAY>`, `<TOUCH>` y los pines por los tuyos. Carpeta de referencia viva:
`~/MicropythonESP32/boards/WAVESHARE_ESP32_S3_TOUCH_LCD147/lvgl/` (su `README.md` tiene el historial de cada problema).

> **Leyenda de confianza.** ✅ = probado en la placa · 🔧 = compilado y verificado en el binario, sin probar en la placa · ❓ = hipótesis.
> Regla de siempre: **mide, no supongas**. Y el flasheo lo hace el usuario: se le dan los comandos, no se ejecutan.

---

## 1. ¿LVGL o firmware normal?

| | Firmware normal (`ports/esp32`) | Firmware LVGL (`lvgl_micropython`) |
|---|---|---|
| MicroPython / IDF | el de tu `~/micropython` (1.29) y tu `~/esp-idf` | **su propio** clon (`lib/micropython`, 1.27 + parches) e IDF (`lib/esp-idf`, 5.5.1) |
| Comando | `make BOARD=...` con el IDF cargado en tu shell | `python3 make.py esp32 ... --custom-board-path=...` (prepara su IDF solo) |
| Tamaño de app | ~1,8 MB | ~3,1 MB (cabe en 1 `factory` de 6 MB; en una ranura OTA de 3 MB sobran ~10 KB) |
| `machine.SPI` | clásico: `SPI(1, ...)` | **sin constructor**: solo `SPI.Bus(...)` + `SPI.Device(...)` |
| `machine.SDCard` | `sck=`, `data=(...)` | `clk=`, `data_pins=(...)` |
| Mantenimiento | actualizas con tu árbol | dependes del fork; `make.py` tiene trampas (§4) |

**Cuándo compensa LVGL:** pantalla con touch donde quieras widgets, gestos, animaciones, o varias pantallas. **Cuándo no:** proyectos sin UI, con OTA, o
que necesiten tu MicroPython al día. Se pueden tener **los dos** firmwares, o un LVGL «general» (§6) que además deja usar los drivers directos sin LVGL.

Costes reales medidos: ~2,8 MB menos de heap libre **con la app cargada** (7980 → ~5150 KB; no es el coste en reposo, que no se midió ❓), y en el LVGL la
instrucción/rodata se ejecuta desde PSRAM si activas `SPIRAM_FETCH_INSTRUCTIONS`/`RODATA` (decisión nuestra, revisable).

## 2. Cómo funciona `lvgl_micropython` (lo que hay que saber)

- **Su propio IDF y MicroPython.** Conviven con los tuyos: `make.py` fija `IDF_PATH` a `lib/esp-idf`, ejecuta su `export.sh` y **filtra del `PATH`** lo que contenga
  `espressif`/`esp-idf` (`builder/esp32.py`). Comparten solo `~/.espressif` (herramientas, `python_env`). No toca tu `~/esp-idf` ni tu `~/micropython`.
- **Necesita** `pip`: `toml` (`sudo apt install python3-toml`). Si tu shell tiene un venv/IDF activo, ese `python3` puede no tenerlo.
- **`.toml` → `display.py`.** Con `--custom-board-path` el `.toml` de la carpeta describe buses, display, touch y qué ejecutar al arrancar; `toml_reader` lo convierte en
  un `build/display.py` que se **congela** en el firmware como módulo `display`. ✅ **No se ejecuta solo al arrancar**: lo ejecuta quien haga `import display`
  (o `main.py`). Quien lo importe obtiene `display.display`, `display.indev`.
- **Qué se congela:** los drivers del `DISPLAY=`/`INDEV=` pedidos, `display_driver_framework`, `pointer_framework`, `i2c`, `task_handler`, más tu `FROZEN_MANIFEST`.
- **LVGL dibuja dentro del intérprete** (`LV_OS_NONE`): el `TaskHandler` usa un `machine.Timer` que programa un callback con `mp_sched_schedule`. **Ese callback lo ejecuta
  cualquier hilo que llame a `mp_handle_pending()`** — incluido un hilo bloqueado en `accept()`/`recv()`. Es la causa de §4 (trampa 9).
- Tras cada compilación `make.py` **restaura los archivos originales** del árbol `lib/micropython` (`revert_files`). Un `grep` en el árbol *después* no ve tus parches:
  comprueba el log del build o el binario (§5).

## 3. Receta para una placa nueva

1. **Pines y chips:** del esquemático oficial + demo (`Arduino/examples`, `ESP-IDF`). La web suele traer solo una imagen. Pide permiso antes de descargar el ZIP.
   Cruza con la ficha: ¿hay IMU/RTC/cámara? (la 1.47 **no** los tiene; el esquemático lo confirma).
2. **¿Existe driver en `lvgl_micropython`?** `ls ~/lvgl_micropython/api_drivers/common_api_drivers/{display,indev}`. Si no hay driver de display, mira el `init` del demo y
   escribe uno (subclase de `display_driver_framework.DisplayDriver` + `_xxx_init.py`). La 1.47 tuvo ambos: `jd9853` y `axs5106`.
3. **Copia la carpeta** de una placa parecida (`.../lvgl/`) y ajusta: `.toml`, `mpconfigboard.h`, `sdkconfig.board`, `partitions.csv`, `board.json`.
4. **`build.sh`**: usa la plantilla del Apéndice A (ya trae todos los arreglos de §4). Cambia `BOARD=` y `INDEV=`.
5. **Compila** (puede tardar mucho la primera vez: submódulos + `install.sh` del IDF 5.5.1): `./build.sh | tee build.log`. Una recompilación incremental es mucho más corta.
6. **Verifica el binario** (§5) **antes** de dárselo al usuario.
7. **El usuario flashea** (comando en §9) y probáis por orden: arranque → `import display` → colores → touch → resto.
8. **Orientación del touch/pantalla** (§7) y ajustes de color (`color_byte_order`, `rgb565_byte_swap`, `set_color_inversion`, `offset_x/y`).
9. Tests y ejemplos (§8) + `README.md` de la carpeta con lo confirmado y lo pendiente.

Estructura (la 1.47):
```
<PLACA>/
├── lvgl/            build.sh, <placa>.toml, mpconfigboard.{h,cmake}, sdkconfig.board, partitions.csv, board.json,
│                    manifest_user.py, touch_fix.py, patch_lvgl_spi.py, README.md, DEVICE_README.md
│   ├── examples/    ejemplos CON LVGL      →  /lvgl en la placa
│   └── tests/       tests CON LVGL + lvb.py →  /lvgl
├── tested_modules/  drivers directos (SIN LVGL) + tests/ + examples/  →  /raw (los .py de la raíz van congelados)
├── mp_board/        solo para el firmware normal
├── firmware/        los .bin
└── deploy.sh, use.py, DEVICE_README.md
```

## 4. Trampas conocidas (síntoma → causa → arreglo)

| # | Síntoma | Causa | Arreglo |
|---|---|---|---|
| 1 ✅ | `ModuleNotFoundError: toml` / «toml library is needed» | falta el paquete en el `python3` que usas | `sudo apt install python3-toml` (revisa `which python3`) |
| 2 ✅ | CMake: `file failed to open ... boards/<BOARD>/sdkconfig.board` | `make.py` toma como nombre de board **el nombre de la carpeta** de `--custom-board-path` (aquí `lvgl`) | `build.sh` compila desde una copia temporal con la carpeta llamada `<BOARD>` (Apéndice A) |
| 3 ✅ | Firmware sin `jd9853`, `i2c`, `task_handler`, `display.py` (`import display` falla) | `make.py` genera `build/manifest.py` pero **no se lo pasa a `make`** (`esp_cmd.extend(extra_args)` está comentado) | `export FROZEN_MANIFEST="$LVGL_DIR/build/manifest.py"` (make lee variables de entorno) |
| 4 ✅ | Falta el driver del touch aunque `display.py` hace `import axs5106` | `toml_reader` no registra el import cuando solo aparece dentro de un parámetro (`dev_id = "axs5106.I2C_ADDR"`) | pasar `INDEV=<touch>` a mano a `make.py` |
| 5 ✅ | Sin prompt por UART (solo por USB) | con boards personalizados `make.py` **ignora** `enable_uart_repl` del `.toml` | `#define MICROPY_HW_ENABLE_UART_REPL (1)` en `mpconfigboard.h` |
| 6 ✅ | `stack overflow in task mp_thread`; o crash al dibujar | pila de MicroPython 16 KB; `--task-stack-size` también se ignora | `#define MICROPY_TASK_STACK_SIZE (32 * 1024)` en `mpconfigboard.h` (respeta `#ifndef` de `mpconfigport.h`) |
| 7 🔧 | `mp_thread` por una pila de **hilo** (`_thread`) pequeña | los hilos nacen con ~5 KB; con `-O3` no alcanzan | `_thread.stack_size(N)` **antes** de crear el hilo. El del `.toml` solo vale tras `import display` |
| 8 ✅ | `E spi_master: check_trans_valid: SPI_TRANS_USE_TXDATA only available for txdata transfer <= 32 bits` | bug del fork en `micropy_updates/esp32/machine_hw_spi.c`: la rama de >4 bytes activa `USE_TXDATA/USE_RXDATA` junto con `tx_buffer/rx_buffer` | `patch_lvgl_spi.py` (idempotente, guarda `.orig`) lo corrige antes de compilar; `build.sh` lo ejecuta |
| 9 🔧 | `stack overflow in task mp_thread` **a los minutos**, con WiFi/FTP activos | un hilo bloqueado en `socket_accept` ejecuta `mp_handle_pending()` → el `TaskHandler` de LVGL (`lv_draw_*`) corre **dentro de ese hilo** y revienta su pila | pila grande para los hilos (7) en el módulo que los crea (`ftp_thread.py`: `_thread.stack_size(24*1024)`); o no arrancar hilos bloqueantes con LVGL |
| 10 ✅ | `mpremote: could not enter raw repl` + traceback de un hilo | un hilo que falla escribe en el REPL durante el handshake; o la placa quedó en **raw REPL** (no hace eco, `\x04>` al pulsar Ctrl-C) | Ctrl-C ×2 y **Ctrl-B** por `pyserial` para volver al REPL normal; `main.py` vacío evita el hilo del arranque |
| 11 ✅ | `AttributeError: 'NoneType' object has no attribute 'close'` en `ftp_thread.dolisten` | `finally` cierra sockets que siguen en `None` si `start_listen()` falla (sin red) | comprobar cada socket antes de cerrarlo (corregido en `ftp_thread.py`) |
| 12 🔧 | `TypeError` al hacer `machine.SPI(1, ...)` | en este fork `machine.SPI` no tiene constructor | `SPI.Bus(host=, sck=, mosi=)` + `SPI.Device(spi_bus=, freq=, cs=-1)` (§6) |
| 13 ✅ | `machine.SDCard(sck=...)` → argumentos desconocidos (con los nombres de LVGL el error pasó a ser el timeout de tarjeta, no de argumentos) | otros nombres de parámetros | `clk=`, `cmd=`, `data_pins=(d0,d1,d2,d3)` |
| 14 ✅ | Touch **espejado** en x | el demo invierte x en vertical y el driver de LVGL no | `touch_cal` con `mirrorX` (§7); probar sin recompilar con `indev._cal = ...` |
| 15 ✅ | `freeze(path, ("carpeta",))` → `AssertionError` en `makemanifest.py` (`KIND_FREEZE_MPY`) | `freeze()` no expande carpetas dentro de la lista | pasar los `.py` **con su ruta relativa** (`fjs/tlc.py`): conserva los paquetes |
| 16 🔧 | `LvReferenceError: Referenced object was deleted!` | un callback de un ejemplo anterior sigue vivo sobre objetos borrados (`screen.clean()`) | pantalla **nueva** por ejemplo (`lv.obj(None)` + `lv.screen_load()`), quitar callbacks en un `finally` |
| 17 🔧 | Tus módulos/drivers propios con nombre `jd9853.py`/`axs5106.py` rompen LVGL | un archivo en el FS o congelado con ese nombre **tapa** el módulo de LVGL (otra API) | nombres distintos: `lcd_jd9853.py`, `touch_axs5106.py` |
| 18 ✅ | `grep` en `lib/micropython/...` después del build no muestra tu parche | `make.py` restaura los originales al terminar | verificar con el log (`Building ... machine_hw_spi.c.obj`) o recompilando el fuente y comparando (§5) |

## 5. Verificar el binario antes de entregarlo

```bash
B=$HOME/lvgl_micropython/lib/micropython/ports/esp32/build-<BOARD>
ls -la $HOME/lvgl_micropython/build/lvgl_micropy_<BOARD>.bin        # imagen completa -> write_flash 0x0
cmp $HOME/lvgl_micropython/build/lvgl_micropy_<BOARD>.bin $B/firmware.bin && echo igual
# ¿están congelados los drivers y tus módulos?
for k in display.mpy jd9853.mpy axs5106.mpy i2c.mpy task_handler.mpy touch_fix.mpy fjs/tlc.mpy; do [ -f $B/frozen_mpy/$k ] && echo "ok $k" || echo "FALTA $k"; done
# ¿entró el cambio de un .py propio? (recompilar con el mpy-cross del árbol LVGL y comparar bytes)
$HOME/lvgl_micropython/lib/micropython/mpy-cross/build/mpy-cross -march=xtensawin -s <ruta/modulo.py> -o /tmp/x.mpy <fuente.py> && cmp /tmp/x.mpy $B/frozen_mpy/<ruta/modulo>.mpy
# ¿usó mis defines? mira la copia temporal que prepara build.sh: /tmp/tmp.*/<BOARD>/mpconfigboard.h
tr '\r' '\n' < build.log | grep "binary size"      # tamaño frente a la partición
sha256sum <bin>                                    # darlo siempre con el .bin
```
Los **nombres de builtins** (`Exception`, ...) no aparecen como texto dentro de un `.mpy`: no uses `grep` de cadenas para validar código; compara bytes.

## 6. Un solo firmware: LVGL **o** drivers directos

Para que el mismo firmware sirva a proyectos con y sin LVGL (los dos modos se **excluyen**: SPI host y I2C los toma LVGL con `import display`; cambia con `machine.reset()`):

- Congela los drivers directos con **otros nombres** (`board`, `st7789`, `lcd_<chip>`, `touch_<chip>`) desde el `manifest_user.py` (Apéndice D).
- `board.py` detecta el firmware: `LVGL_FW = hasattr(machine.SPI, "Bus")` y adapta:
  - `spi()`: `SPI.Bus(host=1, sck=, mosi=)` + `SPI.Device(spi_bus=, freq=, cs=-1)` (el driver mueve su propio CS).  ✅ `test_lcd` corre sin error con el parche del §4.8; el resultado **visual** no se confirmó ❓.
  - `sd_mount()`: `clk=/data_pins=` en LVGL, `sck=/data=` en el normal.
- I2C no cambia: `i2c.I2C.Bus` de LVGL envuelve `machine.I2C`. Lee el touch **con STOP** entre escribir el registro y leer (el `readfrom_mem` con repeated start devolvía ceros en el AXS5106L).
- Despliegue en la placa (ver `deploy.sh`): `/raw` (sin LVGL), `/lvgl` (con LVGL), `use.py` con `use.raw()` / `use.lvgl()` (ajusta `sys.path`). Los nombres de ejemplos se repiten entre modos → carpetas distintas.

## 7. Orientación, color y offsets

- **Touch:** `touch_cal` espera un objeto con `alphaX, betaX, deltaX, alphaY, betaY, deltaY, mirrorX, mirrorY, save()`. Se enlaza desde el `.toml` con una expresión:
  `touch_cal = "__import__('touch_fix').CAL"` (los strings del `.toml` se emiten tal cual en `display.py`). Con matriz identidad y `mirrorX=True` se espeja x (`x' = ancho - x - 1`).
  Probar sin recompilar: `indev._cal = <objeto>` desde el REPL (se pierde al reiniciar). Un objeto propio evita escribir en NVS.
- **Display:** `offset_x/offset_y` para paneles recortados (172 de 240 → `offset_x = 34`); `color_byte_order = RGB|BGR`; `rgb565_byte_swap = true` (LVGL es little-endian, el panel big-endian);
  `[display.set_color_inversion] params=[true]` si los colores salen en negativo; `reset_state` es el valor **activo** del reset (panel con reset activo en bajo → `STATE_LOW`).
- Mira los valores del demo oficial: el `lcd_reg_init` trae MADCTL, COLMOD e inversión.
- **Orden de comprobación:** colores sólidos R/G/B/blanco → barras de 6 colores con marco (recortes) → punto bajo el dedo (touch) → texto legible.

## 8. Tests y ejemplos con LVGL (patrón)

Un ayudante común (`lvb.py`) importa `display` y expone `disp`, `indev`, `screen()`, `label()`, `vbat()`, `sd_mount()`, `touch_orient()`. Cada test es un script corto que imprime `PASS`/`FAIL`.
Funciones LVGL 9 usadas y verificadas contra `~/lvgl_micropython/lvgl.pyi`:

```python
import lvgl as lv
s = lv.obj(None); lv.screen_load(s)                       # pantalla nueva (y borrar la anterior: old.delete())
lb = lv.label(s); lb.set_text("hola"); lb.center(); lb.align(lv.ALIGN.TOP_LEFT, 4, 10)
lb.set_style_text_color(lv.color_hex(0x00FF00), 0)
def on_touch(e):                                          # eventos de touch
    p = lv.point_t(); lv.indev_active().get_point(p)      # p.x, p.y
s.add_event_cb(on_touch, lv.EVENT.PRESSING, None)         # luego: s.remove_event_cb(on_touch) en un finally
sl = lv.slider(s); sl.set_range(5, 100); sl.set_value(80, 0)   # 0 = sin animación (anim_enable_t es un int)
tv = lv.tileview(s); t1 = tv.add_tile(0, 0, lv.DIR.RIGHT); t2 = tv.add_tile(1, 0, lv.DIR.LEFT)   # páginas deslizables
tv.add_event_cb(cb, lv.EVENT.SCROLL_END, None)            # página actual: (tv.get_scroll_x() + ancho//2) // ancho
lv.timer_create(cb, 2000, None)                           # refrescos periódicos
disp.set_backlight(50); disp.set_color_inversion(True)    # métodos del driver de display
```
Reglas: **no bloquees dentro de callbacks** (nada de `sleep` largos, escaneos WiFi, etc.: se ejecutan desde el scheduler y congelan LVGL); no compares objetos LVGL con `==`;
crea una pantalla nueva por ejemplo; quita tus callbacks en un `finally` (un Ctrl-C deja callbacks vivos).

## 9. Entrega y flasheo

- El `.bin` **de `lvgl_micropy_<BOARD>.bin` es la imagen completa**: `write_flash 0x0`. Con el USB nativo no hay auto-reset: BOOT pulsado, RST y soltar; por el puente UART (`/dev/ttyUSB0`) sí resetea solo.
  ```bash
  ~/.espressif/python_env/idf5.5_py3.12_env/bin/python -m esptool --chip esp32s3 -b 460800 [-p /dev/ttyUSB0] write_flash 0x0 <firmware.bin>
  ```
- **El flasheo y el `screen` los maneja el usuario.** Subir `.py` con `mpremote` sí se puede hacer (con el puerto libre: `fuser -v /dev/ttyUSB0`).
- Reflashear a offset 0 **no toca** la partición FAT si el offset de `vfs` coincide (`0x610000` en ambos firmwares): los archivos de la placa sobreviven, también los viejos que taparían módulos congelados → `os.listdir()` tras cambiar de firmware.
- **Seguridad:** el `.bin` lleva congelado `secrets.py`/`webrepl_cfg.py` con claves reales → no publicarlo (`*.bin` va en el `.gitignore`).

## 10. Depurar un crash

Los `Backtrace:` del panic se decodifican con el `.elf` **del mismo build** (compara el prefijo de `ELF file SHA256:` con `sha256sum micropython.elf`):

```bash
A=$(ls ~/.espressif/tools/xtensa-esp-elf/*/xtensa-esp-elf/bin/xtensa-esp32s3-elf-addr2line | head -1)
$A -pfiaC -e ~/lvgl_micropython/lib/micropython/ports/esp32/build-<BOARD>/micropython.elf 0x4213c4d7 0x4211d029 ...
```
Lectura típica: `mp_thread` = hilo de `_thread`; `mp_task` = tarea principal. En un overflow mira quién llamó a `lv_task_handler` (`mp_sched_run_pending` ← `socket_accept` = trampa 9).
Si el backtrace sale `CORRUPTED`/corto no sirve: repite con otro disparo o sube las pilas.
Memoria en vivo: `esp32.idf_heap_info(esp32.HEAP_DATA)` (la región enorme es PSRAM; el resto, RAM interna donde viven las pilas de hilos). Un `mpremote` colgado: Ctrl-C ×2 + Ctrl-B por `pyserial`.

## 11. Checklist para una placa nueva

- [ ] Pines del esquemático; ¿hay IMU/RTC/cámara? (no asumir por la foto del producto)
- [ ] ¿Hay driver `display/` e `indev/` en `lvgl_micropython`? Si no, escribirlo con el `init` del demo
- [ ] Copiar la carpeta `lvgl/` de una placa parecida; `.toml`, `mpconfigboard.h` (UART REPL, pila 32 KB), `sdkconfig.board`, `partitions.csv`
- [ ] `build.sh` del Apéndice A: nombre de carpeta, `FROZEN_MANIFEST`, `INDEV=`, parche SPI, `LVGL_BOARD_DIR`
- [ ] `manifest_user.py` con tus módulos **y** pila de hilos (`ftp_thread`); no congelar los estándar (`_boot`, `machine`, ...)
- [ ] Compilar, **verificar el binario** (§5), anotar SHA256
- [ ] El usuario flashea; probar: arranque → `import display` → colores → touch (¿espejado?) → brillo → resto
- [ ] Probar con WiFi/FTP **varios minutos** si el proyecto los usa (trampa 9)
- [ ] Tests/ejemplos en `lvgl/` y `tested_modules/`; `deploy.sh`; README con lo confirmado (✅) y lo pendiente (❓)
- [ ] Anotar en `NOTAS_PARA_SESIONES.md` y en la memoria

---

## Apéndice A — `build.sh` (plantilla con todos los arreglos)

```bash
#!/bin/bash
# Uso: ./build.sh [lvgl_micropython_dir]
set -e
BOARD=<PLACA>_LVGL                                   # = nombre de carpeta que verá make.py (trampa 2)
HERE="$(cd "$(dirname "$0")" && pwd)"
LVGL_DIR="${1:-$HOME/lvgl_micropython}"
STAGE="$(mktemp -d)/$BOARD"; mkdir -p "$STAGE"
cp "$HERE"/board.json "$HERE"/mpconfigboard.h "$HERE"/mpconfigboard.cmake "$HERE"/sdkconfig.board \
   "$HERE"/partitions.csv "$HERE"/*.toml "$STAGE"/
cd "$LVGL_DIR"
python3 "$HERE/patch_lvgl_spi.py" "$LVGL_DIR/micropy_updates/esp32/machine_hw_spi.c"   # trampa 8
export GEN_SCRIPT=python LV_PORT=esp32
export LVGL_BOARD_DIR="$HERE"                         # manifest_user.py congela touch_fix.py desde aquí
export FROZEN_MANIFEST="$LVGL_DIR/build/manifest.py"  # trampa 3
python3 make.py esp32 BOARD=$BOARD --custom-board-path="$STAGE" INDEV=<touch> \
        FROZEN_MANIFEST="$HERE/manifest_user.py"      # trampa 4 + manifest propio
```

## Apéndice B — `<placa>.toml` (display SPI + touch I2C)

```toml
[MCU.esp32]
BOARD = "<PLACA>_LVGL"
flash_size = 16
enable_jtag_repl = 'n'
enable_cdc_repl = 'n'
enable_uart_repl = 'y'            # ignorado con --custom-board-path (trampa 5): ver mpconfigboard.h
uart_repl_bitrate = 115200

[SPI.Bus.spi_bus]
host = 1
mosi = 39
miso = -1                         # sin MISO
sck = 38

[SPIBus.display_bus]
spi_bus = "spi_bus"
freq = 40000000
dc = 45
cs = 21

[I2C.Bus.i2c_bus]
host = 0
scl = 41
sda = 42
freq = 400000

[I2C.Device.indev_device]
bus = "i2c_bus"
dev_id = "<touch>.I2C_ADDR"
reg_bits = "<touch>.BITS"

[<DISPLAY>.display]               # p. ej. JD9853, ST7789, ST7796...
data_bus = "display_bus"
display_width = 172
display_height = 320
offset_x = 34
reset_pin = 40
reset_state = "<display>.STATE_LOW"
backlight_pin = 46
backlight_on_state = "<display>.STATE_PWM"
color_space = "lv.COLOR_FORMAT.RGB565"
color_byte_order = "<display>.BYTE_ORDER_RGB"
rgb565_byte_swap = true

[<DISPLAY>.display.init]
params = []

[<TOUCH>.indev]                   # p. ej. AXS5106
device = "indev_device"
reset_pin = 47
touch_cal = "__import__('touch_fix').CAL"

[display.set_color_inversion]
params = [true]

[display.set_backlight]
params = [80]

[_thread.stack_size]              # solo para hilos creados DESPUÉS de import display (trampa 7)
params = [16384]

[task_handler.TaskHandler]
params = []
```

## Apéndice C — `mpconfigboard.h`, `sdkconfig.board`, `mpconfigboard.cmake`, `partitions.csv`

```c
// mpconfigboard.h
#ifndef MICROPY_HW_BOARD_NAME
#define MICROPY_HW_BOARD_NAME               "<Nombre> LVGL"
#endif
#define MICROPY_HW_MCU_NAME                 "ESP32-S3R8"
#define MICROPY_HW_ENABLE_UART_REPL         (1)            // trampa 5
#define MICROPY_TASK_STACK_SIZE             (32 * 1024)    // trampa 6
#define MICROPY_HW_I2C0_SCL                 (41)
#define MICROPY_HW_I2C0_SDA                 (42)
```
```
# sdkconfig.board  (16 MB, QIO 80 MHz, PSRAM octal; las dos líneas SPIRAM_FETCH/RODATA mueven código a PSRAM: quítalas si no hace falta)
CONFIG_FREERTOS_HZ=1000
CONFIG_ESP_DEFAULT_CPU_FREQ_MHZ_240=y
CONFIG_ESPTOOLPY_FLASHMODE_QIO=y
CONFIG_ESPTOOLPY_FLASHFREQ_80M=y
CONFIG_ESPTOOLPY_FLASHSIZE_16MB=y
CONFIG_SPIRAM_IGNORE_NOTFOUND=n
CONFIG_SPIRAM_SPEED_80M=y
CONFIG_SPIRAM_RODATA=y
CONFIG_SPIRAM_FETCH_INSTRUCTIONS=y
CONFIG_COMPILER_OPTIMIZATION_PERF=y
CONFIG_PARTITION_TABLE_CUSTOM=y
CONFIG_PARTITION_TABLE_CUSTOM_FILENAME="boards/<PLACA>_LVGL/partitions.csv"
```
```cmake
# mpconfigboard.cmake  (NO uses boards/sdkconfig.usb: no existe en este árbol)
set(IDF_TARGET esp32s3)
set(SDKCONFIG_DEFAULTS
    boards/sdkconfig.base ${SDKCONFIG_IDF_VERSION_SPECIFIC} boards/sdkconfig.ble
    boards/sdkconfig.spiram_sx boards/sdkconfig.spiram_oct boards/sdkconfig.240mhz
    boards/<PLACA>_LVGL/sdkconfig.board)
list(APPEND MICROPY_DEF_BOARD MICROPY_HW_BOARD_NAME="<Nombre> LVGL")
```
```
# partitions.csv  (sin OTA: la app LVGL ocupa ~3,1 MB; 6 MB de factory dejan margen)
nvs,      data, nvs,     0x9000,   0x6000,
phy_init, data, phy,     0xf000,   0x1000,
factory,  app,  factory, 0x10000,  0x600000,
vfs,      data, fat,     0x610000, 0x9F0000,
```

## Apéndice D — `manifest_user.py` y `touch_fix.py`

```python
# manifest_user.py: tus módulos propios (se SUMAN a los drivers de LVGL). Fuente única = ports/esp32/modules del firmware normal.
import os
_SRC = os.environ.get("MPY_USER_MODULES", os.path.expanduser("~/micropython/ports/esp32/modules"))
_STD = ("_boot.py", "machine.py", "flashbdev.py", "inisetup.py", "espnow.py", "apa106.py")   # los estándar los trae LVGL (otra versión): no pisarlos
_files = []
for _root, _dirs, _names in os.walk(_SRC):
    _dirs[:] = sorted(d for d in _dirs if d != "__pycache__" and not d.startswith("."))
    for _n in sorted(_names):
        _rel = os.path.relpath(os.path.join(_root, _n), _SRC)
        if _n.endswith(".py") and _rel not in _STD:
            _files.append(_rel)
freeze(_SRC, tuple(_files))                      # .py con ruta relativa, NO carpetas (trampa 15)
_HERE = os.environ.get("LVGL_BOARD_DIR")
if _HERE:
    freeze(_HERE, "touch_fix.py")
    freeze(os.path.join(_HERE, "..", "tested_modules"), ("board.py", "st7789.py", "lcd_<chip>.py", "touch_<chip>.py"))   # drivers directos (§6)
```
```python
# touch_fix.py: orientación del touch para pointer_framework (sin NVS)
MIRROR_X, MIRROR_Y, SWAP_XY = True, False, False
class _Cal:
    def __init__(self, mx, my, swap):
        self.alphaX, self.betaX = (0.0, 1.0) if swap else (1.0, 0.0)
        self.alphaY, self.betaY = (1.0, 0.0) if swap else (0.0, 1.0)
        self.deltaX = self.deltaY = 0.0
        self.mirrorX, self.mirrorY = mx, my
    def save(self): pass
CAL = _Cal(MIRROR_X, MIRROR_Y, SWAP_XY)
```
```python
# patch_lvgl_spi.py (resumen): quita las dos líneas "transaction->flags |= SPI_TRANS_USE_TXDATA/RXDATA;" que siguen a
# "transaction->tx_buffer = src + offset;" / "rx_buffer = dest + offset;" en micropy_updates/esp32/machine_hw_spi.c (idempotente, guarda .orig).
```

---
*Estado de esta guía (2026-11-03):* ✅ compilación, arranque, pantalla, touch (con `MIRROR_X`), WiFi, REPL por UART/USB y trampas 1–6, 8, 10, 13–15 y 18 confirmadas en la placa.
🔧 Sin validar en la placa (deducidas del código o corregidas sin reprobar): trampas 7, 9, 11, 12, 16 y 17 (compiladas y comprobadas dentro del binario; falta flashear el último `.bin`, quitar el `main.py` vacío y dejar correr minutos con WiFi),
y `board.spi()` en modo LVGL (sin error, resultado visual por confirmar). La SD sigue pendiente de una tarjeta válida.
