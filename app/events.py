from . import commands
from .payload import DeviceEventPayload
from . import claiming

from datetime import datetime

# process_event should...
# - break apart the event
# - handle internally by saving/modifying state to current_app
# - deal with claiming
# - create DeviceEvent models and propagate out if necessary
# all of this is happening within a try:except: in the event loop,
# so don't be afraid to crash out

class PendingClaims(object):
    
    def __init__(self):
        self.encryption_keys = {} # hardware_address_xor: encryption_key
    
    def add_claim_code(self, claim_code):
        hardware_address_xor, encryption_key = claiming.process_claim_code(claim_code)
        #@TODO handle exception
        
        self.encryption_keys[hardware_address_xor] = encryption_key
    
    def key_for_address(self, device_address):
        hardware_address_xor = claiming.make_hardware_address_xor(device_address)
        return self.encryption_keys.get(hardware_address_xor, None)

pending_claims = PendingClaims()


class EventProcessingException(Exception): pass

# @TODO command_sender shouldn't be passed in here, and of course it
# shouldn't be horribly synchronous like it is

def process_event(ws, event, command_sender):
    print "Received event type %r" % event['type']
    if event['type'] == 'DeviceEvent':
        # unwrap here, even though it breaks abstraction... three event
        # types: heartbeat, did_print, did_power_on
        # see device_event.py in hubcode
        payload = DeviceEventPayload.from_base64(event['binary_payload'])
        timestamp = datetime.fromtimestamp(event['timestamp'])
        print "DeviceEvent: %r at %s" % (payload['name'], timestamp.isoformat())
        if payload['name'] == 'heartbeat':
            if command_sender.did_send_image is False:
                print "Sending set_delivery_and_print"
                dc = commands.set_delivery_and_print()
                command_sender.send_to_device(event['device_address'], dc)
                command_sender.did_send_image = True
    elif event['type'] == 'BridgeEvent':
        # unwrap here. use device_connect and device_disconnect to
        # change the command delivery map. there is also power_on,
        # encryption_key_required [4 events are all I can find]
        event_name = event['json_payload']['name']
        timestamp = datetime.fromtimestamp(event['timestamp'])
        print "BridgeEvent: %r at %s" % (event_name, timestamp.isoformat())
        if event_name == 'device_connect':
            command_sender.add_device(event['json_payload']['device_address'], ws)
        elif event_name == 'device_disconnect':
            command_sender.remove_device(event['json_payload']['device_address'], ws)
        elif event_name == 'power_on':
            command_sender.add_bridge_address(event['bridge_address'], ws)
        elif event_name == 'encryption_key_required':
            print "Sending add_device_encryption_key"
            bc = commands.add_device_encryption_key()
            command_sender.send_to_bridge(event['bridge_address'], bc)
        else:
            raise EventProcessingException("Unknown BridgeEvent command name: %r" % command_name)
        pass
    elif event['type'] == 'BridgeLog':
        # print it or something
        pass
    elif event['type'] == 'BridgeCommandResponse':
        # if the return_code is 0 or not set, set state as delivered
        # else mark it as failed
        # (what happens if there is never any update? is there a timeout?)
        # (30 minute time-out in the command gate)
        pass
    elif event['type'] == 'DeviceCommandResponse':
        # if the return_code is 0, set state as delivered
        # else mark it as failed
        # (what happens if there is never any update? is there a timeout?)
        pass
    else:
        raise EventProcessingException("Unknown event type: %r" % event['type'])
