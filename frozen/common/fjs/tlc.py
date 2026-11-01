from secrets import TLC_SSID, TLC_PASS
import network, time

sta_if = network.WLAN(network.STA_IF)
sta_if.active(True)
sta_if.connect(TLC_SSID, TLC_PASS)


print('[waiting for an IP ]',end='')
while sta_if.ifconfig()[0] == '0.0.0.0':
    time.sleep(1)
    print('.',end='')

sta_if.ifconfig(('192.168.0.11','255.255.255.0','192.168.137.1','8.8.8.8'))

import webrepl
webrepl.start()

import netutils.ftp_thread as ftp_thread
ftp = ftp_thread.FtpTiny()
ftp.start()


print('WIFI connected / ftp at:', sta_if.ifconfig()[0]  )
