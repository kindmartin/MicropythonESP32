# eBike2026 — Heltec Vision Master T190
## Documentación del proyecto

---

## 1. Hardware — Heltec Vision Master T190

### MCU
- **ESP32-S3R8** — 384 KB ROM, 512 KB SRAM, 16 MB Flash, 16 MB PSRAM
- WiFi 802.11 b/g/n, BLE 5.0, Bluetooth Mesh
- **Sin DAC analógico** (a diferencia del ESP32 clásico que tenía 2 canales en GPIO25/26)
- Deep sleep: 18 µA

### Display integrado
- **1.9" TFT-LCD** — Panel N190-1732TBWPG01-C30
- Resolución: **170 (RGB) × 320** pixels
- Colores: 262K (RGB565 / 18-bit)
- Controlador: **GC9107** (compatible ST7789 subset)
- Interfaz: 4-wire SPI (pines internos, no en headers)
- Backlight driver: AW9364DNR (controlado por GPIO17)
- Alimentación display: MOSFET AO3401 (GPIO7, LOW = encendido)

### Pines internos del display (NO en headers)

| Señal | GPIO | Función |
|---|---|---|
| TFT_MOSI | 48 | TFT_SDA — datos SPI |
| TFT_SCK | 38 | TFT_SCL — clock SPI |
| TFT_CS | 39 | Chip select |
| TFT_DC | 47 | TFT_RS — Data/Command |
| TFT_RST | 40 | Reset display |
| TFT_BL | 17 | LEDK_EN — backlight |
| TFT_PWR | 7 | VTFT_Ctrl — alimentación display |

### Pines disponibles en headers

**Header J3 (derecho):**

| Pin físico | GPIO | Alternativas |
|---|---|---|
| J3-1 | 5V | Alimentación entrada |
| J3-3 | GPIO12 | ADC2_CH11, TOUCH12, LoRa_RST |
| J3-4 | GPIO11 | ADC2_CH10, TOUCH11, LoRa_MISO |
| J3-5 | GPIO10 | ADC1_CH9, TOUCH10, LoRa_MOSI |
| J3-6 | GPIO9 | ADC1_CH8, TOUCH9, LoRa_SCK |
| J3-7 | GPIO8 | ADC1_CH7, TOUCH8, LoRa_NSS |
| J3-8 | GPIO4 | ADC1_CH3, TOUCH4 |
| J3-9 | GPIO3 | ADC1_CH2, TOUCH3 |
| J3-10 | GPIO2 | ADC1_CH1, TOUCH2, **QL_SDA** |
| J3-11 | GPIO1 | ADC1_CH0, TOUCH1, **QL_SCL** |
| J3-12 | 3V3 | Salida regulada |

**Header J2 (izquierdo):**

| Pin físico | GPIO | Alternativas |
|---|---|---|
| J2-1 | 3V3 | Salida regulada |
| J2-4 | VEXT | 3.3V conmutable (GPIO5 = Ve_Ctrl) |
| J2-5 | GPIO13 | ADC2_CH2, TOUCH13, LoRa_BUSY |
| J2-6 | GPIO14 | ADC2_CH3, TOUCH14, LoRa_DIO1 |
| J2-7 | GPIO15 | ADC2_CH4, 32K_P |
| J2-8 | GPIO16 | ADC2_CH5, 32K_N |
| J2-9 | GPIO44 | **U0_RXD** — UART0 RX |
| J2-10 | GPIO43 | **U0_TXD** — UART0 TX |

### GPIOs internos reservados

| GPIO | Función |
|---|---|
| 5 | Ve_Ctrl (VEXT enable) |
| 6 | VBAT_Read ADC + ADC_Ctrl |
| 7 | VTFT_Ctrl (display power) |
| 17 | LEDK_EN (backlight) |
| 18 | TP_INT (touch interrupt) |
| 21 | **USER_KEY S3** — único botón de usuario, pull-up 10K |
| 38 | TFT_SCK |
| 39 | TFT_CS |
| 40 | TFT_RST |
| 41 | TP_RST |
| 42 | TP_SCL (touch I2C) |
| 45 | TP_SDA (touch I2C) |
| 47 | TFT_DC |
| 48 | TFT_MOSI |
| 0 | BOOT button S2 |
| 43 | UART0 TX |
| 44 | UART0 RX |

