from flask import Blueprint, render_template

from app.models.core import Device

import pprint

main = Blueprint('main', __name__)

@main.route('/')
def index():
	devices = Device.query.all()
	
	return render_template('index.html', devices=devices)

@main.route('/device/<device_address>')
def device(device_address):
	device = Device.query.get_or_404(device_address)

	return render_template('dump.html', dump=pprint.pformat(device))
