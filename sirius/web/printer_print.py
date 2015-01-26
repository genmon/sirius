import datetime
import flask
from flask.ext import login
import flask_wtf
import wtforms
import base64

from sirius.models.db import db
from sirius.models import hardware
from sirius.models import messages as model_messages
from sirius.protocol import protocol_loop
from sirius.protocol import messages
from sirius.coding import image_encoding


blueprint = flask.Blueprint('printer_print', __name__)


class PrintForm(flask_wtf.Form):
    target_printer = wtforms.SelectField(
        'Printer',
        coerce=int,
        validators=[wtforms.validators.DataRequired()],
    )
    message = wtforms.TextAreaField(
        'Message',
        validators=[wtforms.validators.DataRequired()],
    )


@login.login_required
@blueprint.route('/<int:user_id>/<username>/printer/<int:printer_id>/print', methods=['GET', 'POST'])
def printer_print(user_id, username, printer_id):
    assert user_id == login.current_user.id
    assert username == login.current_user.username

    printer = hardware.Printer.query.get(printer_id)
    if printer is None:
        flask.abort(404)

    form = PrintForm()
    # Note that the form enforces access permissions: People can't
    # submit a valid printer-id that's not owned by the user or one of
    # the user's friends.
    choices = [
        (x.id, x.name) for x in login.current_user.printers
    ] + [
        (x.id, x.name) for x in login.current_user.friends_printers()
    ]
    form.target_printer.choices = choices
    form.target_printer.data = printer.id

    if form.validate_on_submit():
        # TODO: move image encoding into a pthread.
        # TODO: use templating to avoid injection attacks
        pixels = image_encoding.html_to_png(
            '<html><body>{}</body></html>'.format(form.message.data))
        hardware_message = messages.SetDeliveryAndPrint(
            device_address=printer.device_address,
            pixels=pixels,
        )

        # If a printer is "offline" then we won't find the printer
        # connected and success will be false.
        success, next_print_id = protocol_loop.send_message(
            printer.device_address, hardware_message)

        if success:
            flask.flash('Sent your message to the printer!')
        else:
            flask.flash(("Could not send message because the "
                         "printer {} is offline.").format(printer.name),
                        'error')

        # Store the same message in the model.
        model_message = model_messages.Message(
            print_id=next_print_id,
            pixels=bytearray(pixels),
            sender_id=login.current_user.id,
            target_printer=printer,
        )
        if not success:
            model_message.failure_message = 'Printer offline'
            model_message.response_timestamp = datetime.datetime.utcnow()
        db.session.add(model_message)

        return flask.redirect(flask.url_for(
            'printer_overview.printer_overview',
            user_id=login.current_user.id,
            username=login.current_user.username,
            printer_id=printer.id))

    return flask.render_template(
        'printer_print.html',
        printer=printer,
        form=form,
    )


@blueprint.route('/<int:user_id>/<username>/printer/<int:printer_id>/preview', methods=['POST'])
@login.login_required
def preview(user_id, username, printer_id):
    assert user_id == login.current_user.id
    assert username == login.current_user.username

    message = flask.request.data

    print "M", message

    pixels = image_encoding.html_to_png(
        '<html><body>{}</body></html>'.format(message))

    return '<img style="width: 6cm;" src="data:image/png;base64,{}">'.format(base64.b64encode(pixels))