### Botones del T190

| Botón | GPIO | Función |
|---|---|---|
| S1 | CHIP_PU | Reset hardware |
| S2 | GPIO0 | Boot mode |
| S3 | GPIO21 | **Único botón de usuario** — pull-up 10K, activo-bajo |

### Alimentación del T190

- USB Type-C (hasta 5V/2A)
- LiPo 1.25mm × 2 pin (3–4.2V) — cargador LGS4056H integrado
- Medición batería: GPIO6 (ADC, divisor R9=390K / R11=100K → factor 4.9)
- VEXT conmutable: GPIO5 controla salida 3.3V para sensores externos

### QuickLink I2C (conector SH1.0-4P P3)

| Pin | Señal | GPIO |
|---|---|---|
| 1 | QL_SCL | GPIO1 |
| 2 | QL_SDA | GPIO2 |
| 3 | GND | — |
| 4 | Ve_3V3 | VEXT conmutable |

---

## 2. Asignación de pines para eBike2026

### Definición actual en HW.py

| Función | GPIO | Conector | Notas |
|---|---|---|---|
| **Phaserunner UART TX** | GPIO4 | J3-8 | UART1 |
| **Phaserunner UART RX** | GPIO3 | J3-9 | UART1 |
| **ADC Throttle** | GPIO4 | J3-8 | ⚠ Conflicto con PR_TX — revisar |
| **ADC Brake** | GPIO2 | J3-10 | QL_SDA — revisar si se usa I2C |
| **I2C SCL** (DAC) | GPIO1 | J3-11 | QL_SCL |
| **I2C SDA** (DAC) | GPIO2 | J3-10 | QL_SDA |
| **Trip counter** | GPIO8 | J3-7 | LoRa_NSS si hay LoRa |
| **Botón PAGE** | GPIO21 | interno | USER_KEY S3 |
| **UP/DOWN ADC** | GPIO9 | J3-6 | LoRa_SCK si hay LoRa |
| **VBAT ADC** | GPIO6 | interno | Solo lectura |

> ⚠ **Pendiente resolver conflictos de pines** antes de conectar hardware:
> - GPIO4 asignado a PR_TX y ADC_Throttle simultáneamente — elegir uno
> - GPIO2 asignado a ADC_Brake y I2C_SDA simultáneamente — elegir uno
> - Si se usa LoRa: GPIO8, 9, 10, 11, 12, 13, 14 están ocupados

### Asignación sugerida sin LoRa (pines LoRa liberados)

| Función | GPIO recomendado | Justificación |
|---|---|---|
| PR UART TX | GPIO10 | J3-5, libre sin LoRa |
| PR UART RX | GPIO11 | J3-4, libre sin LoRa |
| ADC Throttle | GPIO4 | J3-8, ADC1_CH3 |
| ADC Brake | GPIO3 | J3-9, ADC1_CH2 |
| I2C SCL (MCP4725) | GPIO1 | J3-11, QL_SCL |
| I2C SDA (MCP4725) | GPIO2 | J3-10, QL_SDA |
| Trip counter | GPIO8 | J3-7 |
| Botón PAGE | GPIO21 | USER_KEY S3 |

---

## 3. Control de motor

### Lectura de señales (ADC)
- Throttle y brake son señales analógicas 0–3.3V
- El ESP32-S3 tiene ADC de 12-bit (0–4095)
- Misma lógica que el proyecto original: sin cambios en `motor_control.py`

### Salida de señales — DAC externo MCP4725

El **ESP32-S3 NO tiene DAC analógico** (el ESP32 clásico tenía GPIO25/26).
Solución: **2× MCP4725** (mismo que el proyecto original), conectados por I2C:

| Chip | Dirección I2C | Canal |
|---|---|---|
| MCP4725 #1 | 0x60 | Throttle DAC → entrada throttle del Phaserunner |
| MCP4725 #2 | 0x61 | Brake DAC → entrada brake del Phaserunner |

