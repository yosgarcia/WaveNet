from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os
import json
import base64

class PublicKey:
	"""
	Clase que maneja la llave publica de RSA y operaciones relacionadas.
	"""

	def __init__(self, pem=None, public_key=None):
		"""
		Constructor de PublicKey.

		@param pem El pem fuente
		@param public_key La llave pública
		"""
		assert (pem is None)^(public_key is None)
		if pem is not None:
			self.public_key = serialization.load_pem_public_key(pem)
		if public_key is not None:
			self.public_key = public_key
	
	def __str__(self):
		"""
		Conversión a string.

		@return La versión string de la llave pública
		"""
		return self.public_key.public_bytes(
				encoding=serialization.Encoding.PEM,
				format=serialization.PublicFormat.SubjectPublicKeyInfo
				).decode()

	def encrypt(self, data):
		"""
		Genera la versión cifrada de un texto.

		@param data La información a cifrar
		@return La información cifrada
		"""
		return self.public_key.encrypt(
				data,
				padding.OAEP(
					mgf=padding.MGF1(algorithm=hashes.SHA256()),
					algorithm=hashes.SHA256(),
					label=None
					)
				)

class PrivateKey:
	"""
	Clase que maneja la llave privada y funcionalidades asociadas.
	"""

	def __init__(self):
		"""
		Constructor de la llave privada.
		"""
		self.private_key = rsa.generate_private_key(65537, 2048)

	def public_key(self):
		"""
		Genera la llave pública de la llave privada.

		@return La llave pública
		"""
		return PublicKey(public_key=self.private_key.public_key())

	def decrypt(self, data):
		"""
		Decifra información utilizando la llave privada.

		@param data La información a decifrar
		@return La información decifrada
		"""
		return self.private_key.decrypt(
				data,
				padding.OAEP(
					mgf=padding.MGF1(algorithm=hashes.SHA256()),
					algorithm=hashes.SHA256(),
					label=None
					)
				)

def AES_create_key():
	"""
	Genera una llave AES.

	@return Una llave AES en base 64
	"""
	key = AESGCM.generate_key(bit_length=256)
	key64 = base64.b64encode(key).decode()
	return key64

def AES_encrypt(key64, data):
	"""
	Cifra información con una llave AES en base 64.

	@param key64 La llave AES en base 64
	@param data La información a cifrar
	@return El nonce asociado y la información cifrada, todo en base 64
	"""
	key = base64.b64decode(key64.encode())
	aesgcm = AESGCM(key)
	nonce = os.urandom(12)
	body = aesgcm.encrypt(nonce, data.encode(), None)
	nonce64 = base64.b64encode(nonce).decode()
	body64 = base64.b64encode(body).decode()
	return nonce64, body64

def AES_decrypt(key64, nonce64, body64):
	"""
	Decifra información con AES.

	@param key64 La llave AES en base 64
	@param nonce64 El nonce asociado en base 64
	@param body64 La información cifrada en base 64
	@return La información decifrada
	"""
	key = base64.b64decode(key64.encode())
	aesgcm = AESGCM(key)
	nonce = base64.b64decode(nonce64.encode())
	body = base64.b64decode(body64.encode())
	data = aesgcm.decrypt(nonce, body, None)
	return data.decode()
