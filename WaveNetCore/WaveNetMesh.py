from WaveNetNode import *
from WaveNetCommunication import *
from WaveNetCrypto import *
from random import randint
import json
from threading import Thread, Lock, Condition

class PacketWaiter:
	timeout = 60.0

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

class MeshHub(Node):
	def __init__(self, port):
		self.private_key = PrivateKey()
		info = NodeInfo(0, self.private_key)
		self.node = Node(info, [LocalProtocol(port)], self.delegate)
		self.nodes = {0: self.private_key.public_key()}
		self.awaits = dict()
		self.mutex = Lock()
		self.node.listen()
	
	def send(self, dest, mtype, message):
		key = None
		if dest in self.nodes: key = self.nodes[dest]
		self.node.send(dest, mtype, message, public_key=key)
	
	def ping(self, ID):
		self.mutex.acquire()
		if (ID, "pong") not in self.awaits: self.awaits[(ID, "pong")] = PacketWaiter()
		waiter = self.awaits[(ID, "pong")]
		self.mutex.release()
		self.send(ID, "ping", "")
		packet = waiter.wait()
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
		if protocol not in ProtocolType: raise Exception("Protocol doesn't exist")
		link = None
		if ProtocolType[protocol] = ProtocolType.LOCAL: link = Link(dest, LocalProtocol())
		if link is not None: self.node.info.add_neighbor(link)

	def process_ping(self, packet):
		self.send(packet.src, "pong", "")

	def process_pong(self, packet):
		if (packet.src, packet.mtype) in self.awaits:
			waiter = self.awaits.pop((packet.src, packet.mtype))
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
		public_key = PublicKey(pem=pem)
		if ID in self.nodes: raise Exception("Repeated ID")
		self.nodes[ID] = public_key
	
	def delegate(self, packet):
		self.mutex.acquire()
		try:
			if packet.mtype == "connect":
				self.process_connect(packet)
				return False
			if packet.mtype == "ping": self.process_ping(packet)
			if packet.mtype == "pong": self.process_pong(packet)
			if packet.mtype == "request": self.process_request(packet)
			if packet.mtype == "join": self.process_join(packet)
		except Exception as e:
			pass
		finally:
			self.mutex.release()
		return True

class MeshNode(Node):
	def __init__(self, protocols):
		self.private_key = PrivateKey()
		info = NodeInfo(randint(1, (1 << 64) - 1))
		self.node = Node(info, protocols, self.delegate)
		self.awaits = dict()
		self.mutex = Lock()
		self.hub_key = None
		self.node.listen()
	
	def basic_send(self, dest, mtype, message):
		self.node.send(dest, mtype, message)
	
	def request(self, ID):
		self.mutex.acquire()
		key = self.hub_key
		if (ID, "answer") not in self.awaits: self.awaits[(ID, "answer")] = PacketWaiter()
		waiter = self.awaits[(ID, "answer")]
		self.mutex.release()
		message = json.dumps({"id" : ID})
		self.node.send(0, "request", message, public_key=key)
		packet = waiter.wait()
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
		public_key = PublicKey(pem=pem)
		return public_key
	
	def send(self, dest, mtype, message):
		if self.hub_key is None: raise Exception("Node is not yet joined")
		key = request(dest)
		self.node.send(dest, mtype, message, public_key=key)
	
	def join(self):
		self.mutex.acquire()
		message = json.dumps({
			"id" : self.info.ID,
			"pem" : str(self.private_key.public_key())
			})
		self.basic_send(0, "join", message)
		self.mutex.release()
		key = request(0)
		self.mutex.acquire()
		self.hub_key = key
		self.mutex.release()
	
	def ping(self, ID):
		self.mutex.acquire()
		if (ID, "pong") not in self.awaits: self.awaits[(ID, "pong")] = PacketWaiter()
		waiter = self.awaits[(ID, "pong")]
		self.mutex.release()
		if self.hub_key is None: self.basic_send(ID, "ping", "")
		else: self.send(ID, "ping", "")
		packet = waiter.wait()
		if packet.is_null(): return False
		return packet.src == ID

	def send_data(self, dest, message):
		self.send(dest, "data", message)
	
	def recv_data(self, ID=None):
		self.mutex.acquire()
		waiter = None
		if (ID, "data") not in self.awaits: self.awaits[(ID, "data")] = PacketWaiter()
		waiter = self.awaits[(ID, "data")]
		self.mutex.release()
		packet = waiter.wait(60.0*10 if ID is None else None)
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
		if protocol not in ProtocolType: raise Exception("Protocol doesn't exist")
		link = None
		if ProtocolType[protocol] = ProtocolType.LOCAL: link = Link(dest, LocalProtocol())
		if link is not None: self.node.info.add_neighbor(link)

	def process_ping(self, packet):
		self.send(packet.src, "pong", "")

	def process_pong(self, packet):
		if (packet.src, packet.mtype) in self.awaits:
			waiter = self.awaits.pop((packet.src, packet.mtype))
			waiter.send(packet)
	
	def process_answer(self, packet):
		if (packet.src, packet.mtype) in self.awaits:
			waiter = self.awaits.pop((packet.src, packet.mtype))
			waiter.send(packet)

	def process_data(self, packet):
		if (packet.src, packet.mtype) in self.awaits:
			waiter = self.awaits.pop((packet.src, packet.mtype))
			waiter.send(packet)
		elif (None, packet.mtype) in self.awaits:
			waiter = self.awaits.pop(packet.mtype)
			waiter.send(packet)

	def delegate(self, packet):
		self.mutex.acquire()
		try:
			if packet.mtype == "connect":
				self.process_connect(packet)
				return False
			if packet.mtype == "ping": self.process_ping(packet)
			if packet.mtype == "pong": self.process_pong(packet)
			if packet.mtype == "answer": self.process_answer(packet)
			if packet.mtype == "data": self.process_data(packet)
		except Exception as e:
			pass
		finally:
			self.mutex.release()
		return True

