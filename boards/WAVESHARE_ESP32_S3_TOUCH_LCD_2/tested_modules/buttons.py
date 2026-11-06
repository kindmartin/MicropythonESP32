# buttons.py -- botones digitales con gestos short/double/long/extra.
# Origen: New T190/buttons.py (se quito UpDownButtons, rocker ADC).
#
# PageButton           : sondeo (polling) cada POLL_MS.
# InterruptPageButton  : flancos por IRQ + debounce en asyncio (recomendado).
# Ambos son activo-bajo (pulsado = 0): usar PULL_UP interno o externo.
# Las tareas (.task()) deben correr dentro de un loop uasyncio.
#
# Uso:
#   btn = InterruptPageButton(Pin(0, Pin.IN, Pin.PULL_UP),
#       irq_trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING,
#       short=on_short, double=on_double, long=on_long, extra=on_extra)
#   asyncio.create_task(btn.task())

import uasyncio as asyncio
import time

DEBUG = False

PAGE_DEFAULTS = {
    "SHORT_MS": 420,
    "LONG_MS": 1200,
    "EXTRA_MS": 2200,
    "DOUBLE_MS": 320,
    "POLL_MS": 20,
}


def _ticks():
    return time.ticks_ms()


def _diff(a, b):
    return time.ticks_diff(a, b)


if hasattr(time, "ticks_add"):
    _ticks_add = time.ticks_add
else:
    def _ticks_add(base, delta):
        return (base + delta) & 0x7FFFFFFF


class PageButton:
    """Boton digital simple (S3/GPIO21 o BTN0/GPIO0): distingue
    short/double/long/extra por la duracion de la pulsacion y la
    ventana entre clicks sucesivos (DOUBLE_MS)."""

    def __init__(self, pin_in, *, short=lambda: None, double=lambda: None,
                 long=lambda: None, extra=lambda: None, timings=None, label="Page"):
        self.pin = pin_in
        self.cb_short = short
        self.cb_double = double
        self.cb_long = long
        self.cb_extra = extra
        self.t = PAGE_DEFAULTS.copy()
        self.t.update(timings or {})
        self.label = label

        self._is_pressed = False
        self._press_started = 0
        self._pending_clicks = 0
        self._pending_deadline = None

    def _fire(self, kind, callback):
        if DEBUG:
            now = _ticks()
            duration = _diff(now, self._press_started) if self._press_started else 0
            print("[{}] {:>6}ms {}".format(self.label, duration, kind))
        if callable(callback):
            callback()

    def _handle_release(self, now):
        duration = _diff(now, self._press_started)
        short_ms = int(self.t.get("SHORT_MS", PAGE_DEFAULTS["SHORT_MS"]))
        long_ms = int(self.t.get("LONG_MS", PAGE_DEFAULTS["LONG_MS"]))
        extra_ms = int(self.t.get("EXTRA_MS", PAGE_DEFAULTS["EXTRA_MS"]))
        double_ms = int(self.t.get("DOUBLE_MS", PAGE_DEFAULTS["DOUBLE_MS"]))

        if duration >= extra_ms:
            self._fire("extra", self.cb_extra)
            self._pending_clicks = 0
            self._pending_deadline = None
        elif duration >= long_ms:
            self._fire("long", self.cb_long)
            self._pending_clicks = 0
            self._pending_deadline = None
        elif duration <= short_ms:
            self._pending_clicks += 1
            if self._pending_clicks == 1:
                self._pending_deadline = _ticks_add(now, double_ms)
            elif (self._pending_deadline is not None and
                  _diff(self._pending_deadline, now) > 0):
                self._fire("double", self.cb_double)
                self._pending_clicks = 0
                self._pending_deadline = None
            else:
                self._fire("short", self.cb_short)
                self._pending_clicks = 1
                self._pending_deadline = _ticks_add(now, double_ms)

    async def task(self):
        poll_ms = max(5, int(self.t.get("POLL_MS", 20)))

        while True:
            now = _ticks()
            value = self.pin.value()

            if value == 0 and not self._is_pressed:
                self._is_pressed = True
                self._press_started = now

            if value == 1 and self._is_pressed:
                self._is_pressed = False
                self._handle_release(now)

            if self._pending_clicks == 1 and self._pending_deadline is not None:
                if _diff(now, self._pending_deadline) >= 0:
                    self._fire("short", self.cb_short)
                    self._pending_clicks = 0
                    self._pending_deadline = None

            await asyncio.sleep_ms(poll_ms)


class InterruptPageButton(PageButton):
    """PageButton con captura de flancos por IRQ y debounce en asyncio."""

    _EDGE_QUEUE_SIZE = 16
    _EDGE_QUEUE_MASK = _EDGE_QUEUE_SIZE - 1

    def __init__(self, pin_in, *, irq_trigger, debounce_ms=25,
                 timings=None, **kwargs):
        super().__init__(pin_in, timings=timings, **kwargs)
        self.debounce_ms = max(1, int(debounce_ms))
        self._edge_values = [1] * self._EDGE_QUEUE_SIZE
        self._edge_ticks = [0] * self._EDGE_QUEUE_SIZE
        self._edge_head = 0
        self._edge_tail = 0
        self._edge_overflows = 0
        self._stable_value = 1
        self._candidate_value = int(pin_in.value())
        self._candidate_tick = _ticks()
        self.pin.irq(handler=self._on_edge, trigger=irq_trigger)

    def _on_edge(self, pin):
        head = self._edge_head
        if head - self._edge_tail >= self._EDGE_QUEUE_SIZE:
            self._edge_tail += 1
            self._edge_overflows += 1
        index = head & self._EDGE_QUEUE_MASK
        self._edge_values[index] = pin.value()
        self._edge_ticks[index] = _ticks()
        self._edge_head = head + 1

    def close(self):
        self.pin.irq(handler=None)

    async def task(self):
        poll_ms = max(2, min(10, int(self.t.get("POLL_MS", 5))))
        while True:
            while self._edge_tail < self._edge_head:
                index = self._edge_tail & self._EDGE_QUEUE_MASK
                value = self._edge_values[index]
                tick = self._edge_ticks[index]
                self._edge_tail += 1
                if value != self._candidate_value:
                    self._candidate_value = value
                    self._candidate_tick = tick

            now = _ticks()
            if (self._candidate_value != self._stable_value and
                    _diff(now, self._candidate_tick) >= self.debounce_ms):
                if self.pin.value() == self._candidate_value:
                    self._stable_value = self._candidate_value
                    if self._stable_value == 0:
                        self._is_pressed = True
                        self._press_started = self._candidate_tick
                    elif self._is_pressed:
                        self._is_pressed = False
                        self._handle_release(self._candidate_tick)
                else:
                    self._candidate_value = int(self.pin.value())
                    self._candidate_tick = now

            if self._pending_clicks == 1 and self._pending_deadline is not None:
                if _diff(now, self._pending_deadline) >= 0:
                    self._fire("short", self.cb_short)
                    self._pending_clicks = 0
                    self._pending_deadline = None

            await asyncio.sleep_ms(poll_ms)
