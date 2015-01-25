# Using Sirius

First point your bridge at your laptop, port 5002 (or similar).

Then run:

```console
$ bin/gunicorn -k flask_sockets.worker sirius.server:app -b 0.0.0.0:5002 -w 1
```

Navigate browser to http://127.0.0.1:5002/


## Creating fake printers and friends

Resetting the actual hardware all the time gets a bit tiresome so
there's a fake command that creates unclaimed fake little printers:

```console
$ ./manage.py fake printer
[...]
Created printer
     address: 602d48d344b746f5
       DB id: 8
      secret: 66a596840f
  claim code: 5oop-e9dp-hh7v-fjqo
```

Functionally there is no difference between resetting and creating a
new printer so we don't distinguish between the two.

To create a fake friend from twitter who signed up do this:

```console
$ ./manage.py fake user stephenfry
```

# Sirius Architecture

## Layers

The design is somewhat stratified: each layer only talks to the one
below and above. The ugliest bits are how database and protocol loop
interact.

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


## Claim codes

Devices are associated with an account when a user enters a "claim
code". This claim code contains a "hardware-xor" which is derived via
a lossy 3-byte hash from the device address. The XOR-code for a device
is always the same even though the address changes!

The claim codes are meant to be used "timely", i.e. within a short
window of the printer reset. If there are multiple, conflicting claim
codes we always pick the most recently created code.

We are also deriving this hardware xor when a device calls home with
an "encryption_key_required". In that case we connect the device to
the claim code via the hardware-xor and send back the correct
encryption key.
