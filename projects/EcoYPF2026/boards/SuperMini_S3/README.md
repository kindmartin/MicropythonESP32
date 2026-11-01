# Super Mini S3 — Nodo de sensores y métricas

**Hardware:** ESP32-S3 Super Mini  
**Rol:** adquisición de datos y cálculo de todas las métricas de tracción.
El T190 no recalcula nada; el Super Mini es la fuente de verdad.

Para la documentación completa de funcionalidades ver
[`../FUNCIONALIDADES.md`](../FUNCIONALIDADES.md).  
Para cambios de diseño pendientes ver
[`../New T190/CONTINUACION_DESARROLLO.md`](../New%20T190/CONTINUACION_DESARROLLO.md).

## Sensores

| Sensor | Interfaz | GPIO |
|---|---|---|
| ADS1115 (tensiones B1–B4, taps acumulativos) | I2C | SCL=12 / SDA=13 |
| ADS1220 + Hall toroidal (corriente) | SPI1 | SCK=4 / MOSI=1 / MISO=2 / CS=3 |
| Pulsos de velocidad | IRQ | GPIO10, pull-up |
| LED NeoPixel (estado) | GPIO | 48 |

## Archivos principales

| Archivo | Rol |
|---|---|
| `main.py` | App completa (hilo de fondo, REPL libre) |
| `HW.py` | Pinout y fábricas de buses |
| `config.py` | Carga y validación de `config.json` |
| `config.json` | Calibración: ratios divisor, sensibilidad Hall, metros/pulso |
| `espnow_link.py` | Pairing y TX/RX ESP-NOW con el T190 |
| `status_led.py` | Control del NeoPixel por estado de sensores |
| `drivers/ads1115.py` | Driver ADS1115 (I2C, 4 canales single-ended) |
| `drivers/ads1220.py` | Driver ADS1220 (SPI, 24 bit) |

## REPL rápido

```python
status()                    # snapshot compacto
values(10)                  # dashboard prolijo, 10 s
diag()                      # scan I2C + estado de cada sensor
calibrate_current_zero()    # calibrar offset corriente (con I=0)
reload_config()             # recargar config.json sin detener
dump_config()               # ver config activa
espnow_status()             # estado del enlace con T190
debug(True)                 # stream continuo de lecturas
```

## Calibración

1. **Ratios de divisor** (`battery.tap_divider_ratio`): cuatro valores en
   `config.json`. Ajustar si las tensiones medidas no coinciden con el
   multímetro. El canal A1 (B1+B2 ≈ 24 V) tiene margen de saturación muy
   pequeño con VDD = 3.3 V — si el ADS1115 satura, revisar los ratios o
   el cableado.
2. **Factores gruesos B1–B4** (`battery.voltage_factor_milli`): ajuste
   adicional por banco; 1000 = sin corrección. Configurables desde la
   página del AP del T190 (se envían por ESP-NOW como `CFG`).
3. **Metros por pulso** (`speed.meters_per_pulse`): 0.1 m/pulso
   provisional. Medir una distancia conocida, contar pulsos, calcular el
   cociente y guardar en `config.json`. Recargar con `reload_config()`.
4. **Offset de corriente**: llamar `calibrate_current_zero()` con el
   vehículo en reposo (corriente nula) una vez por sesión o después de
   reiniciar el ADS1220.
