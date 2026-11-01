# rx_t190.py -- Heltec WiFi LoRa 32 V2 (SX1276) como receptor del T190.
# Perfil identico a New T190/HW.py: 915 MHz, BW125, SF9, CR4/6, sync 0x12,
# preambulo 12, CRC on, header explicito.
# Uso:  mpremote connect /dev/ttyUSB1 run rx_t190.py   (usa sx127x.py y ssd1306.py de la placa)
import time
from machine import Pin, I2C, SPI
from sx127x import SX127x
import ssd1306

pins = {'miso': 19, 'mosi': 27, 'ss': 18, 'sck': 5, 'dio_0': 26, 'reset': 14, 'led': 25}

# reset por hardware (GPIO14 en el V2)
rst = Pin(pins['reset'], Pin.OUT)
rst.value(0); time.sleep_ms(10); rst.value(1); time.sleep_ms(10)

# OLED (reset GPIO16)
oled = None
try:
    r = Pin(16, Pin.OUT); r.value(0); time.sleep_ms(10); r.value(1)
    oled = ssd1306.SSD1306_I2C(128, 64, I2C(scl=Pin(15), sda=Pin(4), freq=400000), 0x3c)
except Exception as e:
    print("OLED no disponible:", e)

spi = SPI(baudrate=10000000, polarity=0, phase=0, bits=8, firstbit=SPI.MSB,
          sck=Pin(pins['sck'], Pin.OUT, Pin.PULL_DOWN),
          mosi=Pin(pins['mosi'], Pin.OUT, Pin.PULL_UP),
          miso=Pin(pins['miso'], Pin.IN, Pin.PULL_UP))

params = {
    'frequency': 915E6, 'tx_power_level': 2, 'signal_bandwidth': 125E3,
    'spreading_factor': 9, 'coding_rate': 6, 'preamble_length': 12,
    'implicit_header': False, 'sync_word': 0x12, 'enable_CRC': True,
    'invert_IQ': False,
}
lora = SX127x(spi, pins=pins, parameters=params)
lora.receive()  # RX continuo
print("Escuchando 915 MHz BW125 SF9 CR4/6 sync 0x12 ...")


def decode(raw):
    s = raw.decode('utf-8', 'ignore')
    if s.startswith("TLM:"):
        s = s[4:]
    d = {}
    for part in s.split(";"):
        k, _, v = part.partition("=")
        d[k] = v
    return d


def show(lines):
    if oled:
        oled.fill(0)
        for i, l in enumerate(lines[:6]):
            oled.text(l, 0, i * 10)
        oled.show()


n = ok = bad = 0
if oled:
    show(["T190 RX", "915MHz SF9", "esperando..."])
while True:
    f = lora.get_irq_flags()
    if f & 0x40:  # RX_DONE
        n += 1
        rssi, snr = lora.packet_rssi(), lora.packet_snr()
        if f & 0x20:  # CRC error
            bad += 1
            print("RX#{} CRC_ERROR rssi={} snr={}".format(n, rssi, snr))
            continue
        raw = lora.read_payload()
        ok += 1
        print("RX#{} rssi={} snr={} len={} | {}".format(n, rssi, snr, len(raw), raw.decode('utf-8', 'ignore')))
        try:
            d = decode(raw)
            print("   Q={} AGE={}ms V={}km/h D={}m I={}A VBATS={}V P={}W WT={}Wh B={}/{}/{}/{} AV={} IV={}".format(
                d.get('Q'), d.get('AGE'), d.get('V'), d.get('D'), d.get('I'), d.get('VBATS'),
                d.get('P'), d.get('WT'), d.get('B1'), d.get('B2'), d.get('B3'), d.get('B4'),
                d.get('AV'), d.get('IV')))
            show(["Q:%s ok:%d" % (d.get('Q'), ok), "V:%s km/h" % d.get('V'),
                  "Vp:%s I:%s" % (d.get('VBATS'), d.get('I')), "P:%sW" % d.get('P'),
                  "RSSI:%s SNR:%s" % (rssi, snr)])
        except Exception as e:
            print("   (no decodificable:", e, ")")
    time.sleep_ms(20)
