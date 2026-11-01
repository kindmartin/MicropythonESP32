# Corre los tests no interactivos en orden; los que piden accion llevan aviso.
for name in ("test_lcd", "test_backlight", "test_imu", "test_vbat", "test_sd", "test_touch", "test_button", "test_camera", "test_camera_preview"):
    print("\n==== %s ====" % name)
    try:
        __import__(name)
    except Exception as e:
        print("FAIL", name, "->", repr(e))
    import sys
    sys.modules.pop(name, None)      # permite re-ejecutar
