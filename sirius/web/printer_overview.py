import flask
from flask.ext import login
from sqlalchemy import desc

from sirius.models import hardware
from sirius.models import messages

blueprint = flask.Blueprint('printer_overview', __name__)


@login.login_required
@blueprint.route('/printer/<int:printer_id>')
def printer_overview(printer_id):
	printer = hardware.Printer.query.get(printer_id)
	if printer is None:
		flask.abort(404)
	
	# only show messages history to printer owner
	if printer.owner.id == login.current_user.id:
		messages.Message.timeout_updates()
		message_list = printer.messages.order_by(desc('created'))
	else:
		message_list = []

	# TODO - pagination?
	return flask.render_template(
		'printer_overview.html',
		printer=printer,
		messages=message_list[:10],
	)
