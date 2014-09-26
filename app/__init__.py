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
    
    from .admin import admin as admin_blueprint
    app.register_blueprint(admin_blueprint, url_prefix='/admin')
    
    #from .core import coresocket
    from .core.events import process_event
    #from .core.command_sender import CommandSender

    from queues import CommandSender
    sender = CommandSender()
    sender.run()
    app.sender = sender

    @sockets.route('/api/v1/connection') 
    def coresocket(ws):
        print "here"
        while True: 
            message = ws.receive()            
            #pprint(message)
       
            #try:
            event = json.loads(message)
            with app.request_context(ws.environ):
                process_event(ws, event, sender)
            #except Exception, e:
            #    print "Exception: %r" % e
    
    return app
