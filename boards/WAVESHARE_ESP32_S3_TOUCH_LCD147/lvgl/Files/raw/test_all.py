# Corre los tests en orden; test_touch, test_sd y test_button piden accion/hardware.
import sys
for name in ("test_lcd", "test_backlight", "test_touch", "test_temp", "test_vbat", "test_sd", "test_button"):
    print("\n==== %s ====" % name)
    try:
        __import__(name)
    except Exception as e:
        print("FAIL", name, "->", repr(e))
    sys.modules.pop(name, None)
