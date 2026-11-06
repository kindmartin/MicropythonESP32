# /lvgl — ejemplos CON LVGL

Uso:  `import use; use.lvgl()` y luego `import <nombre>`.   `lvb.py` (ayudante) importa `display`: LVGL inicializa pantalla y touch.
No uses `board.lcd()` / `board.touch()` en este modo (SPI e I2C ocupados por LVGL).

| Archivo | Que hace |
|---|---|
| `app` | app de 3 paginas que se cambian DESLIZANDO: UI, FEATURES (chequeos + Repetir) y TOUCH. `app.stop()` para parar |
| `features` | pantalla de estado con chequeos + touch interactivo (BOOT sale) |
| `ui_demo` | slider de brillo, barra de bateria, temperatura, switch de inversion, boton |
| `test_all` | corre los tests en orden |
| `test_display` / `test_backlight` / `test_touch` / `test_battery` / `test_temp` / `test_sd` / `test_button` | tests por periferico |
| `lvb.py` | ayudante: `lvb.screen()`, `lvb.label()`, `lvb.vbat()`, `lvb.sd_mount()`, `lvb.touch_orient()` |

Touch espejado: ya corregido en el firmware (`touch_fix.MIRROR_X = True`). Para probar otra orientacion sin recompilar:
`lvb.touch_orient(mirror_x=..., mirror_y=..., swap=...)`.
