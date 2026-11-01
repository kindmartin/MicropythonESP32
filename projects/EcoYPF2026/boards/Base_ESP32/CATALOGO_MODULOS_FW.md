# Catálogo de módulos congelados en el FW propio

Fuente: `/home/martin/micropython/ports/esp32/modules` (congelado con
`freeze("$(PORT_DIR)/modules")` en `ports/esp32/boards/manifest.py`).
Los proyectos **no necesitan copiar** estos módulos al filesystem: ya están en
`.frozen`. Un archivo con el mismo nombre en `/` o `/lib` **tiene prioridad**
(el filesystem va antes que `.frozen` en `sys.path`), útil para parchear sin
reflashear.

Si cambia el contenido de `modules/`, actualizar este catálogo.

## Cómo lo usa la plantilla Base ESP32

| Archivo de la base | Depende del FW |
|---|---|
| `boot.py` | — (llama a `startup_cleanup` / `startup_fallback` locales) |
| `startup_fallback.py` | `wifiConnect` (congelado) |
| `w.py` | `wifiConnect` |
| `r.py` | `reset` |
| `wifi_config.py`, `ipaddress.cfg` | leídos por `wifiConnect` |
| `main.py` | `uasyncio` (asyncio congelado vía manifest) |

`startup_cleanup.py`, `startup_fallback.py`, `d.py`, `p.py`, `r.py`, `w.py`,
`ipaddress.cfg` también existen congelados con el mismo contenido (la base los
trae para poder editarlos por proyecto, p. ej. `BOOT_PIN`).

## Módulos de arranque y recuperación (raíz de `modules/`)

| Módulo | Qué hace | Uso |
|---|---|---|
| `_boot.py`, `flashbdev.py`, `inisetup.py` | Estándar de MicroPython: monta/formatea el FS en flash. | No tocar. |
| `r.py` / `reset.py` | `import r` → `machine.reset()`. | REPL: `import r` |
| `d.py` | Deshabilita `main.py` (→ `mainBkp.py`) y reinicia. | REPL: `import d` |
| `p.py` | Restaura `mainBkp.py` → `main.py` y reinicia. | REPL: `import p` |
| `startup_cleanup.py` | `run()`: si GPIO0 (BOOT) está en bajo al arrancar, borra `main.py`. | Llamado desde `boot.py` |
| `startup_fallback.py` | `run()`: si no hay `main.py`, importa `wifiConnect`. | Llamado desde `boot.py` |
| `wifiConnect.py` | Conecta WiFi al importarlo (ver detalle abajo). | `import w` / `import wifiConnect` |
| `wifiCfgExample.py` | Al importarlo **sobrescribe** `/ipaddress.cfg` con un ejemplo. | Solo para regenerar el cfg |
| `webrepl_cfg.py` | `PASS = ''` (WebREPL **sin contraseña**). | Definir clave en producción |

### `wifiConnect` (efecto al importar, no hay función `connect()`)

1. Activa STA, hostname `ESP-XXXX` (sufijo del `unique_id`).
2. Lee `wifi_config.NETWORKS` (lista de dicts `ssid`, `password`, opcionales
   `ip`, `netmask`, `gateway`, `dns`). Ordena por RSSI con `scan()` y prueba
   hasta 3 rondas (20 × 500 ms por red).
3. Si falla, usa la red de `/ipaddress.cfg` (línea 1 `ssid,password`, línea 2
   `ip,mask,gw,dns`; `#` comentario). Sin cfg → no intenta default.
   Ojo: si existe el cfg pero vacío, cae en los defaults del código
   (`iot` / IP `192.168.0.11`).
4. Fija IP estática si corresponde y espera IP válida.
5. Si conectó: `webrepl.start()` y `FtpTiny().start()` (servidores en threads).
   Imprime `WIFI connected: ssid=… rssi=… ip=… gw=…`.

Consecuencia: importarlo **bloquea** hasta 1–2 min si no hay red, y deja
FTP/WebREPL abiertos sin autenticación. En apps con `main.py` conviene
importarlo desde un thread o después del arranque crítico.

## Red y utilidades

