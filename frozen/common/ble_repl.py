"""Bluetooth Low Energy REPL bridge using the Nordic UART Service."""

try:
    import bluetooth
    from micropython import const
except ImportError:  # pragma: no cover - host fallback
    bluetooth = None  # type: ignore
    const = lambda x: x  # type: ignore

try:
    import uos
except ImportError:  # pragma: no cover
    import os as uos  # type: ignore

try:
    import io
except ImportError:  # pragma: no cover
    import uio as io  # type: ignore
import struct
try:
    import utime as time  # type: ignore
except ImportError:  # pragma: no cover
    import time  # type: ignore
    if not hasattr(time, "sleep_ms"):
        def _sleep_ms(ms):
            time.sleep(ms / 1000.0)
        time.sleep_ms = _sleep_ms  # type: ignore
try:
    from machine import Timer  # type: ignore
except ImportError:  # pragma: no cover
    Timer = None  # type: ignore

try:
    from machine import unique_id  # type: ignore
except ImportError:  # pragma: no cover
    unique_id = None  # type: ignore


def _call_later_ms(delay, cb):
    if Timer is None:
        time.sleep_ms(delay)
        cb()
        return
    try:
        t = Timer(3)
    except Exception:
        time.sleep_ms(delay)
        cb()
        return

    def _wrapped(timer):
        timer.deinit()
        cb()

    t.init(mode=Timer.ONE_SHOT, period=delay, callback=_wrapped)

_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)
_IRQ_MTU_EXCHANGED = const(21)

_MP_STREAM_POLL = const(3)
_MP_STREAM_POLL_RD = const(0x0001)
_MP_STREAM_POLL_WR = const(0x0004)
_MP_STREAM_POLL_ERR = const(0x0008)

_UART_UUID = bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E") if bluetooth else None
_UART_TX = bluetooth.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E") if bluetooth else None
_UART_RX = bluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E") if bluetooth else None
if bluetooth:
    _UART_SERVICE = (
        _UART_UUID,
        (
            (_UART_TX, bluetooth.FLAG_READ | bluetooth.FLAG_NOTIFY,),
            (_UART_RX, bluetooth.FLAG_WRITE,),
        ),
    )
else:
    _UART_SERVICE = None

def _default_name():
    if unique_id:
        try:
            uid = unique_id()
            if isinstance(uid, (bytes, bytearray)) and uid:
                tail = uid[-2:] if len(uid) >= 2 else uid
                hex_tail = "".join("{:02X}".format(b) for b in tail)
                return "BLE-{}".format(hex_tail)
        except Exception:
            pass
    return "BLE-REPL"


_DEFAULT_NAME = _default_name()
_MAX_ADV_PAYLOAD = const(31)


def _append_adv(payload, adv_type, value):
    if not value:
        return
    item = struct.pack("BB", len(value) + 1, adv_type) + value
    if len(payload) + len(item) > _MAX_ADV_PAYLOAD:
        raise ValueError("advertising payload too long")
    payload.extend(item)


def _advertising_payload(*, name=None, services=None, appearance=0):
    payload = bytearray()
    flags = 0x02 | 0x04  # general discoverable, no BR/EDR
    _append_adv(payload, 0x01, struct.pack("B", flags))
    if name:
        enc = name.encode("utf-8")
        if len(enc) > (_MAX_ADV_PAYLOAD - 5):
            enc = enc[:_MAX_ADV_PAYLOAD - 5]
        _append_adv(payload, 0x09, enc)
    if services:
        for svc in services:
            if isinstance(svc, int):
                _append_adv(payload, 0x03, struct.pack("<H", svc))
            else:
                _append_adv(payload, 0x07, bytes(svc))
    if appearance:
        _append_adv(payload, 0x19, struct.pack("<H", appearance))
    return bytes(payload)


def _format_addr(addr):
    if isinstance(addr, (bytes, bytearray)):
        return ":".join("{:02X}".format(b) for b in addr)
    return str(addr)


