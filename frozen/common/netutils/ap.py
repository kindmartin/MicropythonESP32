import network, time

ap_if = network.WLAN(network.AP_IF)
ap_if.config(essid='ESP32_AP', authmode=network.AUTH_WPA_WPA2_PSK, password='12345678')
ap_if.active(True)

import netutils.ftp_thread
ftp = netutils.ftp_thread.FtpTiny()
ftp.start()

connected_sta = ap_if.status('stations')

def stations():
   global connected_sta
   connected_sta = ap_if.status('stations')
   print('connected_sta',connected_sta)
