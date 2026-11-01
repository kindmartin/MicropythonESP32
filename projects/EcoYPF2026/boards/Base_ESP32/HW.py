"""Minimal, board-specific hardware settings for an ESP32 MicroPython app."""

import machine

BOARD_NAME = "ESP32"
APP_TICK_MS = 1000

# Set this to the onboard LED GPIO for the target board, or leave None if
# the board has no user LED / its LED pin is not yet known.
USER_LED_PIN = None
USER_LED_ACTIVE_LOW = False

# Botones (activo-bajo, ver buttons.py). None = no usado.
# BOOT/GPIO0 sirve en runtime una vez que main.py ya esta corriendo
# (startup_cleanup.py lo lee solo al arrancar).
BTN0_PIN = 0
PAGE_BTN_PIN = None      # segundo boton de usuario (p.ej. GPIO21 en T190)
BTN_PULL_UP = True       # False si la placa trae pull-up externo


def make_user_led():
    """Return a configured LED output, or None when no LED pin is configured."""
    if USER_LED_PIN is None:
        return None
    initial = 1 if USER_LED_ACTIVE_LOW else 0
    return machine.Pin(USER_LED_PIN, machine.Pin.OUT, value=initial)


def make_button(pin_num):
    """Return an input Pin for an active-low button, or None if pin_num is None."""
    if pin_num is None:
        return None
    if BTN_PULL_UP:
        return machine.Pin(pin_num, machine.Pin.IN, machine.Pin.PULL_UP)
    return machine.Pin(pin_num, machine.Pin.IN)
