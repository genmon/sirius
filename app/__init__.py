from flask import Flask, render_template
from flask.ext.bootstrap import Bootstrap
from flask.ext.sqlalchemy import SQLAlchemy
from flask_sockets import Sockets
from config import config

from pprint import pprint
import json
import gevent

bootstrap = Bootstrap()
db = SQLAlchemy()
sockets = Sockets()

from . import commands
from events import process_event


# @TODO
# for this to work, I have to put the following line at line 38 of
# flask_sockets, to inject it into the environment
# environment.environ['HTTP_SEC_WEBSOCKET_PROTOCOL'] = 'bergcloud-bridge-v1'
def protocol_name():
    print "asked for protocol"
    return 'bergcloud-bridge-v1'

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    bootstrap.init_app(app)
    db.init_app(app)
    sockets.init_app(app)

    # maybe this sets the HTTP_SEC_WEBSOCKET_PROTOCOL ?
    app.protocol_name = protocol_name

    # attach routes and custom error pages
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
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
    def echo_socket(ws):
        print "here"
        done_once = False
        counting = 0
        command_sender.register(ws)
        while True: 
            message = ws.receive()            
            #pprint(message)
           
            try:
                event = json.loads(message)
                process_event(ws, event, command_sender)
            except Exception, e:
                print "Exception: %r" % e
      
    return app
