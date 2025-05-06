from threading import Thread, Lock

import hashlib
from WaveNetCommunication import *

class NodeInfo:
	def __init__(self, ID, neighbors=set()):
		self.ID = ID
		self.neighbors = neighbors
	
	def add_neighbor(self, link):
		self.neighbors.add(link)

class Node:
	message_reset_time = int(5e9) # 5 segundos

	def __init__(self, info, protocols, process):
		self.info = info
		self.protocols = {i.protocol_type: i for i in protocols}
		self.process = process
		self.message_queue = dict()
		self.mutex = Lock()
	
	def listen(self):
		for protocol_type, protocol in self.protocols: protocol.listen(self.recv)

	def recv(self, packet, rlink):
		self.mutex.acquire()

		self.info.add_neighbor(rlink)

		time = get_time()
		data = packet.form()
		if data in self.message_queue and time - self.message_queue[data] < Node.message_reset_time: return
		self.message_queue[data] = time
		if packet.dest == str(self.info.ID): self.process(packet.message)
		prop(packet)

		self.mutex.release()
	
	def send(self, message, dest):
		packet = Packet(message, dest)
		prop(packet)

	def prop(self, packet):
		for neighbor in self.info.neighbors:
			neighbor.link.send(packet)
