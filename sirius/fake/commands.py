"""Fake a few printer interactions for testing.
"""
from __future__ import print_function

import os

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

    print('Created printer')
    print('     address: {}'.format(device_address))
    print('       DB id: {}'.format(printer.id))
    print('      secret: {}'.format(secret))
    print('         xor: {}'.format(xor))
    print('  claim code: {}'.format(cc))


@fake_manager.command
def claim(device_address, owner, code, name):
    user = user_model.User.query.filter_by(username=owner).first()
    if user is None:
        print("User not found: {}".format(owner))

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
