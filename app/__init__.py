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
    
    # shouldn't be here, should be attached as a blueprint
    @sockets.route('/api/v1/connection') 
    def echo_socket(ws):
        print "here"
        done_once = False
        counting = 0
        while True: 
            message = ws.receive()            
            pprint(message)
            print ""
            
            # temporary logic
            try:
                event = json.loads(message)
                if event['type'] == 'BridgeEvent' and event['json_payload']['name'] == 'encryption_key_required':
                    print "==> encryption_key_required"
                    j = commands.add_device_encryption_key().to_json()
                    ws.send(j)
                    #gevent.sleep(0.5)
                    #print "===> %s" % j
                    #j = commands.set_delivery_and_print().to_json()
                    #ws.send(j)
                if event['type'] == 'DeviceEvent':
                    counting += 1
                    if counting == 4:
                        gevent.sleep(0.5)
                        j = commands.set_delivery_and_print().to_json()
                        ws.send(j)
                        print "===> tried to send image"
                        pprint(j)
                        done_once = True
            except:
                pass
            
            #ws.send(message)
      
    return app
