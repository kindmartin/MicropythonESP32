# Corre los tests en orden; test_button, test_sd y test_rgb piden accion/hardware.
import sys
for name in ("test_lcd", "test_backlight", "test_imu", "test_vbat", "test_rgb", "test_sd", "test_button"):
    print("\n==== %s ====" % name)
    try:
        __import__(name)
    except Exception as e:
        print("FAIL", name, "->", repr(e))
    sys.modules.pop(name, None)
