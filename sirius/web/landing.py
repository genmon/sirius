import flask

from sirius.web import login

blueprint = flask.Blueprint('landing', __name__)


@blueprint.route('/')
def landing():
    return flask.render_template('index.html')
