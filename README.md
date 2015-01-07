sirius
======

First point your bridge at your laptop, port 5002 (or similar).

Then run:

```sh
$ bin/gunicorn -k flask_sockets.worker sirius.server:app -b 0.0.0.0:5002 -w 1
```

## Layers

```
UI / database
----------------------------
protocol_loop / send_message
----------------------------
encoders / decoders
----------------------------
websockets
----------------------------
```

## Information flow (websockets)

The entry point for the bridge is in `sirius.web.webapp`. Each new
websocket connection spawns a gevent thread (specified by running the
flask_sockets gunicorn worker) which runs
`sirius.protocol.protocol_loop.accept` immediately. `accept` registers
the websocket/bridge_address mapping in a global dictionary; it then
loops forever, decoding messages as they come in.


## Information flow (user-facing)

So far we aren't sending any messages to the devices or bridges other
than encryption keys derived from claim codes (see below).

In order to inject messages into the flow we need to look up a device
in the `connected_devices` member of
`sirius.protocol.protocol_loop.BridgeState`. If we found a matching
`BridgeState` we can use its websocket to send the message.

As gunicorn spawns several processes we'll need to publish updates
over the process boundary which will probably necessitate a message
broker like redis.


## Claim codes

Devices are associated with an account when a user enters a "claim
code". This claim code contains a "hardware-xor" which is derived via
a lossy 3-byte hash from the device address. These codes are meant to
be used "timely", i.e. within a short window of the printer
reset. Hence collisions shouldn't be an issue.

We are also deriving this hardware xor when a device calls home with
an "encryption_key_required". In that case we connect the device to
the claim code via the hardware-xor and send back the correct
encryption key.
