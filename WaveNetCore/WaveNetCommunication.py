from threading import Thread, Lock
import time
import socket

def get_time():
	return time.time_ns()

class Packet:
	max_message_length = 1 << 9
	max_destination_length = 1 << 8

	def __init__(self, message, dest):
		self.message = message
		assert(len(self.message) < Packet.max_message_length)
		self.dest = dest
		self.dest_encode = self.dest.encode()
		assert(len(self.dest_encode) < Packet.max_destination_length)
	
	def form(self):
		return len(self.dest_encode).to_bytes() + self.dest_encode + self.message

	def create(data):
		length = data[0]
		return Packet(data[1:1 + length].decode(), data[1 + length:])

"""
	def split(message, dest):
		packets = []
		for i in range((len(message) + Packet.max_message_length - 1)//Packet.max_message_length):
			data = message[i*Packet.max_message_length:(i + 1)*Packet.max_message_length]
			packets.append(Packet(data, dest))
		return packets
"""

class Protocol:
	def __init__(self, sender, listener):
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

	def __init__(self, port=None):
		self.port = port
		super().__init__(self.sender, self.listener)

	def sender(self, packet, dest):
		data = packet.form()

		PORT = int(dest)

		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		sock.sendto(data, (LocalProtocol.IP, PORT))

	def listener(self, func):
		assert(self.port is not None)

		PORT = self.port

		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		sock.bind((LocalProtocol.IP, PORT))

		while True:
			data, _ = sock.recvfrom(1024)
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

