import pytest
from WaveNetCore import WaveNetCrypto as crypto

def test_aes_encryption_decryption():
	key = crypto.AES_create_key()
	original_data = "Do you even crypt, bro??"

	nonce64, ciphertext64 = crypto.AES_encrypt(key, original_data)
	decrypted_data = crypto.AES_decrypt(key, nonce64, ciphertext64)

	assert decrypted_data == original_data

def test_rsa_encryption_decryption():
	priv = crypto.PrivateKey()
	pub = priv.public_key()

	message = b"bro...??"
	encrypted = pub.encrypt(message)
	decrypted = priv.decrypt(encrypted)

	assert decrypted == message

def test_rsa_export_import_pem():
	priv = crypto.PrivateKey()
	pub = priv.public_key()

	pem = str(pub).encode()
	pub2 = crypto.PublicKey(pem=pem)

	message = b"I think you might want to crypt that shi up bro"
	encrypted = pub2.encrypt(message)
	decrypted = priv.decrypt(encrypted)

	assert decrypted == message
