import os
import paho.mqtt.publish as publish
from .common import mqtt_resp

TRAIT="action.devices.traits.OpenClose"
ACTIONS=["action.devices.commands.OpenClose"]
def set_percent(device, percent):
    print("Opening", device, percent, flush=True)
    publish.single(topic=device + "/ctrl", payload=100-percent, hostname=os.environ["MQTT_ADDRESS"], port=int(os.environ["MQTT_PORT"]), auth={'username': os.environ["MQTT_USERNAME"], 'password':os.environ["MQTT_PASSWORD"]})
    return True

def execute(device, params):
    if "openPercent" in params:
        return set_percent(device["id"], params["openPercent"])
    else:
        return False

def query(devices):
    pub_topics = []
    sub_topics = {}
    for device in devices:
        pub_topic = device + "/ctrl"
        pub_topics.append(pub_topic)
        sub_topics[pub_topic] = [device  + "/pos", device + "/bat"]
    rets = mqtt_resp(pub_topics, sub_topics, 2.0)
    formatted_ret = {}
    for device in devices:
        result = rets[device + "/ctrl"][device + "/pos"]
        formatted_ret[device] =  {"openState" : [{"openPercent" : 100 - int(result)}]} if result else None
    return formatted_ret
