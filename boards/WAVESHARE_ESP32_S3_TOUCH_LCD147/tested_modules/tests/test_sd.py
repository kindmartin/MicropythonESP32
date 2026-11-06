# microSD por SDMMC 4 bits. Inserta una tarjeta FAT.
import os, board
sd = board.sd_mount()
print(os.listdir("/sd"))
with open("/sd/_t.txt", "w") as f:
    f.write("ok")
print("PASS" if open("/sd/_t.txt").read() == "ok" else "FAIL")
os.remove("/sd/_t.txt")
