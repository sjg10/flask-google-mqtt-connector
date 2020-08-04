from . import onoff, openclose

from functools import reduce

SUPPORTED_TRAITS = [onoff, openclose]

TRAIT_MAP = {trait.TRAIT : trait for trait in SUPPORTED_TRAITS}
ACTION_MAP = reduce(lambda a,b :a.update(b) or a, [{a :trait for a in trait.ACTIONS} for trait in SUPPORTED_TRAITS])

def execute(action, device, parameters):
    if action in ACTION_MAP:
        return ACTION_MAP[action].execute(device, parameters) # TODO: allow for more than one action per trait
    else:
        raise NotImplementedError("Unrecognised action ", str(action), "for devices", str(devices))

def query(trait, devices):
    if trait in TRAIT_MAP:
        return TRAIT_MAP[trait].query(devices)
    else:
        raise NotImplementedError("Unrecognised trait ", str(trait), "for devices", str(devices))
