import os
import paho.mqtt.publish as publish
from .common import mqtt_resp, ConcreteDevice

class TasmotaU2S(ConcreteDevice):
    def __init__(self, db_device):
        super().__init__(db_device) 
        self.trait_map = {"action.devices.traits.OnOff": self.query_onoff}
        self.action_map = {"action.devices.commands.OnOff": self.execute_onoff}

    def query(self):
        out = {}
        for trait,queryfunc in self.trait_map.items():
            result = queryfunc()
            if result:
                out.update(result)
            else:
                return None
        return out

    def execute(self, action, parameters):
        if action in self.action_map:
            return self.action_map[action](parameters)
        else:
            raise NotImplementedError("Unrecognised action ", str(action), "for devices", type(self).__name__)

    def sync(self):
        out = self.db_device.generate_common_sync()
        out["willReportState"] = False # TODO: implement ReportState
        out["type"] = "action.devices.types.LIGHT"
        out["traits"] = [*self.trait_map]
        return out


    def execute_onoff(self, parameters):
        device = self.id
        action = "ON" if parameters["on"] else "OFF"
        print("Switching", self.id, action, flush=True)
        publish.single(topic=self.id + "/cmnd/Power", payload=action, hostname=os.environ["MQTT_ADDRESS"], port=int(os.environ["MQTT_PORT"]), auth={'username': os.environ["MQTT_USERNAME"], 'password':os.environ["MQTT_PASSWORD"]})
        return True

    def query_onoff(self):
        pub_topic = self.id + "/cmnd/Power"
        sub_topics = [self.id + "/stat/POWER"]
        rets = mqtt_resp(pub_topic, sub_topics,  2.0)
        result = rets[sub_topics[0]]
        return  {"on" : result == "ON"} if result else None