- Resolución: 12-bit (0–4095)
- Salida: 0–3.3V (referencia = VDD del chip)
- Bus I2C: GPIO1 (SCL) + GPIO2 (SDA) @ 400 kHz
- El código `motor_control.py` original se reutiliza **sin cambios**

---

## 4. Phaserunner — Modbus RTU

### Comunicación directa en el S3 (sin ESP32 offload)

En el proyecto original se usó un segundo ESP32 "offload" para manejar el Modbus. **Con el ESP32-S3 esto NO es necesario:**
- El S3 corre `uasyncio` con mayor estabilidad que el ESP32 clásico
- El worker de Phaserunner corre como tarea asyncio directamente
- UART1 disponible en los headers (GPIO10/GPIO11 si se libera LoRa)

### Puerto TRRS del Phaserunner V6

| Pin TRRS | Señal |
|---|---|
| Tip | TX (salida del Phaserunner) |
| Ring 1 | RX (entrada al Phaserunner) |
| Ring 2 | **5V** (nuevo en V6, no presente en V2) |
| Sleeve | GND |

**Niveles lógicos: 0–5V TTL.**
El ESP32-S3 opera a **3.3V** — se necesita divisor resistivo o level shifter en la línea TX del Phaserunner → RX del S3 si el nivel es realmente 5V (verificar en hardware).

### Registros Modbus disponibles (PR_REGISTERS)

| Registro | Dirección | Unidad |
|---|---|---|
| vehicle_speed | 260 | km/h |
| battery_voltage | 265 | V |
| battery_current | 266 | A |
| motor_input_power | 334 | W |
| controller_temp | 259 | °C |
| motor_temp | 261 | °C |
| motor_current | 262 | A |
| motor_rpm | 263 | RPM |
| soc | 267 | % |
| faults | 258 | bitmap |
| throttle_voltage | 270 | V |
| brake_voltage_1 | 271 | V |
| (+ 20 registros más) | | |

---

## 5. Alimentación del T190 en la bici

### El problema
- Batería de la bici: **21S LiPo** = 88.2V llena / 75.6V vacía
- Este voltaje supera el límite de la mayoría de buck converters comunes (75V max)
- El 5V del TRRS del Phaserunner existe pero **su corriente máxima no está documentada**; fue diseñado para futuros dongles BT (~20–50 mA), insuficiente para el T190

### Consumo del T190

| Modo | Corriente |
|---|---|
| Idle + display | ~80–100 mA |
| + WiFi activo | ~150–200 mA |
| + LoRa TX 20dBm | ~200–220 mA |
| Deep sleep | ~18 µA |

### Solución recomendada — Buck converter HV

Usar un regulador buck que soporte Vin hasta 100V:

| Chip/módulo | Vin máx | Iout | Disponibilidad |
|---|---|---|---|
| **MP4560** | 100V | 1A | AliExpress ~$3 |
| **LM5017** (TI) | 100V | 600 mA | Digikey/LCSC |
| **XL7015** | 80V | 300 mA | AliExpress ~$1 — límite justo para 21S |

Buscar: `"MP4560 DC DC 100V to 5V step-down module"` o `"HV buck 90V 5V 1A module"`

### Esquema de conexión

```
Batería 21S (88V)
      │
  Buck HV 100V→5V/1A   (MP4560 o similar)
      │
  USB-C del T190        ← opción A: directo
      │   ó
  LiPo 1.25mm del T190  ← opción B: con celda 18650 de buffer
```

### Alternativa: celda LiPo buffer + carga lenta desde PR

Si se acepta el riesgo de corriente limitada del PR TRRS:
```
PR TRRS 5V (corriente desconocida, ~100mA?)
      │
  Puerto LiPo 1.25mm T190 (cargador LGS4056H integrado)
      │
  Celda 18650 (3.7V, 2500mAh)  ← alimenta el T190 directamente
```
El T190 tiene autonomía propia y el PR solo carga la celda mientras la bici está encendida.

---

## 6. Firmware — Estado actual

### Archivos creados en `T190/`

