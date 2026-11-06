#!/bin/bash
# Compila el firmware LVGL de esta placa. Uso: ./build.sh [lvgl_micropython_dir]
# No modifica ninguna otra board de este repo.
# make.py usa como nombre de board el NOMBRE DE LA CARPETA de --custom-board-path, y mpconfigboard.cmake
# referencia boards/<BOARD>/sdkconfig.board: por eso se compila desde una copia temporal con ese nombre
# (esta carpeta se llama "lvgl" y no coincidiria).
set -e
BOARD=WAVESHARE_ESP32_S3_TOUCH_LCD147_LVGL
HERE="$(cd "$(dirname "$0")" && pwd)"
LVGL_DIR="${1:-$HOME/lvgl_micropython}"
STAGE="$(mktemp -d)/$BOARD"
mkdir -p "$STAGE"
cp "$HERE"/board.json "$HERE"/mpconfigboard.h "$HERE"/mpconfigboard.cmake "$HERE"/sdkconfig.board \
   "$HERE"/partitions.csv "$HERE"/*.toml "$STAGE"/
cd "$LVGL_DIR"
# Parche a lvgl_micropython: SPI.Device.write() de >4 bytes falla (SPI_TRANS_USE_TXDATA con tx_buffer). Ver patch_lvgl_spi.py
python3 "$HERE/patch_lvgl_spi.py" "$LVGL_DIR/micropy_updates/esp32/machine_hw_spi.c"
# make.py no las propaga a CMake en modo --custom-board-path
export GEN_SCRIPT=python
export LV_PORT=esp32
# make.py tampoco pasa FROZEN_MANIFEST al make (esp_cmd.extend(extra_args) esta comentado): sin esto el firmware sale SIN los
# drivers Python (jd9853, axs5106, i2c, task_handler, display.py). make lee las variables del entorno.
export LVGL_BOARD_DIR="$HERE"      # manifest_user.py congela touch_fix.py desde aqui
export FROZEN_MANIFEST="$LVGL_DIR/build/manifest.py"
# INDEV=axs5106 a mano: toml_reader no registra el import del touch cuando solo aparece en un parametro ("axs5106.I2C_ADDR"),
# y sin esto el driver del touch no se congela (display.py haria "import axs5106" y fallaria al arrancar).
# FROZEN_MANIFEST como argumento de make.py = manifest del usuario (se suma a los drivers de LVGL): ver manifest_user.py
python3 make.py esp32 BOARD=$BOARD --custom-board-path="$STAGE" INDEV=axs5106 FROZEN_MANIFEST="$HERE/manifest_user.py"
