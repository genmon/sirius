from . import db

import json

# BridgeCommand has
# - timestamp (datetime in UTC)
# - bridge_address (store the hex value as a string)
# - id (primary key)
# - return_code -- init as null, integer
# - json_payload -- text
class BridgeCommand(db.Model):
    __tablename__ = 'bridge_commands'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False)
    bridge_address = db.Column(db.String, nullable=False)
    json_payload = db.Column(db.UnicodeText, nullable=False)
    return_code = db.Column(db.SmallInteger, nullable=True)

    def to_json(self):
        try:
            json_payload = json.loads(self.json_payload)
        except:
            json_payload = None
        json_hash = {
            'type': 'BridgeCommand',
            'bridge_address': self.bridge_address,
            'command_id': self.id,
            'json_payload': json_payload,
            'timestamp': self.timestamp.isoformat()
        }
        return json.dumps(json_hash, encoding='utf-8')

# DeviceCommand has
# - device_address (store the hex value as a string)
# - id (primary key)
# - binary_payload (store base64 encoded)
# - state (ready, failed, delivered, skipped)
# - deliver_at (timestamp)
class DeviceCommand(db.Model):
    __tablename__ = 'device_commands'
    id = db.Column(db.Integer, primary_key=True)
    device_address = db.Column(db.String, nullable=False)
    binary_payload = db.Column(db.Text, nullable=False)
    state = db.Column(db.Enum('ready', 'failed', 'delivered', 'skipped'), nullable=False)
    deliver_at = db.Column(db.DateTime, nullable=False)
    
    def to_json(self):
        json_hash = {
            'command_id': self.id,
            'type': 'DeviceCommand',
            'device_address': self.device_address,
            'binary_payload': self.binary_payload
        }
        return json.dumps(json_hash, encoding='utf-8')
