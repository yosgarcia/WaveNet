import pytest
import json
import base64
from WaveNetCore import WaveNetPacketeering as pkt
from WaveNetCore import WaveNetCrypto as crypto

def test_normal_packet_roundtrip():
	original = pkt.Packet(1, 2, "ping", "Hello atcoder")
	data = original.form()
	reconstructed = pkt.reconstruct_packet(data)
	print(data)
	print(reconstructed)

	assert isinstance(reconstructed, pkt.Packet)
	assert reconstructed.src == original.src
	assert reconstructed.dest == original.dest
	assert reconstructed.mtype == original.mtype
	assert reconstructed.body == original.body
	assert reconstructed.timestamp == original.timestamp

def test_secret_packet_roundtrip():
	sp = pkt.SecretPacket("unga bunga bro", "duga buga lala")
	data = sp.form()
	reconstructed = pkt.reconstruct_packet(data)

	assert isinstance(reconstructed, pkt.SecretPacket)
	assert reconstructed.meta == sp.meta
	assert reconstructed.body == sp.body

def test_reconstruct_bad_data_returns_null():
	p = pkt.reconstruct_packet("I want a fish that does not taste like json")
	assert p.is_null()
	assert p.body.startswith("Formation Error")

	bad_json = json.dumps({"enc": False, "src": 1})
	p2 = pkt.reconstruct_packet(bad_json)
	assert p2.is_null()
	assert "Missing" in p2.body

def test_packet_encrypt_decrypt_cycle():
	priv = crypto.PrivateKey()
	pub = priv.public_key()

	original = pkt.Packet(10, 20, "data", "Secure data hmmmjmjmmmxmmm")
	secret = pkt.encrypt_packet(original, pub)

	print(secret)
	assert isinstance(secret, pkt.SecretPacket)

	decrypted = pkt.decrypt_packet(secret, priv)

	assert isinstance(decrypted, pkt.Packet)
	assert decrypted.src == original.src
	assert decrypted.dest == original.dest
	assert decrypted.mtype == original.mtype
	assert decrypted.body == original.body
	assert decrypted.timestamp == original.timestamp

def test_corrupted_secret_packet_fails_gracefully():
	priv = crypto.PrivateKey()
	pub = priv.public_key()

	original = pkt.Packet(5, 6, "pong", "VERY VERY secret (but only at night)")
	secret = pkt.encrypt_packet(original, pub)

	corrupted_body = bytearray(secret.body.encode())
	if corrupted_body[0] == ord('a'): corrupted_body[0] = ord('b')
	else: corrupted_body[0] = ord('a')
	corrupted_body = corrupted_body.decode()

	corrupted_packet = pkt.SecretPacket(secret.meta, corrupted_body)
	decrypted = pkt.decrypt_packet(corrupted_packet, priv)

	assert isinstance(decrypted, pkt.SecretPacket)
	assert decrypted.meta == secret.meta
	assert decrypted.body == corrupted_body
