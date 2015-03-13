CONNECT = """\
{
   "type" : "BridgeEvent",
   "json_payload" : {
      "ncp_version" : "0x46C5",
      "uptime" : "45.71 23.94",
      "firmware_version" : "v2.3.1-f3c7946",
      "network_info" : {
         "extended_pan_id" : "0x42455247fbbbbd7f",
         "node_type" : "EMBER_COORDINATOR",
         "radio_power_mode" : "EMBER_TX_POWER_MODE_BOOST",
         "security_level" : 5,
         "network_status" : "EMBER_JOINED_NETWORK",
         "channel" : 11,
         "security_profile" : "Custom",
         "power" : 8,
         "node_eui64" : "0x000d6f0001b3719d",
         "pan_id" : "0xDF3A",
         "node_id" : "0x0000"
      },
      "name" : "power_on",
      "local_ip_address" : "192.168.1.98",
      "uboot_environment" : "YXBwZW5kX3J1bl9tb2RlPXNldGVudiBib290YXJncyAke2Jvb3RhcmdzfSBydW5tb2RlPSR7cnVubW9kZX07CmF1dG9sb2FkPW5vCmJhdWRyYXRlPTExNTIwMApib2FyZF9tYW51ZmFjdHVyZV9pbmZvPUJSSURHRUFBMTI0MzA0MzYKYm9vdGFyZ3M9Y29uc29sZT10dHlTMCwxMTUyMDAgcm9vdD0vZGV2L210ZGJsb2NrNSBtdGRwYXJ0cz1hdG1lbF9uYW5kOjEyOGsoYm9vdHN0cmFwKXJvLDI1NmsodWJvb3Qpcm8sMTI4ayhlbnYxKXJvLDEyOGsoZW52MilybywyTShsaW51eCksLShyb290KSBydyByb290ZnN0eXBlPWpmZnMyCmJvb3RjbWQ9cnVuIGNhdGNoX2J0bjsgcnVuIGluc3RfaWZfcmVxdWlyZWQ7IHJ1biBhcHBlbmRfcnVuX21vZGU7IHJ1biByZXNldF9sZWRzOyBuYW5kIHJlYWQgJHtrZXJuZWxfbG9hZF9hZGRyZXNzfSAke2tlcm5lbF9mbGFzaF9hZGRyZXNzfSAke2tlcm5lbF9zaXplfTsgYm9vdG0gJHtrZXJuZWxfbG9hZF9hZGRyZXNzfQpib290ZGVsYXk9MQpjYXRjaF9idG49c2V0ZW52IHJ1bm1vZGUgc3RhbmRhcmQ7IHNldGVudiBsb29wIDE7IHdoaWxlIHRlc3QgJHtsb29wfSAtZXEgIjEiIDsgZG8gcnVuIGZsYXNoX3doZW5faGVsZDsgZG9uZTsgc2V0X2Nsb3VkX2xlZCAwOyBzZXRfZXRoX2xlZCAwOyBzZXRfemlnYmVlX2xlZCAwCmV0aGFjdD1tYWNiMApldGhhZGRyPTQwOkQ4OjU1OjAxOkMxOkIzCmZhY3RvcnlfZmV0Y2hfaW1hZ2U9ZGhjcDsgdGZ0cCAweDIwODAwMDAwIGZhY3RvcnlfZmxhc2guaW1nCmZhY3RvcnlfcnVuX2ltYWdlPXNvdXJjZSAweDIwODAwMDAwCmZhY3Rvcnlfc2V0dXA9cnVuIGZhY3RvcnlfZmV0Y2hfaW1hZ2UgZmFjdG9yeV9ydW5faW1hZ2UKZmFpbF9sb29wPXNldGVudiBsb29wIDE7IHdoaWxlIHRlc3QgJHtsb29wfSAtZXEgIjEiIDsgZG8gbGVkX3NlcSAwOyBkb25lCmZpbGVhZGRyPTIwMDAwMDAwCmZpbGVzaXplPTEwRTUwM0MKZmxhc2hfd2hlbl9oZWxkPWdldF9lbmdfYnRuOyBpZiB0ZXN0ICQ/IC1lcSAwOyB0aGVuIHNldGVudiBydW5tb2RlIGVuZ3Rlc3Q7IGxlZF9zZXEgMTsgZWxzZSBzZXRlbnYgbG9vcCAwOyBmaTsKZ2F0ZXdheWlwPTEwLjEwLjAuMQppbnN0X2ZldGNoX2ltYWdlPWRoY3A7IHRmdHAgJHtrZXJuZWxMb2FkQWRkcn0gJHtmYWN0b3J5U2NyaXB0RmlsZW5hbWV9Cmluc3RfaWZfcmVxdWlyZWQ9aWYgdGVzdCAiJHtydW5tb2RlfSIgPSAiZW5ndGVzdCI7IHRoZW4gcnVuIGluc3Rfc2V0dXA7IGZpOwppbnN0X3J1bl9pbWFnZT1zb3VyY2UgJHtrZXJuZWxMb2FkQWRkcn0KaW5zdF9zZXR1cD1ydW4gZmFjdG9yeV9mZXRjaF9pbWFnZSBmYWN0b3J5X3J1bl9pbWFnZQppcGFkZHI9MTAuMTAuMC4yNwprZXJuZWxfZmlsZW5hbWU9dUltYWdlCmtlcm5lbF9mbGFzaF9hZGRyZXNzPTB4YTAwMDAKa2VybmVsX2xvYWRfYWRkcmVzcz0weDIwODAwMDAwCmtlcm5lbF9zaXplPTB4MjAwMDAwCm1lbV9sb2FkX2FkZHJlc3M9MHgyMDAwMDAwMApuZXRtYXNrPTI1NS4yNTUuMjQ4LjAKcmVzZXRfbGVkcz1zZXRfZXRoX2xlZCAwOyBzZXRfemlnYmVlX2xlZCAwOyBzZXRfY2xvdWRfbGVkIDA7CnJvb3Rmc19lcmFzZV9zaXplPTB4ZmQ2MDAwMApyb290ZnNfZmlsZW5hbWU9cm9vdGZzLmpmZnMyCnJvb3Rmc19mbGFzaF9hZGRyZXNzPTB4MmEwMDAwCnJvb3Rmc193cml0ZV9zaXplPTB4MTUwMDAwMApzZXJ2ZXJpcD0xMC4xMC4wLjEKc3RkZXJyPXNlcmlhbApzdGRpbj1zZXJpYWwKc3Rkb3V0PXNlcmlhbAp3cml0ZV9rZXJuZWw9ZWNobyAiRmV0Y2ggKyBXcml0ZSBrZXJuZWwiOyBtdy5iICR7bWVtX2xvYWRfYWRkcmVzc30gMHhmZiAke2tlcm5lbF9zaXplfTsgdGZ0cCAke21lbV9sb2FkX2FkZHJlc3N9ICR7a2VybmVsX2ZpbGVuYW1lfTsgbmFuZCBlcmFzZSAke2tlcm5lbF9mbGFzaF9hZGRyZXNzfSAke2tlcm5lbF9zaXplfTsgbmFuZCB3cml0ZSAke21lbV9sb2FkX2FkZHJlc3N9ICR7a2VybmVsX2ZsYXNoX2FkZHJlc3N9ICR7a2VybmVsX3NpemV9Owp3cml0ZV9yb290ZnM9ZWNobyAiRmV0Y2ggKyBXcml0ZSByb290ZnMiOyBtdy5iICR7bWVtX2xvYWRfYWRkcmVzc30gMHhmZiAke3Jvb3Rmc193cml0ZV9zaXplfTsgdGZ0cCAke21lbV9sb2FkX2FkZHJlc3N9ICR7cm9vdGZzX2ZpbGVuYW1lfTsgc2V0X2Nsb3VkX2xlZCAxOyBuYW5kIGVyYXNlICR7cm9vdGZzX2ZsYXNoX2FkZHJlc3N9ICR7cm9vdGZzX2VyYXNlX3NpemV9OyBuYW5kIHdyaXRlICR7bWVtX2xvYWRfYWRkcmVzc30gJHtyb290ZnNfZmxhc2hfYWRkcmVzc30gJHtyb290ZnNfd3JpdGVfc2l6ZX07Cg==",
      "mac_address" : "40:d8:55:01:c1:b3",
      "model" : "A"
   },
   "bridge_address" : "%(bridge_address)s",
   "timestamp" : 1426256447.70695
}
"""

DEVICE_CONNECT = """\
{
   "timestamp" : 1426256449.81701,
   "json_payload" : {
      "device_address" : "%(device_address)s",
      "name" : "device_connect"
   },
   "bridge_address" : "%(bridge_address)s",
   "type" : "BridgeEvent"
}
"""

HEARTBEAT = """\
{
   "rssi_stats" : [
      -20,
      -20,
      -19
   ],
   "device_address" : "%(device_address)s",
   "binary_payload" : "AQAAAAAABAAAAG4AAAA=",
   "type" : "DeviceEvent",
   "bridge_address" : "%(bridge_address)s",
   "timestamp" : 1426256547.52687
}
"""

ENCRYPTION_KEY_REQUIRED = """\
{
   "timestamp" : 1419107228.91187,
   "type" : "BridgeEvent",
   "json_payload" : {
      "name" : "encryption_key_required",
      "device_address" : "%(device_address)s"
   },
   "bridge_address" : "%(bridge_address)s"
}
"""
