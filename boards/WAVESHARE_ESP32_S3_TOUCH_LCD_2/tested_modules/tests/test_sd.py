# microSD (SPI compartido con LCD): monta, escribe, lee, lista y desmonta.
import os, board
spi = board.spi()                # un solo bus compartido LCD + SD
lcd = board.lcd(spi)
sd = board.sd_mount("/sd", spi)  # usa el modulo sdcard (micropython-lib)
print("ls /sd:", os.listdir("/sd"))
data = b"test-" * 1000
with open("/sd/_test.bin", "wb") as f:
    f.write(data)
with open("/sd/_test.bin", "rb") as f:
    ok = f.read() == data
os.remove("/sd/_test.bin")
print("PASS" if ok else "FAIL", "- escritura/lectura", len(data), "bytes")
lcd.fill(0x07E0)         # el LCD sigue funcionando tras usar la SD?
os.umount("/sd")
