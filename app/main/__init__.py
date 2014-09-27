from flask import Blueprint, render_template, flash, current_app
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
	sender = current_app.sender
	
	if form.validate_on_submit():
		html = """<html><body><h1>Hello, World!</h1><p>My name is Little Printer</p></html>"""
		flash('Form submitted')
		q = sender.for_device(device)
		if q is not None:
			dc = set_delivery_and_print(device.device_address, html=html)
			q.queue_device_command(dc)
	return render_template('dump.html', dump=pprint.pformat(device), form=form)
