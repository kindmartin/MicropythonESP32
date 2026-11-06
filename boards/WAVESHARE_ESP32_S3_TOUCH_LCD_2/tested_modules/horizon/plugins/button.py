# Boton BOOT (GPIO0) con la libreria buttons.py (gestos con IRQ + debounce). Emite eventos:
#   button_short / button_double / button_long / button_extra
# Acciones del nucleo: doble = cambiar de modo; largo o extra = parar. Cada modo se suscribe a button_short
# (horizonte: cero; bola: reiniciar nivel) y a lo que quiera.
from machine import Pin
import uasyncio as asyncio
import buttons


def setup(app):
    btn = buttons.InterruptPageButton(
        Pin(0, Pin.IN, Pin.PULL_UP), irq_trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, timings=app.cfg["buttons"],
        short=lambda: app.emit("button_short"), double=lambda: app.emit("button_double"),
        long=lambda: app.emit("button_long"), extra=lambda: app.emit("button_extra"), label="BOOT")
    app.on("button_double", app.next_mode)
    app.on("button_long", app.stop)
    app.on("button_extra", app.stop)

    async def task(app):
        await btn.task()

    app.add_task("button", task)
    app.on_stop(btn.close)
