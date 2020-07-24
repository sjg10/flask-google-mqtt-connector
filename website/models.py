import time
from flask_sqlalchemy import SQLAlchemy
from authlib.integrations.sqla_oauth2 import (
    OAuth2ClientMixin,
    OAuth2AuthorizationCodeMixin,
    OAuth2TokenMixin,
)

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(40), unique=True)

    def __str__(self):
        return self.username

    def get_user_id(self):
        return self.id

    def check_password(self, password):
        return password == 'valid'


class OAuth2Client(db.Model, OAuth2ClientMixin):
    __tablename__ = 'oauth2_client'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))
    user = db.relationship('User')


class OAuth2AuthorizationCode(db.Model, OAuth2AuthorizationCodeMixin):
    __tablename__ = 'oauth2_code'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))
    user = db.relationship('User')


class OAuth2Token(db.Model, OAuth2TokenMixin):
    __tablename__ = 'oauth2_token'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))
    user = db.relationship('User')

    def is_refresh_token_active(self):
        if self.revoked:
            return False
        expires_at = self.issued_at + self.expires_in * 2
        return expires_at >= time.time()

class Device(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(50), unique=True)
    device_type = db.Column(db.String(50))
    traits = db.Column(db.String(200))
    name = db.Column(db.String(50), unique=True)
    nicknames = db.Column(db.String(200))
    willReportState = db.Column(db.Integer)
    roomHint = db.Column(db.String(50))
    array_sep = ':'
    def syncdict(self):
        out = {}
        out["id"] = self.device_id
        out["type"] = self.device_type
        out["traits"] = self.traits.split(self.array_sep)
        out["name"] = {"name": self.name, "nicknames" : self.nicknames.split(self.array_sep)}
        out["willReportState"] = bool(self.willReportState)
        out["roomHint"] = self.roomHint
        return out
    def update_from_syncdict(self, d):
        self.device_id = d["id"]
        self.device_type = d["type"]
        self.traits = self.array_sep.join(d["traits"])
        self.name = d["name"]["name"]
        self.nicknames = self.array_sep.join( d["name"]["nicknames"])
        self.willReportState = int(d["willReportState"])
        self.roomHint = d["roomHint"]


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

def default_devices():
    for d in devices:
        device = Device.query.filter_by(device_id = d['id']).first()
        if device is None:
            device = Device()
            db.session.add(device)
        device.update_from_syncdict(d)
    db.session.commit()
