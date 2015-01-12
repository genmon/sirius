import flask

from flask.ext import login

blueprint = flask.Blueprint('printer_print', __name__)


@login.login_required
@blueprint.route('/<int:user_id>/<username>/print')
def printer_print(user_id, username):
    assert user_id == login.current_user.id
    assert username == login.current_user.username

    return flask.render_template('printer_print.html')
