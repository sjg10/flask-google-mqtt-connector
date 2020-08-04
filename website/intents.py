import sys
import os
from threading import Thread
from .models import db, Device
from .devices.factory import DeviceFactory

#using https://developers.google.com/assistant/smarthome/develop/process-intents
def sync(inputs):
    print("sync", flush=True)
    syncstruct = {"devices": [DeviceFactory(d).sync() for d in db.session.query(Device).all()]}
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
                dev_obj = DeviceFactory(db.session.query(Device).filter_by(id=device["id"]).first())
                if dev_obj:
                    try:
                        if dev_obj.execute(execution["command"], execution["params"]): # TODO: return a struct not a status
                            success.append(device["id"])
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
    threads = {}
    # worker thread to query a device
    def worker(device, responses):
        print("Querying", device.id, flush=True)
        result = device.query()
        print("Result", device.id, result, flush=True)
        responses[device.id] = {}
        responses[device.id]["online"] = result is not None
        responses[device.id]["status"] = "SUCCESS" if result else "OFFLINE"
        if result is not None: responses[device.id].update(result)


    for device in devices:
        dev_obj = DeviceFactory(db.session.query(Device).filter_by(id=device["id"]).first())
        if dev_obj:
            threads[device["id"]] = Thread(target=worker,args=(dev_obj, responses))
            threads[device["id"]].start()
        else:
            responses[device["id"]] = {"online": False, "status" : "ERROR"}
    for thread in threads.values():
        thread.join()
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
