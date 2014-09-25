from app import sockets

from .events import process_event
from .command_sender import CommandSender

import json

#sender = CommandSender()
#sender.run()

# shouldn't be here, should be attached as a blueprint
# there needs to be a single backend object per process
# that allows sockets to register themselves, and remember
# what bridge_address and device_address are present
# then messages can be sent via this object.
# at some point, the object should pass messages around itself
# using redis, so it works over multiple processes
# see https://devcenter.heroku.com/articles/python-websockets
# for a good pattern
#@sockets.route('/api/v1/connection') 
def coresocket(ws):
    print "here"
    while True: 
        message = ws.receive()            
        #pprint(message)
       
        #try:
        event = json.loads(message)
        with app.request_context(ws.environ):
            process_event(ws, event, sender)
        #except Exception, e:
        #    print "Exception: %r" % e