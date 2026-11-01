# Waveshare ESP32-S3-Touch-LCD-2 — Display secundario "fase 1"

**Rol:** segundo display del vehículo (igual rol que `ESP32 IdeaSpark 2nd display/`,
hardware distinto). Recibe por **ESP-NOW broadcast** la telemetría ya calculada por
el Super Mini (`super-mini-s3/`) y muestra las mismas 4 magnitudes "grandes" del
T190: potencia, velocidad, baterías y distancia. No duplica ningún cálculo, no
pairea, no manda nada por ESP-NOW — solo recepción + render.

**Alcance de esta primera versión:** display + recepción del broadcast del Super
Mini. "Info local" (IMU, batería propia ya incluida en el status row) queda
para una fase siguiente — ver §6. (Touch descartado: esta unidad es el SKU
"No Touch-No Camera", ver `README.md` §1.)

---

## 1. Por qué NO replica el protocolo de `ESP32 IdeaSpark 2nd display/`

La Ideaspark pairea con el **T190** (`T190_PAIR_REQ`/`T190_PAIR_ACK`), que es el
protocolo **viejo y descartado** — ver el comentario en `t190/espnow_link.py` (el
T190 "ya no manda telemetria a nadie por ESP-NOW"). El protocolo **actual** es:
el Super Mini mide/calcula todo, manda unicast al T190, y además difunde el mismo
frame `TLM:` por **broadcast** para displays secundarios de solo lectura, sin
pairing ni ACK (`send_telemetry_broadcast` en `super-mini-s3/espnow_link.py`, ver
`docs/ARQUITECTURA_TELEMETRIA_ECOYPF.md`).

Esta placa escucha ese broadcast directo — `espnow_link.py` de esta carpeta NO
pairea con nadie: solo recuerda la MAC del primer frame `TLM:` válido (para
filtrar ruido de otro emisor) y persiste esa memoria en `espnow_peer.bin`, sin
handshake. `repair()` la olvida.

## 2. Arquitectura de archivos

| Archivo | Rol |
|---|---|
| `board.py`, `st7789.py`, `cst816.py`, `qmi8658.py` | BSP ya frozen en el firmware (ver `README.md`), sin cambios |
| `espnow_link.py` | `EspNowLink` — receptor de solo lectura del broadcast del Super Mini (ver §1) |
| `telemetry.py` | `TelemetryRuntime` — mismo parseo VER=3 que `t190/telemetry.py`, sin la parte de reenvío LoRa (esta placa no tiene LoRa) |
| `seven_seg.py` | Renderizador de texto — ver §4, distinto del de `t190/seven_seg.py` |
| `buttons.py`, `d.py`, `p.py` | Copiados sin cambios de `ESP32 IdeaSpark 2nd display/` (mismo caso: un solo botón BOOT, sin combos) |
| `fonts/seven_segment_24/40/80.py` | Copiados sin cambios de `t190/fonts/` — datos de glifos, no dependen de la placa |
| `main.py` | App "REPL libre" — display + receptor ESP-NOW + 4 pantallas de valor + debug — ver §4 |
| `boot.py` | Hostname `WaveDisp-XXXX` + llama a `startup_cleanup`/`startup_fallback`, igual lógica que `t190/boot.py` |
| `startup_cleanup.py`, `startup_fallback.py` | Copiados sin cambios de `t190/` — genéricos, usan `machine.Pin(0, ...)` (mismo GPIO que `board.BOOT_PIN`) |
| `r.py`, `w.py` | Copiados sin cambios de `t190/` (`import reset` / `import wifiConnect` respectivamente) — ver §3 sobre por qué quedan así |
| `wifi_config.py`, `ipaddress.cfg` | Copiados sin cambios de `super-mini-s3/`, solo se cambió la IP a `192.168.0.28` siguiendo la secuencia de las demás placas (.25/.26/.27) — no la usa nada hoy, ver §3 |

**No se agregó `HW.py`:** `board.py` ya es el BSP autoritativo frozen en el
firmware (pines, constructores) — duplicar pines en un `HW.py` aparte arriesgaba
que se desincronicen. `main.py` usa `import board` directo.

## 3. `r.py`/`w.py` y por qué no se replica `wifiConnect.py`

`boot.py`, `r.py`, `d.py`, `p.py` y `w.py` replican la lógica actual del T190
(no la versión recortada que había quedado en `ESP32 IdeaSpark 2nd display/`,
donde `startup_cleanup`/`startup_fallback` no estaban conectados a `boot.py`).

- `r.py` (`import reset`) se copia tal cual pese a que `reset.py` **no existe
  en ningún lado del repo** — es una referencia colgante ya presente en
  `t190/r.py` (y en los demás tableros). Se mantiene por consistencia de
  estructura de carpeta, no porque sea funcional hoy.
