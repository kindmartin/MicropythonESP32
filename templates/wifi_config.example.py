"""Plantilla de credenciales WiFi. Copiala como wifi_config.py (esta en .gitignore) y completa tus redes."""

NETWORKS = [
    {
        "ssid": "TU_SSID",
        "password": "TU_PASSWORD",
        "ip": "192.168.0.50",        # IP fija (opcional)
        "mask": "255.255.255.0",
        "gw": "192.168.0.1",
        "dns": "8.8.8.8",
    },
]
