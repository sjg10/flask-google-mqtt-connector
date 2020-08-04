import time
from flask_sqlalchemy import SQLAlchemy
from authlib.integrations.sqla_oauth2 import (
    OAuth2ClientMixin,
    OAuth2AuthorizationCodeMixin,
    OAuth2TokenMixin,
)

db = SQLAlchemy()

class DBArray(db.TypeDecorator):
    impl = db.Text

    def process_bind_param(self, value, dialect):
        # Accept input as \n seperated string or if not as iterable
        if isinstance(value, str):
            return value
        else:
            return "\n".join(value)

    def process_result_value(self, value, dialect):
        return value.split("\n")

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
    keyid = db.Column(db.Integer, primary_key=True)
    id = db.Column(db.String(50), unique=True, default="tasmotaX", nullable=False)
    name = db.Column(db.String(50), unique=True, nullable=False, default="human name")
    nicknames = db.Column(DBArray, nullable=False, default="nicknames\nseperated\nas newlines")
    roomHint = db.Column(db.String(50),nullable=False, default="human readable room")
    manufacturer = db.Column(db.String(50), nullable=False, default="manufacturer")
    model = db.Column(db.String(50), nullable=False, default="model")
    def generate_common_sync(self):
        out = {}
        out["id"] = self.id
        out["name"] = {"name": self.name, "nicknames" : self.nicknames}
        out["roomHint"] = self.roomHint
        out["deviceInfo"] = {"manufacturer": self.manufacturer, "model": self.model}
        return out
    def update(self, d):
        for item, content in d.items():
            setattr(self, item, content)
    @classmethod
    def get_col_type(cls, col):
        if hasattr(cls, col):
            return getattr(cls, col).type
        else:
            return None
        
#Example devices loaded in at boot
devices = [
        {"id" : "tasmota1", 
        "name" : "stair lights",
        "nicknames" : ["stair light", "stairs light", "stairs lights"],
        "roomHint": "downstairs",
        "manufacturer" : "tasmota",
        "model": "u2s"},
        {"id" : "tasmota2", 
        "name" : "table light",
        "nicknames" : ["table lights"],
        "roomHint": "downstairs",
        "manufacturer" : "tasmota",
        "model": "u2s"},
        {"id" : "tasmota3", 
        "name" : "sofa light",
        "nicknames" : ["sofa lights", "corner light", "corner lights"],
        "roomHint": "downstairs",
        "manufacturer" : "tasmota",
        "model": "u2s"},
        {"id" : "tasmota4", 
        "name" : "door light",
        "nicknames" : ["door lights"],
        "roomHint": "downstairs",
        "manufacturer" : "tasmota",
        "model": "u2s"},
        {"id" : "tasmota6", 
        "name" : "cabin light",
        "nicknames" : ["cabin lights", "cabin lamp"],
        "roomHint": "cabin",
        "manufacturer" : "tasmota",
        "model": "u2s"},
        {"id" : "blind1", 
        "name" : "blind",
        "nicknames" : ["blinds"],
        "roomHint": "downstairs",
        "manufacturer" : "A-OK",
        "model": "AM43"}
        ]

def default_devices():
    for d in devices:
        device = Device.query.filter_by(id = d['id']).first()
        if device is None:
            device = Device()
            db.session.add(device)
        device.update(d)
    db.session.commit()
