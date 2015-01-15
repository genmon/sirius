"""Data structures for device events.

This is a mix of BridgeEvent, DeviceEvent, BridgeCommand, etc.

TODO: The messages are messy because I added them as I encountered
them. I will group and sort them at some point.
"""
from collections import namedtuple


PowerOn = namedtuple('PowerOn', [
    'bridge_address',
    'model',
    'firmware_version',
    'ncp_version',
    'local_ip_address',
    'mac_address',
    'uptime',
    'uboot_environment',
    'network_info',
])

BridgeLog = namedtuple('BridgeLog', [
    'bridge_address',
    'records',
])

EncryptionKeyRequired = namedtuple('EncryptionKeyRequired', [
    'bridge_address',
    'device_address',
    'hardware_xor',
])

DeviceConnect = namedtuple('DeviceConnect', [
    'bridge_address',
    'device_address',
])

DeviceDisconnect = namedtuple('DeviceDisconnect', [
    'bridge_address',
    'device_address',
])

# BridgeCommands
AddDeviceEncryptionKey = namedtuple('AddDeviceEncryptionKey', [
    'bridge_address',
    'device_address',
    'claim_code',
])

BridgeCommandResponse = namedtuple('BridgeCommandResponse', [
    'bridge_address',
    'command_id',
    'return_code',
    'timestamp',
])

SetDeliveryAndPrint = namedtuple('SetDeliveryAndPrint', [
    'device_address',
    'pixels', # 384 pixels wide
])

SetDelivery = namedtuple('SetDelivery', [
    'device_address',
    'pixels',
])

SetLogLevel = namedtuple('SetLogLevel', [
    'level', # lower-case string, e.g. 'critical'
])

EnableCloudLogging = namedtuple('EnableCloudLogging', [])

DisableCloudLogging = namedtuple('DisableCloudLogging', [])

Leave = namedtuple('Leave', [])

Form = namedtuple('Form', [
    'channels', # list of numbers
])

Pjoin = namedtuple('Pjoin', [
    'duration', # int
])

Restart = namedtuple('Restart', [])

Reboot = namedtuple('Reboot', [])

SetCommandPollFrequency = namedtuple('SetCommandPollFrequency', [
    'frequency', # int in seconds, clamped to [10, 30]
])

SetBridgeLogFrequency = namedtuple('SetBridgeLogFrequency', [
    'frequency', # int in seconds, clamped to [10, 30]
])

EnableSlowEvents = namedtuple('EnableSlowEvents', [])

DisableSlowEvents = namedtuple('DisableSlowEvents', [])

DeviceHeartbeat = namedtuple('DeviceHeartbeat', [
    'bridge_address',
    'device_address',
    'uptime',
])

DeviceDidPrint = namedtuple('DeviceDidPrint', [
    'device_address',
    'type',
    'id',
])

DeviceDidPowerOn = namedtuple('DeviceDidPowerOn', [
    'device_address',
    'device_type',
    'firmware_build_version',
    'loader_build_version',
    'protocol_version',
    'reset_description',
])

BergCloudProductAnnounce = namedtuple('BergCloudProductAnnounce', [
    'device_address',
    'product_id',
    'product_version',
])

BergCloudStartBinary = namedtuple('BergCloudStartBinary', [
    'device_address',
    'event_id',
    'data',
])

BergCloudStartPacked = namedtuple('BergCloudStartPacked', [
    'device_address',
    'event_id',
    'data',
])

UnknownEvent = namedtuple('UnknownEvent', [
    'raw_dict',
])

MalformedEvent = namedtuple('MalformedEvent', [
    'raw_data',
    'error',
])
