from threading import Thread, Lock
import time

def get_time():
	return time.time_ns()

class Packet:
	def __init__(self, message, dest):
		self.message = message
		self.dest = dest
	
	def form(self):
		pass

	def create(data):
		pass

class Protocol:
	def __init__(self, sender, listener):
		self.sender = sender
		self.listener = listener

	def send(self, message, dest):
		self.sender(message, dest)

	def listen(self, func):
		t = Thread(target=self.listener, args=[func])
		t.run()

class Link:
	def __init__(self, src, dest, protocol):
		self.protocol = Protocol
		self.src = src
		self.dest = dest
	
	def reverse(self):
		return Link(self.dest, self.src, protocol)

	def send(self, packet):
		self.protocol.send(packet.form(), self.dest)

