import flask
from flask.ext import login
from sqlalchemy import desc

from sirius.models import hardware
from sirius.models import messages

blueprint = flask.Blueprint('printer_overview', __name__)


@login.login_required
@blueprint.route('/<int:user_id>/<username>/printer/<int:printer_id>')
def printer_overview(user_id, username, printer_id):
    assert user_id == login.current_user.id
    assert username == login.current_user.username

    printer = hardware.Printer.query.get(printer_id)
    if printer is None:
        flask.abort(404)

    messages.Message.timeout_updates()
    message_list = printer.messages.order_by(desc('created'))

    # TODO - pagination?
    return flask.render_template(
        'printer_overview.html',
        printer=printer,
        messages=message_list[:10],
    )
