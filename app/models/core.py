from app import db

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
    state = db.Column(db.Enum('ready', 'failed', 'delivered', 'skipped'), nullable=False)
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
    return_code = db.Column(db.SmallInteger, nullable=True)
    
    def to_json(self):
        json_hash = {
            'command_id': self.id,
            'type': 'DeviceCommand',
            'device_address': self.device_address,
            'binary_payload': self.binary_payload
        }
        return json.dumps(json_hash, encoding='utf-8')

class Bridge(db.Model):
    __tablename__ = 'bridges'
    bridge_address = db.Column(db.String, primary_key=True)
    last_power_on = db.Column(db.DateTime, nullable=True) #@TODO should be false
    
    @classmethod
    def get_or_create(cls, bridge_address):
        b = cls.query.get(bridge_address)
        if b is None:
            b = cls(bridge_address=bridge_address)
            db.session.add(b)
            db.session.commit()
        return b           


class Device(db.Model):
    __tablename__ = 'devices'
    device_address = db.Column(db.String, primary_key=True)
    hardware_xor = db.Column(db.Integer, nullable=False)
    
    @classmethod
    def get_or_create(cls, device_address):
        d = cls.query.get(device_address)
        if d is None:
            d = cls(device_address=device_address,
                    hardware_xor=Device.make_hardware_xor(device_address))
            db.session.add(d)
            db.session.commit()
        return d
    
    @staticmethod
    def make_hardware_xor(device_address):
        # the hardware_xor from device_address 000d6f000273ce0b
        # should match the hardware_xor from claim_code
        # ps2f-gsjg-8wsq-7hc4
        # and (I think) 000d6f00015ff77f should lead to 6290192
        # and match claim code 6xwh441j8115zyrh
        # and this 0011223344aabb01 leads to 10087971
        b = bytearray.fromhex(device_address)
        
        # little endian
        b.reverse()
    
        claim_address = bytearray(3)
        claim_address[0] = b[0] ^ b[5]
        claim_address[1] = b[1] ^ b[3] ^ b[6]
        claim_address[2] = b[2] ^ b[4] ^ b[7]

        result = claim_address[2] << 16 | claim_address[1] << 8 | claim_address[0]
    
        return result


class PendingClaim(db.Model):
    __tablename__ = 'pending_claims'
    id = db.Column(db.Integer, primary_key=True)
    claim_code = db.Column(db.String, nullable=False)
    hardware_xor = db.Column(db.String, nullable=False)
