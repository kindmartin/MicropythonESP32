# Notas de traspaso para otras sesiones (Waveshare ESP32-S3 + MicroPython)

Resumen de lo aprendido al sacar adelante la **Waveshare ESP32-S3-Touch-LCD-2** (firmware con camara, LCD, IMU, bateria,
video con horizonte). Sirve como punto de partida para compilar firmware de **otras placas Waveshare** y para no repetir
errores. Escrito el 2026-11-02. Si algo de aqui contradice lo que ves en el hardware, manda el hardware: actualiza esta nota.

> **Regla de oro de esta sesion:** nada de esto estaba escrito en la web del producto. Los pines salieron del ZIP de demos
> oficial; los ejes del IMU, el espejo del LCD y el orden de color se midieron en la placa. **Mide, no supongas.**

---

## 1. Como trabaja el usuario (preferencias)

- Idioma: **espanol**. Respuestas directas; para decisiones reales, 2-3 opciones con una recomendacion.
- **El flasheo lo hace el usuario.** No ejecutes `machine.bootloader()` ni `esptool write_flash` por tu cuenta (lo rechazo una vez):
  da los comandos listos (con la ruta del python del IDF y el puerto) y espera confirmacion. Subir `.py` por `mpremote` y correr tests si esta bien.
- **Compilar el firmware lo hace el usuario** en su shell (tiene ESP-IDF cargado); en la sesion de Claude `idf.py` no esta en el PATH.
  Excepcion: `lvgl_micropython` usa su propio IDF y si se pudo compilar desde la sesion.
