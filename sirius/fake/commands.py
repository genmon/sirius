"""Fake a few printer interactions for testing.
"""
from __future__ import print_function

import os
import sys

from flask.ext import script
from sirius.models import hardware
from sirius.models import user as user_model
from sirius.models.db import db
from sirius.coding import bitshuffle
from sirius.coding import claiming


def sub_opts(app, **kwargs):
    pass


fake_manager = script.Manager(sub_opts, usage="Fake printer interactions.")


@fake_manager.command
def printer():
    device_address = os.urandom(8).encode('hex')
    xor = bitshuffle.hardware_xor_from_device_address(device_address)
    secret = os.urandom(5).encode('hex')

    cc = claiming.encode(xor, int(secret, 16))
    printer = hardware.Printer(
        device_address=device_address,
        hardware_xor=xor,
    )
    db.session.add(printer)
    db.session.commit()

    def out(x):
        x.write('     address: {}\n'.format(device_address))
        x.write('       DB id: {}\n'.format(printer.id))
        x.write('      secret: {}\n'.format(secret))
        x.write('         xor: {}\n'.format(xor))
        x.write('  claim code: {}\n'.format(cc))

    path = device_address + '.printer'
    with open(path, 'w') as f:
        out(f)

    out(sys.stdout)
    print('\nCreated printer and saved as {}'.format(path))


@fake_manager.command
def claim(device_address, owner, code, name):
    user = user_model.User.query.filter_by(username=owner).first()
    if user is None:
        print("User not found: {}".format(owner))
        return

    hardware.Printer.phone_home(device_address)
    user.claim_printer(code, name)


@fake_manager.command
def user(screen_name):
    new_user = user_model.User(
        username=screen_name,
    )
    oauth = user_model.TwitterOAuth(
        user=new_user,
        screen_name=screen_name,
        token='token',
        token_secret='secret',
    )
    db.session.add(new_user)
    db.session.add(oauth)
    db.session.commit()
