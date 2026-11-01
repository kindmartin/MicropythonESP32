# Base ESP32

Plantilla para proyectos MicroPython sobre el FW propio. Consolida lo común
de `New T190`, `Paddock S3` y `SUPER MINI S3`. El catálogo de módulos
congelados está en [CATALOGO_MODULOS_FW.md](CATALOGO_MODULOS_FW.md): revisarlo
antes de agregar librerías (muchas ya vienen en el FW).

## Archivos

| Archivo | Función |
|---|---|
| `boot.py` | Corre `startup_cleanup` → `startup_fallback` y fija hostname `<PREFIJO>-XXXX`. Editar `HOSTNAME_PREFIX`. |
| `startup_cleanup.py` | Con BOOT (GPIO0) presionado al arrancar borra `main.py` (recuperación). `BOOT_PIN` configurable. |
| `startup_fallback.py` | Sin `main.py` importa `wifiConnect` (WiFi + WebREPL + FTP) para subir código por red. |
| `r.py` / `d.py` / `p.py` / `w.py` | REPL: `import r` reinicia; `import d` deshabilita `main.py`; `import p` lo restaura; `import w` conecta WiFi. |
| `wifi_config.py` | Lista `NETWORKS` (ssid, password, ip estática opcional) para `wifiConnect`. |
| `ipaddress.cfg` | Red de último recurso: `ssid,password` y `ip,mask,gw,dns`. |
| `buttons.py` | `PageButton` / `InterruptPageButton`: gestos short, double, long, extra (activo-bajo, uasyncio). |
| `HW.py` | Pines y helpers (LED, botones). Lo único que cambia por placa. |
| `main.py` | App `uasyncio` en un `_thread`, REPL libre, botones opcionales. |

## Uso

1. Copiar todo (excepto los `.md`) a la raíz del ESP32.
2. Editar `HW.py` (`BOARD_NAME`, `USER_LED_PIN`, `BTN0_PIN`, `PAGE_BTN_PIN`),
   `HOSTNAME_PREFIX` en `boot.py`, y completar `wifi_config.py` /
   `ipaddress.cfg` (los valores `MI_SSID` / `MI_PASSWORD` son placeholders; no
   guardar claves reales en la plantilla).
3. Poner la lógica en `main.py` (`_app_task` y handlers `_gesture_handlers`).

Comandos REPL: `main.status()`, `main.stop()`, `main.start()`.

## Flujo de recuperación

- `main.py` bloquea el REPL: mantener BOOT al resetear → se borra `main.py`.
- Sin `main.py` el fallback conecta WiFi y deja FTP (puerto 21) + WebREPL
  para subir el código corregido.
- Para deshabilitar sin perder el archivo: `import d`; para volver, `import p`.

## Notas

- `wifiConnect` es el módulo **congelado** del FW (no está en esta carpeta) y
  bloquea hasta conectar; ver detalle en el catálogo.
- FTP y WebREPL quedan sin autenticación; ver "Duplicados y cuidados" del
  catálogo.
- `startup_cleanup`, `startup_fallback`, `d`, `p`, `r`, `w` existen también
  congelados; las copias locales permiten ajustarlos por proyecto.
