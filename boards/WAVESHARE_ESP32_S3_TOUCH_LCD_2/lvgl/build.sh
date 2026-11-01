#!/bin/bash
# Compila el firmware LVGL de esta placa. Uso: ./build.sh [lvgl_micropython_dir]
# No modifica ninguna otra board de este repo. El .toml de esta carpeta lo toma
# make.py automaticamente (--custom-board-path).
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
LVGL_DIR="${1:-$HOME/lvgl_micropython}"
cd "$LVGL_DIR"
# make.py no las propaga a CMake en modo --custom-board-path
export GEN_SCRIPT=python
export LV_PORT=esp32
python3 make.py esp32 BOARD=WAVESHARE_ESP32_S3_TOUCH_LCD_LVGL --custom-board-path="$HERE"
