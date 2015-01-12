import flask

from flask.ext import login

blueprint = flask.Blueprint('landing', __name__)


@blueprint.route('/')
def landing():
    if not login.current_user.is_authenticated():
        return flask.render_template('landing.html')

    return printer_overview()


@login.login_required
def printer_overview():
    return "Hi"