- **Push a GitHub solo con su OK explicito.** Los commits locales si se pueden hacer (identidad ya configurada en el repo: `kindmartin <kindmartin@gmail.com>`).
- Suele tener **`screen` abierto en `/dev/ttyUSB0`** (REPL por UART). Mientras este abierto **no se puede usar el puerto desde la sesion**
  (`fuser -v /dev/ttyUSB0`). Pidele que lo cierre (`Ctrl-A` y luego `\`) y dale el comando para copiar/ejecutar.
- Valora que le expliques **por que** algo falla, y las verificaciones hechas (que se probo y que no). Di siempre "probado en la placa" vs "solo compila/simulado".
- No imprimas archivos con credenciales (ver seccion 7).

## 2. Entorno y rutas (equipo de trabajo del usuario)

| Que | Ruta / dato |
|---|---|
| Repo propio (este) | `~/MicropythonESP32`  ->  `github.com/kindmartin/MicropythonESP32` (**publico**; se recomendo pasarlo a privado) |
| MicroPython local | `~/micropython` (v1.29.0, commit `0fd6c573e`; remoto `origin` = upstream, sin permisos de escritura) |
| ESP-IDF | `~/esp-idf` (v5.5.2); python del IDF: `~/.espressif/python_env/idf5.5_py3.12_env/bin/python` |
| Driver de camara | `~/micropython-camera-driver` (`cnadler86/micropython-camera-API`, commit `8df3f70`, submodulo `esp32-camera` `32a7654`) |
| LVGL | `~/lvgl_micropython` (usa su propio MicroPython e IDF 5.5.1 en `lib/`) |
| mpremote | **no esta instalado**: `python3 ~/micropython/tools/mpremote/mpremote.py connect /dev/ttyUSB0 ...` |
| mpy-cross | `~/micropython/mpy-cross/build/mpy-cross` (para codigo `@micropython.viper` usar `-march=xtensawin`) |
| Respaldo previo a instalar | `~/respaldo_micropython_antes_de_instalar.tar.gz` (**contiene credenciales**, permisos 600) |
| Clave SSH para el push | `~/.ssh/id_ed25519_mpyesp32` (deploy key del repo, con escritura; `core.sshCommand` solo en el repo) |
| Memoria de Claude | `~/.claude/projects/-home-martin-micropython/memory/` (`feedback_flash_by_user.md`, `waveshare-s3-touch-lcd-2-board.md`) |

## 3. Estructura del repo (3 capas)

```
boards/<PLACA>/
  mp_board/         carpeta COMPLETA para compilar (va a ports/esp32/boards/<PLACA>/): board.json, mpconfigboard.{h,cmake},
                    sdkconfig.board, partitions*.csv, manifest.py
  tested_modules/   .py de la placa ya probados (drivers) + tests/ + examples/
  frozen_modules.txt   cuales de tested_modules se congelan en el firmware
  lvgl/  firmware/  docs/   variante LVGL, binarios + BUILD.md, README y fotos
frozen/common/      modulos congelados COMPARTIDOS por todas las placas (publicos)
frozen/secrets.py   credenciales (gitignored). Plantilla: templates/secrets.example.py
projects/<PROYECTO>/boards/<DISPOSITIVO>/   scripts de cada ESP32 de un proyecto (EcoYPF2026 ya migrado)
scripts/install_board.sh   prepara tu ~/micropython para compilar una placa
```

`scripts/install_board.sh <PLACA> [~/micropython] [--force] [--no-shared]` copia `mp_board/` + los drivers de `frozen_modules.txt` a
`ports/esp32/boards/<PLACA>/` y `frozen/common/` + `secrets.py` a `ports/esp32/modules/` (**compartido por todas las placas**; copia sin borrar).
`--force` **regenera la carpeta de la placa borrando lo que hubiera dentro**: haz respaldo antes.

Los modulos que se congelan salen de `ports/esp32/modules/` (via `boards/manifest.py`) **y** de `<board>/modules/` (via el `manifest.py` de la placa).
No metas en ellos `boot.py` ni credenciales por descuido: quedan dentro del `.bin`.

## 4. Checklist para una placa Waveshare nueva

1. **Pines**: la pagina web NO los lista (solo una imagen). Descarga el ZIP de demos del wiki (`docs.waveshare.com/<PRODUCTO>` -> *Resources*)
   y lee los `.ino` / `main.c` (busca `PIN_NUM`, `EXAMPLE_PIN`, `#define ... GPIO`). **Pide permiso al usuario antes de descargar**; extrae en una carpeta nueva y vacia.
   Cruza con el diagrama del header (el usuario puede pasar una captura).
2. **Chip y memoria**: sufijo `R8` = PSRAM octal de 8 MB (`sdkconfig.spiram_oct`); `R2` = quad. Tamano de flash de la ficha (16 MB tipico).
3. Copia la carpeta `mp_board/` de una placa parecida (`boards/WAVESHARE_ESP32_S3_TOUCH_LCD_2/`) y ajusta nombre, pines y `board.json`.
   `sdkconfig.board`: QIO 80 MHz, `FLASHSIZE_16MB`, PSRAM octal, tabla de particiones propia (`partitions-16MB.csv`: 2 OTA de 3 MB + FAT ~10 MB).
4. **Display**: ST7789 / ST7796 / etc. Reusa `st7789.py` (parametros `x_offset`, `y_offset`, `invert`, `bgr`). Los paneles con recorte (1,9" -> 170x320) necesitan offsets.
5. **Touch / IMU / SD**: confirma con `i2c.scan()` (el CST816 **duerme** y no aparece hasta que lo tocas) y con tests minimos.
6. Escribe/copia **tests por periferico** (`tests/test_*.py`: lcd, backlight, touch, imu, sd, vbat, button, camera) y corrilos en la placa.
7. `scripts/install_board.sh <PLACA> ~/micropython --force`, comprueba con `mpy-cross` que los `.py` compilan y **pide al usuario** compilar y flashear.
8. Verifica en la placa que lo congelado coincide (`import secrets, st7789, board` sin archivos copiados).
9. Documenta en `boards/<PLACA>/docs/README.md` (pines, hallazgos, trampas) y haz commit local.

Placas ya existentes en `~/micropython/ports/esp32/boards/` **sin migrar todavia al repo**: `WAVESHARE_ESP32_S3_LCD147B`, `WAVESHARE_ESP32_S3_LCD19`
(tienen `st7789.py`, `qmi8658.py`, `test_*.py` propios), `ESP32_HELTECLORALCD`, `XIAO_S3`. Buen primer candidato para reutilizar los drivers de esta.

## 5. Waveshare ESP32-S3-Touch-LCD-2: datos comprobados

ESP32-S3R8 (16 MB flash, 8 MB PSRAM octal), LCD 2" ST7789T3 240x320 SPI (sin pin RST), touch CST816D (I2C 0x15), IMU QMI8658 (0x6B),
TF en modo SPI, camara OV2640/OV5640 (24 pines DVP), conector de bateria con divisor 1/3. **Nota del usuario**: esta unidad podria ser el SKU
"No Touch-No Camera" (`PROYECTO_WAVESHARE.md`): la camara SI funciona (OV2640); el **touch nunca se confirmo** (no aparece en el scan).

| Funcion | GPIO |
|---|---|
| LCD SCK / MOSI / MISO | 39 / 38 / 40 (SPI id 1, **compartido con la SD**) |
| LCD CS / DC / BL | 45 / 42 / 1 (BL con PWM 5 kHz; sin RST) |
| SD CS | 41 |
| I2C0 SDA / SCL | 48 / 47 (touch + IMU) |
| Bateria | 5 (ADC1_CH4, V = Vadc x 3) |
| BOOT | 0 |
| Camara XCLK/PCLK/VSYNC/HREF | 8 / 9 / 6 / 4 |
| Camara D0..D7 | 12, 13, 15, 11, 14, 10, 7, 2 |
| Camara SIOD/SIOC/PWDN | 21 / 16 / 17 |
| REPL UART (fase 1) | TX 43 / RX 44 -> `/dev/ttyUSB0` |

Header de 28 pines: 47/48 (I2C), 43/44 (UART), 19/20 (USB nativo) y los pines de la camara quedan libres si no usas la camara; solo el GPIO18 no lo usa nadie.

### Ejes del IMU (QMI8658), medidos con lecturas reales
Placa apaisada y video derecho: **+x = tu izquierda, +y = arriba, +z = hacia dentro de la pantalla** (plana con pantalla arriba: az = -0,97 g).
El acelerometro lee +1 g en el eje que apunta hacia arriba. Gravedad en tu vista: `dx = +ax`, `dy = +ay`.

### Video / camara / display (probado, ~24 fps)
- `R240X240` RGB565 arriba + franja libre 240x80 abajo; SPI del LCD a 40 MHz (a 80 MHz no gana nada: manda la camara, ~25 fps).
- La camara entrega RGB565 **big-endian**, justo lo que espera el ST7789: **se envia sin procesar**. Orden de bytes mal = mosaico psicodelico.
- El driver del LCD **no debe activar el bit BGR** de MADCTL (`bgr=False`); con BGR el rojo sale azul-turquesa.
- El driver aplica **MADCTL MX (espejo en x)**: la camara lo compensa con `set_hmirror(True)` y `overlay.Overlay._p()` con `MIRROR_X = True`.
  Sin esto el overlay sale volteado en vertical (y parece que "cierra" otro modo del IMU).
- Tras `cam.reconfigure()` descarta **2 frames** (el primero es del tamano anterior). La camara se puede crear directamente en el modo deseado.
- `capture()` devuelve un `memoryview`: pasalo tal cual a `lcd.blit_buffer` (un `bytes(data)` copia 150 KB y baja de 25 a 10 fps).
- Rotar 90 grados por software (viper, bloques 2x2 de 32 bit) cuesta ~16 ms para 240x240 (~16 fps en total). Mejor no rotar: gira el video con
  `hmirror/vflip` y la orientacion fisica de la placa.
- Overlay (`examples/overlay.py`): horizonte tipo avion (verde a +-5 grados), arco de alabeo, escala vertical de cabeceo, flechas de giro (giroscopio), bateria.
  **BOOT corto = cero** (se guarda en `/imu_zero.txt`), **BOOT largo = salir**. `video.run()` se puede repetir.
- Signos aun **sin confirmar en la placa**: `PITCH_SIGN = +1` y `GZ_SIGN = -1` (deducidos de las lecturas, ver `overlay.py`).

## 6. Trampas conocidas y como resolverlas

| Sintoma | Causa / solucion |
|---|---|
| `mpremote: could not enter raw repl` + traceback de `netutils/ftp_thread.py` | Un hilo FTP (de `boot.py` -> `startup_fallback` -> `wifiConnect`) se cae en bucle y llena el REPL. Crear un `main.py` **vacio** y reiniciar (`import r`). Si el REPL queda raro, enviar `\x03\x03` y `\x02` por pyserial. |
| `mpremote fs cp` falla con `SyntaxError: invalid \x escape` | Pasa con algunos binarios. Reintentar tras 2-3 s, o volcar por texto (base64 con CRC por linea y **muestreo reducido**: volcar 150 KB por UART pierde datos). |
| `machine.SDCard(spi=...)` -> `extra keyword arguments given` | En este puerto no admite `spi=` (crea su propio bus). Usar `sdcard.py` de micropython-lib sobre el **mismo** `machine.SPI` que el LCD (`require("sdcard")` en el manifest). Bus compartido a 20 MHz; poner el CS del LCD en alto antes. |
| La SD monta y lee pero **las escrituras no persisten** | Probado con `sdcard.py` y con `machine.SDCard` nativo (slot 2): igual. Sospecha: tarjeta protegida contra escritura. **Sin resolver**: probar con otra tarjeta. |
| `import st7789` -> `no module named` tras reflashear | El firmware viejo no lo congelaba y el archivo del FS no sobrevive a un cambio de particiones/borrado. Copiarlo, o recompilar con el driver congelado. |
| El CST816 no aparece en `i2c.scan()` | Duerme hasta que lo tocan. Escanear **mientras se toca**. Sin pin de reset/IRQ en el demo. Tolerar `OSError` en `read()`. |
| Ctrl-C no corta `video.py` en `screen` | Causa no determinada. `video.py` sale con **BOOT largo** o la tecla `q`. Comprobar que `screen` no esta en modo copia (`Ctrl-A [`). |
| `esptool` no resetea la placa a bootloader | Con el USB nativo (CDC de TinyUSB) no hay auto-reset: mantener BOOT, pulsar RST y soltar. Por el puente UART (`/dev/ttyUSB0`) si funciona. |
| `--after no_reset` en el comando de `make` | Para scripts de flasheo usar `hard_reset` (o `no_reset` solo si se quiere seguir en modo descarga). Imagen completa: `write_flash 0x0 build-<PLACA>/firmware.bin`. |
| `pkill -f "mpremote ..."` mata tu propia shell | El patron coincide con la linea de comando del propio shell. Usar el PID de `fuser -v <puerto>`. |
| El firmware sale **con claves WiFi dentro** | Lo congelado va en el `.bin`: `frozen/secrets.py`, `wifiConnect.py`, `fjs/*`. **No publicar `.bin`** compilados con credenciales reales. `*.bin` / `*.elf` / `*.uf2` estan en `.gitignore` (regla anadida el 2026-11-05: antes **no** estaba y un `.bin` con claves casi se sube). |
| `lvgl_micropython` con `--custom-board-path`: build falla o sale sin drivers | (1) La plantilla `MY_CUSTOM_BOARD` referencia `boards/sdkconfig.usb` que no existe: quitarla. (2) `make.py` **no propaga** `GEN_SCRIPT`/`LV_PORT` (exportarlos como variables de entorno) **ni `FROZEN_MANIFEST`**: el firmware sale **sin los drivers Python** (`st7789`, `cst816s`, `i2c`, `task_handler`...). Pendiente: exportar `FROZEN_MANIFEST=$LVGL_DIR/build/manifest.py` en `lvgl/build.sh` y recompilar. |
| Al probar `display.py` de LVGL la placa entro en bucle de reinicios (`rst:0x1 POWERON`) | Causa sin determinar (alimentacion del USB o inicializacion del panel). Se recupero con BOOT+RST y reflasheando. |

## 7. Seguridad y credenciales

- Credenciales en **un solo archivo**: `frozen/secrets.py` (gitignored). `wifiConnect.py`, `webrepl_cfg.py` y `fjs/*` lo importan (con respaldo de placeholders).
- Quedan fuera del repo: `wifi_config.py`, `ipaddress.cfg`, `wifi.cfg`, `netb.py`, `backup_original_*/`, `.venv`, `*.zip`, `*.bin`.
- Antes de cada commit: buscar las contrasenas reales en todo lo que git subiria (`git ls-files --cached --others --exclude-standard`) **sin imprimirlas**.
  Cuidado con los formatos CSV (`ipaddress.cfg`): un `sed` mal hecho **imprimio una clave WiFi en el log de esta sesion**.
- Hay dos `webrepl_cfg.py` extra (`fjs/` y `netutils/`) con una clave escrita; se congelan en el `.bin` y no estan en el repo.

## 8. Tecnicas de verificacion sin hardware (utiles, reutilizables)

- `mpy-cross -o /dev/null archivo.py` (con `-march=xtensawin` si usa `@micropython.viper`): detecta errores de sintaxis antes de gastar 25 min de build.
- **Simular `framebuf` con PIL** (`line/rect/ellipse/poly`) para ver el overlay y comprobar geometria; simular el espejo del LCD (`FLIP_LEFT_RIGHT`) y la rotacion de la vista.
- **Mock de `run()`** en CPython (camara, LCD, boton, IMU, stdin falsos) para cazar errores de alcance/logica; redirigir archivos del dispositivo (`/imu_zero.txt`) a un temporal.
- Para decidir formatos (orden de bytes, RGB/BGR) **decodificar un frame real de todas las formas y compararlo** con el JPEG de la misma escena.
- Medir antes de optimizar (`test_camera_fps.py`: captura vs envio al LCD por separado).

## 9. Estado al cierre de la sesion y pendientes

- Firmware de fase 1 con camara compilado y flasheado por el usuario (2026-11-02) con `secrets.py` y los drivers congelados (lo que se compilo; **no se verifico en la placa**
  despues de flashear: comprobar `import secrets, st7789, board`). `video.run()` funciono con versiones anteriores del overlay; la ultima
  (escala de cabeceo, cero con BOOT, horizonte verde a +-5) **no se ha probado en la placa**.
- **Commits locales sin push** en `~/MicropythonESP32` (el usuario debe dar el OK): `9d71bcb` (estructura), `6c2008a`, `48d86e7`, `7cbf19c`, `986609b` (video/overlay).
  Este archivo (`docs/NOTAS_PARA_SESIONES.md`) tampoco esta commiteado.
- Sin hacer: recompilar un firmware "dorado" y guardarlo en `boards/WAVESHARE_ESP32_S3_TOUCH_LCD_2/firmware/` con su SHA256 (ver `BUILD.md`); migrar al repo las otras placas;
  arreglar `lvgl/build.sh` (FROZEN_MANIFEST); resolver SD; confirmar touch; decidir visibilidad del repo; completar `device.json` de los demas dispositivos de EcoYPF2026.
- En el repo local hay cosas del usuario sin seguimiento (`tested_modules/fotos/`, `tested_modules/tests/board.py`) y `examples/bench_rot.py` aparece borrado en su copia
  de trabajo: no tocarlos sin preguntar.

## 10. Comandos utiles

```bash
# estado del puerto
fuser -v /dev/ttyUSB0
# copiar y ejecutar (con screen cerrado)
M="python3 ~/micropython/tools/mpremote/mpremote.py connect /dev/ttyUSB0"
$M fs cp archivo.py :archivo.py ; $M exec "import video; video.run()"
# preparar y compilar una placa (el usuario compila; necesita IDF cargado)
~/MicropythonESP32/scripts/install_board.sh WAVESHARE_ESP32_S3_TOUCH_LCD_2 ~/micropython --force
cd ~/micropython/ports/esp32 && make BOARD=WAVESHARE_ESP32_S3_TOUCH_LCD_2 \
  CMAKE_ARGS="-DUSER_C_MODULES=$HOME/micropython-camera-driver/micropython.cmake -DEXTRA_COMPONENT_DIRS=$HOME/micropython-camera-driver"
# flasheo (lo ejecuta el usuario); imagen completa a offset 0
~/.espressif/python_env/idf5.5_py3.12_env/bin/python -m esptool --chip esp32s3 -p /dev/ttyUSB0 -b 460800 write_flash 0x0 build-<PLACA>/firmware.bin
```
