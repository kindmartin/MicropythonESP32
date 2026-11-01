# Firmware probado — Waveshare ESP32-S3-Touch-LCD-2 (fase 1, con camara)

**No hay .bin en el repo todavia.** El `firmware.bin` del 27/10 se compilo *antes* de los ultimos cambios
(`board.py`, `st7789.py` sin BGR, `sdcard` congelado): no reproduce lo probado. Hay que recompilar y
guardar aqui el .bin con su SHA256.

## Versiones usadas
| Componente | Version |
|---|---|
| MicroPython | 0fd6c573e (v1.29.0) |
| ESP-IDF | v5.5.2 |
| micropython-camera-API | 8df3f70 (esp32-camera 32a7654) |

## Compilar (con IDF cargado: `. $IDF_PATH/export.sh`)
```bash
scripts/install_board.sh WAVESHARE_ESP32_S3_TOUCH_LCD_2 ~/micropython --force
cd ~/micropython/ports/esp32
make BOARD=WAVESHARE_ESP32_S3_TOUCH_LCD_2 \
  CMAKE_ARGS="-DUSER_C_MODULES=$HOME/micropython-camera-driver/micropython.cmake -DEXTRA_COMPONENT_DIRS=$HOME/micropython-camera-driver"
```

## Flashear (imagen completa, offset 0)
```bash
python -m esptool --chip esp32s3 -p /dev/ttyUSB0 -b 460800 write_flash 0x0 build-WAVESHARE_ESP32_S3_TOUCH_LCD_2/firmware.bin
```
El REPL de este firmware sale por UART (`/dev/ttyUSB0`), no por USB nativo.

## Al guardar un .bin aqui
Anota fecha, `sha256sum` y los commits de arriba.
