from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes

class PublicKey:
	def __init__(self, pem=None, public_key=None):
		assert((pem is None)^(public_key is None))
		if pem is not None:
			self.public_key = serialization.load_pem_public_key(pem)
		if public_key is not None:
			self.public_key = public_key
	
	def __str__(self):
		return public_key.public_bytes(
				encoding=serialization.Encoding.PEM,
				format=serialization.PublicFormat.SubjectPublicKeyInfo
				)

	def encrypt(self, data):
		return public_key.encrypt(
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
		return private_key.decrypt(
				data,
				padding.OAEP(
					mgf=padding.MGF1(algorithm=hashes.SHA256()),
					algorithm=hashes.SHA256(),
					label=None
					)
				)
