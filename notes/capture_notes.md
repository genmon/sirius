# Capture the connect attempt with nc

```
$ nc -l -p 5002
GET /api/v1/connection HTTP/1.1
Host: 192.168.1.88
Connection: Upgrade
Upgrade: websocket
Sec-WebSocket-Key: LJUqJa44qfNRKHts7rnNsQ==
Origin: ws://192.168.1.88:5002/api/v1/connection
Sec-WebSocket-Version: 13
Sec-WebSocket-Protocol: bergcloud-bridge-v1
```

Apparently `Sec-WebSocket-Protocol: bergcloud-bridge-v1` is for
protocol negotiation. CF Accept headers in HTTP.

# Lets provide a websocket and see what happens.

```python
from eventlet import wsgi, websocket
import eventlet

@websocket.WebSocketWSGI
def bridge(ws):
    while True:
        print ws.wait()
        eventlet.sleep(1)

wsgi.server(eventlet.listen(('', 5002)), bridge)
```

Output is two messages:

```
{"bridge_address": "000d6f0002ff7a91", "type": "BridgeEvent", "timestamp": 1346500898.052285, "json_payload": {"uptime": "89.52 68.99", "name": "power_on", "uboot_environment": "YXBwZW5kX3J1bl9tb2RlPXNldGVudiBib290YXJncyAke2Jvb3RhcmdzfSBydW5tb2RlPSR7cnVubW9kZX07CmF1dG9sb2FkPW5vCmJhdWRyYXRlPTExNTIwMApib2FyZF9tYW51ZmFjdHVyZV9pbmZvPUJSSURHRUFBMTM0NzIyNTUKYm9vdGFyZ3M9Y29uc29sZT10dHlTMCwxMTUyMDAgcm9vdD0vZGV2L210ZGJsb2NrNiBtdGRwYXJ0cz1hdG1lbF9uYW5kOjEyOGsoYm9vdHN0cmFwKXJvLDI1NmsodWJvb3Qpcm8sMTI4ayhlbnYxKSwxMjhrKGVudjIpLDJNKGxpbnV4KSwxNk0oY29uZmlnKSwtKHJvb3QpIHJ3IHJvb3Rmc3R5cGU9amZmczIKYm9vdGNtZD1ydW4gY2F0Y2hfYnRuOyBydW4gaW5zdF9pZl9yZXF1aXJlZDsgcnVuIGFwcGVuZF9ydW5fbW9kZTsgcnVuIHJlc2V0X2xlZHM7IG5hbmQgcmVhZCAke2tlcm5lbF9sb2FkX2FkZHJlc3N9ICR7a2VybmVsX2ZsYXNoX2FkZHJlc3N9ICR7a2VybmVsX3NpemV9OyBib290bSAke2tlcm5lbF9sb2FkX2FkZHJlc3N9CmJvb3RkZWxheT0xCmNhdGNoX2J0bj1zZXRlbnYgcnVubW9kZSBzdGFuZGFyZDsgc2V0ZW52IGxvb3AgMTsgd2hpbGUgdGVzdCAke2xvb3B9IC1lcSAiMSIgOyBkbyBydW4gZmxhc2hfd2hlbl9oZWxkOyBkb25lOyBzZXRfY2xvdWRfbGVkIDA7IHNldF9ldGhfbGVkIDA7IHNldF96aWdiZWVfbGVkIDAKZXRoYWN0PW1hY2IwCmV0aGFkZHI9NDA6RDg6NTU6MTk6Nzc6MkUKZmFjdG9yeV9mZXRjaF9pbWFnZT1kaGNwOyB0ZnRwIDB4MjA4MDAwMDAgZmFjdG9yeV9mbGFzaC5pbWcKZmFjdG9yeV9ydW5faW1hZ2U9c291cmNlIDB4MjA4MDAwMDAKZmFjdG9yeV9zZXR1cD1ydW4gZmFjdG9yeV9mZXRjaF9pbWFnZSBmYWN0b3J5X3J1bl9pbWFnZQpmYWlsX2xvb3A9c2V0ZW52IGxvb3AgMTsgd2hpbGUgdGVzdCAke2xvb3B9IC1lcSAiMSIgOyBkbyBsZWRfc2VxIDA7IGRvbmUKZmlsZWFkZHI9MjAwMDAwMDAKZmlsZXNpemU9QkI2NzM0CmZsYXNoX3doZW5faGVsZD1nZXRfZW5nX2J0bjsgaWYgdGVzdCAkPyAtZXEgMDsgdGhlbiBzZXRlbnYgcnVubW9kZSBlbmd0ZXN0OyBsZWRfc2VxIDE7IGVsc2Ugc2V0ZW52IGxvb3AgMDsgZmk7CmdhdGV3YXlpcD0xMC4xMC4wLjEKaW5zdF9mZXRjaF9pbWFnZT10ZnRwICR7a2VybmVsTG9hZEFkZHJ9ICR7ZmFjdG9yeVNjcmlwdEZpbGVuYW1lfQppbnN0X2lmX3JlcXVpcmVkPWlmIHRlc3QgIiR7cnVubW9kZX0iID0gImVuZ3Rlc3QiOyB0aGVuIHJ1biBpbnN0X3NldHVwOyBmaTsKaW5zdF9ydW5faW1hZ2U9c291cmNlICR7a2VybmVsTG9hZEFkZHJ9Cmluc3Rfc2V0dXA9cnVuIGZhY3RvcnlfZmV0Y2hfaW1hZ2UgZmFjdG9yeV9ydW5faW1hZ2UKaXBhZGRyPTEwLjEwLjAuMTUyCmtlcm5lbF9maWxlbmFtZT11SW1hZ2UKa2VybmVsX2ZsYXNoX2FkZHJlc3M9MHhhMDAwMAprZXJuZWxfbG9hZF9hZGRyZXNzPTB4MjA4MDAwMDAKa2VybmVsX3NpemU9MHgyMDAwMDAKbWVtX2xvYWRfYWRkcmVzcz0weDIwMDAwMDAwCm5ldG1hc2s9MjU1LjI1NS4yNDguMApvcHRfZmlsZW5hbWU9YnJpZGdlX29wdC5qZmZzMgpvcHRfZmxhc2hfYWRkcmVzcz0weDJhMDAwMApvcHRfc2l6ZT0weDE2MDAwMDAKcmVzZXRfbGVkcz1zZXRfZXRoX2xlZCAwOyBzZXRfemlnYmVlX2xlZCAwOyBzZXRfY2xvdWRfbGVkIDA7CnJvb3Rmc19lcmFzZV9zaXplPTB4ZTc2MDAwMApyb290ZnNfZmlsZW5hbWU9cm9vdGZzLmpmZnMyCnJvb3Rmc19mbGFzaF9hZGRyZXNzPTB4MThBMDAwMApyb290ZnNfd3JpdGVfc2l6ZT0weDE4MDAwMDAKc2VydmVyaXA9MTAuMTAuMC4xCnN0ZGVycj1zZXJpYWwKc3RkaW49c2VyaWFsCnN0ZG91dD1zZXJpYWwKd3JpdGVfa2VybmVsPWVjaG8gIkZldGNoICsgV3JpdGUga2VybmVsIjsgbXcuYiAke21lbV9sb2FkX2FkZHJlc3N9IDB4ZmYgJHtrZXJuZWxfc2l6ZX07IHRmdHAgJHttZW1fbG9hZF9hZGRyZXNzfSAke2tlcm5lbF9maWxlbmFtZX07IG5hbmQgZXJhc2UgJHtrZXJuZWxfZmxhc2hfYWRkcmVzc30gJHtrZXJuZWxfc2l6ZX07IG5hbmQgd3JpdGUgJHttZW1fbG9hZF9hZGRyZXNzfSAke2tlcm5lbF9mbGFzaF9hZGRyZXNzfSAke2tlcm5lbF9zaXplfTsKd3JpdGVfb3B0PWVjaG8gIkZldGNoICsgV3JpdGUgb3B0IjsgbXcuYiAke21lbV9sb2FkX2FkZHJlc3N9IDB4ZmYgJHtvcHRfc2l6ZX07IHRmdHAgJHttZW1fbG9hZF9hZGRyZXNzfSAke29wdF9maWxlbmFtZX07IG5hbmQgZXJhc2UgJHtvcHRfZmxhc2hfYWRkcmVzc30gJHtvcHRfc2l6ZX07IG5hbmQgd3JpdGUgJHttZW1fbG9hZF9hZGRyZXNzfSAke29wdF9mbGFzaF9hZGRyZXNzfSAke29wdF9zaXplfTsKd3JpdGVfcm9vdGZzPWVjaG8gIkZldGNoICsgV3JpdGUgcm9vdGZzIjsgbXcuYiAke21lbV9sb2FkX2FkZHJlc3N9IDB4ZmYgJHtyb290ZnNfd3JpdGVfc2l6ZX07IHRmdHAgJHttZW1fbG9hZF9hZGRyZXNzfSAke3Jvb3Rmc19maWxlbmFtZX07IHNldF9jbG91ZF9sZWQgMTsgbmFuZCBlcmFzZSAke3Jvb3Rmc19mbGFzaF9hZGRyZXNzfSAke3Jvb3Rmc19lcmFzZV9zaXplfTsgbmFuZCB3cml0ZSAke21lbV9sb2FkX2FkZHJlc3N9ICR7cm9vdGZzX2ZsYXNoX2FkZHJlc3N9ICR7cm9vdGZzX3dyaXRlX3NpemV9Owo=", "local_ip_address": "192.168.2.117", "mac_address": "40:d8:55:19:77:2e", "ncp_version": "0x46C5", "network_info": {"network_status": "EMBER_JOINED_NETWORK", "power": 8, "node_eui64": "0x000d6f0002ff7a91", "pan_id": "0xDCC9", "node_type": "EMBER_COORDINATOR", "node_id": "0x0000", "security_level": 5, "extended_pan_id": "0x42455247b439420c", "security_profile": "Custom", "channel": 25, "radio_power_mode": "EMBER_TX_POWER_MODE_BOOST"}, "firmware_version": "v2.3.1-f3c7946", "model": "B"}}
{"bridge_address": "000d6f0002ff7a91", "type": "BridgeLog", "records": [{"name": "cloud.socket", "created": 1346500877.330243, "process": 465, "levelno": 40, "processName": "MainProcess", "message": "Socket connection refused", "levelname": "ERROR"}, {"name": "cloud.socket", "created": 1346500882.4734199, "process": 465, "levelno": 40, "processName": "MainProcess", "message": "Socket connection refused", "levelname": "ERROR"}, {"name": "cloud.socket", "created": 1346500887.6230842, "process": 465, "levelno": 40, "processName": "MainProcess", "message": "Socket connection refused", "levelname": "ERROR"}, {"name": "cloud.socket", "created": 1346500892.7610618, "process": 465, "levelno": 40, "processName": "MainProcess", "message": "Socket connection refused", "levelname": "ERROR"}], "timestamp": 1346500898.143672}
```

