from enum import Enum
import json
import psutil
import socket
from threading import Thread, Event, Lock
from wavenetcore.WaveNetPacketeering import *
from dispositivo_wavenet.dispositivo_wavenet import DispositivoWaveNet as wn
import logging
import time

class ProtocolType(Enum):
	"""
	Enum que maneja los tipos de protocolos disponibles.
	"""

	LOCAL = 1
	IP = 2
	SOUND = 3

class Protocol:
	"""
	Clase que maneja la base de los protocolos.
	"""

	def __init__(self, protocol_type, sender, listener, as_public):
		"""
		Constructor para los protocolos.

		@param protocol_type El tipo de protocolo
		@param sender La función a utilizar para enviar datos
		@param listener La función a utilizar para recibir datos
		@param as_public La función a utilizar para obtener la versión compartida
		"""

		self.protocol_type = protocol_type
		self.sender = sender
		self.listener = listener
		self.as_public = as_public
		self.switch = Event()
		self.wait_kill = Event()

	def send(self, packet, dest):
		"""
		Envía datos por medio del protocolo.

		@param packet El paquete a enviar
		@param dest El destino de la información
		@return Generalmente None pero en algunos casos puede ser un thread
		"""

		return self.sender(packet, dest)

	def listen(self, func):
		"""
		Escucha por conexión entrantes y recibe información.

		@param func Funciona a utilizar para procesar los paquetes entrantes
		@return El thread encargado de escuchar
		"""

		self.switch.clear()
		self.wait_kill.clear()
		t = Thread(target=self.listener, args=[func, self.switch, self.wait_kill], daemon=True)
		t.start()
		return t

	def public(self):
		"""
		Genera la versión pública del protocolo (cómo conectarse al host del protocolo externamente).

		@return Un string que corresponde a su conexión pública.
		"""

		return self.as_public()

	def kill(self):
		"""
		Mata al thread de esucha.
		"""

		self.switch.set()
		self.wait_kill.wait()
		

class LocalProtocol(Protocol):
	"""
	Clase que maneja el protocolo de TCP/IP sobre la interfaz de Loopback.
	"""

	IP = "127.0.0.1"
	protocol_type = ProtocolType.LOCAL

	def __init__(self, port=None):
		"""
		Constructor de la clase.

		@param port El puerto a utilizar
		"""

		self.port = port
		if self.port is not None: assert type(self.port) == int
		super().__init__(LocalProtocol.protocol_type, self.sender, self.listener, self.as_public)

	def sender(self, packet, dest):
		"""
		Envía datos por medio del protocolo.

		@param packet El paquete a enviar
		@param dest El destino de la información
		"""

		data = packet.form()

		PORT = int(dest)

		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
			s.connect((LocalProtocol.IP, PORT))
			s.sendall(data.encode())

	def listener(self, func, switch, kill):
		"""
		Escucha por conexión entrantes y recibe información.

		@param func Funciona a utilizar para procesar los paquetes entrantes
		@param switch El indicador de terminación para el thread
		"""

		assert self.port is not None

		PORT = self.port

		def process_conn(conn):
			parts = []
			with conn:
				while True:
					data = conn.recv(1 << 12)
					if not data: break
					parts.append(data)
			data = b''.join(parts)
			packet = reconstruct_packet(data)
			func(packet)

		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
			s.bind((LocalProtocol.IP, PORT))
			s.listen(10)
			s.settimeout(1)
			while not switch.is_set():
				try:
					conn, _ = s.accept()
					Thread(target=process_conn, args=(conn,), daemon=True).start()
				except socket.timeout:
					pass
		kill.set()

	def as_public(self):
		"""
		Genera la versión pública del protocolo (cómo conectarse al host del protocolo externamente).

		@return Un string que corresponde a su conexión pública.
		"""

		assert self.port is not None
		return str(self.port)