| Archivo | Estado | Descripción |
|---|---|---|
| `HW.py` | ✅ Creado | Mapa de pines T190 + helpers |
| `drivers/tft170.py` | ✅ Creado | Driver GC9107/ST7789 170×320 |
| `drivers/__init__.py` | ✅ Creado | Package marker |
| `boot.py` | ✅ Creado | Arranque mínimo + hostname |
| `main.py` | ✅ Creado | Display + botón S3 cicla pantallas |

### Funcionalidad del main.py actual

- Enciende el display (GPIO7 LOW + SPI init)
- Renderiza 5 pantallas de prueba con colores y texto
- Botón S3 (GPIO21, polling asyncio 30ms) cicla entre pantallas
- Arquitectura: `uasyncio` con tasks independientes
- Fuente: framebuf.text() 8×8px (provisional — agregar fuentes 7-seg después)

### Para subir al T190

```bash
# Con mpremote:
mpremote cp boot.py :
mpremote cp main.py :
mpremote cp HW.py :
mpremote mkdir :drivers
mpremote cp drivers/tft170.py :drivers/
mpremote cp drivers/__init__.py :drivers/

# O con Thonny: copiar los 5 archivos directamente
```

### Nota sobre offset del display (GC9107)

El controlador GC9107 en el panel 170×320 tiene un offset interno en su frame buffer.
Valor configurado: `x_offset=0, y_offset=35` (rotation 0, portrait).
Si la imagen aparece desplazada verticalmente al probar en hardware, ajustar `y_offset`
en `drivers/tft170.py` líneas del dict `_ROTATION`.

---

## 7. Próximos pasos planificados

| Paso | Descripción | Dependencia |
|---|---|---|
| 1 | **Validar display** — verificar que enciende y el offset es correcto | Hardware físico |
| 2 | **Resolver conflictos de pines** en HW.py (throttle/brake vs I2C vs UART) | Definir cableado |
| 3 | **Agregar fuentes 7-segmentos** — copiar de proyecto original | Paso 1 ok |
| 4 | **Conectar MCP4725** (×2) al I2C, probar salida DAC | Hardware |
| 5 | **Conectar Phaserunner** — UART directo, test Modbus | Hardware + level shifter |
| 6 | **Worker Phaserunner asyncio** — leer registros en loop | Paso 5 ok |
| 7 | **Dashboard principal** — velocidad + potencia + batería en display | Pasos 3+6 ok |
| 8 | **Motor control** — integrar motor_control.py + MCP4725 | Pasos 4+6 ok |
| 9 | **Batería app state** — SOC, guard, pack config | Paso 6 ok |
| 10 | **Alimentación definitiva** — buck HV o LiPo buffer | Hardware |

---

## 8. Módulos del proyecto original a reutilizar

| Módulo | Reutilizable | Cambios necesarios |
|---|---|---|
| `motor_control.py` | ✅ Directo | Solo adaptar pines en HW.py |
| `bats.py` | ✅ Sin cambios | — |
| `phaserunner/` (todos) | ✅ Sin cambios | Solo cambiar pines UART |
| `fonts/` (todos) | ✅ Sin cambios | — |
| `UI_helpers/writer.py` | ✅ Sin cambios | — |
| `runtime/rtc_snapshot.py` | ✅ Sin cambios | — |
| `runtime/tasks.py` | ✅ Con ajustes | Quitar referencias a offload ESP32 |
| `buttons.py` | ✅ Solo PageButton | UpDownButtons: revisar pin ADC |
| `drivers/mcp4725.py` | ✅ Sin cambios | — |
| `app_state.py` | ✅ Con ajustes | Quitar campos alarm/GPS/cellular |
| `drivers/lcd1p69.py` | ❌ No aplica | Reemplazado por `drivers/tft170.py` |
| `drivers/axp192.py` | ❌ No aplica | T190 no tiene AXP192 |
| `CellularLte/` | ❌ Excluido | Sin cellular en este proyecto |
| `gnss.py` | ❌ Excluido | Sin GPS |
| `alarm_mode.py` | ❌ Excluido | Depende de cellular |
| `runtime/phaserunner_worker.py` | ⚠ Reescribir | Eliminar bridge MSP, Modbus directo |
