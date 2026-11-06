# Waveshare ESP32-S3-Touch-LCD-1.47 — firmware LVGL

Un solo firmware para dos formas de trabajar (se excluyen: para cambiar, `machine.reset()`):

    import use; use.raw()     # SIN LVGL  -> ejemplos en /raw   (board.lcd(), board.touch()...)
    import use; use.lvgl()    # CON LVGL  -> ejemplos en /lvgl  (pantalla y touch los crea LVGL)

Los drivers vienen DENTRO del firmware (no hay que copiarlos):
- sin LVGL: `board`, `st7789`, `lcd_jd9853`, `touch_axs5106`
- con LVGL: `jd9853`, `axs5106`, `display`, `i2c`, `task_handler`, `touch_fix`
- tus modulos: `fjs`, `wifiConnect`, `ftp*`, `netutils`, `fonts`, `drivers`, ...

Hardware: JD9853 172x320 (SPI 38/39, CS21 DC45 RST40 BL46), touch AXS5106L (I2C SDA42 SCL41 RST47 INT48), bateria ADC GPIO12 (x3),
SD SDMMC 4 bits (CLK16 CMD15 D0 17 D1 18 D2 13 D3 14), BOOT GPIO0. SIN IMU, RTC ni camara.

Reglas: NO nombres `jd9853.py` / `axs5106.py` en el FS (taparian los drivers de LVGL). Con LVGL no uses `board.lcd()`; sin LVGL no importes `display`.
Detalle y compilacion: carpeta `lvgl/` del repo (README.md) — `~/MicropythonESP32/boards/WAVESHARE_ESP32_S3_TOUCH_LCD147/`.
