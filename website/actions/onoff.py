import os
import paho.mqtt.publish as publish

def switch_light(device, on):
    action = "ON" if on else "OFF"
    print("Switching", device, action, flush=True)
    #TODO: generalise from tasmota
    publish.single(topic=device + "/cmnd/Power", payload=action, hostname=os.environ["MQTT_ADDRESS"], port=int(os.environ["MQTT_PORT"]), auth={'username': os.environ["MQTT_USERNAME"], 'password':os.environ["MQTT_PASSWORD"]})

def execute(device, params):
    switch_light(device["id"], params["on"])
