import os
from .common import ConcreteDevice
from threading import Lock
import serial

class TH585LL():
    def __init__(self, serial_address):
        self.lock = Lock()
        self.serial = serial.Serial(serial_address,baudrate=115200,timeout=5) # TODO: add close to destructor #TODO: handle failure
    def _write(self, target, action):
        self.lock.acquire()
        command = f"\r*{target}={action}#\r"
        b=self.serial.write(command.encode()) #TODO: handle failure
        cmd_echo = self.serial.readline() #TODO: handle failure
        self.lock.release()
        print("WRITE", command,cmd_echo, flush=True)
        return b, cmd_echo
    def _read(self, target):
        self.lock.acquire()
        command = f"\r*{target}=?#\r".encode()
        self.serial.write(command)
        cmd_echo = self.serial.readline() #TODO: handle failure
        result = self.serial.readline() #TODO: handle failure
        self.lock.release()
        print("READ", cmd_echo, command, result, flush=True) # TODO: check cmd_echo is correct
        success=True # TODO
        return success, result
    SOURCES = ["HDMI", "HDMI2", "RGB"]
    def parse_result(self, result):
        try:
            startindex = result.index(b'=')
            endindex = result.index(b'#')
            return result[startindex + 1: endindex]
        except ValueError:
            return None
    def set_power(self, on): return self._write("POW", "ON" if on else "OFF")
    def get_power(self): return self._read("POW")
    def set_source(self, source): return self._write("SOUR", source)
    def get_source(self): return self._read("SOUR")
    def set_volume(self, vol): return self._write("VOL", vol)
    def get_volume(self): return self._read("VOL")
    def set_mute(self, on): return self._write("MUTE", b'ON' if on else 'OFF')
    def get_mute(self): return self._read("MUTE")
    def get_baud(self): return self._read("BAUD")



class TH585(ConcreteDevice):
    def __init__(self, db_device):
        super().__init__(db_device) 
        self.th585=TH585LL(self.id)# TODO: add close to destructor #TODO: handle failure
        self.trait_map = {"action.devices.traits.OnOff": self.query_onoff, "action.devices.traits.InputSelector": self.query_getinput, "action.devices.traits.Volume": self.query_volume, "action.devices.traits.AppSelector": None, "action.devices.traits.MediaState": None, "action.devices.traits.TransportControl": None}
        self.attribute_map = [self.attributes_setinput, self.attributes_volume,self.attributes_applications, self.attributes_transport]
        self.action_map = {"action.devices.commands.OnOff": self.execute_onoff, "action.devices.commands.setInput": self.execute_setinput, "action.devices.commands.mute": self.execute_mute, "action.devices.commands.setVolume": self.execute_setvolume}

    def query(self):
        out = {}
        for trait,queryfunc in self.trait_map.items():
            if queryfunc is not None:
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
        out["type"] = "action.devices.types.TV"
        out["traits"] = [*self.trait_map]
        out["attributes"] = {}
        for d in self.attribute_map:
            out["attributes"].update(d())
        return out

    def attributes_applications(self):
        return {"availableApplications": []}

    def attributes_transport(self):
        return {"transportControlSupportedCommands": []}

    def attributes_setinput(self): #action.devices.traits.InputSelector
        def generate_device(key, names):
            ret = {}
            ret["key"] = key
            ret["names"] = []
            ret["names"].append({})
            ret["names"][0]["lang"] = "en"
            ret["names"][0]["name_synonym"] = names
            return ret;
        ret = {}
        ret["availableInputs"] = []
        ret["availableInputs"].append(generate_device("HDMI",  ["hdmi 1"]))
        ret["availableInputs"].append(generate_device("HDMI2", ["hdmi 2"]))
        ret["availableInputs"].append(generate_device("RGB", ["rgb"]))
        ret["orderedInputs"] = False
        return ret

    def query_getinput(self): #action.devices.traits.InputSelector
        curInput = self.th585.get_source()
        if curInput[0]:
            res = self.th585.parse_result(curInput[1])
            if res is not None:
                return {"currentInput": res.decode('utf-8')}
            else:
                return {"currentInput": ""}
        return None #TODO: handle failure

    def execute_setinput(params): #action.devices.commands.setInput
        res = self.th585.set_source(params["newInput"])
        return res[0] #TODO: handle failure
        """
        Supports: (as action.devices.types.TV)
        action.devices.traits.InputSelector
            action.devices.commands.setInput

        action.devices.traits.OnOff
            action.devices.commands.OnOff

        action.devices.traits.Volume

            action.devices.commands.mute
            action.devices.commands.setVolume
        """

    def execute_onoff(self, parameters):
        self.th585.set_power(parameters["on"])
        return True # TODO: handle failure

    def query_onoff(self):
        result = self.th585.get_power()
        return  {"on" : result[1][5:7] == b'ON'} if result[0] else None # TODO: handle failure


    def attributes_volume(self):
        ret = {}
        ret["volumeMaxLevel"] = 20
        ret["volumeCanMuteAndUnmute"] = True
        return ret

    def query_volume(self):
        suc1, currentVolume = self.th585.get_volume()
        suc2, currentMute = self.th585.get_mute()
        if suc1: 
            res = self.th585.parse_result(currentVolume)
            if res is not None:
                currentVolume = int(res)
            else:
                return {"currentVolume": 0,"isMuted": False} # Dummy data when device is off
        if suc2:
            res = self.th585.parse_result(currentMute)
            if res is not None:
                currentMute = (res == b'ON')
            else:
                return {"currentVolume":currentVolume,"isMuted": False} # Dummy data when device is off
        if suc1 and suc2:
            return {"currentVolume":int(currentVolume),"isMuted": currentMute}
        else: return None

    def execute_mute(self, parameters):
        self.th585.set_mute(parameters["mute"])
        return True # TODO: handle failure

    def execute_setvolume(self, parameters):
        self.th585.set_volume(str(parameters["volumeLevel"]))
        return True # TODO: handle failure
