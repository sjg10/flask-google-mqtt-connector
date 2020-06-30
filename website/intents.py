import sys
import os
import queue
import paho.mqtt.publish as publish
import paho.mqtt.client as mqtt

devices = [
        {"id" : "tasmota1", 
        "type" : "action.devices.types.LIGHT",
        "traits" : ["action.devices.traits.OnOff"],
        "name" : {"name" : "stair lights", "nicknames" : ["stair light", "stairs light", "stairs lights"]},
        "willReportState": False, # TODO better as true with https://developers.google.com/assistant/smarthome/develop/report-state
        "roomHint": "downstairs"},
        {"id" : "tasmota2", 
        "type" : "action.devices.types.LIGHT",
        "traits" : ["action.devices.traits.OnOff"],
        "name" : {"name" : "table light", "nicknames" : ["table lights"]},
        "willReportState": False, # TODO better as true with https://developers.google.com/assistant/smarthome/develop/report-state
        "roomHint": "downstairs"},
        {"id" : "tasmota3", 
        "type" : "action.devices.types.LIGHT",
        "traits" : ["action.devices.traits.OnOff"],
        "name" : {"name" : "sofa light", "nicknames" : ["sofa lights", "corner light", "corner lights"]},
        "willReportState": False, # TODO better as true with https://developers.google.com/assistant/smarthome/develop/report-state
        "roomHint": "downstairs"},
        {"id" : "tasmota4", 
        "type" : "action.devices.types.LIGHT",
        "traits" : ["action.devices.traits.OnOff"],
        "name" : {"name" : "door light", "nicknames" : ["door lights"]},
        "willReportState": False, # TODO better as true with https://developers.google.com/assistant/smarthome/develop/report-state
        "roomHint": "downstairs"}
        ]

#TODO: replace the use of this with a database Model
def find_device(idx):
    for device in devices:
        if device["id"] == idx:
            return device
    return None


def switch_light(device, on):
    action = "ON" if on else "OFF"
    print("Switching", device, action)
    #TODO: generalise from tasmota
    publish.single(topic=device + "/cmnd/Power", payload=action, hostname=os.environ["MQTT_ADDRESS"], port=int(os.environ["MQTT_PORT"]), auth={'username': os.environ["MQTT_USERNAME"], 'password':os.environ["MQTT_PASSWORD"]})

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
    return {"devices": devices}

def execute(inputs):
    print("execute", file=sys.stderr)
    success = []
    offlines = []
    errors = []
    for command in inputs["payload"]["commands"]:
        for execution in command["execution"]:
            for device in command["devices"]:
                dev_desc = find_device(device["id"])
                if dev_desc:
                    #customData not supported yet
                    if execution["command"] == "action.devices.commands.OnOff":
                        if "on" in execution["params"]:
                            switch_light(dev_desc["id"], execution["params"]["on"])
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
        dev_desc = find_device(device["id"])
        if dev_desc:
            devices_for_search.append(dev_desc["id"])
        else:
            responses[dev_desc["id"]] = {"online": False, "status" : "ERROR"}
    for device, result in switch_state(devices_for_search).items():
        print(device, result, file=sys.stderr)
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
