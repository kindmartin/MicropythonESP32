#!/bin/bash
# Prepara tu MicroPython local para compilar una placa de este repo.
#
#   scripts/install_board.sh <PLACA> [ruta_micropython] [--force] [--no-shared]
#
# Capas que instala:
#   1) boards/<PLACA>/mp_board/*   -> <mp>/ports/esp32/boards/<PLACA>/        (opciones de compilacion)
#   2) boards/<PLACA>/tested_modules/<los de frozen_modules.txt>
#                                  -> <mp>/ports/esp32/boards/<PLACA>/modules/ (drivers de la placa)
#   3) frozen/common/* + frozen/secrets.py
#                                  -> <mp>/ports/esp32/modules/                (tus modulos congelados +
#      tus credenciales; secrets.py NO esta en git. Si falta, se instala la plantilla con placeholders)
#
# OJO con 3): ports/esp32/modules/ es COMPARTIDO por todas las placas (lo congela boards/manifest.py).
# Se copia/sobrescribe archivo a archivo, sin borrar nada. --no-shared lo omite.
# ruta_micropython: argumento, o $MICROPYTHON_DIR, o ~/micropython.
set -e
REPO="$(cd "$(dirname "$0")/.." && pwd)"
BOARD="${1:?uso: $0 <PLACA> [ruta_micropython] [--force] [--no-shared]}"
FORCE=0; SHARED=1; MP=""
shift
for a in "$@"; do
    case "$a" in
        --force) FORCE=1 ;;
        --no-shared) SHARED=0 ;;
        *) MP="$a" ;;
    esac
done
MP="${MP:-${MICROPYTHON_DIR:-$HOME/micropython}}"

SRC="$REPO/boards/$BOARD"
DST="$MP/ports/esp32/boards/$BOARD"
[ -d "$SRC/mp_board" ] || { echo "No existe $SRC/mp_board"; exit 1; }
[ -d "$MP/ports/esp32/boards" ] || { echo "No parece un MicroPython: $MP"; exit 1; }
if [ -e "$DST" ] && [ $FORCE -eq 0 ]; then
    echo "Ya existe $DST. Usa --force para regenerarla (se reemplaza todo su contenido)."; exit 1
fi

# 1) + 2) carpeta de la board y sus drivers
rm -rf "$DST"
mkdir -p "$DST/modules"
cp "$SRC"/mp_board/* "$DST"/
while read -r f; do
    [ -z "$f" ] && continue
    cp "$SRC/tested_modules/$f" "$DST/modules/$f"
done < "$SRC/frozen_modules.txt"
echo "[1/3] Board instalada en $DST"
echo "[2/3] Drivers congelados de la placa: $(tr '\n' ' ' < "$SRC/frozen_modules.txt")"

# 3) modulos compartidos + credenciales (frozen/secrets.py)
if [ $SHARED -eq 1 ]; then
    mkdir -p "$MP/ports/esp32/modules"
    cp -r "$REPO"/frozen/common/. "$MP/ports/esp32/modules/"
    if [ -f "$REPO/frozen/secrets.py" ]; then
        cp "$REPO/frozen/secrets.py" "$MP/ports/esp32/modules/secrets.py"
        echo "[3/3] Modulos compartidos + secrets.py -> $MP/ports/esp32/modules/"
    else
        cp "$REPO/templates/secrets.example.py" "$MP/ports/esp32/modules/secrets.py"
        echo "[3/3] Modulos compartidos. AVISO: falta frozen/secrets.py -> se instalo la PLANTILLA con placeholders."
        echo "      Copia templates/secrets.example.py a frozen/secrets.py y completalo."
    fi
else
    echo "[3/3] Modulos compartidos omitidos (--no-shared)"
fi
echo "Compilar:  cd $MP/ports/esp32 && make BOARD=$BOARD   (ver boards/$BOARD/docs/README.md para la camara)"
