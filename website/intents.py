import sys
import os
import queue
import paho.mqtt.publish as publish
import paho.mqtt.client as mqtt
from .actions import onoff
from .models import db, Device

def switch_state(devices):
    client = mqtt.Client()
    client.username_pw_set(os.environ["MQTT_USERNAME"], os.environ["MQTT_PASSWORD"])
    client.connect(os.environ["MQTT_ADDRESS"], int(os.environ["MQTT_PORT"]))
    q = {device : queue.Queue() for device in devices}
    def on_rcv(client, userdata, message):
        st = message.topic.split('/')
        if st[1] == "stat" and st[2] == "POWER" and st[0] in q:
            q[st[0]].put(message.payload.decode("utf-8"))
    client.on_message = on_rcv
    for device in devices:
        client.subscribe(device + "/stat/POWER")
        client.publish(device + "/cmnd/Power","")
    client.loop_start()
    rets = {}
    for device in devices:
        try:
            rets[device] = q[device].get(timeout = 1.0)
        except queue.Empty:
            rets[device] = "OFFLINE"
    client.loop_stop()
    return rets

#using https://developers.google.com/assistant/smarthome/develop/process-intents
def sync(inputs):
    print("sync", file=sys.stderr)
    return {"devices": [d.syncdict() for d in db.session.query(Device).all()]}

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
                    #customData not supported yet
                    if execution["command"] == "action.devices.commands.OnOff":
                        if "on" in execution["params"]:
                            onoff.execute(dev_desc, execution["params"])
                            success.append(dev_desc["id"])
                        else:
                            errors.append(device["id"])
                    else:
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
    print("query", file=sys.stderr)
    devices=inputs["payload"]["devices"]
    responses = {}
    devices_for_search = []
    for device in devices:
        dev_obj = db.session.query(Device).filter_by(device_id=device["id"]).first()
        if dev_obj:
            devices_for_search.append(dev_obj.device_id)
        else:
            responses[device["id"]] = {"online": False, "status" : "ERROR"}
    for device, result in switch_state(devices_for_search).items():
        print(device, result, flush=True)
        responses[device] = {"online": result != "OFFLINE", "on": result == "ON"}
    payload =  {"devices" : responses}
    print(payload, file=sys.stderr)
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
