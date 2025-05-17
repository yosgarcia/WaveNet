from WaveNetMesh import *
from WaveNetCommunication import *

# Nada más crear instancia de y ya con esto basta
# ping hace ping
class WaveNetBasicMeshHub(WaveNetMeshHub):
	def __init__(self, port=8000):
		assert(type(port) == int)
		super().__init__(port)
	
	def ping(self, ID):
		assert(type(ID) == int)
		return super().ping(ID)

# Crear instancia de, conectar con vecinos por medio de connect, unirse a la red con join y ya
# Seguro para empleo con threads
# send manda un mensaje al destinario
# listen recibe de cualquiera -> retorna (src_id, mensaje)
# recv recibe de un ID en particular -> retorna (src_id, mensaje)
# my_id devuelve la identifiacion del nodo
class WaveNetBasicMeshNode(WaveNetMeshNode):
	def __init__(self, protocols):
		assert(type(protocols) == list)
		assert(len(protocols) > 0)
		for protocol in protocols: assert(isinstance(protocol, Protocol))
		super().__init__(protocols)

	def ping(self, ID):
		assert(type(ID) == int)
		return super().ping(ID)

	def my_id(self):
		return super().node.info.ID;
	
	def connect(self, ID, protocol, dest):
		assert(type(ID) == int)
		assert(isinstance(protocol, Protocol))
		assert(type(dest) == str)
		super().connect(ID, protocol, dest)

	def join(self):
		super().join()
	
	def send(self, dest, message):
		assert(type(dest) == int)
		assert(type(message) == str)
		super().send_data(dest, message)
	
	def listen(self):
		return super().recv_data()

	def recv(self, ID):
		assert(type(ID) == int)
		return super().recv_data(ID)
