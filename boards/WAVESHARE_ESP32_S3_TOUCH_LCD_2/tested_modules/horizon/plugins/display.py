# LCD compartido por todos los modos: app.lcd (portrait 240x320, ya con backlight).
import board
import st7789


def setup(app):
    app.lcd = board.lcd(board.spi(app.cfg["spi_hz"]))
    board.backlight(app.cfg["backlight"])
    app.lcd.fill(st7789.BLACK)

    def cleanup():
        app.lcd.fill(st7789.BLACK)
        board.backlight(0)

    app.on_stop(cleanup)
