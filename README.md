# MicropythonESP32

Proyectos con el puerto ESP32 de MicroPython: definiciones de board para compilar, drivers ya probados y
los proyectos que los usan.

## Flujo de trabajo (3 capas)

1. **Placa** (`boards/<PLACA>/`): elijo la placa y veo sus opciones especificas de compilacion
   (`mp_board/`: sdkconfig, particiones, pines, manifest) y los drivers ya probados (`tested_modules/`).
2. **Modulos congelados** (`frozen/`): mis modulos compartidos por todas las placas (`frozen/common/`, publicos).
   Mis credenciales estan en **un solo archivo**, `frozen/secrets.py`, que **no se versiona** y se congela en el fw.
3. **Proyecto** (`projects/<PROYECTO>/boards/<DISPOSITIVO>/`): los scripts del proyecto para cada ESP32
   (uno o varios por proyecto). Cada dispositivo indica que placa usa (`device.json`).

## Estructura

```
boards/<PLACA>/              una carpeta por placa
├── mp_board/                la carpeta COMPLETA para compilar (va a ports/esp32/boards/<PLACA>/)
├── tested_modules/          .py especificos de la placa, ya probados (drivers) + tests/ + examples/
├── frozen_modules.txt       cuales de tested_modules se congelan en el firmware
├── lvgl/  firmware/  docs/  variante LVGL, binarios probados + BUILD.md, README y fotos

frozen/
├── common/                  modulos congelados compartidos (publicos; leen las claves de secrets.py)
└── secrets.py               TUS credenciales (gitignored; plantilla en templates/secrets.example.py)

projects/<PROYECTO>/
├── docs/                    arquitectura, funcionalidades, PDFs
└── boards/<DISPOSITIVO>/    un ESP32 por carpeta + device.json

scripts/install_board.sh     prepara tu MicroPython local (las 3 capas de arriba)
templates/                   plantillas sin credenciales
```

## Compilar una placa

```bash
scripts/install_board.sh WAVESHARE_ESP32_S3_TOUCH_LCD_2 ~/micropython   # --force si ya existe
cd ~/micropython/ports/esp32 && make BOARD=WAVESHARE_ESP32_S3_TOUCH_LCD_2
```

`install_board.sh` copia: la board + sus drivers (los de `frozen_modules.txt`), y `frozen/common/` + `frozen/secrets.py`
a `ports/esp32/modules/`, **que comparten todas las placas**. Usa `--no-shared` para omitir esto.
Lo que congelas queda dentro del `.bin`: **no publiques firmwares compilados con tu `secrets.py` real**.

## Placas

| Placa | Estado | Notas |
|---|---|---|
| [WAVESHARE_ESP32_S3_TOUCH_LCD_2](boards/WAVESHARE_ESP32_S3_TOUCH_LCD_2/docs/README.md) | LCD, IMU, vbat, camara OV2640 y video probados | SD y touch pendientes; variante LVGL en `lvgl/` |

## Proyectos

| Proyecto | Dispositivos |
|---|---|
| [EcoYPF2026](projects/EcoYPF2026/README.md) | T190, SuperMini_S3, Paddock_S3, Heltec_V2_Rx, Base_ESP32, Waveshare_S3_LCD2_display |

## Credenciales (equipo nuevo)

1. `git clone` de este repo.
2. Copia **un archivo**: tu `frozen/secrets.py` (o `cp templates/secrets.example.py frozen/secrets.py` y completalo).

`secrets.py` define `WIFI_SSID`, `WIFI_PASS`, `TLC_SSID`, `TLC_PASS` y `WEBREPL_PASS`; `wifiConnect.py`, `webrepl_cfg.py` y
`fjs/*` lo importan. Si falta, el instalador deja la plantilla con placeholders y avisa. `wifi_config.py`, `ipaddress.cfg`
y similares por proyecto tampoco se versionan (ver `.gitignore` y `templates/`).
