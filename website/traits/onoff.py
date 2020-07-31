import os
import paho.mqtt.publish as publish
from .common import mqtt_resp

TRAIT="action.devices.traits.OnOff"
ACTIONS = ["action.devices.commands.OnOff"]
def switch_light(device, on):
    action = "ON" if on else "OFF"
    print("Switching", device, action, flush=True)
    #TODO: generalise from tasmota
    publish.single(topic=device + "/cmnd/Power", payload=action, hostname=os.environ["MQTT_ADDRESS"], port=int(os.environ["MQTT_PORT"]), auth={'username': os.environ["MQTT_USERNAME"], 'password':os.environ["MQTT_PASSWORD"]})
    return True

def execute(device, params):
    if "on" in params:
        return switch_light(device["id"], params["on"])
    else:
        return False

def query(devices):
    pub_topics = sorted([device + "/cmnd/Power" for device in devices])
    sub_topics = {topic: [topic.split('/')[0]  + "/stat/POWER"] for topic in pub_topics}
    rets = mqtt_resp(pub_topics, sub_topics,  2.0)
    formatted_ret = {}
    for device in devices:
        result = rets[device + "/cmnd/Power"][device + "/stat/POWER"]
        formatted_ret[device]=  {"on" : result == "ON"} if result else None
    return formatted_ret
