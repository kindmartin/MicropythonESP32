# /raw — ejemplos SIN LVGL (drivers directos)

Uso:  `import use; use.raw()` y luego `import <nombre>`.   NO importes `display` (es LVGL y se queda con el SPI/I2C).

| Archivo | Que hace |
|---|---|
| `test_all` | corre todos los tests en orden (touch, SD y boton piden accion) |
| `test_lcd` | colores, barras y marco de la pantalla |
| `test_backlight` | brillo por PWM (GPIO46) |
| `test_touch` | touch AXS5106L: punto verde donde tocas (10 s) |
| `test_touch_raw` | bytes crudos + nivel de INT (diagnostico del touch) |
| `test_vbat` | bateria GPIO12 (x3); sin bateria ~0 V |
| `test_temp` | temperatura del chip |
| `test_sd` | microSD por SDMMC 4 bits (FAT32) |
| `test_button` | boton BOOT |
| `features` | todo en una pantalla de estado + touch interactivo (BOOT sale) |

API (modulo `board`, congelado): `board.lcd()`, `board.backlight(%)`, `board.touch()`, `board.sd_mount()`, `board.vbat()`,
`board.battery_percent()`, `board.temp()`, `board.button()`, `board.i2c()`, `board.spi()`. `board.LVGL_FW` es True en este firmware:
`board.spi()` usa `SPI.Bus`+`SPI.Device` y `sd_mount()` los nombres `clk`/`data_pins` (lo resuelve solo).
