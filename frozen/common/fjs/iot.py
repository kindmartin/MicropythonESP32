from secrets import WIFI_SSID, WIFI_PASS
import network, time

DEFAULT_IFCONFIG = ('192.168.0.11','255.255.255.0','192.168.0.1','8.8.8.8')

def load_ifconfig(path='/ipaddress.cfg'):
    # Prefer external config when available to avoid hard coding network params.
    try:
        with open(path) as cfg:
            lines = [ln.strip() for ln in cfg if ln.strip() and not ln.lstrip().startswith('#')]
    except OSError:
        return DEFAULT_IFCONFIG

    for line in lines:
        tokens = [item.strip().strip("'\"") for item in line.split(',') if item.strip()]
        if len(tokens) == 4:
            return tuple(tokens)
    return DEFAULT_IFCONFIG

sta_if = network.WLAN(network.STA_IF)
sta_if.active(True)
sta_if.connect(WIFI_SSID, WIFI_PASS)

print('[waiting for an IP ]',end='')
while sta_if.ifconfig()[0] == '0.0.0.0':
    time.sleep(1)
    print('.',end='')

sta_if.ifconfig(load_ifconfig())

import webrepl
webrepl.start()

import netutils.ftp_thread as ftp_thread
ftp = ftp_thread.FtpTiny()
ftp.start()


print('WIFI connected / ftp at:', sta_if.ifconfig()[0]  )