| Módulo | Qué es | API principal |
|---|---|---|
| `espnow.py` | Wrapper de `_espnow` (`ESPNow` con `irecv`, `recv`, `irq`, iterable). | `e = espnow.ESPNow(); e.active(True)` |
| `ftp_thread.py` (= `netutils/ftp_thread.py`) | Servidor FTP mínimo en thread, puerto 21, PASV en 13333. Responde 230 al USER sin pedir clave (sin autenticación). | `FtpTiny().start()` / `.stop()` |
| `ftp.py` | Arranca `FtpTiny` al importar. | `import ftp` |
| `ftplib.py`, `ftpupload.py` | Cliente FTP (portado de CPython) y helper `upload(ftp, path, remote_path)`. | `ftpupload.upload(...)` |
| `uping.py` | Ping ICMP. | `ping(host, count=3, timeout=5000, interval=15, quiet=False, size=64)` |
| `ble_repl.py` | Puente REPL sobre BLE (Nordic UART, vía `dupterm`). | `start_ble_repl(name, rxbuf, dupterm_index, auto_dupterm, debug)` |
| `bleREPL.py` | Atajo de `ble_repl`; **arranca al importarlo**. | `import bleREPL`; `.start()`, `.stop()`, `.is_running()` |
| `machine.py` | Extiende `machine` con `Counter` y `Encoder` (PCNT del ESP32). Importa el `machine` nativo y agrega clases. | `machine.Counter(0, src=Pin(4))`, `machine.Encoder(0, a, b)` |
| `apa106.py` | `APA106(NeoPixel)` (LED RGB tipo APA106). | `APA106(Pin(n), 1)` |

## Subcarpetas

| Carpeta | Contenido |
|---|---|
| `drivers/` | `ssd1306.py` (`SSD1306_I2C`/`_SPI`), `sh1106.py` (`SH1106_I2C`/`_SPI`), `bmp180.py` (`BMP180`/`BMP085`: temperatura, presión, altitud), `mcp4725.py` (`MCP4725` DAC I2C). |
| `fonts/` | `seven_segment_24/40/80.py` (generados con `font_to_py`, API `get_ch`, `height`, …; para writer sobre display). |
| `lib/` | `ble_advertising.py` (`advertising_payload`), `ble_uart_peripheral.py` (`BLEUART`), `deque.py` (deque simple sobre lista), `delemain.py` (**borra `main.py` al importarlo**). |
| `netutils/` | `ap.py` (AP `ESP32_AP`/`12345678` + FTP), `BLE.py` (PoC REPL BLE, LED en GPIO2), `ftpServer.py`, `urequests.py` (cliente HTTP), más copias de `ftp_thread`, `ftplib`, `ftpupload`, `uping`, `webrepl_cfg`. |
| `fjs/` | Scripts personales de conexión (`iot.py`, `tlc.py`, `webrepl_cfg.py`) con **SSID/clave fijos en el código**. No usar como base. |

Para importar desde subpaquetes: `import netutils.ftp_thread`, `import netutils.urequests`,
`from drivers.ssd1306 import SSD1306_I2C`.

## Paquetes de micropython-lib incluidos (manifest)

`asyncio` (extmod), `bundle-networking` (incluye `urequests`/`requests`, `mip`,
`ntptime`, `webrepl`, etc.), `aioespnow`, `dht`, `ds18x20`, `neopixel`,
`onewire`, `umqtt.simple`, `umqtt.robust`, `upysh`.

## Duplicados y cuidados

- `ftp_thread`, `ftplib`, `ftpupload`, `uping` y `webrepl_cfg` están idénticos en la raíz y en
  `netutils/`; preferir `netutils.<mod>` en código nuevo.
- Hay dos `urequests`: `netutils/urequests.py` (propio) y el de `bundle-networking`.
  Para código portable usar `import requests`/`urequests` estándar.
- Seguridad: FTP sin autenticación, WebREPL con `PASS=''` y AP de `netutils/ap.py` con clave
  pública. Cambiar antes de dejar un equipo en una red no confiable.
- `ssd1306.py` usa `const()` sin importar: funciona porque está congelado (compilado con
  mpy-cross); si se copia al FS como `.py` hay que agregar `from micropython import const`.
- Drivers **no** congelados que usan los proyectos EcoYPF (copiar al FS): `st7789py`,
  `sx126x`/`sx1262`, `sdcard`, `drivers/ads1115`, `drivers/ads1220` — ver las carpetas
  `New T190`, `Paddock S3`, `SUPER MINI S3`.
