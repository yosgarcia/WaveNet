from .WaveNetMesh import *
from .WaveNetCommunication import *
from .WaveNetProtocols import *

# Nada más crear instancia de, activate listen, y ya con esto basta
# ping hace ping
class WaveNetBasicMeshHub(WaveNetMeshHub):
	def __init__(self, protocols):
		assert type(protocols) == list
		assert len(protocols) > 0
		for protocol in protocols: assert isinstance(protocol, Protocol)
		self.is_alive = False
		super().__init__(port)
	
	def listen(self):
		assert not self.is_alive
		self.is_alive = True
		return super().listen()

	def kill(self):
		assert self.is_alive
		self.is_alive = False
		return super().kill()
	
	def ping(self, ID):
		assert self.is_alive
		assert type(ID) == int
		return super().ping(ID)

# Crear instancia de, activar listen, conectar con vecinos por medio de connect, unirse a la red con join y ya
# Seguro para empleo con threads
# send manda un mensaje al destinario
# listen recibe de cualquiera -> retorna (src_id, mensaje)
# recv recibe de un ID en particular -> retorna (src_id, mensaje)
# my_id devuelve la identifiacion del nodo
class WaveNetBasicMeshNode(WaveNetMeshNode):
	def __init__(self, protocols):
		assert type(protocols) == list
		assert len(protocols) > 0
		for protocol in protocols: assert isinstance(protocol, Protocol)
		self.is_alive = False
		super().__init__(protocols)

	def ping(self, ID):
		assert self.is_alive
		assert type(ID) == int
		return super().ping(ID)

	def my_id(self):
		return super().node.info.ID;
	
	def connect(self, ID, protocol, dest):
		assert self.is_alive
		assert type(ID) == int
		assert isinstance(protocol, Protocol)
		assert type(dest) == str
		super().connect(ID, protocol, dest)

	def join(self):
		assert self.is_alive
		super().join()
	
	def send(self, dest, message):
		assert self.is_alive
		assert type(dest) == int
		assert type(message) == str
		super().send_data(dest, message)
	
	def listen(self, timeout=None):
		assert self.is_alive
		assert timeout is None or type(timeout) is float
		return super().recv_data(timeout=timeout)

	def recv(self, ID, timeout=None):
		assert self.is_alive
		assert type(ID) == int
		assert timeout is None or type(timeout) is float
		return super().recv_data(ID=ID, timeout=timeout)
	
	def listen(self):
		assert not self.is_alive
		self.is_alive = True
		return super().listen()

	def kill(self):
		assert self.is_alive
		self.is_alive = False
		return super().kill()
	
