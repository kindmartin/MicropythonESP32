CFG_PATH = '/ipaddress.cfg'
CFG_TEMPLATE = """# ssid,password then ip,mask,gw,dns (use commas or new lines; quotes optional)
TU_SSID,TU_PASSWORD
192.168.0.11,255.255.255.0,192.168.0.1,8.8.8.8
"""


def write_example(path=CFG_PATH, template=CFG_TEMPLATE):
    # Overwrite/create the config so the device has a known-good example to tweak.
    try:
        with open(path, 'w') as cfg:
            cfg.write(template)
        print('Example config written to {}'.format(path))
    except OSError as exc:
        print('Failed to write {}: {}'.format(path, exc))


write_example()
