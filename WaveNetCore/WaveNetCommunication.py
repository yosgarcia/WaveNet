from enum import Enum
from threading import Thread, Lock
import time
import socket

def get_time():
	return time.time_ns()

class Packet:
	max_destination_length = (1 << 8)

	def __init__(self, message, dest):
		self.message = message
		self.dest = dest
		self.dest_encode = self.dest.encode()
		assert(len(self.dest_encode) < Packet.max_destination_length)
	
	def form(self):
		return len(self.dest_encode).to_bytes() + self.dest_encode + self.message

	def create(data):
		length = data[0]
		return Packet(data[1:1 + length].decode(), data[1 + length:])

class ProtocolType(Enum):
	LOCAL = 1

class Protocol:
	def __init__(self, protocol_type, sender, listener):
		self.protocol_type = protocol_type
		self.sender = sender
		self.listener = listener

	def send(self, data, dest):
		self.sender(data, dest)

	def listen(self, func):
		t = Thread(target=self.listener, args=[func])
		t.run()
		return t

class LocalProtocol(Protocol):

	IP = "127.0.0.1"
	protocol_type = ProtocolType.LOCAL

	def __init__(self, port=None):
		self.port = port
		super().__init__(LocalProtocol.protocol_type, self.sender, self.listener)

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
				packet = Packet.create(data)
				func(packet)

class Link:
	def __init__(self, src, dest, protocol):
		self.protocol = protocol
		self.src = src
		self.dest = dest
	
	def reverse(self):
		return Link(self.dest, self.src, self.protocol)

	def send(self, packet):
		self.protocol.send(packet, self.dest)

