from wavenetcore.WaveNetNode import *
from wavenetcore.WaveNetPacketeering import *
from wavenetcore.WaveNetProtocols import *
from wavenetcore.WaveNetCrypto import *
from random import randint
import json
import time
from threading import Thread, Lock, Condition
import logging

class PacketWaiter:
	"""
	Clase que abstrae la acción de "esperar por una respuesta".
	"""

	timeout = 20.0 # En segundos

	def __init__(self):
		"""
		Constructor.
		"""
		self.condition = Condition()
		self.packet = Packet.null("Timeout")

	def recv(self, timeout=None):
		"""
		Deja el thread actual pendiente de la recepción de información.

		@param timeout La duración del timeout
		"""

		with self.condition:
			if timeout is None: timeout = PacketWaiter.timeout
			self.condition.wait(timeout)
			return self.packet

	def send(self, packet):
		"""
		Despierta a los threads pendientes de un paquete en particular.

		@param el paquete
		"""
		
		self.packet = packet
		self.condition.notify_all()
	
	def __enter__(self):
		"""
		Método que permite agarrar el recurso.
		"""

		self.condition.acquire()
	
	def __exit__(self, exc_type, exc_value, traceback):
		"""
		Método que permite liberar el recurso.

		@param exc_type N/A
		@param exc_value N/A
		@param exc_traceback N/A
		@return N/A
		"""

		self.condition.release()
		return False

class MeshHub(Node):
	"""
	Clase que maneja el mesh hub.
	"""

	def __init__(self, protocols, encrypt=True):
		"""
		El constructor del mesh hub.

		@param protocols Los protocolos disponibles al hub
		@param encrypt Si se debería cifrar las comunicaciones o no
		"""

		self.private_key = PrivateKey()
		info = NodeInfo(0, self.private_key)
		self.node = Node(info, protocols, self.delegate)
		self.nodes = {0: self.private_key.public_key()}
		self.encrypt = encrypt
		self.awaits = dict()
		self.mutex = Lock()
	
	def __send(self, dest, mtype, message):
		"""
		Método privado para enviar un mensaje a la red.

		@param dest El destinario
		@param mtype El tipo de mensaje
		@param message El cuerpo del mensaje
		"""

		key = self.nodes[dest] if dest in self.nodes and self.encrypt else None
		self.node.send(dest, mtype, message, public_key=key)
	
	def sends(self, dest, mtype, message):
		"""
		Método que genera un thread para enviar un mensaje a la red (para evitar deadlocks).

		@param dest El destinario
		@param mtype El tipo de mensaje
		@param message El cuerpo del mensaje
		"""

		Thread(target=self.__send, args=(dest, mtype, message,), daemon=True).start()
	
	def ping(self, ID):
		"""
		Ejecuta un ping a un nodo.

		@param ID Algún nodo
		"""

		with self.mutex:
			if (ID, "pong") not in self.awaits: self.awaits[(ID, "pong")] = PacketWaiter()
			waiter = self.awaits[(ID, "pong")]
		self.sends(ID, "ping", "")
		packet = waiter.recv()
		if packet.is_null(): return False
		return packet.src == ID
	
	def process_connect(self, packet):
		"""
		Procesa una solicitud de conexión.

		@param packet El paquete recibido
		"""

		data = json.loads(packet.body)
		"""
		{
			"protocol" : str
			"dest" : str
		}
		"""
		status, protocol = verify_tag(data, "protocol", str)
		if not status: raise Exception(protocol)
		status, dest = verify_tag(data, "dest", str)
		if not status: raise Exception(dest)
		link = Link(dest, empty_protocol_from_str(protocol))
		self.node.info.add_neighbor(link)

	def process_ping(self, packet):
		"""
		Procesa una solicitud de ping.

		@param packet El paquete recibido
		"""

		self.sends(packet.src, "pong", "")

	def process_pong(self, packet):
		"""
		Procesa una respuesta de pong.

		@param packet El paquete recibido
		"""

		if (packet.src, packet.mtype) in self.awaits:
			waiter = self.awaits.pop((packet.src, packet.mtype))
			with waiter: waiter.send(packet)

	def process_request(self, packet):
		"""
		Procesa un request por la llave pública de algún nodo en particular.

		@param packet El paquete recibido
		"""

		data = json.loads(packet.body)
		"""
		{
			"id" : int
		}
		"""
		status, ID = verify_tag(data, "id", int)
		if not status: raise Exception(ID)
		if ID not in self.nodes: raise Exception("ID not found")
		pem = str(self.nodes[ID])
		ans = {"id" : ID, "pem" : pem}
		message = json.dumps(ans)
		self.sends(packet.src, "answer", message)
	
	def process_join(self, packet):
		"""
		Procesa una solicitud de un nodo para unirse a la red.

		@param packet El paquete recibido
		"""

		data = json.loads(packet.body)
		"""
		{
			"id" : int
			"pem" : str
		}
		"""
		status, ID = verify_tag(data, "id", int)
		if not status: raise Exception(ID)
		status, pem = verify_tag(data, "pem", str)
		if not status: raise Exception(pem)
		public_key = PublicKey(pem=pem.encode())
		if ID in self.nodes: raise Exception("Repeated ID")
		self.nodes[ID] = public_key
	
	def delegate(self, packet):
		"""
		Delega el procesamiento de un paquete dependiendo de su tipo.

		@param packet El paquete recibido
		@return Si se puede propagar el paquete a los vecinos o no
		"""

		with self.mutex:
			try:
				if packet.mtype == "connect":
					self.process_connect(packet)
					return False
				if packet.mtype == "ping": self.process_ping(packet)
				if packet.mtype == "pong": self.process_pong(packet)
				if packet.mtype == "request": self.process_request(packet)
				if packet.mtype == "join": self.process_join(packet)
			except Exception as e:
				logging.warning("Couldn't process a message properly...")
				logging.error(str(e))
		return True

	def listen(self):
		"""
		Inicializa la escucha del nodo.
		"""

		self.node.listen()
	
	def kill(self):
		"""
		Mata al nodo.
		"""

		self.node.kill()

