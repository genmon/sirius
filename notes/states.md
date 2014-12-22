# (OBSOLETE)

# Possible events:

- BridgeEvent (json_payload)
    - power_on
    - encryption_key_required
    - device_connect
    - device_disconnect
- BridgeLog (list of records)
- BridgeCommandResponse
- DeviceEvent
- DeviceCommandResponse
- WifiEvent

# Bridge states

- unknown (never seen)
- up (websocket connected)
- down

# Device events

- unknown (never seen)
- unclaimed_encryption_key_required
- claimed_encryption_key_required (encryption_key_required is sent as a BridgeEvent but it's really a device event).
- claimed_connected
- claimed_disconnected
