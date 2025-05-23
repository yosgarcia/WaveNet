import pytest
import json
import base64
import wavenetcore.WaveNetPacketeering as pkt
import wavenetcore.WaveNetCrypto as crypto
from datetime import datetime, timezone
import time

def test_packet_equality():
	date1 = datetime.now(timezone.utc).isoformat()
	time.sleep(0.5)
	date2 = datetime.now(timezone.utc).isoformat()
	A1 = pkt.Packet(1, 2, "ping", "Hello atcoder", date1)
	A2 = pkt.Packet(1, 2, "ping", "Hello atcoder", date1)
	A3 = pkt.Packet(1, 2, "ping", "Bye atcoder", date1)
	A4 = pkt.Packet(1, 2, "waka", "Hello atcoder", date1)
	A5 = pkt.Packet(1, 3, "ping", "Hello atcoder", date1)
	A6 = pkt.Packet(5, 2, "ping", "Hello atcoder", date1)
	A7 = pkt.Packet(1, 2, "ping", "Hello atcoder", date2)
	B1 = pkt.SecretPacket("unga bunga bro", "duga buga lala")
	B2 = pkt.SecretPacket("unga bunga bro", "duga buga lala")
	B3 = pkt.SecretPacket("unga bunga bro", "NOT duga buga lala")
	B4 = pkt.SecretPacket("unga bunga shorty", "duga buga lala")

	assert A1 == A2
	assert A1 != A3
	assert A1 != A4
	assert A1 != A5
	assert A1 != A6
	assert A1 != A7

	assert B1 == B2
	assert B1 != B3
	assert B1 != B4

def test_normal_packet_roundtrip():
	original = pkt.Packet(1, 2, "ping", "Hello atcoder")
	data = original.form()
	reconstructed = pkt.reconstruct_packet(data)

	assert original == reconstructed

def test_secret_packet_roundtrip():
	sp = pkt.SecretPacket("unga bunga bro", "duga buga lala")
	data = sp.form()
	reconstructed = pkt.reconstruct_packet(data)

	assert sp == reconstructed

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

	assert isinstance(secret, pkt.SecretPacket)
	data = secret.form()
	secret = pkt.reconstruct_packet(data)

	decrypted = pkt.decrypt_packet(secret, priv)

	assert original == decrypted

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

	assert decrypted == corrupted_packet 
