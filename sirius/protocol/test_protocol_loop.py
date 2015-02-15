"""Simple protocol_loop steps.

Run like:

$ bin/nosetests sirius/
"""
from flask.ext import testing

# TODO: It's a bit ugly that the protocol loop depends on the flask setup
# for database access but it's the easiest solution for now.
from sirius.web import webapp
from sirius.models.db import db
from sirius.models import hardware

from sirius.protocol import messages
from sirius.protocol import protocol_loop

# The messages are taken from a real network dump so slightly ugly.
m_power_on = messages.PowerOn(
    bridge_address=u'000d6f0001b3719d',
    model=u'A',
    firmware_version=u'v2.3.1-f3c7946',
    ncp_version=u'0x46C5',
    local_ip_address=u'192.168.1.98',
    mac_address=u'40:d8:55:01:c1:b3',
    uptime=u'4135.25 4083.53',
    uboot_environment=u'truncated',
    network_info={
        u'network_status': u'EMBER_JOINED_NETWORK',
        u'power': 8,
        u'node_eui64': u'0x000d6f0001b3719d',
        u'pan_id': u'0xDF3A',
        u'node_type': u'EMBER_COORDINATOR',
        u'node_id': u'0x0000',
        u'security_level': 5,
        u'extended_pan_id': u'0x42455247fbbbbd7f',
        u'security_profile': u'Custom',
        u'channel': 25,
        u'radio_power_mode': u'EMBER_TX_POWER_MODE_BOOST',
    }
)

m_hearbeat = messages.DeviceHeartbeat(
    bridge_address=u'000d6f0001b3719d',
    device_address=u'000d6f000273ce0b',
    uptime=(1,))

m_hearbeat_2 = messages.DeviceHeartbeat(
    bridge_address=u'000d6f0001b3719d',
    device_address=u'000d6f00cafecccc',
    uptime=(1,))

m_bridge_log = messages.BridgeLog(
    bridge_address=u'000d6f0001b3719d',
    records=[
        {u'name': u'cloud.socketclient', u'created': 1419267045.369878,
         u'process': 490, u'levelno': 30, u'processName': u'MainProcess',
         u'message': u'Closed down websocket, code: 1006, reason: Going away',
         u'levelname': u'WARNING'},
        {u'name': u'cloud.socket', u'created': 1419267045.569464,
         u'process': 490, u'levelno': 40, u'processName': u'MainProcess',
         u'message': u'Socket connection refused', u'levelname': u'ERROR'}
    ]
)

m_device_connect = messages.DeviceConnect(
    bridge_address=u'000d6f0001b3719d',
    device_address=u'000d6f000273ce0b')

m_device_disconnect = messages.DeviceDisconnect(
    bridge_address=u'000d6f0001b3719d',
    device_address=u'000d6f000273ce0b')

m_encryption_key_required = messages.EncryptionKeyRequired(
    bridge_address=u'000d6f0001b3719d',
    device_address=u'000d6f000273ce0b',
    hardware_xor=0xaacafe,
)

m_command_response = messages.BridgeCommandResponse(
    bridge_address=u'000d6f0001b3719d',
    command_id=10,
    return_code=0,
    timestamp=0,
)

class BaseTest(testing.TestCase):

    def create_app(self):
        app = webapp.create_app('test')
        return app

    def setUp(self):
        testing.TestCase.setUp(self)
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()


class FakeWebsocket:
    "Use to create an in-memory a BridgeState."
    def __init__(self):
        self.messages = []
    def send(self, message):
        self.messages.append(message)


# pylint: disable=no-member
class TestNormalFlow(BaseTest):
    "A bunch of smoke tests that exercise the _accept_step."
    def setUp(self):
        BaseTest.setUp(self)
        self.bridge_state = protocol_loop.BridgeState(
            FakeWebsocket(), m_power_on.bridge_address)

    def test_bridge_log(self):
        protocol_loop._accept_step(m_bridge_log, self.bridge_state)

    def test_heartbeat(self):
        self.assertNotIn(m_hearbeat.device_address, self.bridge_state.connected_devices)

        protocol_loop._accept_step(m_hearbeat, self.bridge_state)

        self.assertIn(m_hearbeat.device_address, self.bridge_state.connected_devices)

    def test_device_connect(self):
        self.assertNotIn(m_device_connect.device_address, self.bridge_state.connected_devices)

        protocol_loop._accept_step(m_device_connect, self.bridge_state)

        self.assertIn(m_device_connect.device_address, self.bridge_state.connected_devices)

    def test_device_disconnect(self):
        self.assertNotIn(m_hearbeat.device_address, self.bridge_state.connected_devices)

        protocol_loop._accept_step(m_device_connect, self.bridge_state)
        protocol_loop._accept_step(m_device_disconnect, self.bridge_state)

        self.assertNotIn(m_hearbeat.device_address, self.bridge_state.connected_devices)

    def test_encryption_key_required(self):
        # Pretend this printer is claimed:
        hardware.Printer.phone_home('000d6f000273ce0b')
        p = hardware.Printer.query.first()
        p.used_claim_code = 'n5ry-p6x6-kth7-7hc4'
        db.session.add(p)
        db.session.commit()

        protocol_loop.bridge_by_address = {
            self.bridge_state.address: self.bridge_state
        }
        protocol_loop._accept_step(m_encryption_key_required, self.bridge_state)

        self.assertEquals(len(self.bridge_state.websocket.messages), 1)


class TestBrokenFlow(BaseTest):
    "Check unexpected interactions."
    def setUp(self):
        BaseTest.setUp(self)
        self.bridge_state = protocol_loop.BridgeState(
            None, m_power_on.bridge_address)

    def test_device_double_disconnect(self):
        self.assertNotIn(m_hearbeat.device_address, self.bridge_state.connected_devices)

        protocol_loop._accept_step(m_device_connect, self.bridge_state)
        protocol_loop._accept_step(m_device_disconnect, self.bridge_state)
        protocol_loop._accept_step(m_device_disconnect, self.bridge_state)

        self.assertNotIn(m_hearbeat.device_address, self.bridge_state.connected_devices)

    def test_device_double_power_on(self):
        protocol_loop._accept_step(m_power_on, self.bridge_state)
        protocol_loop._accept_step(m_power_on, self.bridge_state)

    def test_command_response_unseed_command_id(self):
        protocol_loop._accept_step(m_command_response, self.bridge_state)


class TestMultiDevice(BaseTest):
    "What happens when we have more than one device."
    def setUp(self):
        BaseTest.setUp(self)
        self.bridge_state = protocol_loop.BridgeState(
            FakeWebsocket(), m_power_on.bridge_address)

    def test_two_heartbeats(self):
        protocol_loop._accept_step(m_hearbeat, self.bridge_state)
        protocol_loop._accept_step(m_hearbeat_2, self.bridge_state)

        self.assertEquals(len(self.bridge_state.connected_devices), 2)
