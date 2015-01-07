import flask

blueprint = flask.Blueprint('landing', __name__)


@blueprint.route('/')
def landing():
    return flask.render_template('index.html')