class IPProtocol(Protocol):
	"""
	Clase que maneja el protocolo de TCP/IP.
	"""

	protocol_type = ProtocolType.IP

	def __init__(self, ip=None, port=None):
		"""
		Constructor de la clase.

		@param ip El ip sobre el cual abrirse
		@param port El puerto sobre el cual abrirse
		"""
		self.ip = ip
		self.port = port
		if self.ip is not None: assert type(self.ip) == str
		if self.port is not None: assert type(self.port) == int
		super().__init__(IPProtocol.protocol_type, self.sender, self.listener, self.as_public)

	def sender(self, packet, dest):
		"""
		Envía datos por medio del protocolo.

		@param packet El paquete a enviar
		@param dest El destino de la información
		"""

		IP, PORT = None, None

		data = json.loads(dest)
		status, IP = verify_tag(data, "ip", str)
		if not status: raise Exception(IP)
		status, PORT = verify_tag(data, "port", int)
		if not status: raise Exception(PORT)

		data = packet.form()

		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
			s.connect((IP, PORT))
			s.sendall(data.encode())

	def listener(self, func, switch, kill):
		"""
		Escucha por conexión entrantes y recibe información.

		@param func Funciona a utilizar para procesar los paquetes entrantes
		@param switch El indicador de terminación para el thread
		"""

		assert self.port is not None
		assert self.ip is not None

		IP = self.ip
		PORT = self.port

		def process_conn(conn):
			parts = []
			with conn:
				while True:
					data = conn.recv(1 << 12)
					if not data: break
					parts.append(data)
			data = b''.join(parts)
			packet = reconstruct_packet(data)
			func(packet)

		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
			s.bind((IP, PORT))
			s.listen(10)
			s.settimeout(1)
			while not switch.is_set():
				try:
					conn, _ = s.accept()
					Thread(target=process_conn, args=(conn,), daemon=True).start()
				except socket.timeout:
					pass
		kill.set()

	def as_public(self):
		"""
		Genera la versión pública del protocolo (cómo conectarse al host del protocolo externamente).

		@return Un string que corresponde a su conexión pública.
		"""

		assert self.ip is not None
		assert self.port is not None
		return IPProtocol.ip_to_json(self.ip, self.port)

	def ip_to_json(ip, port):
		"""
		Convierte un par IP, Puerto a su versión en json.

		@param ip El IP
		@param port El puerto
		@return El string que corresponde al json del IP y el puerto
		"""

		assert type(ip) == str
		assert type(port) == int
		return json.dumps({"ip" : ip, "port" : port})

	def get_interfaces():
		"""
		Obtiene las interfaces disponibles en la máquina actual (exluyendo a loopback).

		@return Lista de las interfaces disponibles
		"""

		results = []
		for iface, addrs in psutil.net_if_addrs().items():
			for addr in addrs:
				if addr.family == socket.AF_INET and not addr.address.startswith("127."):
					results.append((iface, addr.address))
		return results

class SoundProtocol(Protocol):
	"""
	Clase que maneja el protocolo de capa 1 de sonido.
	"""

	protocol_type = ProtocolType.SOUND
	MAC = None
	mutex = Lock()

	def __init__(self, mac=None):
		"""
		Constructor de la clase.

		@param mac El MAC address a utilizar
		"""
		if mac is not None: SoundProtocol.MAC = mac
		else: assert SoundProtocol.MAC is not None
		assert type(SoundProtocol.MAC) == str
		super().__init__(SoundProtocol.protocol_type, self.sender, self.listener, self.as_public)
	
	def sender(self, packet, dest):
		"""
		Manda un paquete.

		@param packet El paquete
		@param dest El MAC address del destino
		"""

		def temp():
			with SoundProtocol.mutex:
				w = wn(self.MAC, dest)
				w.send(packet.form(), timeout=60*3)
			time.sleep(15)

		t = Thread(target=temp, args=(), daemon=True)
		t.start()
		return t
	

	def listener(self, func, switch, kill):
		"""
		Escucha por conexión entrantes y recibe información.

		@param func Funciona a utilizar para procesar los paquetes entrantes
		@param switch El indicador de terminación para el thread
		"""

		while not switch.is_set():
			try:
				with SoundProtocol.mutex:
					w = wn(self.MAC, "")
					data = w.listen(timeout=60*3, init_timeout=5)
				packet = reconstruct_packet(data)
				func(packet)
			except Exception as e:
				logging.info(f"SoundProtocol listener died again : {str(e)}")
		kill.set()

	def as_public(self):
		"""
		Genera la versión pública del protocolo (cómo conectarse al host del protocolo externamente).

		@return Un string que corresponde a su conexión pública.
		"""

		return SoundProtocol.MAC


def empty_protocol_from_str(name):
	"""
	Crea una instancia vacía de un protocolo a partir de su nombre.

	@param name El nombre del protocolo
	@return La instancia vacía del protocolo
	"""

	assert name in ProtocolType.__members__
	if ProtocolType[name] == ProtocolType.LOCAL: return LocalProtocol()
	if ProtocolType[name] == ProtocolType.IP: return IPProtocol()
	if ProtocolType[name] == ProtocolType.SOUND: return SoundProtocol()
	assert False

class Link:
	"""
	Clase que maneja las conexiones entre nodos.
	"""

	def __init__(self, dest, protocol):
		"""
		Constructor para las conexiones.

		@param dest El destino de la conexión
		@param protocol El protocolo a utilizar
		"""

		self.protocol = protocol
		self.dest = dest

	def send(self, packet):
		"""
		Manda un paquete a través del protocolo.

		@param packet El paquete a mandar
		@return Generalmente none pero en el caso de algunos protocolos puede ser un thread
		"""

		return self.protocol.send(packet, self.dest)

	def __str__(self):
		"""
		Genera la versión textual de la conexión.

		@return La versión textual de la conexión
		"""

		return "|" + self.protocol.protocol_type.name + "|" + self.dest

	def __hash__(self):
		"""
		Genera el hash de la conexión.

		@return El hash de la conexión
		"""

		return hash(str(self))

	def __eq__(self, other):
		"""
		Determina si dos conexiones son iguales.

		@param other La otra conexión
		@return Si las dos conexiones son iguales
		"""
		return str(self) == str(other)
