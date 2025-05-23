from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os
import json
import base64

class PublicKey:
	def __init__(self, pem=None, public_key=None):
		assert (pem is None)^(public_key is None)
		if pem is not None:
			self.public_key = serialization.load_pem_public_key(pem)
		if public_key is not None:
			self.public_key = public_key
	
	def __str__(self):
		return self.public_key.public_bytes(
				encoding=serialization.Encoding.PEM,
				format=serialization.PublicFormat.SubjectPublicKeyInfo
				).decode()

	def encrypt(self, data):
		return self.public_key.encrypt(
				data,
				padding.OAEP(
					mgf=padding.MGF1(algorithm=hashes.SHA256()),
					algorithm=hashes.SHA256(),
					label=None
					)
				)

class PrivateKey:
	def __init__(self):
		self.private_key = rsa.generate_private_key(65537, 2048)

	def public_key(self):
		return PublicKey(public_key=self.private_key.public_key())

	def decrypt(self, data):
		return self.private_key.decrypt(
				data,
				padding.OAEP(
					mgf=padding.MGF1(algorithm=hashes.SHA256()),
					algorithm=hashes.SHA256(),
					label=None
					)
				)

def AES_create_key():
	key = AESGCM.generate_key(bit_length=256)
	key64 = base64.b64encode(key).decode()
	return key64

def AES_encrypt(key64, data):
	key = base64.b64decode(key64.encode())
	aesgcm = AESGCM(key)
	nonce = os.urandom(12)
	body = aesgcm.encrypt(nonce, data.encode(), None)
	nonce64 = base64.b64encode(nonce).decode()
	body64 = base64.b64encode(body).decode()
	return nonce64, body64

def AES_decrypt(key64, nonce64, body64):
	key = base64.b64decode(key64.encode())
	aesgcm = AESGCM(key)
	nonce = base64.b64decode(nonce64.encode())
	body = base64.b64decode(body64.encode())
	data = aesgcm.decrypt(nonce, body, None)
	return data.decode()
