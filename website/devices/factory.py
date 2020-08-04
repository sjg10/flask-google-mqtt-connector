from .tasmota_u2s import TasmotaU2S
from .am43 import AM43


SUPPORTED_DEVICES=[TasmotaU2S, AM43]

def DeviceFactory(device):
    for sd in SUPPORTED_DEVICES:
        if sd.matches_device_info(device.manufacturer, device.model): return sd(device)
    return None