Note that the bridge also sends power_on after being disconnected from
it's websocket, e.g. by removing the cable or by killing the websocket server.

# What happens when I plug little printer in?

Getting the following on before sending the device-connect message:

```
{"device_address": "000d6f000273ce0b", "timestamp": 1346504081.836229, "bridge_address": "000d6f0002ff7a91", "binary_payload": "AwAAAAAASgAAAAAAAAB2MC41LTEyLWcyNmU4MmYwAAAAAAAAAAAAAAAAAAAAAHYwLjUtMC1nMTQ4NTljYgAAAAAAAAAAAAAAAAAAAAAABAAAAAEE", "rssi_stats": [-30, -30, -30], "type": "DeviceEvent"}
```
Decoding that:

>>> DeviceEventPayload.from_base64('AwAAAAAASgAAAAAAAAB2MC41LTEyLWcyNmU4MmYwAAAAAAAAAAAAAAAAAAAAAHYwLjUtMC1nMTQ4NTljYgAAAAAAAAAAAAAAAAAAAAAABAAAAAEE')
{'event_code': 3, 'event_payload_length': 74, 'reset_text': 'Power on', 'command_invocation_id': 0, 'reset_description': 1025, 'device_type': 0, 'protocol_version': 4, 'loader_build_version': 'v0.5-0-g14859cb\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00', 'firmware_build_version': 'v0.5-12-g26e82f0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00', 'name': 'did_power_on'}


