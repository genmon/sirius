import flask

from flask.ext import login

blueprint = flask.Blueprint('landing', __name__)


@blueprint.route('/')
def landing():
    if not login.current_user.is_authenticated():
        return flask.render_template('landing.html')

    return overview()


@login.login_required
def overview():
    my_printers = login.current_user.printers.all()

    return flask.render_template(
        'overview.html',
        my_printers=my_printers,
    )
