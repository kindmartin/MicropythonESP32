# Como se compilo el firmware del T190 (HELTEC T190 LORA LCD)

Datos **leidos del directorio de build real** (`~/micropython/ports/esp32/build-ESP32_HELTECLORALCD`, 2026-04-10) y de los archivos de
la placa, no reconstruidos de memoria. Lo que no se pudo comprobar esta marcado como **(sin verificar)**.

## 1. Resumen
| Dato | Valor |
|---|---|
| Placa MicroPython | `ESP32_HELTECLORALCD` (`board.json`: product "HELTEC T190 LORA LCD", mcu `esp32s3`) |
| Version del binario | **MicroPython v1.27.0-dirty**, compilado el **2026-04-10** ("Machine: ESP32S3 module (spiram octal)") |
| ESP-IDF | **5.5.1** (`CONFIG_IDF_INIT_VERSION`), python env `idf5.5_py3.12_env` |
| Comando | `cd ports/esp32 && make BOARD=ESP32_HELTECLORALCD`  (cmake: `-DMICROPY_BOARD=ESP32_HELTECLORALCD -DMICROPY_BOARD_DIR=.../boards/ESP32_HELTECLORALCD -DCCACHE_ENABLE=0`; **sin** `BOARD_VARIANT`, **sin** `USER_C_MODULES`, **sin** `FROZEN_MANIFEST`) |
| Manifest | el de la placa **no existe** -> `boards/manifest.py` por defecto (congela `ports/esp32/modules/` + asyncio + `bundle-networking` + aioespnow, dht, ds18x20, neopixel, onewire, umqtt, upysh) |
| Flash / PSRAM | 16 MB, PSRAM **octal** 80 MHz, CPU 240 MHz |
| Consola | UART0 (115200) + USB-Serial/JTAG secundario (no TinyUSB) |
| Binario | `firmware.bin` 1 814 912 B, `micropython.bin` 1 749 376 B (en abril) |

## 2. Archivos de la placa (`mp_board/`, tal cual se compilo)
`board.json`, `mpconfigboard.h` (nombre "ESP32S3 module (spiram octal)", `UART_REPL=1`, I2C0 SCL=9 / SDA=8), `mpconfigboard.cmake`, `sdkconfig.board`, `partitions-16MB.csv`.
El `mpconfigboard.cmake` se modifico el 10/04 a las 13:24, **antes** del build (13:32-13:38): es el mismo que se uso.

## 3. Inconsistencias / trampas (importantes para reproducir)
1. **`partitions-16MB.csv` NO se uso.** `sdkconfig.board` fija `CONFIG_PARTITION_TABLE_FILENAME` (simbolo derivado) y deja comentado `CUSTOM_FILENAME`;
   el sdkconfig final quedo con `CUSTOM_FILENAME="partitions-4MiBplus.csv"`. La tabla real (decodificada de `partition-table.bin`):
   `nvs 0x9000 24K`, `phy_init 0xf000 4K`, `factory 0x10000 1984K`. El **resto de la flash (~14 MB) es el sistema de archivos** (asi lo
   define `partitions-4MiBplus.csv`: "the remaining flash is for the user filesystem"). **Sin OTA.** El firmware ocupaba ~1,7 MB de los 1984 KB.
2. **`mpconfigboard.cmake` referencia archivos que ya no existen:** `boards/sdkconfig.usb` (eliminado de MicroPython el 2025-11-12, ya no esta en v1.27.0)
   y `boards/sdkconfig.spiram_sx` (existe en v1.27.0; **renombrado a `sdkconfig.spiram_quad` el 2026-06-04**, ya no existe en 1.29).
   En v1.27.0 el build tolero el archivo ausente; **con MicroPython 1.29 el build falla** ("file failed to open for reading ... sdkconfig.usb").
3. **`sdkconfig.board` usa simbolos dudosos:** `CONFIG_FLASHMODE_QIO` (el de IDF es `CONFIG_ESPTOOLPY_FLASHMODE_QIO`), `CONFIG_ESPTOOLPY_FLASHSIZE_DETECT`.
   Efecto comprobado en el sdkconfig final: `FLASHSIZE_16MB=y`, `AFTER_NORESET=y` (por eso el `flash_args` termina con `--after no_reset`), `FLASHFREQ=80m`,
   `flash_args` con `--flash_mode dio`. **(sin verificar)** si el modo QIO se aplica en ejecucion.
