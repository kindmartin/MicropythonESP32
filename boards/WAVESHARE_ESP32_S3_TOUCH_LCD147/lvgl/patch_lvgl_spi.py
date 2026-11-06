#!/usr/bin/env python3
"""Parche a lvgl_micropython: machine.SPI.Device.write()/readinto() con mas de 4 bytes falla con
"spi_master: check_trans_valid: SPI_TRANS_USE_TXDATA only available for txdata transfer <= 32 bits".
En micropy_updates/esp32/machine_hw_spi.c la rama de >4 bytes activa SPI_TRANS_USE_TXDATA / USE_RXDATA a la vez que asigna
tx_buffer / rx_buffer (esos flags son solo para transferencias de <= 32 bits con tx_data / rx_data). Se quitan esos dos flags en esa rama.
Idempotente; guarda machine_hw_spi.c.orig la primera vez. Uso: patch_lvgl_spi.py <ruta a micropy_updates/esp32/machine_hw_spi.c>"""
import shutil, sys

path = sys.argv[1]
s = open(path).read()
tx_old = "                transaction->tx_buffer = src + offset;\n                transaction->flags |= SPI_TRANS_USE_TXDATA;\n"
tx_new = "                transaction->tx_buffer = src + offset;\n"
rx_old = "                transaction->rx_buffer = dest + offset;\n                transaction->flags |= SPI_TRANS_USE_RXDATA;\n"
rx_new = "                transaction->rx_buffer = dest + offset;\n"
if tx_old not in s and rx_old not in s:
    print("parche SPI: ya aplicado (o el archivo cambio) -> nada que hacer")
    sys.exit(0)
shutil.copyfile(path, path + ".orig") if not __import__("os").path.exists(path + ".orig") else None
s = s.replace(tx_old, tx_new).replace(rx_old, rx_new)
open(path, "w").write(s)
print("parche SPI aplicado en", path)
