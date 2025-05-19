from .WaveNetNode import *
from .WaveNetPacketeering import *
from .WaveNetProtocols import *
from .WaveNetCrypto import *
from random import randint
import json
import time
from threading import Thread, Lock, Condition

class PacketWaiter:
	timeout = 5.0

	def __init__(self):
		self.condition = Condition()
		self.packet = Packet.null("Timeout")

	def recv(self, timeout=None):
		with self.condition:
			if timeout is None: timeout = PacketWaiter.timeout
			self.condition.wait(timeout)
			return self.packet

	def send(self, packet):
		self.packet = packet
		self.condition.notify_all()
	
	def __enter__(self):
		self.condition.acquire()
	
	def __exit__(self, exc_type, exc_value, traceback):
		self.condition.release()
		return False

class MeshHub(Node):
	def __init__(self, protocols):
		self.private_key = PrivateKey()
		info = NodeInfo(0, self.private_key)
		self.node = Node(info, protocols, self.delegate)
		self.nodes = {0: self.private_key.public_key()}
		self.awaits = dict()
		self.mutex = Lock()
	
	def __send(self, dest, mtype, message):
		key = None
		if dest in self.nodes: key = self.nodes[dest]
		self.node.send(dest, mtype, message, public_key=key)
	
	def send(self, dest, mtype, message):
		Thread(target=self.__send, args=(dest, mtype, message,), daemon=True).start()
	
	def ping(self, ID):
		with self.mutex:
			if (ID, "pong") not in self.awaits: self.awaits[(ID, "pong")] = PacketWaiter()
			waiter = self.awaits[(ID, "pong")]
		self.send(ID, "ping", "")
		packet = waiter.recv()
		if packet.is_null(): return False
		return packet.src == ID
	
	def process_connect(self, packet):
		data = json.loads(packet.body)
		"""
		{
			"protocol" : str
			"dest" : str
		}
		"""
		status, protocol = verify_tag(data, "protocol", str)
		if not status: raise Exception(protocol)
		status, dest = verify_tag(data, "dest", str)
		if not status: raise Exception(dest)
		link = Link(dest, empty_protocol_from_str(protocol))
		self.node.info.add_neighbor(link)

	def process_ping(self, packet):
		self.send(packet.src, "pong", "")

	def process_pong(self, packet):
		if (packet.src, packet.mtype) in self.awaits:
			waiter = self.awaits.pop((packet.src, packet.mtype))
			with waiter:
				waiter.send(packet)

	def process_request(self, packet):
		data = json.loads(packet.body)
		"""
		{
			"id" : int
		}
		"""
		status, ID = verify_tag(data, "id", int)
		if not status: raise Exception(ID)
		if ID not in self.nodes: raise Exception("ID not found")
		pem = str(self.nodes[ID])
		ans = {"id" : ID, "pem" : pem}
		message = json.dumps(ans)
		self.send(packet.src, "answer", message)
	
	def process_join(self, packet):
		data = json.loads(packet.body)
		"""
		{
			"id" : int
			"pem" : str
		}
		"""
		status, ID = verify_tag(data, "id", int)
		if not status: raise Exception(ID)
		status, pem = verify_tag(data, "pem", str)
		if not status: raise Exception(pem)
		public_key = PublicKey(pem=pem.encode())
		if ID in self.nodes: raise Exception("Repeated ID")
		self.nodes[ID] = public_key
	
	def delegate(self, packet):
		with self.mutex:
			try:
				if packet.mtype == "connect":
					self.process_connect(packet)
					return False
				if packet.mtype == "ping": self.process_ping(packet)
				if packet.mtype == "pong": self.process_pong(packet)
				if packet.mtype == "request": self.process_request(packet)
				if packet.mtype == "join": self.process_join(packet)
			except Exception as e:
				raise e
		return True

	def listen(self):
		self.node.listen()
	
	def kill(self):
		self.node.kill()

