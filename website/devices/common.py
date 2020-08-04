import os
import queue
from abc import ABC, abstractmethod
import paho.mqtt.client as mqtt

def mqtt_resp(pub_topic, sub_topics, response_timeout):
    client = mqtt.Client()
    client.username_pw_set(os.environ["MQTT_USERNAME"], os.environ["MQTT_PASSWORD"])
    client.connect(os.environ["MQTT_ADDRESS"], int(os.environ["MQTT_PORT"]))
    q = queue.Queue()
    ret = {subtopic : None for subtopic in sub_topics}
    responses_left = len(sub_topics)

    def on_rcv(client, userdata, message):
        q.put((message.topic, message.payload.decode("utf-8")))
    client.on_message = on_rcv

    for sub_topic in sub_topics:
        client.subscribe(sub_topic)
    client.publish(pub_topic)

    timed_out = False
    client.loop_start()
    while not timed_out and responses_left:
        try:
            sub_topic,msg = q.get(timeout=response_timeout)
            if not ret[sub_topic]: # if this is a new message for this topic, we dont need to wait on it any more
                responses_left = responses_left - 1
            ret[sub_topic] = msg
        except queue.Empty:
            timed_out = True
    client.loop_stop()
    return ret

class ConcreteDevice(ABC):
    def __init__(self, db_device):
        self.id = db_device.id
        self.db_device = db_device
    @classmethod
    def matches_device_info(cls, manufacturer, model):
        return cls.manufacturer == manufacturer and cls.model == model
    @abstractmethod
    def execute(self, action, parameters):
        pass
    @abstractmethod
    def query(self):
        pass
    @abstractmethod
    def sync(self):
        pass
