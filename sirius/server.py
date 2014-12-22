"""Main server entry. Run like:

$ bin/gunicorn -k flask_sockets.worker sirius.server:app -b 0.0.0.0:5002 -w 1
"""

import logging
import flask
import flask_sockets

from sirius.protocol import protocol_loop
from sirius import stats

logger = logging.getLogger(__name__)


def create_app():
    sockets = flask_sockets.Sockets()

    logging.basicConfig(level=logging.DEBUG)

    app = flask.Flask(__name__)
    app.debug = True
    sockets.init_app(app)

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
