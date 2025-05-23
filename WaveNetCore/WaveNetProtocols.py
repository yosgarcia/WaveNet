from enum import Enum
import json
import socket
from threading import Thread, Event
from .WaveNetPacketeering import *
import logging

class ProtocolType(Enum):
	LOCAL = 1

class Protocol:
	def __init__(self, protocol_type, sender, listener, as_public):
		self.protocol_type = protocol_type
		self.sender = sender
		self.listener = listener
		self.as_public = as_public
		self.switch = Event()

	def send(self, data, dest):
		self.sender(data, dest)

	def listen(self, func):
		self.switch.clear()
		t = Thread(target=self.listener, args=[func, self.switch], daemon=True)
		t.start()
		return t

	def public(self):
		return self.as_public()

	def kill(self):
		self.switch.set()

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
			s.connect((LocalProtocol.IP, PORT))
			s.sendall(data.encode())

	def listener(self, func, switch):
		assert self.port is not None

		PORT = self.port

		def process_conn(conn):
			parts = []
			with conn:
				while True:
					data = conn.recv(1 << 12)
					if not data: break
					parts.append(data)
			data = b''.join(parts)
			packet = reconstruct_packet(data)
			func(packet)

		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
			s.bind((LocalProtocol.IP, PORT))
			s.listen(10)
			s.settimeout(1)
			while not switch.is_set():
				try:
					conn, _ = s.accept()
					Thread(target=process_conn, args=(conn,), daemon=True).start()
				except socket.timeout:
					pass

	def as_public(self):
		return str(self.port)

def empty_protocol_from_str(name):
	assert name in ProtocolType.__members__
	if ProtocolType[name] == ProtocolType.LOCAL: return LocalProtocol()
	assert False

class Link:
	def __init__(self, dest, protocol):
		self.protocol = protocol
		self.dest = dest

	def send(self, packet):
		self.protocol.send(packet, self.dest)

	def __str__(self):
		return "|" + self.protocol.protocol_type.name + "|" + self.dest

	def __hash__(self):
		return hash(str(self))

	def __eq__(self, other):
		return str(self) == str(other)
