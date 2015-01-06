"""Main server entry. Run like:

$ bin/gunicorn -k flask_sockets.worker sirius.server:app -b 0.0.0.0:5002 -w 1
"""

import logging
import flask
import flask_sockets

from sirius.protocol import protocol_loop
from sirius import stats
from sirius import config

logger = logging.getLogger(__name__)


def create_app(config):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    bootstrap.init_app(app)
    db.init_app(app)
    sockets.init_app(app)

    logging.basicConfig(level=logging.DEBUG if app.debug else logging.INFO)

    @app.route('/_/stats')
    def showstats():
        "Expose some trivial stats"
        return stats.as_text()

    @sockets.route('/api/v1/connection')
    def api_v1_connection(ws):
        protocol_loop.accept(ws)

    logger.info('Creating app.')
    return app


app = create_app()
