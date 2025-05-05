from threading import Thread, Lock

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

	def send(self, message):
		self.protocol.send(message, self.dest)

