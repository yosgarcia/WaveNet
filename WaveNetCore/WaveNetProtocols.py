from enum import Enum
import json
import socket
from threading import Thread, Lock
from WaveNetPacketeering import *

class ProtocolType(Enum):
	LOCAL = 1

class Protocol:
	def __init__(self, protocol_type, sender, listener, as_public):
		self.protocol_type = protocol_type
		self.sender = sender
		self.listener = listener
		self.as_public = as_public

	def send(self, data, dest):
		self.sender(data, dest)

	def listen(self, func):
		t = Thread(target=self.listener, args=[func])
		t.run()
		return t

	def public(self):
		return self.as_public()

class LocalProtocol(Protocol):

	IP = "127.0.0.1"
	protocol_type = ProtocolType.LOCAL

	def __init__(self, port=None):
		self.port = port
		super().__init__(LocalProtocol.protocol_type, self.sender, self.listener, self.as_public)

	def sender(self, packet, dest):
		data = packet.form()

		PORT = int(dest)

		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
			s.connect((IP, PORT))
			s.sendall(data)

	def listener(self, func):
		assert(self.port is not None)

		PORT = self.port

		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
			s.bind((IP, PORT))
			s.listen()
			while True:
				conn, _ = s.accept()
				parts = []
				with conn:
					while True:
						data = conn.recv(1 << 12)
						if not data: break
						parts.append(data)
				data = b''.join(parts)
				packet = reconstruct_packet(data)
				func(packet)

	def as_public(self):
		return str(self.port)

def empty_protocol_from_str(name):
	assert(name in ProtocolType)
	if ProtocolType[name] == ProtocolType.LOCAL: return LocalProtocol()
	assert(False)

class Link:
	def __init__(self, dest, protocol):
		self.protocol = protocol
		self.dest = dest

	def send(self, packet):
		try:
			self.protocol.send(packet, self.dest)
		except Exception as e:
			pass

	def __str__(self):
		return "|" + self.protocol.protocol_type.name + "|" + self.dest

	def __hash__(self):
		return str(self)

	def __eq__(self, other):
		return str(self) == str(other)
