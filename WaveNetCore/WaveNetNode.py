from threading import Thread, Lock
import time
import hashlib
from WaveNetCommunication import *

class NodeInfo:
	def __init__(self, ID, private_key, neighbors=set()):
		self.ID = ID
		self.neighbors = neighbors
		self.private_key = private_key
	
	def add_neighbor(self, link):
		self.neighbors.add(link)

class Node:
	def __init__(self, info, protocols, process):
		self.info = info
		self.protocols = {i.protocol_type: i for i in protocols}
		self.process = process
		self.messages = set()
		self.mutex = Lock()
	
	def listen(self):
		for protocol_type, protocol in self.protocols: protocol.listen(self.recv)

	def recv(self, packet):
		self.mutex.acquire()

		data = packet.form()
		if data in self.messages: return
		self.messages.add(data)

		if type(packet) == SecretPacket: packet = decrypt_packet(packet, self.info.private_key)
		if type(packet) == Packet and packet.is_null(): return

		if type(packet) == Packet and packet.dest == self.info.ID: self.process(packet)
		prop(packet)

		self.mutex.release()
	
	def send(self, message, dest):
		packet = Packet(message, dest)
		prop(packet)

	def prop(self, packet):
		for neighbor in self.info.neighbors:
			neighbor.link.send(packet)
