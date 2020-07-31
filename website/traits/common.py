import os
import queue
import paho.mqtt.client as mqtt

def mqtt_resp(pub_topics, sub_topics, response_timeout):
    client = mqtt.Client()
    client.username_pw_set(os.environ["MQTT_USERNAME"], os.environ["MQTT_PASSWORD"])
    client.connect(os.environ["MQTT_ADDRESS"], int(os.environ["MQTT_PORT"]))
    q = queue.Queue()
    ret = {pubtopic :{subtopic : None for subtopic in sub_topics[pubtopic]} for pubtopic in pub_topics}
    responses_left = sum([len(sub_topics[topic]) for topic in pub_topics])

    def on_rcv(client, userdata, message):
        q.put((message.topic, message.payload.decode("utf-8")))
    client.on_message = on_rcv

    for pub_topic in pub_topics:
        for sub_topic in sub_topics[pub_topic]:
            client.subscribe(sub_topic)
        client.publish(pub_topic)

    timed_out = False
    client.loop_start()
    while not timed_out and responses_left:
        try:
            sub_topic,msg = q.get(timeout=response_timeout)
            for pub_topic in pub_topics:
                if sub_topic in sub_topics[pub_topic]:
                    if not ret[pub_topic][sub_topic]:
                        responses_left = responses_left - 1
                    ret[pub_topic][sub_topic] = msg
        except queue.Empty:
            timed_out = True
    client.loop_stop()
    return ret
