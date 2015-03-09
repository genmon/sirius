"""Main server entry. Run like:

$ bin/gunicorn -k flask_sockets.worker sirius.server:app -b 0.0.0.0:5002 -w 1
"""
# Temporary hack until gevent fixes
# https://github.com/gevent/gevent/issues/477.
import _gevent_polyfill

import gevent
import logging
import flask
import flask_sockets
from flask.ext import bootstrap

from sirius.protocol import protocol_loop
from sirius import stats
from sirius import config

# Import models so they get picked up for migrations. Do not remove.
from sirius.models import db
from sirius.models import user
from sirius.models import hardware
from sirius.models import messages

from sirius.web import landing
from sirius.web import twitter
from sirius.web import login
from sirius.web import admin
from sirius.web import printer_print
from sirius.web import printer_overview


logger = logging.getLogger(__name__)
bootstrap = bootstrap.Bootstrap()
sockets = flask_sockets.Sockets()


def create_app(config_name):
    app = flask.Flask(__name__)
    app.config.from_object(config.config[config_name])
    config.config[config_name].init_app(app)

    # Configure various plugins and logging
    bootstrap.init_app(app)
    db.db.init_app(app)
    sockets.init_app(app)
    login.manager.init_app(app)
    logging.basicConfig(level=logging.DEBUG if app.debug else logging.INFO)

    # Register blueprints
    app.register_blueprint(stats.blueprint)
    app.register_blueprint(landing.blueprint)
    app.register_blueprint(twitter.blueprint)
    app.register_blueprint(printer_overview.blueprint)
    app.register_blueprint(printer_print.blueprint)
    app.register_blueprint(admin.blueprint)

    # Live interactions.
    gevent.spawn(protocol_loop.mark_dead_loop)
    @sockets.route('/api/v1/connection')
    def api_v1_connection(ws):
        with app.app_context():
            protocol_loop.accept(ws)

    logger.debug('Creating app.')
    return app
