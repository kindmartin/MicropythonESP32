# EcoYPF 2026 — telemetria del vehiculo

Documentacion: [docs/ARQUITECTURA_TELEMETRIA_ECOYPF.md](docs/ARQUITECTURA_TELEMETRIA_ECOYPF.md),
[docs/FUNCIONALIDADES.md](docs/FUNCIONALIDADES.md) y los PDFs (reglamento, arquitectura v0.9, instrumentacion).

## Dispositivos (`boards/`)

| Carpeta | Rol |
|---|---|
| `T190/` | Medidor de potencia (LilyGo T-Display?). `T190/original/` = version de referencia previa |
| `SuperMini_S3/` | ESP32-S3 Super Mini: calcula la telemetria y la emite por ESP-NOW |
| `Paddock_S3/` | Receptor en el paddock |
| `Heltec_V2_Rx/` | Receptor LoRa Heltec V2 |
| `Base_ESP32/` | Base comun de modulos (ver `CATALOGO_MODULOS_FW.md`) |
| `Waveshare_S3_LCD2_display/` | Segundo display: Waveshare ESP32-S3-Touch-LCD-2. Definicion de la placa en `/boards/WAVESHARE_ESP32_S3_TOUCH_LCD_2/` |
| `Agus_ESP32_original/` | Version original de referencia |

Los nombres y roles de la tabla salen de los nombres de carpeta y de `PROYECTO_WAVESHARE.md`: revisalos.

## Credenciales
Copia `/templates/wifi_config.example.py` como `wifi_config.py` en cada dispositivo (no se versiona).
