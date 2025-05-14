from enum import Enum
import json
from threading import Thread, Lock
from datetime import datetime, timezone
import socket
from WaveNetCrypto import *

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
			"type" : self.mtype,
			"body" : self.body,
			"timestamp" : self.timestamp
			})
	
	def null(message):
		return Packet(-1, -1, "error", message)

	def is_null(self):
		return self.mtype == "error"
		

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
			}))
		return SecretPacket(meta, body64)
	except Exception as e:
		return Packet.null("Formation Error " + str(e))

def decrypt_packet(packet, private_key):
	try:
		parsed = json.loads(private_key.decrypt(packet.meta))
		status, dec = verify_tag(parsed, "decrypted", bool)
		if not status or not dec: return packet
		status, key64 = verify_tag(parsed, "key", str)
		if not status: return packet
		status, nonce64 = verify_tag(parsed, "nonce", str)
		if not status: return packet
		data = AES_decrypt(key64, nonce64, packet.body)
		return reconstruct_packet(data)
	except Exception as e:
		return packet

class ProtocolType(Enum):
	LOCAL = 1

class Protocol:
	def __init__(self, protocol_type, sender, listener):
		self.protocol_type = protocol_type
		self.sender = sender
		self.listener = listener

	def send(self, data, dest):
		self.sender(data, dest)

	def listen(self, func):
		t = Thread(target=self.listener, args=[func])
		t.run()
		return t

class LocalProtocol(Protocol):

	IP = "127.0.0.1"
	protocol_type = ProtocolType.LOCAL

	def __init__(self, port=None):
		self.port = port
		super().__init__(LocalProtocol.protocol_type, self.sender, self.listener)

	def sender(self, packet, dest):
		data = packet.form()

		PORT = int(dest)

		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
			s.connect((IP, PORT))
			s.sendall(data)

	def listener(self, func):
		assert(self.port is not None)

		PORT = self.port

		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
			s.bind((IP, PORT))
			s.listen()
			while True:
				conn, _ = s.accept()
				parts = []
				with conn:
					while True:
						data = conn.recv(1 << 12)
						if not data: break
						parts.append(data)
				data = b''.join(parts)
				packet = reconstruct_packet(data)
				func(packet)

class Link:
	def __init__(self, dest, protocol):
		self.protocol = protocol
		self.dest = dest
	
	def send(self, packet):
		self.protocol.send(packet, self.dest)
	
	def __str__(self):
		return "|" + self.protocol.protocol_type.name + "|" + self.dest

	def __hash__(self):
		return str(self)
	
	def __eq__(self, other):
		return str(self) == str(other)

