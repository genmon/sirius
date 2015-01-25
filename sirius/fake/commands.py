"""Fake a few printer interactions for testing.
"""
from __future__ import print_function

import os

from flask.ext import script
from sirius.models import hardware
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
