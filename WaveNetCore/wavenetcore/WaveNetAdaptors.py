import wavenetcore.WaveNetMesh as mesh
import wavenetcore.WaveNetProtocols as prot

class WaveNetBasicMeshHub(mesh.MeshHub):
	"""
	El adaptador del MeshHub.
	"""

	def __init__(self, protocols, encrypt=True):
		"""
		Constructor del adaptador del mesh hub.

		@param protocols Los protocolos disponibles del mesh hub
		@param encrypt Si se debería cifrar la comuniación
		"""

		assert type(protocols) == list
		assert len(protocols) > 0
		for protocol in protocols: assert isinstance(protocol, prot.Protocol)
		assert type(encrypt) == bool
		self.is_alive = False
		super().__init__(protocols, encrypt=encrypt)

	def my_id(self):
		"""
		Devuelve el id del nodo.

		@return El id del nodo
		"""

		return 0
	
	def run(self):
		"""
		Inicializa el mesh hub.
		"""

		assert not self.is_alive
		self.is_alive = True
		return super().listen()

	def kill(self):
		"""
		Mata el mesh hub.
		"""

		assert self.is_alive
		self.is_alive = False
		return super().kill()
	
	def ping(self, ID):
		"""
		Ejecuta un ping a algún nodo en la misma red mesh.

		@param ID El ID del nodo a hacer ping
		@return Si la conexión ping fue exitosa
		"""

		assert self.is_alive
		assert type(ID) == int
		return super().ping(ID)

class WaveNetBasicMeshNode(mesh.MeshNode):
	"""
	Clase que maneja el adaptador del nodo mesh.
	"""

	def __init__(self, protocols, ID=None, encrypt=True):
		"""
		Constructor del adaptador del mesh node.

		@param protocols Los protocolos disponibles del mesh node
		@param ID El identificador que se debería asociar al nodo
		@param encrypt Si se debería cifrar la comuniación
		"""

		assert ID is None or type(ID) == int
		assert type(protocols) == list
		assert len(protocols) > 0
		for protocol in protocols: assert isinstance(protocol, prot.Protocol)
		assert type(encrypt) == bool
		self.is_alive = False
		super().__init__(protocols, ID=ID, encrypt=encrypt)

	def ping(self, ID):
		"""
		Ejecuta un ping a algún nodo en la misma red mesh.

		@param ID El ID del nodo a hacer ping
		@return Si la conexión ping fue exitosa
		"""

		assert self.is_alive
		assert type(ID) == int
		return super().ping(ID)

	def my_id(self):
		"""
		Devuelve el id del nodo.

		@return El id del nodo
		"""

		return self.node.info.ID
	
	def connect(self, ID, protocol, dest):
		"""
		Forma una conexión con un vecino.

		@param ID El identificador del vecino
		@param protocol El protocolo a utilizar para la conexión
		@param dest El destinario del vecino en formato correspondiente al protocolo
		"""

		assert self.is_alive
		assert type(ID) == int
		assert isinstance(protocol, prot.Protocol)
		assert type(dest) == str
		super().connect(ID, protocol, dest)

	def join(self):
		"""
		Une el nodo a la red mesh (publica su llave pública al hub).
		"""

		assert self.is_alive
		super().join()
	
	def send(self, dest, message):
		"""
		Manda un mensaje.

		@param dest El identificador del destinario
		@param message El cuerpo del mensaje
		"""

		assert self.is_alive
		assert type(dest) == int
		assert type(message) == str
		super().send_data(dest, message)
	
	def listen(self, timeout=None):
		"""
		Espera una conexión.

		@param timeout El tiempo máximo de espera
		@return La tupla de (ID fuente, el cuerpo del mensaje)
		"""

		assert self.is_alive
		assert timeout is None or type(timeout) is float
		if timeout is None: timeout = 3600.0
		return super().recv_data(timeout=timeout)

	def recv(self, ID, timeout=None):
		"""
		Espera un mensaje de un nodo en particular.

		@param ID El ID de quien se espera el mensaje
		@param timeout El tiempo máximo de espera
		@return La tupla de (ID fuente, el cuerpo del mensaje)
		"""

		assert self.is_alive
		assert type(ID) == int
		assert timeout is None or type(timeout) is float
		if timeout is None: timeout = 60.0
		return super().recv_data(ID=ID, timeout=timeout)
	
	def run(self):
		"""
		Inicializa el mesh hub.
		"""

		assert not self.is_alive
		self.is_alive = True
		return super().listen()

	def kill(self):
		"""
		Mata el mesh hub.
		"""

		assert self.is_alive
		self.is_alive = False
		return super().kill()
	
