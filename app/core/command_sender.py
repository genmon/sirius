from ..models.core import BridgeCommand, DeviceCommand

import gevent

class CommandSender(object):
	""" Single object per process to send bridge and device commands
	down the Websocket connection.
	@TODO use Reddis to pass information around between processes.
	"""
	
	def __init__(self):
		self.queues = {}  # ws: _CommandQueue
		self.did_send_image = False # temporary
	
	def register(self, ws, bridge):
		# when a power_on event is received from a bridge,
		# register its websocket so that bridge (and devices
		# connected to that bridge) can receive commands
		for k, v in self.queues.items():
			if bridge.bridge_address == v.bridge:
				self.queues.pop(k)
		q = _CommandQueue(bridge=bridge)
		self.queues[ws] = q
		# queue old bridge commands
		commands = BridgeCommand.query.filter_by(state='ready', bridge_address=bridge.bridge_address).all()
		for c in commands:
			q.queue_bridge_command(c)
	
	def device_connect(self, bridge, device):
		# device can be connected only to one bridge at a time
		qb = self.for_bridge(bridge)
		for q in [qq for qq in self.queues.values() if qq != qb]:
			if q.has_device(device):
				q.remove_device(device)
		qb.add_device(device)
		# queue old device commands
		commands = DeviceCommand.query.filter_by(state='ready', device_address=device.device_address).all()
		for c in commands:
			qb.queue_device_command(c)
	
	def device_disconnect(self, bridge, device):
	    q = self.for_bridge(bridge)
	    q.remove_device(device)
	
	def for_bridge(self, bridge):
		queues = [q for q in self.queues.values() if q.bridge == bridge.bridge_address]
		if queues:
			return queues[0]
		else:
			return None
	
	def for_device(self, device):
		queues = [q for q in self.queues.values() if q.has_device(device)]
		if queues:
			return queues[0]
		else:
			return None
	
	def send_commands(self):
		""" called periodically by run """
		for ws, q in self.queues.items():
			for c in q.prepare_commands_to_send():
				ws.send(c)
	
	def _run(self):
		while True:
			self.send_commands()
			gevent.sleep(0.5)
	
	def run(self):
		""" spawns and loops, calling send_commands periodically """
		gevent.spawn(self._run)
	
	
class _CommandQueue(object):
	""" There is one _CommandQueue per websocket connection,
	and it handles the command queues and pending commands.
	Uses bridge_address and device_address internally. """
	
	def __init__(self, bridge):
		self.bridge = bridge.bridge_address
		self.devices = set()
		self.bridge_queue = []
		self.device_queue = {} # device_address: [DeviceCommand]
		self.bridge_pending = None
		self.device_pending = {} # device_address: None|DeviceCommand
	    
	def add_device(self, device):
		da = device.device_address
		if da not in self.devices:
			print "==> Adding device %s to queue for bridge %s" % (da, self.bridge)
			self.devices.add(da)
			self.device_queue[da] = []
			self.device_pending[da] = None
	
	def remove_device(self, device):
		da = device.device_address
		self.devices.remove(da)
		self.device_queue.pop(da, None)
		self.device_pending.pop(da, None)
	
	def has_device(self, device):
		return device.device_address in self.devices
	
	def queue_bridge_command(self, command):
		self.bridge_queue.insert(0, (command.id, command.to_json()))
	
	def queue_device_command(self, command):
		da = command.device_address
		self.device_queue[da].insert(0, (command.id, command.to_json()))
	
	def handle_bridge_response(self, command):
		if self.bridge_pending[0] == command.id:
			self.bridge_pending = None
		self.bridge_queue = [c for c in self.bridge_queue if c[0] != command.id]
	
	def handle_device_response(self, command):
		da = command.device_address
		if self.device_pending[da][0] == command.id:
			self.device_pending[da] = None
		self.device_queue[da] = \
			[c for c in self.device_queue[da] if c.id != command.id]
	
	def prepare_commands_to_send(self):
		commands_to_send = []
		if self.bridge_pending is None and len(self.bridge_queue) > 0:
			c = self.bridge_queue.pop()
			self.bridge_pending = c
			commands_to_send.append(c[1])
		for da in self.devices:
			if self.device_pending[da] is None and \
			  len(self.device_queue[da]) > 0:
				c = self.device_queue[da].pop()
				self.device_pending[da] = c
				commands_to_send.append(c[1])
		return commands_to_send