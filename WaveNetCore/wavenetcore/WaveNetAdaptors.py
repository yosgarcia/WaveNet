import wavenetcore.WaveNetMesh as mesh
import wavenetcore.WaveNetProtocols as prot

class WaveNetBasicMeshHub(mesh.MeshHub):
	def __init__(self, protocols, encrypt=True):
		assert type(protocols) == list
		assert len(protocols) > 0
		for protocol in protocols: assert isinstance(protocol, prot.Protocol)
		assert type(encrypt) == bool
		self.is_alive = False
		super().__init__(protocols, encrypt=encrypt)

	def my_id(self):
		return 0
	
	def run(self):
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

class WaveNetBasicMeshNode(mesh.MeshNode):
	def __init__(self, protocols, ID=None, encrypt=True):
		assert ID is None or type(ID) == int
		assert type(protocols) == list
		assert len(protocols) > 0
		for protocol in protocols: assert isinstance(protocol, prot.Protocol)
		assert type(encrypt) == bool
		self.is_alive = False
		super().__init__(protocols, ID=ID, encrypt=encrypt)

	def ping(self, ID):
		assert self.is_alive
		assert type(ID) == int
		return super().ping(ID)

	def my_id(self):
		return self.node.info.ID
	
	def connect(self, ID, protocol, dest):
		assert self.is_alive
		assert type(ID) == int
		assert isinstance(protocol, prot.Protocol)
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
		if timeout is None: timeout = 3600.0
		return super().recv_data(timeout=timeout)

	def recv(self, ID, timeout=None):
		assert self.is_alive
		assert type(ID) == int
		assert timeout is None or type(timeout) is float
		if timeout is None: timeout = 10.0
		return super().recv_data(ID=ID, timeout=timeout)
	
	def run(self):
		assert not self.is_alive
		self.is_alive = True
		return super().listen()

	def kill(self):
		assert self.is_alive
		self.is_alive = False
		return super().kill()
	
