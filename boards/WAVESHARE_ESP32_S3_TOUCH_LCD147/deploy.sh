#!/bin/bash
# Sube a la placa (firmware LVGL de la Touch-LCD-1.47) los ejemplos y tests: /raw (sin LVGL), /lvgl (con LVGL) y use.py en la raiz.
# Los DRIVERS no se suben: vienen congelados en el firmware. Uso: ./deploy.sh [puerto]   (por defecto /dev/ttyUSB0; cerrar screen antes)
set -e
PORT="${1:-/dev/ttyUSB0}"
HERE="$(cd "$(dirname "$0")" && pwd)"
M="python3 $HOME/micropython/tools/mpremote/mpremote.py connect $PORT"
$M fs mkdir :raw 2>/dev/null || true
$M fs mkdir :lvgl 2>/dev/null || true
echo "== raiz: use.py + README.md"; $M fs cp "$HERE/use.py" :use.py; $M fs cp "$HERE/DEVICE_README.md" :README.md
echo "== /raw (sin LVGL)"
for f in "$HERE"/tested_modules/tests/*.py "$HERE"/tested_modules/examples/*.py; do $M fs cp "$f" :raw/$(basename "$f"); done
$M fs cp "$HERE/tested_modules/DEVICE_README.md" :raw/README.md
echo "== /lvgl (con LVGL)"
for f in "$HERE"/lvgl/tests/*.py "$HERE"/lvgl/examples/*.py; do [ "$(basename "$f")" = main.py ] && continue; $M fs cp "$f" :lvgl/$(basename "$f"); done   # main.py (vacio) no se sube
$M fs cp "$HERE/lvgl/DEVICE_README.md" :lvgl/README.md
$M fs ls : ; $M fs ls :raw ; $M fs ls :lvgl
echo; echo "listo. En el REPL:  import use; use.raw()  o  use.lvgl()"
