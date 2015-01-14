"""Fake a few printer interactions for testing.
"""
import os

from flask.ext import script
from sirius.models import hardware
from sirius.coding import bitshuffle

def sub_opts(app, **kwargs):
    pass

fake_manager = script.Manager(sub_opts, usage="Fake printer interactions.")

@fake_manager.command
def create_printer():
    device_address = os.urandom(8).encode('hex')
    xor = bitshuffle.hardware_xor_from_device_address(device_address)

    claim_code = ''

    hardware.Printer(
    )