## device-connect:

```
{"bridge_address": "000d6f0002ff7a91", "type": "BridgeEvent", "timestamp": 1346504081.8327731, "json_payload": {"device_address": "000d6f000273ce0b", "name": "device_connect"}}
```

## This looks like heart-beat:

```
{"device_address": "000d6f000273ce0b", "timestamp": 1346504091.5216279, "bridge_address": "000d6f0002ff7a91", "binary_payload": "AQAAAAAABAAAABQAAAA=", "rssi_stats": [-31, -32, -30], "type": "DeviceEvent"}
```

decoding:

>>> p.DeviceEventPayload.from_base64('AQAAAAAABAAAABQAAAA=')
{'event_payload_length': 4, 'uptime': (20,), 'command_invocation_id': 0, 'event_code': 1, 'name': 'heartbeat'}



# disconnecting the device

```
{"bridge_address": "000d6f0002ff7a91", "type": "BridgeEvent", "timestamp": 1346504219.3027338, "json_payload": {"device_address": "000d6f000273ce0b", "name": "device_disconnect"}}
```

# intermission (bridge died)


# What happens after reset

```
{"bridge_address": "000d6f0001b3719d", "type": "BridgeEvent", "timestamp": 1419107228.911871, "json_payload": {"device_address": "000d6f000273ce0b", "name": "encryption_key_required"}}
```

