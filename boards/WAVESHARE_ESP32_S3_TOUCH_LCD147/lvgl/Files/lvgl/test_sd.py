# microSD por SDMMC 4 bits. Inserta una tarjeta FAT32.
import os, lvb
sd = lvb.sd_mount()
try:
    print(os.listdir("/sd"))
    with open("/sd/_t.txt", "w") as f:
        f.write("ok")
    ok = open("/sd/_t.txt").read() == "ok"
    os.remove("/sd/_t.txt")
    print("PASS" if ok else "FAIL")
finally:
    os.umount("/sd")
    sd.deinit()
