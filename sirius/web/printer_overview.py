import flask
from flask.ext import login

from sirius.models import hardware

blueprint = flask.Blueprint('printer_overview', __name__)


@login.login_required
@blueprint.route('/<int:user_id>/<username>/printer/<int:printer_id>')
def printer_overview(user_id, username, printer_id):
    assert user_id == login.current_user.id
    assert username == login.current_user.username

    printer = hardware.Printer.query.get(printer_id)
    if printer is None:
        flask.abort(404)

    return flask.render_template(
        'printer_overview.html',
        printer=printer,
    )