I.e. the bridge will send encryption_key_required every ~30 seconds.

While in this state there will be no device_connected, device_disconnected events.


# Notes

The bridge itself doesn't send any health pings. The only way we know
the bridge is online is by websocket-connect. That's TCP which doesn't
send any health pings so we don't really know whether a bridge by
itself is online.

# What to model on the high level layer

- bridges
    - address
    - devices
- devices
    - claim code (entered by user)
    - address
- users


# What is this?

{u'device_address': u'000d6f000273ce0b',
u'timestamp': 1421336620.588616,
u'transfer_time': 3.43,
u'bridge_address': u'000d6f0001b3719d',
u'return_code': 144,
u'rssi_stats': [-19,-19,-19],
u'type': u'DeviceCommandResponse',
u'command_id': 0}

Note the `return_code` of 144 (0x90). Looks like it is this:

    COMMAND_NAME_ID_MAP = { :set_delivery_and_print => 0x0001,
                            :set_delivery => 0x0002,
                            :set_delivery_and_print_no_face => 0x0011,
                            :set_delivery_no_face => 0x0012,
                            :set_personality => 0x0102,
                            :set_personality_with_message => 0x0101,
                            :set_quip => 0x0202,
                            :firmware_update => 0xf000 }

    RESPONSE_CODE_MAP = { :success => 0,
                          :eui64_not_found => 0x01,
                          :failed_network => 0x02,
                          :invalid_sequence => 0x20,
                          :busy => 0x30,
                          :invalid_size => 0x80,
                          :invalid_devicetype => 0x81,
                          :filesystem_error => 0x82,
                          :filesystem_invalid_id => 0x90,
                          :filesystem_no_free_filehandles => 0x91,
                          :filesystem_write_error => 0x92,
                          :bridge_error => 0xff }


# What happens when the binary payload has an extra 'x' at the end
  before encoding:

{u'device_address': u'000d6f000273ce0b',
u'timestamp': 1421339025.755868,
u'transfer_time': 3.44,
u'bridge_address': u'000d6f0001b3719d',
u'return_code': 128,
u'rssi_stats': [-19,-19,-19],
u'type': u'DeviceCommandResponse',
u'command_id': 0}