class MeshNode(Node):
	"""
	Clase que maneja los nodos del mesh.
	"""

	def __init__(self, protocols, ID=None, encrypt=True):
		"""
		Constructor de los nodos del mesh.

		@param protocols Los protocolos disponibles al nodo
		@param ID La identificación del nodo
		@param encrypt Si la comunicación del nodo se debería cifrar o no
		"""

		self.private_key = PrivateKey()
		if ID is None: ID = randint(1, (1 << 64) - 1)
		info = NodeInfo(ID, self.private_key)
		self.node = Node(info, protocols, self.delegate)
		self.encrypt = encrypt
		self.awaits = dict()
		self.mutex = Lock()
		self.hub_key = None
	
	def __basic_send(self, dest, mtype, message):
		"""
		Método que envía un mensaje sin procesamiento adicional.

		@param dest El destinario
		@param mtype El tipo de mensaje
		@param message El cuerpo del mensaje
		"""

		self.node.send(dest, mtype, message)

	def basic_send(self, dest, mtype, message):
		"""
		Crea un thread que envía un mensaje sin procesamiento adicional.

		@param dest El destinario
		@param mtype El tipo de mensaje
		@param message El cuerpo del mensaje
		"""

		Thread(target=self.__basic_send, args=(dest, mtype, message,), daemon=True).start()
	
	def request(self, ID):
		"""
		Solicita la llave de un nodo en particular al hub central.

		@param ID La identificación del nodo
		@return La llave pública del nodo solicitado
		"""

		with self.mutex:
			key = self.hub_key if self.encrypt else None
			if (ID, "answer") not in self.awaits: self.awaits[(ID, "answer")] = PacketWaiter()
			waiter = self.awaits[(ID, "answer")]
		message = json.dumps({"id" : ID})
		self.node.send(0, "request", message, public_key=key)
		packet = waiter.recv()
		if packet.is_null(): raise Exception(packet.body)
		data = json.loads(packet.body)
		"""
		{
			"id" : int
			"pem" : str
		}
		"""
		status, ID = verify_tag(data, "id", int)
		if not status: raise Exception(ID)
		status, pem = verify_tag(data, "pem", str)
		if not status: raise Exception(pem)
		public_key = PublicKey(pem=pem.encode())
		return public_key
	
	def __send(self, dest, mtype, message):
		"""
		Método privado para enviar un mensaje a la red.

		@param dest El destinario
		@param mtype El tipo de mensaje
		@param message El cuerpo del mensaje
		"""

		if self.hub_key is None: raise Exception("Node is not yet joined")
		key = self.request(dest) if self.encrypt else None
		self.node.send(dest, mtype, message, public_key=key)
	
	def sends(self, dest, mtype, message):
		"""
		Método que genera un thread para enviar un mensaje a la red (para evitar deadlocks).

		@param dest El destinario
		@param mtype El tipo de mensaje
		@param message El cuerpo del mensaje
		"""

		Thread(target=self.__send, args=(dest, mtype, message,), daemon=True).start()
	
	def join(self):
		"""
		Ejecuta la conexión a la red mesh.
		"""

		with self.mutex:
			message = json.dumps({
				"id" : self.node.info.ID,
				"pem" : str(self.private_key.public_key())
				})
			self.basic_send(0, "join", message)
		time.sleep(0.5)
		key = self.request(0)
		with self.mutex: self.hub_key = key
	
	def ping(self, ID):
		"""
		Ejecuta un ping a un nodo.

		@param ID Algún nodo
		"""

		with self.mutex:
			if (ID, "pong") not in self.awaits: self.awaits[(ID, "pong")] = PacketWaiter()
			waiter = self.awaits[(ID, "pong")]
		if self.hub_key is None: self.basic_send(ID, "ping", "")
		else: self.sends(ID, "ping", "")
		packet = waiter.recv()
		if packet.is_null(): return False
		return packet.src == ID

	def send_data(self, dest, message):
		"""
		Envia un paquete de tipo data.

		@param dest El destinario del paquete
		@param message El cuerpo del mensaje
		"""

		self.sends(dest, "data", message)
	
	def recv_data(self, ID=None, timeout=None):
		"""
		Recibe un paquete de tipo data.

		@param ID La identificación del nodo fuente (o nulo si se puede recibir un mensaje de cualquiera)
		@param timeout El timeout del mensaje en el peor caso
		@return La tupla de (ID fuente, texto del cuerpo)
		"""

		with self.mutex:
			waiter = None
			if (ID, "data") not in self.awaits: self.awaits[(ID, "data")] = PacketWaiter()
			waiter = self.awaits[(ID, "data")]
		packet = waiter.recv(timeout)
		if packet.is_null(): raise Exception(packet.body)
		return packet.src, packet.body

	def connect(self, ID, protocol, dest):
		"""
		Ejecuta una solicitud de conexión a otro nodo en el mesh.

		@param ID La identificación del otro nodo
		@param protocol El protocolo utilizado para la conexión
		@param dest El destinario en formato aceptado por el protocolo
		"""

		link = Link(dest, protocol)
		self.node.info.add_neighbor(link)
		message = json.dumps({
			"protocol" : protocol.protocol_type.name,
			"dest" : protocol.public()
			})
		link.send(Packet(-1, ID, "connect", message))

	def process_connect(self, packet):
		"""
		Procesa una solicitud de conexión.

		@param packet El paquete recibido
		"""

		data = json.loads(packet.body)
		"""
		{
			"protocol" : str
			"dest" : str
		}
		"""
		status, protocol = verify_tag(data, "protocol", str)
		if not status: raise Exception(protocol)
		status, dest = verify_tag(data, "dest", str)
		if not status: raise Exception(dest)
		link = Link(dest, empty_protocol_from_str(protocol))
		self.node.info.add_neighbor(link)

	def process_ping(self, packet):
		"""
		Procesa una solicitud de ping.

		@param packet El paquete recibido
		"""

		self.sends(packet.src, "pong", "")

	def process_pong(self, packet):
		"""
		Procesa una respuesta de pong.

		@param packet El paquete recibido
		"""

		if (packet.src, packet.mtype) in self.awaits:
			waiter = self.awaits.pop((packet.src, packet.mtype))
			with waiter: waiter.send(packet)
	
	def process_answer(self, packet):
		"""
		Procesa la respuesta a un request al hub.

		@param packet El paquete recibido
		"""

		data = json.loads(packet.body)
		status, ID = verify_tag(data, "id", int)
		if not status: raise Exception(ID)
		if (ID, packet.mtype) in self.awaits:
			waiter = self.awaits.pop((ID, packet.mtype))
			with waiter: waiter.send(packet)

	def process_data(self, packet):
		"""
		Procesa la recepción de un paquete de data.

		@param packet El paquete recibido
		"""

		if (packet.src, packet.mtype) in self.awaits:
			waiter = self.awaits.pop((packet.src, packet.mtype))
			with waiter: waiter.send(packet)
		elif (None, packet.mtype) in self.awaits:
			waiter = self.awaits.pop((None, packet.mtype))
			with waiter: waiter.send(packet)

	def delegate(self, packet):
		"""
		Delega el procesamiento de un paquete dependiendo de su tipo.

		@param packet El paquete recibido
		@return Si se puede propagar el paquete a los vecinos o no
		"""

		with self.mutex:
			try:
				if packet.mtype == "connect":
					self.process_connect(packet)
					return False
				if packet.mtype == "ping": self.process_ping(packet)
				if packet.mtype == "pong": self.process_pong(packet)
				if packet.mtype == "answer": self.process_answer(packet)
				if packet.mtype == "data": self.process_data(packet)
			except Exception as e:
				logging.warning("Couldn't process a message properly...")
				logging.error(str(e))
		return True

	def listen(self):
		"""
		Inicializa la escucha del nodo.
		"""

		self.node.listen()
	
	def kill(self):
		"""
		Mata al nodo.
		"""

		self.node.kill()

