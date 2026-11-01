"""Minimal ESP32 app: uasyncio on a background thread, REPL stays available.

Optional buttons (HW.BTN0_PIN / HW.PAGE_BTN_PIN) report short/double/long/
extra gestures through the on_* handlers below."""

import _thread
import sys
import time
import uasyncio as asyncio

import machine

import HW
from buttons import InterruptPageButton

AUTO_START = True
_BG_THREAD_STACK = 8192
_RUNNING = False
_STOP_REQUESTED = False
_ticks = 0
_led = None


def _set_led(on):
    if _led is None:
        return
    active_value = 0 if HW.USER_LED_ACTIVE_LOW else 1
    inactive_value = 1 - active_value
    _led.value(active_value if on else inactive_value)


async def _app_task():
    global _ticks
    print("[{}] asyncio app started".format(HW.BOARD_NAME))
    while not _STOP_REQUESTED:
        _ticks += 1
        _set_led(_ticks % 2 == 0)
        await asyncio.sleep_ms(HW.APP_TICK_MS)
    _set_led(False)


def _gesture_handlers(label):
    # Reemplazar por la accion real de cada proyecto.
    def make(kind):
        return lambda: print("[{}] {}".format(label, kind))
    return {"short": make("short"), "double": make("double"),
            "long": make("long"), "extra": make("extra")}


def _start_buttons():
    for label, pin_num in (("BTN0", HW.BTN0_PIN), ("PAGE", HW.PAGE_BTN_PIN)):
        pin = HW.make_button(pin_num)
        if pin is None:
            continue
        button = InterruptPageButton(
            pin,
            irq_trigger=machine.Pin.IRQ_FALLING | machine.Pin.IRQ_RISING,
            label=label,
            **_gesture_handlers(label))
        asyncio.create_task(button.task())


async def _main_async():
    global _led
    _led = HW.make_user_led()
    _start_buttons()
    await _app_task()


def _background():
    global _RUNNING, _STOP_REQUESTED
    try:
        asyncio.run(_main_async())
    except Exception as exc:
        print("[main] background app failed:", exc)
        try:
            sys.print_exception(exc)
        except AttributeError:
            pass
    finally:
        _RUNNING = False
        _STOP_REQUESTED = False


def start():
    """Start the async app on a thread and return immediately to the REPL."""
    global _RUNNING, _STOP_REQUESTED
    if _RUNNING:
        print("[main] already running")
        return False
    _STOP_REQUESTED = False
    _RUNNING = True
    try:
        _thread.stack_size(_BG_THREAD_STACK)
    except (AttributeError, OSError) as exc:
        print("[main] could not set thread stack size:", exc)
    try:
        _thread.start_new_thread(_background, ())
    except Exception as exc:
        _RUNNING = False
        print("[main] could not start background thread:", exc)
        return False
    return True


def stop(wait_ms=0):
    """Request app shutdown; optionally wait for the background thread."""
    global _STOP_REQUESTED
    if not _RUNNING:
        print("[main] not running")
        return False
    _STOP_REQUESTED = True
    remaining = int(wait_ms)
    while _RUNNING and remaining > 0:
        time.sleep_ms(10)
        remaining -= 10
    return True


def status():
    """Print app state from the REPL."""
    print("[STATUS] board={} running={} ticks={} led_pin={}".format(
        HW.BOARD_NAME, _RUNNING, _ticks, HW.USER_LED_PIN))


if AUTO_START:
    start()
