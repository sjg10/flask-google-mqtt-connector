import sys
import os
from .traits import traits
from .models import db, Device

#using https://developers.google.com/assistant/smarthome/develop/process-intents
def sync(inputs):
    print("sync", flush=True)
    syncstruct = {"devices": [d.syncdict() for d in db.session.query(Device).all()]}
    print(syncstruct, flush=True)
    return syncstruct

def execute(inputs):
    print("execute", file=sys.stderr)
    success = []
    offlines = []
    errors = []
    for command in inputs["payload"]["commands"]:
        for execution in command["execution"]:
            for device in command["devices"]:
                dev_obj = db.session.query(Device).filter_by(device_id=device["id"]).first()
                if dev_obj:
                    dev_desc=dev_obj.syncdict()
                    try:
                        if traits.execute(execution["command"], dev_desc, execution["params"]): # TODO: return a struct not a status
                            success.append(dev_desc["id"])
                        else:
                            errors.append(device["id"])
                    except NotImplementedError as e:
                        errors.append(device["id"])
                else:
                    errors.append(device["id"])
    payload = {"commands": []}
    if len(success):
        payload["commands"].append({"ids":success,"status":"SUCCESS"})
    if len(offlines):
        payload["commands"].append({"ids":offlines,"status":"OFFLINE"})
    if len(errors):
        payload["commands"].append({"ids":errors,"status":"ERROR"})
    print(payload, file=sys.stderr)
    return payload

def query(inputs):
    print("query", flush=True)
    devices=inputs["payload"]["devices"]
    responses = {}
    devices_for_search = []
    for device in devices:
        dev_obj = db.session.query(Device).filter_by(device_id=device["id"]).first()
        if dev_obj:
            devices_for_search.append(dev_obj)
        else:
            responses[device["id"]] = {"online": False, "status" : "ERROR"}
    dev_by_trait = {}
    for device in devices_for_search:
        for trait in device.traits:
            if trait in dev_by_trait:
                dev_by_trait[trait].append(device.device_id)
            else:
                dev_by_trait[trait] = [device.device_id]
    for trait, devices in dev_by_trait.items():
            print("Querying",devices, trait, flush=True)
            for device, result in traits.query(trait, devices).items():
                print("Result", device, trait, result, flush=True)
                if device in responses:
                    if not device["online"]:  # dont bother with results for offline devices
                        continue
                else:
                    responses[device] = {}
                responses[device]["online"] = result is not None
                responses[device]["status"] = "SUCCESS" if result else "OFFLINE"
                if result is not None: responses[device].update(result)
    payload =  {"devices" : responses}
    print(payload, flush=True)
    return payload

def disconnect(inputs):
    print("disconnect", file=sys.stderr)
    return None

def api_delegate(request):
    if "inputs" in request:
        inputs = request["inputs"]
        if len(inputs) > 0  and "intent" in inputs[0]:
            if inputs[0]["intent"] == "action.devices.SYNC":
                return sync(inputs[0])
            if inputs[0]["intent"] == "action.devices.EXECUTE":
                return execute(inputs[0])
            if inputs[0]["intent"] == "action.devices.QUERY":
                return query(inputs[0])
            if inputs[0]["intent"] == "action.devices.DISCONNECT":
                return disconnect(inputs[0])
            else:
                return None
        else:
            return None
    else:
        return None
