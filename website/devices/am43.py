import os
import paho.mqtt.publish as publish
from .common import mqtt_resp, ConcreteDevice

class AM43(ConcreteDevice):
    def __init__(self, db_device):
        super().__init__(db_device)
        self.trait_map = {"action.devices.traits.OpenClose": self.query_openclose}#TODO: other required traits (mode)+battery trait
        self.action_map = {"action.devices.commands.OpenClose": self.execute_openclose}

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
        out["type"] = "action.devices.types.BLINDS"
        out["traits"] = [*self.trait_map]
        return out

    def execute_openclose(self, params):
        if "openPercent" in params:
            percent = params["openPercent"]
            print("Opening", self.id, percent, flush=True)
            publish.single(topic=self.id + "/ctrl", payload=100-percent, hostname=os.environ["MQTT_ADDRESS"], port=int(os.environ["MQTT_PORT"]), auth={'username': os.environ["MQTT_USERNAME"], 'password':os.environ["MQTT_PASSWORD"]})
            return True
        else:
            return False

    def query_openclose(self):
        pub_topic = self.id + "/ctrl"
        sub_topics = [self.id + "/pos", self.id + "/bat"]
        rets = mqtt_resp(pub_topic, sub_topics, 2.0)
        print(rets, flush=True)
        result = rets[self.id + "/pos"]
        return {"openState" : [{"openPercent" : 100 - int(result)}]} if result else None
