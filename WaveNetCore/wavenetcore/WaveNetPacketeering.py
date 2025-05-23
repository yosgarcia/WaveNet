import json
import base64
from datetime import datetime, timezone
from wavenetcore.WaveNetCrypto import *
import logging

class Packet:
	params = (
			("src", int),
			("dest", int),
			("mtype", str),
			("body", str),
			("timestamp", str),
		)

	def __init__(self, src, dest, mtype, body, timestamp=None):
		self.src = src
		self.dest = dest
		self.mtype = mtype
		self.body = body
		self.timestamp = timestamp if timestamp is not None else datetime.now(timezone.utc).isoformat()
	
	def form(self):
		return json.dumps({
			"enc" : False,
			"src" : self.src,
			"dest" : self.dest,
			"mtype" : self.mtype,
			"body" : self.body,
			"timestamp" : self.timestamp
			})
	
	def null(message):
		return Packet(-1, -1, "error", message)

	def is_null(self):
		return self.mtype == "error"

	def __str__(self):
		return self.form()

	def __hash__(self):
		return hash(str(self))

	def __eq__(self, other):
		if type(other) != type(self): return False
		return self.form() == other.form()


class SecretPacket:
	params = (
			("meta", str),
			("body", str),
		)

	def __init__(self, meta, body):
		self.meta = meta
		self.body = body

	def form(self):
		return json.dumps({
			"enc" : True,
			"meta" : self.meta,
			"body" : self.body
			})

	def __str__(self):
		return self.form()

	def __hash__(self):
		return hash(str(self))

	def __eq__(self, other):
		if type(other) != type(self): return False
		return self.form() == other.form()

def verify_tag(parsed, name, etype):
	if name not in parsed: return False, f"Missing {name} tag"
	v = parsed[name]
	if type(v) != etype: return False, f"Bad {name} tag"
	return True, v

def reconstruct_packet(data):
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
		logging.warning("Received a bad data")
		return Packet.null("Formation Error " + str(e))


def encrypt_packet(packet, public_key):
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

