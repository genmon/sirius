import io
from PIL import Image
import flask
from flask.ext import login

from sirius.protocol import protocol_loop
from sirius.protocol import messages
from sirius.coding import image_encoding


blueprint = flask.Blueprint('admin', __name__)



@blueprint.route('/admin', methods=['GET'])
def admin_landing():
    return flask.render_template(
        'admin.html',
    )

@blueprint.route('/admin/randomly-change-personality', methods=['POST'])
def randomly_change_personality():
    # Restrict to debug for now until we have a proper user management
    # system.
    assert flask.current_app.config['DEBUG'], "Debug not enabled"

    im = image_encoding.threshold(Image.open('./tests/normalface.png'))

    msg = messages.SetPersonality(
        device_address='000d6f000273ce0b',
        face_pixels=im,
        nothing_to_print_pixels=image_encoding.default_pipeline('Nothing to print'),
        cannot_see_bridge_pixels=image_encoding.default_pipeline('Cannot see bridge'),
        cannot_see_internet_pixels=image_encoding.default_pipeline('Cannot see internet'),
    )
    success, next_print_id = protocol_loop.send_message(
        '000d6f000273ce0b', msg)

    if success:
        flask.flash('Sent your message to the printer!')
    else:
        flask.flash(("Could not send message because the "
                     "printer {} is offline.").format('000d6f000273ce0b'),
                    'error')

    return flask.redirect('/admin')