- `w.py` (`import wifiConnect`) se copia igual, pero **`wifiConnect.py` no se
  replica**: ese módulo conecta a un AP Wi-Fi real con credenciales de
  `wifi_config.py` (ver `t190/wifiConnect.py`) — es infraestructura interna
  para los tableros que levantan un AP/servidor de configuración (T190,
  Paddock, Super Mini). Este display no necesita unirse a ningún Wi-Fi, solo
  ESP-NOW (`network.WLAN(STA_IF).active(True)`, sin `connect()`), así que
  `wifiConnect.py` quedaría sin uso. Si alguna vez se invoca `w.py` desde el
  REPL, el `import wifiConnect` falla con `ImportError` sin romper nada (no
  está en ningún `try/except` que dependa de él salvo `startup_fallback.py`,
  que ya atrapa ese error).
- `wifi_config.py`/`ipaddress.cfg` son copia directa de `super-mini-s3/`
  (plantilla placeholder `YOUR_SSID_HERE`/`YOUR_PASSWORD_HERE`), cambiando
  solo la IP a `192.168.0.28` (siguiente libre en la secuencia .25/.26/.27
  de las demás placas). **No** se copiaron las credenciales reales que
  tiene `ESP32 IdeaSpark 2nd display/wifi_config.py` (ver nota aparte en la
  conversación sobre ese archivo).

## 4. Por qué `seven_seg.py` es distinto al de las otras placas

El driver `st7789.py` de esta placa **no tiene framebuffer propio ni método
`text()`** (a diferencia de `drivers/tft170.py` del T190/Ideaspark, que envuelve
un `framebuf.FrameBuffer` y expone `.text()`/`.blit()`): solo expone
`blit_buffer(buf, x, y, w, h)`, que escribe un buffer RGB565 directo por SPI
(ver README §3).

- Para los valores grandes (fuentes `seven_segment_*`), `seven_seg.draw_text()`
  arma el glifo como `bytearray` plano (igual lógica que `t190/seven_seg.py`,
  pero sin pasar por `framebuf.FrameBuffer`) y lo manda con `blit_buffer`.
- Para prosa corta (filas de estado/pie, sin fuente propia) se agregó
  `seven_seg.text()`: usa el framebuf 8x8 **integrado** de MicroPython sobre un
  buffer chico (`framebuf.FrameBuffer(..., framebuf.RGB565)`) y lo manda con el
  mismo `blit_buffer` — mismo truco que usa el driver del T190 internamente.
  `framebuf.RGB565` ya guarda los píxeles en big-endian, igual que arma
  `draw_text()` a mano, así que **no debería** hacer falta swap de bytes para
  ninguno de los dos caminos — a confirmar en hardware real (ver §6).

## 5. Pantallas

Botón único (BOOT, GPIO0, `board.button()`):
- **corto** → siguiente pantalla (POTENCIA → VELOCIDAD → BATERIAS → DISTANCIA → …)
- **largo** → pantalla de DEBUG (estado ESP-NOW crudo, payload, batería propia) / otra larga vuelve a las pantallas de valor

Las 4 pantallas de valor usan el mismo lenguaje visual que `t190/main.py`
(`_draw_big_value_page`): fila de estado (link ESP-NOW + batería propia), código +
valor grande + unidad, grupo/etiqueta, fila de pie (frescura del origen + índice
de pantalla). Las lecturas vienen directo del frame `TLM:` del Super Mini — sin
`settings.py` ni acumulados de viaje propios (eso vive solo en el T190).

Desde el REPL: `main.status()`, `main.repair()`, `main.next_field()` /
`main.prev_field()` (sin botón físico), `main.toggle_debug()`.

## 6. Próximos pasos (info local — fase 2)

1. Probar en hardware real: orientación/offset del panel (el propio `README.md`
   marca el ST7789 como heredado del driver 1.9" y sin verificar), y el byte
   order de `seven_seg.text()` (si el texto sale con colores invertidos/corridos,
   revisar ahí primero).
2. Probar la recepción end-to-end con el Super Mini real emitiendo el broadcast
   (confirmar que ese firmware trae `espnow` compilado, mismo riesgo que ya
   documentó el T190).
3. ~~Touch como alternativa o complemento al botón BOOT para paginar~~ --
   **descartado**: esta unidad es el SKU "No Touch-No Camera" (ver nota en
   `README.md` §1), confirmado en banco (`i2c.scan()` no encuentra el
   CST816D) y contra el esquemático oficial. El botón BOOT sigue siendo la
   única entrada.
4. IMU (`board.imu()`) para datos propios sin depender del Super Mini (ej.
   inclinación, aceleración) — info "local" que no viene por ESP-NOW.
5. Si el T190 llega a emitir un segundo broadcast (GPS, "modo activado", etc. —
   ver conversación de diseño), este receptor necesita distinguirlo por un
   prefijo nuevo (no reusar `TLM:`, que es del Super Mini) y una pantalla extra.
