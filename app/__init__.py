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
    
    from .core import socket, command_sender
      
    return app
