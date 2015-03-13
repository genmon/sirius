"""Fake a few printer interactions for testing.
"""
from __future__ import print_function

import os
import gevent
import gevent.monkey
gevent.monkey.patch_all()
import websocket
import json
import re
import random
import time
import struct
import base64

from flask.ext import script

from sirius.emulate import protocol_fragments as pf

def sub_opts(app, **kwargs):
    pass

manager = script.Manager(
    sub_opts, usage="Emulate a real printer, websockets and all.")


class State:
    """Keep track of printer state. Only one per process so global state
    is OK."""
    online = True
    needs_key = True
    device_address = None
    bridge_address = None

def heartbeat(ws):
    while True:
        if (State.online, State.needs_key) == (True, True):
            ws.send(pf.ENCRYPTION_KEY_REQUIRED %
                    dict(bridge_address=State.bridge_address,
                         device_address=State.device_address))
            print("Asked for encryption key")
            gevent.sleep(30.0) # key request is sent every 30s
        elif (State.online, State.needs_key) == (True, False):
            ws.send(pf.HEARTBEAT %
                    dict(bridge_address=State.bridge_address,
                         device_address=State.device_address))
            print("Heartbeat. Pom pom.")
            gevent.sleep(10.0) # heartbeate is sent every 10s
        elif State.online == False:
            gevent.sleep(10.0) # sleep for a while to burn cycles

        else:
            assert False # unreachable


def _decode_binary(base64_data):
    bdata = base64.b64decode(base64_data)
    _, _, command, print_id, _, length = struct.unpack("<BBHIII", bdata[:16])

    print("command", command, print_id, length)


def _decode(data):
    try:
        data = json.loads(data)
    except ValueError as e:
        print("Server sent invalid JSON!", e)
        return

    if data['type'] == 'BridgeCommand':
        key = data['json_payload'].get('params', {}).get('encryption_key')
        print("Received encryption key, switching to heartbeat mode.")
        State.needs_key = False

    if data['type'] == 'DeviceCommand':
        payload = data['binary_payload']
        command_id = data['command_id']

        _decode_binary(payload)

        # TODO(tom): Decode binary payload for debugging.

        return {u'device_address': State.device_address,
                u'timestamp': time.time(),
                u'transfer_time': 3.44,
                u'bridge_address': State.bridge_address,
                u'return_code': 0,
                u'rssi_stats': [-19,-19,-19],
                u'type': u'DeviceCommandResponse',
                u'command_id': command_id}


@manager.command
def printer(printer_data_path, websocket_url):

    with open(printer_data_path) as f:
        printer_data = f.read()

    print("Contacting", websocket_url)
    print(printer_data)
    print("-----------------------------")

    # Parse data from printer file
    State.device_address = re.search('address: ([a-f0-9]{16})', printer_data).group(1)
    State.bridge_address = '{:016x}'.format(random.randrange(0, 2**64))

    # Sanity check websocket connection URL:
    if not websocket_url.endswith('/api/v1/connection'):
        print("Websocket URL must end with '/api/v1/connection'")
        print("Maybe you meant {}/api/v1/connection ?".format(websocket_url))
        return 1

    # Connect and initialize
    ws = websocket.create_connection(websocket_url)
    ws.send(pf.CONNECT % dict(bridge_address=State.bridge_address))

    gevent.spawn(heartbeat, ws)

    try:
        while True:
            data = ws.recv()
            response = _decode(data)
            if response is not None:
                ws.send(json.dumps(response))

    finally:
        ws.close()