class MeshNode(Node):
	def __init__(self, protocols, ID=None):
		self.private_key = PrivateKey()
		if ID is None: ID = randint(1, (1 << 64) - 1)
		info = NodeInfo(ID, self.private_key)
		self.node = Node(info, protocols, self.delegate)
		self.awaits = dict()
		self.mutex = Lock()
		self.hub_key = None
	
	def __basic_send(self, dest, mtype, message):
		self.node.send(dest, mtype, message)

	def basic_send(self, dest, mtype, message):
		Thread(target=self.__basic_send, args=(dest, mtype, message,), daemon=True).start()
	
	def request(self, ID):
		with self.mutex:
			key = self.hub_key
			if (ID, "answer") not in self.awaits: self.awaits[(ID, "answer")] = PacketWaiter()
			waiter = self.awaits[(ID, "answer")]
		message = json.dumps({"id" : ID})
		self.node.send(0, "request", message, public_key=key)
		packet = waiter.recv()
		if packet.is_null(): raise Exception(packet.body)
		data = json.loads(packet.body)
		"""
		{
			"id" : int
			"pem" : str
		}
		"""
		status, ID = verify_tag(data, "id", int)
		if not status: raise Exception(ID)
		status, pem = verify_tag(data, "pem", str)
		if not status: raise Exception(pem)
		public_key = PublicKey(pem=pem.encode())
		return public_key
	
	def __send(self, dest, mtype, message):
		if self.hub_key is None: raise Exception("Node is not yet joined")
		key = self.request(dest)
		self.node.send(dest, mtype, message, public_key=key)
	
	def send(self, dest, mtype, message):
		Thread(target=self.__send, args=(dest, mtype, message), daemon=True).start()
	
	def join(self):
		with self.mutex:
			message = json.dumps({
				"id" : self.node.info.ID,
				"pem" : str(self.private_key.public_key())
				})
			self.basic_send(0, "join", message)
		time.sleep(0.5)
		key = self.request(0)
		with self.mutex:
			self.hub_key = key
	
	def ping(self, ID):
		with self.mutex:
			if (ID, "pong") not in self.awaits: self.awaits[(ID, "pong")] = PacketWaiter()
			waiter = self.awaits[(ID, "pong")]
		if self.hub_key is None: self.basic_send(ID, "ping", "")
		else: self.send(ID, "ping", "")
		packet = waiter.recv()
		if packet.is_null(): return False
		return packet.src == ID

	def send_data(self, dest, message):
		self.send(dest, "data", message)
	
	def recv_data(self, ID=None, timeout=None):
		with self.mutex:
			waiter = None
			if (ID, "data") not in self.awaits: self.awaits[(ID, "data")] = PacketWaiter()
			waiter = self.awaits[(ID, "data")]
		packet = waiter.recv(timeout)
		if packet.is_null(): raise Exception(packet.body)
		return packet.src, packet.body

	def connect(self, ID, protocol, dest):
		link = Link(dest, protocol)
		self.node.info.add_neighbor(link)
		message = json.dumps({
			"protocol" : protocol.protocol_type.name,
			"dest" : protocol.public()
			})
		link.send(Packet(-1, ID, "connect", message))

	def process_connect(self, packet):
		data = json.loads(packet.body)
		"""
		{
			"protocol" : str
			"dest" : str
		}
		"""
		status, protocol = verify_tag(data, "protocol", str)
		if not status: raise Exception(protocol)
		status, dest = verify_tag(data, "dest", str)
		if not status: raise Exception(dest)
		link = Link(dest, empty_protocol_from_str(protocol))
		self.node.info.add_neighbor(link)

	def process_ping(self, packet):
		self.send(packet.src, "pong", "")

	def process_pong(self, packet):
		if (packet.src, packet.mtype) in self.awaits:
			waiter = self.awaits.pop((packet.src, packet.mtype))
			with waiter:
				waiter.send(packet)
	
	def process_answer(self, packet):
		data = json.loads(packet.body)
		status, ID = verify_tag(data, "id", int)
		if not status: raise Exception(ID)
		if (ID, packet.mtype) in self.awaits:
			waiter = self.awaits.pop((ID, packet.mtype))
			with waiter:
				waiter.send(packet)

	def process_data(self, packet):
		if (packet.src, packet.mtype) in self.awaits:
			waiter = self.awaits.pop((packet.src, packet.mtype))
			with waiter:
				waiter.send(packet)
		elif (None, packet.mtype) in self.awaits:
			waiter = self.awaits.pop((None, packet.mtype))
			with waiter:
				waiter.send(packet)

	def delegate(self, packet):
		with self.mutex:
			try:
				if packet.mtype == "connect":
					self.process_connect(packet)
					return False
				if packet.mtype == "ping": self.process_ping(packet)
				if packet.mtype == "pong": self.process_pong(packet)
				if packet.mtype == "answer": self.process_answer(packet)
				if packet.mtype == "data": self.process_data(packet)
			except Exception as e:
				raise e
		return True

	def listen(self):
		self.node.listen()
	
	def kill(self):
		self.node.kill()