class _BLEStream(io.IOBase):
    def __init__(self, *, name=_DEFAULT_NAME, rxbuf=512, dupterm_index=None, auto_dupterm=True, debug=False):
        if bluetooth is None:
            raise RuntimeError("bluetooth module not available")
        self._ble = bluetooth.BLE()
        self._ble.active(True)
        self._ble.irq(self._irq)
        if _UART_SERVICE is None:
            raise RuntimeError('uart service unavailable')
        services_result = self._ble.gatts_register_services((_UART_SERVICE,))
        if not services_result:
            raise RuntimeError('unable to register BLE services')
        handles = services_result[0]
        if len(handles) == 1 and isinstance(handles[0], (tuple, list)):
            handles = handles[0]
        if len(handles) == 2:
            self._tx_handle, self._rx_handle = handles
        elif len(handles) >= 3:
            self._service_handle = handles[0]
            self._tx_handle = handles[1]
            self._rx_handle = handles[2]
        else:
            raise ValueError('unexpected handle layout: {}'.format(handles))
        self._ble.gatts_set_buffer(self._rx_handle, rxbuf, True)
        self._conn_handle = None
        self._max_tx = 20
        self._rx_buffer = bytearray()
        self._name = name
        self._advertise()
        self._dup_index = None
        self._preferred_index = dupterm_index
        self._dupterm_supports_index = None
        self._debug = debug
        if auto_dupterm:
            try:
                self.attach(dupterm_index)
            except ValueError as exc:
                print('BLE REPL: unable to attach to REPL ({})'.format(exc))

    def _advertise(self):
        payload = _advertising_payload(name=self._name, services=[_UART_UUID])
        try:
            self._ble.gap_advertise(100_000, adv_data=payload)
        except OSError as exc:
            if exc.args and exc.args[0] in (-30, 12):
                # Radio busy; retry shortly.
                _call_later_ms(50, self._advertise)
            else:
                raise

    def _irq(self, event, data):
        if event == _IRQ_CENTRAL_CONNECT:
            self._conn_handle, addr_type, addr = data
            print("BLE REPL: central connected (handle {}, addr type {}, addr {})".format(
                self._conn_handle,
                addr_type,
                _format_addr(addr),
            ))
        elif event == _IRQ_CENTRAL_DISCONNECT:
            self._conn_handle = None
            print("BLE REPL: central disconnected")
            _call_later_ms(50, self._advertise)
        elif event == _IRQ_GATTS_WRITE:
            conn_handle, value_handle = data
            if conn_handle == self._conn_handle and value_handle == self._rx_handle:
                chunk = self._ble.gatts_read(self._rx_handle)
                if chunk:
                    self._rx_buffer.extend(chunk)
                    notifier = getattr(uos, 'dupterm_notify', None)
                    if notifier:
                        try:
                            notifier(None)
                        except Exception:
                            pass
                self._ble.gatts_write(self._rx_handle, b"")
        elif event == _IRQ_MTU_EXCHANGED:
            conn_handle, mtu = data
            if self._conn_handle == conn_handle:
                self._max_tx = mtu - 3

    def any(self):
        return len(self._rx_buffer)

    def read(self, size=None):
        if not self._rx_buffer:
            return None
        if size is None or size < 0 or size > len(self._rx_buffer):
            size = len(self._rx_buffer)
        chunk = bytes(self._rx_buffer[:size])
        self._rx_buffer = self._rx_buffer[size:]
        return chunk

    def readinto(self, buf):
        if not self._rx_buffer:
            return None
        n = min(len(buf), len(self._rx_buffer))
        buf[:n] = self._rx_buffer[:n]
        self._rx_buffer = self._rx_buffer[n:]
        return n

    def write(self, data):
        if not self._conn_handle:
            return len(data)
        total = 0
        for offset in range(0, len(data), self._max_tx):
            fragment = data[offset:offset + self._max_tx]
            retries = 0
            while True:
                try:
                    self._ble.gatts_notify(self._conn_handle, self._tx_handle, fragment)
                    break
                except OSError as exc:
                    if exc.args and exc.args[0] == 12 and retries < 5:
                        time.sleep_ms(10)
                        retries += 1
                        continue
                    return total
            total += len(fragment)
        return total

    def ioctl(self, request, arg):
        if request == _MP_STREAM_POLL:
            mask = _MP_STREAM_POLL_WR
            if self.any():
                mask |= _MP_STREAM_POLL_RD
            return mask
        return 0

    def close(self):
        if self._dup_index is not None:
            try:
                self._clear_dupterm(self._dup_index)
            except Exception:
                pass
            self._dup_index = None
        try:
            self._ble.gap_advertise(None)
        except Exception:
            pass
        self._ble.active(False)

    def _ensure_dupterm_capability(self):
        if self._dupterm_supports_index is not None:
            return self._dupterm_supports_index
        try:
            uos.dupterm(None, 1)
        except TypeError:
            self._dupterm_supports_index = False
        except ValueError:
            self._dupterm_supports_index = False
        except OSError:
            self._dupterm_supports_index = False
        else:
            self._dupterm_supports_index = True
        if self._debug:
            print('BLE REPL debug: dupterm indexed support = {}'.format(self._dupterm_supports_index))
        return self._dupterm_supports_index

    def _set_dupterm(self, stream, index=None):
        supports_index = self._ensure_dupterm_capability()
        if supports_index:
            slot = 0 if index is None else index
            if self._debug:
                print('BLE REPL debug: attaching to dupterm slot {}'.format(slot))
            uos.dupterm(stream, slot)
            return slot
        if index not in (None, 0):
            raise ValueError('dupterm slots unavailable on this build')
        if self._debug:
            print('BLE REPL debug: attaching to legacy dupterm (no slots)')
        uos.dupterm(stream)
        return 0

    def _clear_dupterm(self, index=None):
        supports_index = self._ensure_dupterm_capability()
        if supports_index:
            slot = 0 if index is None else index
            if self._debug:
                print('BLE REPL debug: clearing dupterm slot {}'.format(slot))
            uos.dupterm(None, slot)
        else:
            if index not in (None, 0):
                raise ValueError('dupterm slots unavailable on this build')
            if self._debug:
                print('BLE REPL debug: clearing legacy dupterm')
            uos.dupterm(None)

    def attach(self, index=None):
        if index is not None and self._dup_index == index:
            return index
        if index is None and self._dup_index is not None:
            return self._dup_index
        supports_index = self._ensure_dupterm_capability()
        if not supports_index:
            try:
                used = self._set_dupterm(self)
                self._dup_index = used
                self._preferred_index = used
                if self._debug:
                    print('BLE REPL debug: attached to legacy dupterm slot {}'.format(used))
                return used
            except Exception as exc:
                if self._debug:
                    print('BLE REPL debug: legacy dupterm attach failed: {}'.format(exc))
                raise ValueError('dupterm not available') from exc
        candidates = []
        if index is not None:
            candidates.append(index)
        else:
            if self._preferred_index is not None:
                candidates.append(self._preferred_index)
            candidates.extend(range(0, 8))
        seen = set()
        last_exc = None
        for candidate in candidates:
            if candidate in seen:
                continue
            seen.add(candidate)
            try:
                used = self._set_dupterm(self, candidate)
                self._dup_index = used
                self._preferred_index = used
                if self._debug:
                    print('BLE REPL debug: attached to dupterm slot {}'.format(used))
                return used
            except Exception as exc:
                if self._debug:
                    print('BLE REPL debug: slot {} attach failed: {}'.format(candidate, exc))
                last_exc = exc
                continue
        raise ValueError('no dupterm slot available') from last_exc


def start_ble_repl(*, name=_DEFAULT_NAME, rxbuf=512, dupterm_index=None, auto_dupterm=True, debug=False):
    """Start advertising a BLE REPL bridge."""
    stream = _BLEStream(
        name=name,
        rxbuf=rxbuf,
        dupterm_index=dupterm_index,
        auto_dupterm=auto_dupterm,
        debug=debug,
    )
    return stream


__all__ = ["start_ble_repl"]
