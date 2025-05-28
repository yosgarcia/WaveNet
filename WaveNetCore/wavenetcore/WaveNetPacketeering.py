import json
import base64
from datetime import datetime, timezone
from wavenetcore.WaveNetCrypto import *
import logging

class Packet:
	"""
	Clase que maneja los paquetes de la capa 2 y 3.
	"""

	params = (
			("src", int),
			("dest", int),
			("mtype", str),
			("body", str),
			("timestamp", str),
		)

	def __init__(self, src, dest, mtype, body, timestamp=None):
		"""
		Constructor de la clase.

		@param src El fuente del paquete
		@param dest El destino del paquete
		@param mtype El tipo de mensaje del paquete
		@param body El cuerpo del paquete
		@param timestamp El tiempo de creación de paquete
		"""
		self.src = src
		self.dest = dest
		self.mtype = mtype
		self.body = body
		self.timestamp = timestamp if timestamp is not None else datetime.now(timezone.utc).isoformat()
	
	def form(self):
		"""
		Genera la versión textual del paquete.

		@return La versión textual del paquete
		"""
		return json.dumps({
			"enc" : False,
			"src" : self.src,
			"dest" : self.dest,
			"mtype" : self.mtype,
			"body" : self.body,
			"timestamp" : self.timestamp
			})
	
	def null(message):
		"""
		Crea un paquete vacío para errores.

		@param message El mensaje de error
		@return El paquete vacío
		"""
		return Packet(-1, -1, "error", message)

	def is_null(self):
		"""
		Determina si un paquete es vacío.

		@return Si el paquete es vacío
		"""
		return self.mtype == "error"

	def __str__(self):
		"""
		Genera la versión textual del paquete.

		@return La versión textual del paquete
		"""
		return self.form()

	def __hash__(self):
		"""
		Genera el hash del paquete.

		@return El hash del paquete.
		"""
		return hash(str(self))

	def __eq__(self, other):
		"""
		Determina si un paquete es igual a otro.

		@param other El otro paquete
		@return Si un paquete es igual a otro
		"""
		if type(other) != type(self): return False
		return self.form() == other.form()


class SecretPacket:
	"""
	Clase que maneja paquetes cifrados.
	"""
	params = (
			("meta", str),
			("body", str),
		)

	def __init__(self, meta, body):
		"""
		Constructor de la clase.

		@param meta La metainformación del paquete
		@param body El cuerpo del paquete
		"""
		self.meta = meta
		self.body = body

	def form(self):
		"""
		Genera la versión textual del paquete.

		@return La versión textual del paquete
		"""
		return json.dumps({
			"enc" : True,
			"meta" : self.meta,
			"body" : self.body
			})

	def __str__(self):
		"""
		Genera la versión textual del paquete.

		@return La versión textual del paquete
		"""
		return self.form()

	def __hash__(self):
		"""
		Genera el hash del paquete.

		@return El hash del paquete.
		"""
		return hash(str(self))

	def __eq__(self, other):
		"""
		Determina si un paquete es igual a otro.

		@param other El otro paquete
		@return Si un paquete es igual a otro
		"""
		if type(other) != type(self): return False
		return self.form() == other.form()

def verify_tag(parsed, name, etype):
	"""
	Verifica que un tag de json fue correctamente incluido.

	@param parsed El json parseado
	@param name El nombre de la llave
	@param etype El tipo de valor asociado a la llave
	@return Si fue parseado correctamente o no
	"""
	if name not in parsed: return False, f"Missing {name} tag"
	v = parsed[name]
	if type(v) != etype: return False, f"Bad {name} tag"
	return True, v

def reconstruct_packet(data):
	"""
	Reconstruye un paquete a partir de información entrante.
	
	@param data Información entrante
	@return El paquete parseado
	"""
	try:
		parsed = json.loads(data)
		status, enc = verify_tag(parsed, "enc", bool)
		if not status: return Packet.null(enc)
		if enc:
			data = []
			for name, etype in SecretPacket.params:
				status, v = verify_tag(parsed, name, etype)
				if not status: return Packet.null(v)
				data.append(v)
			return SecretPacket(data[0], data[1])
		else:
			data = []
			for name, etype in Packet.params:
				status, v = verify_tag(parsed, name, etype)
				if not status: return Packet.null(v)
				data.append(v)
			return Packet(data[0], data[1], data[2], data[3], data[4])
	except Exception as e:
		logging.warning(f"Received a bad data: {data}")
		return Packet.null("Formation Error " + str(e))


def encrypt_packet(packet, public_key):
	"""
	Cifra un paquete normal.

	@param packet El paquete a cifrar
	@param public_key La llave publica a utilizar
	@return El paquete cifrado
	"""
	try:
		data = packet.form()
		key64 = AES_create_key()
		nonce64, body64 = AES_encrypt(key64, data)
		meta = public_key.encrypt(json.dumps({
			"decrypted" : True,
			"key" : key64,
			"nonce" : nonce64,
			}).encode())
		meta64 = base64.b64encode(meta).decode()
		return SecretPacket(meta64, body64)
	except Exception as e:
		logging.error("Yeah, I couldn't encrypt this packet...")
		return Packet.null("Formation Error " + str(e))

def decrypt_packet(packet, private_key):
	"""
	Decifra un paquete cifrado.

	@param packet El paquete cifrado
	@param private_key La llave privada
	@return El paquete decifrado
	"""
	try:
		meta = base64.b64decode(packet.meta.encode())
		parsed = json.loads(private_key.decrypt(meta))
		status, dec = verify_tag(parsed, "decrypted", bool)
		if not status or not dec: return packet
		status, key64 = verify_tag(parsed, "key", str)
		if not status: return packet
		status, nonce64 = verify_tag(parsed, "nonce", str)
		if not status: return packet
		data = AES_decrypt(key64, nonce64, packet.body)
		return reconstruct_packet(data)
	except Exception as e:
		logging.info("Couldn't decrypt packet, maybe it's not for me?")
		return packet

