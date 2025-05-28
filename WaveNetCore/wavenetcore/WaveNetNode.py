from threading import Thread, Lock
import time
import hashlib
from wavenetcore.WaveNetPacketeering import *
from wavenetcore.WaveNetProtocols import *

class NodeInfo:
	"""
	Clase que maneja la información asociada a cada nodo.
	"""

	def __init__(self, ID, private_key, neighbors=None):
		"""
		El constructor de los nodos.

		@param ID La identificación del nodo
		@param private_key La llave privada del nodo
		@param neighbors Los vecinos del nodo
		"""

		self.ID = ID
		self.neighbors = neighbors if neighbors is not None else set()
		self.private_key = private_key
		self.mutex = Lock()
	
	def add_neighbor(self, link):
		"""
		Añade un vecino.

		@param link La conexión al vecino
		"""

		with self.mutex:
			self.neighbors.add(link)
	
	def get_neighbors(self):
		"""
		Devuelve los vecinos actuales.

		@return Una copia de los vecinos actuales
		"""
		with self.mutex:
			return self.neighbors.copy()

class Node:
	"""
	Clase que maneja la interacción básica entre nodos.
	"""

	def __init__(self, info, protocols, process):
		"""
		Constructor para los nodos.

		@param info El contenedor de información del nodo
		@param protocols Los protocolos disponibles al nodo
		@param process La función que procesa todos los paquetes destinados para este nodo
		"""

		self.info = info
		self.protocols = {i.protocol_type: i for i in protocols}
		self.process = process
		self.messages = set()
		self.mutex = Lock()
	
	def listen(self):
		"""
		Inicializa la escucha de los protocolos.
		"""

		for protocol_type, protocol in self.protocols.items(): protocol.listen(self.recv)
	
	def kill(self):
		"""
		Mata a todos los nodos.
		"""

		for protocol_type, protocol in self.protocols.items(): protocol.kill()

	def recv(self, original):
		"""
		Método para procesar paquetes entrantes

		@param original El paquete
		"""

		with self.mutex:
			packet = original

			if hash(packet) in self.messages: return
			self.messages.add(hash(packet))

			if type(packet) == SecretPacket: packet = decrypt_packet(packet, self.info.private_key)
			if type(packet) == Packet and packet.is_null(): return

			should_prop = True

			if type(packet) == Packet and packet.dest == self.info.ID: should_prop = self.process(packet)
			if should_prop: self.prop(original)
		
	def send(self, dest, mtype, message, show_src=True, public_key=None):
		"""
		Envía un mensaje a la red de nodos.

		@param dest El destinario
		@param mtype El tipo del mensaje
		@param message El cuerpo del mensaje
		@param show_src Determina si se debería incluir el emisor
		@param public_key La llave pública a utilizar para cifrar
		"""

		with self.mutex:
			src = self.info.ID if show_src else -1
			packet = Packet(src, dest, mtype, message)
			if public_key is not None:
				packet = encrypt_packet(packet, public_key)
				if type(packet) == Packet:return
			self.messages.add(hash(packet))
			self.prop(packet)

	def prop(self, packet):
		"""
		Propaga un paquete a todos sus vecinos.

		@param packet El paquete a propagar
		"""

		for neighbor in self.info.get_neighbors(): neighbor.send(packet)
