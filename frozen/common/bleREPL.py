"""Convenience helpers for starting and stopping the BLE REPL bridge."""

import ble_repl

_bridge = None


def start(*, name=None, rxbuf=512, dupterm_index=1, auto_dupterm=True, debug=False):
    """Start the BLE REPL bridge if it is not already running."""
    global _bridge
    if _bridge is not None:
        return _bridge
    kwargs = {
        "rxbuf": rxbuf,
        "dupterm_index": dupterm_index,
        "auto_dupterm": auto_dupterm,
        "debug": debug,
    }
    if name is not None:
        kwargs["name"] = name
    _bridge = ble_repl.start_ble_repl(**kwargs)
    return _bridge


def stop():
    """Stop the BLE REPL bridge and release dupterm."""
    global _bridge
    if _bridge is None:
        return
    try:
        _bridge.close()
    finally:
        _bridge = None


def is_running():
    """Return True if the BLE REPL bridge is active."""
    return _bridge is not None

start()  # Auto-start the bridge on import