4. **"-dirty":** el binario dice `v1.27.0-dirty`: el arbol tenia cambios en archivos **rastreados** que no se pueden recuperar. El tag `v1.27.0` existe en el clon
   local de `~/micropython`.
5. **No es reproducible bit a bit:** lo congelado en abril incluia `boot.py`, `main.py`, `fjs/*`, `wifiConnect.py`, `webrepl_cfg.py` (con **credenciales reales**) que ya
   no estan asi; hoy esos modulos se reparten en `frozen/common/` + `frozen/secrets.py`.

## 4. Modulos congelados en ese build (72 archivos `.py`)
`aioespnow, apa106, asyncio/*, ble_repl, bleREPL, boot, _boot, dht, drivers/{bmp180,mcp4725,sh1106,ssd1306,sim7600/*}, ds18x20, espnow, fjs/{iot,tlc,webrepl_cfg},
flashbdev, ftplib, ftp, ftp_thread, ftpupload, inisetup, lib/{ble_advertising,ble_uart_peripheral,delemain,deque}, machine, main, mip, neopixel,
netutils/{ap,BLE,ftplib,ftpServer,ftp_thread,ftpupload,uping,urequests,webrepl_cfg}, ntptime, onewire, requests, reset, ssl, uasyncio, umqtt/{robust,simple},
uping, upysh, urequests, webrepl, webrepl_setup, wifiCfgExample, wifiConnect`.
Atencion: `boot.py` y `main.py` **van congelados** (un `main.py` congelado no se puede borrar del FS) y `fjs/*`, `wifiConnect`, `webrepl_cfg` llevan claves.

## 5. Reproducir con el mismo MicroPython (v1.27.0)
```bash
git clone https://github.com/micropython/micropython.git ~/micropython_127 && cd ~/micropython_127
git checkout v1.27.0 && git submodule update --init --recursive && make -C mpy-cross
# ESP-IDF 5.5.1 cargado:  . $IDF_PATH/export.sh   (el build usa el python env de IDF 5.5)
cp -r <repo>/boards/ESP32_HELTECLORALCD/mp_board ports/esp32/boards/ESP32_HELTECLORALCD
# modulos compartidos: copiar a ports/esp32/modules/ (de <repo>/frozen/common + tu frozen/secrets.py)
cd ports/esp32 && make BOARD=ESP32_HELTECLORALCD
```

## 6. Compilar con MicroPython 1.29 (cambios necesarios en `mpconfigboard.cmake`)
- Quitar la linea `boards/sdkconfig.usb`.
- Cambiar `boards/sdkconfig.spiram_sx` por `boards/sdkconfig.spiram_quad` (y se mantiene `boards/sdkconfig.spiram_oct` debajo, que fija el modo octal).
- Decidir la tabla de particiones: o se deja la por defecto (1984 KB + FS de ~14 MB, como en abril) o se apunta de verdad a `partitions-16MB.csv`
  con `CONFIG_PARTITION_TABLE_CUSTOM_FILENAME="boards/ESP32_HELTECLORALCD/partitions-16MB.csv"`.
**(sin verificar)**: este cambio no se ha compilado.

## 7. Flasheo (imagen completa a offset 0; datos de `flash_args`)
```bash
python -m esptool --chip esp32s3 -p <PUERTO> -b 460800 --before default_reset --after hard_reset write_flash \
  --flash_mode dio --flash_freq 80m --flash_size 16MB 0x0 build-ESP32_HELTECLORALCD/firmware.bin
# equivalente por partes: 0x0 bootloader/bootloader.bin  0x8000 partition_table/partition-table.bin  0x10000 micropython.bin
```

## 8. El .bin de abril
Esta en el equipo original: `~/micropython/ports/esp32/build-ESP32_HELTECLORALCD/firmware.bin` (1,8 MB, 2026-04-10). **No esta en el repo** (lleva claves congeladas y el repo
es publico): copialo por `scp`/USB al otro host si lo necesitas.

## 9. Pendiente de verificar en el hardware
- Tabla de particiones real en el dispositivo: `import esp32; [p.info() for p in esp32.Partition.find(esp32.Partition.TYPE_APP)]` y `os.statvfs('/')` (esperado ~14 MB libres).
- Si la placa necesita el `main.py`/`boot.py` congelados o los de la carpeta `projects/EcoYPF2026/boards/T190/`.
