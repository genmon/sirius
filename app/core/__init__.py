from app import sockets

from .events import process_event

import json

class CommandBackend(object):
    """ Interface for registering and updating Websocket clients
    to receive commands. """
    
    def __init__(self):
        self.clients = list()
        self.bridge_commands_queue = {} # bridge_address: [bc]
        self.pending_bridge_command = {} # bridge_address: bc
        self.device_commands_queue = {} # device_address: [dc]
        self.pending_device_command = {} # device_address: dc
        
        self.did_send_image = False
    
    def register(self, ws):
        self.clients.append( WebsocketClient(ws) )
    
    def add_bridge_address(self, bridge_address, ws):
        for c in self.clients:
            if c.ws == ws:
                c.bridge_address = bridge_address
    
    def add_device(self, device_address, ws):
        [c.add_device(device_address) for c in self.clients if c.ws == ws]
    
    def remove_device(self, device_address, ws):
        [c.remove_device(device_address) for c in self.clients if c.ws == ws]

    def send_to_bridge(self, bridge_address, command):
        matches = [c for c in self.clients if c.bridge_address == bridge_address]
        if matches:
            matches[0].ws.send(command.to_json())
        
    def send_to_device(self, device_address, command):
        matches = [c for c in self.clients if c.has_device(device_address)]
        if matches:
            matches[0].ws.send(command.to_json())
    
command_sender = CommandBackend()
#command_sender.run()            

class WebsocketClient(object):
    
    def __init__(self, ws):
        self.ws = ws
        self.bridge_address = None
        self.connected_devices = set() # device_address
    
    def add_device(self, device_address):
        self.connected_devices.add(device_address)
    
    def remove_device(self, device_address):
        self.connected_devices.remove(device_address)
    
    def has_device(self, device_address):
        return device_address in self.connected_devices

# shouldn't be here, should be attached as a blueprint
# there needs to be a single backend object per process
# that allows sockets to register themselves, and remember
# what bridge_address and device_address are present
# then messages can be sent via this object.
# at some point, the object should pass messages around itself
# using redis, so it works over multiple processes
# see https://devcenter.heroku.com/articles/python-websockets
# for a good pattern
@sockets.route('/api/v1/connection') 
def coresocket(ws):
    print "here"
    command_sender.register(ws)
    while True: 
        message = ws.receive()            
        #pprint(message)
       
        try:
            event = json.loads(message)
            process_event(ws, event, command_sender)
        except Exception, e:
            print "Exception: %r" % e