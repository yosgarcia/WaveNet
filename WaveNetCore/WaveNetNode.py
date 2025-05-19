from threading import Thread, Lock
import time
import hashlib
from .WaveNetPacketeering import *
from .WaveNetProtocols import *

class NodeInfo:
	def __init__(self, ID, private_key, neighbors=set()):
		self.ID = ID
		self.neighbors = neighbors
		self.private_key = private_key
		self.mutex = Lock()
	
	def add_neighbor(self, link):
		self.mutex.acquire()
		self.neighbors.add(link)
		self.mutex.release()
	
	def get_neighbors(self):
		self.mutex.acquire()
		ans = self.neighbors.copy()
		self.mutex.release()
		return ans

class Node:
	def __init__(self, info, protocols, process):
		self.info = info
		self.protocols = {i.protocol_type: i for i in protocols}
		self.process = process
		self.messages = set()
		self.mutex = Lock()
	
	def listen(self):
		for protocol_type, protocol in self.protocols.items(): protocol.listen(self.recv)
	
	def kill(self):
		for protocol_type, protocol in self.protocols.items(): protocol.kill()

	def recv(self, original):
		self.mutex.acquire()

		packet = original

		data = packet.form()
		if data in self.messages: return
		self.messages.add(data)

		if type(packet) == SecretPacket: packet = decrypt_packet(packet, self.info.private_key)
		if type(packet) == Packet and packet.is_null(): return

		should_prop = True

		if type(packet) == Packet and packet.dest == self.info.ID: should_prop = self.process(packet)
		if should_prop: self.prop(original)

		self.mutex.release()
	
	def send(self, dest, mtype, message, show_src=True, public_key=None):
		src = self.info.ID if show_src else -1
		packet = Packet(src, dest, mtype, message)
		if public_key is not None:
			packet = encrypt_packet(packet, public_key)
			if type(packet) == Packet: return
		self.prop(packet)

	def prop(self, packet):
		for neighbor in self.info.get_neighbors():
			neighbor.send(packet)
