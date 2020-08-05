from .tasmota_u2s import TasmotaU2S
from .am43 import AM43


SUPPORTED_DEVICES=[TasmotaU2S, AM43]

def DeviceFactory(device):
    if device:
        try:
            idx = [x.__name__ for x in SUPPORTED_DEVICES].index(device.device_type)
            return SUPPORTED_DEVICES[idx](device)
        except ValueError as e:
            pass
    return None

def populate(db, DeviceType):
    classnames = [x.__name__ for x in SUPPORTED_DEVICES]
    # Add classes that don't appear yet
    for classname in classnames:
        devicetype = DeviceType.query.filter_by(classname = classname).first()
        if devicetype is None:
            devicetype = DeviceType(classname=classname)
            db.session.add(devicetype)
    # Delete classes that have been removed in code
    for devicetype in DeviceType.query.all():
        if devicetype.classname not in classnames:
            db.session.delete(devicetype)
    db.session.commit()
