from flask import Blueprint, render_template, flash
from flask.ext.wtf import Form
from wtforms import StringField, TextAreaField, BooleanField, SelectField,\
    SubmitField

from app.models.core import Device
from app.core.commands import set_delivery_and_print

import pprint

main = Blueprint('main', __name__)

class SendDeliveryForm(Form):
	submit = SubmitField('Send Delivery')

@main.route('/')
def index():
	devices = Device.query.all()
	
	return render_template('index.html', devices=devices)

@main.route('/device/<device_address>', methods=['GET', 'POST'])
def device(device_address):
	device = Device.query.get_or_404(device_address)
	form = SendDeliveryForm()
	
	if form.validate_on_submit():
		flash('Form submitted')
		#dc = set_delivery_and_print(device_address)
		# now queue it, but where?
	return render_template('dump.html', dump=pprint.pformat(device), form=form)
