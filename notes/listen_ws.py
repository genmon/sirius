"""We accept commands from two sources: The web-UI and from the
individual bridges connecting through websockets.
"""

import collections
from eventlet import wsgi, websocket
import eventlet
import json


@websocket.WebSocketWSGI
def bridge(ws):
    print "accepted", ws
    while True:
        data = json.loads(ws.wait())
        print data
        if data['type'] == 'BrideEvent':
            if data['json_payload']['name'] == 'encryption_key_required':
                ws.send('{name = "add_device_encryption_key"}')

wsgi.server(eventlet.listen(('', 5002)), bridge)
