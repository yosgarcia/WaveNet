import os
import time
import base64
from typing import Any, Dict, Tuple, Generator

from wavenetaplicacion.Protocol import Protocol
from wavenetaplicacion.NodeManager import NodeManager

	
def send_message(node, dest_id: int, msg_type: str, resource: str, body: Any) -> None:
	msg = {"type": msg_type, "resource": resource, "body": body}
	raw = Protocol.encode(msg)
	node.send(dest=dest_id, message=raw)


def receive_message(node, src_id=None) -> Tuple[int, Dict[str, Any]]:
	from_id, raw = None, None
	if src_id is None: from_id, raw = node.listen()
	else: from_id, raw = node.recv(src_id)
	msg = Protocol.decode(raw)
	return from_id, msg


def send_and_wait_response(node, dest_id: int,
						   resource: str,
						   body: Any,
						   timeout: float = 50.0,
						   poll_interval: float = 0.1) -> Any:
	send_message(node, dest_id, "REQUEST", resource, body)
	start = time.time()
	while True:
		if time.time() - start > timeout:
			raise TimeoutError(f"No llegó RESPONSE para '{resource}' tras {timeout}s")
		from_id, msg = receive_message(node, src_id = dest_id)
		if msg.get("type") == "RESPONSE" and msg.get("resource") == resource:
			return msg.get("body")
		time.sleep(poll_interval)


def _read_in_chunks(filepath: str, chunk_size: int = 1024) -> Generator[bytes, None, None]:
	with open(filepath, 'rb') as f:
		while True:
			data = f.read(chunk_size)
			if not data:
				break
			yield data


def send_file(node, dest_id: int, filepath: str, chunk_size: int = 1024) -> None:
	filename = os.path.basename(filepath)
	print(f"[Service] Iniciando envío de '{filename}' a nodo {dest_id}")
	# init
	send_message(node, dest_id, "REQUEST", "file_transfer_init", {"filename": filename})
	time.sleep(0.01)
	# chunks
	for chunk in _read_in_chunks(filepath, chunk_size):
		print(f"[Service] Enviando chunk de {len(chunk)} bytes")
		b64 = base64.b64encode(chunk).decode('utf-8')
		send_message(node, dest_id, "DATA", "file_chunk", {"data": b64})
		time.sleep(0.1)
	# end
	print(f"[Service] Enviando señal de fin para '{filename}'")
	send_message(node, dest_id, "DATA", "file_end", {"filename": filename})


def receive_file(node, save_dir: str) -> str:
	print(f"[Service] Esperando inicio de transferencia...")
	# buscar init
	while True:
		from_id, msg = receive_message(node)
		if msg.get("type") == "REQUEST" and msg.get("resource") == "file_transfer_init":
			filename = msg["body"]["filename"]
			print(f"[Service] Transferencia iniciada para '{filename}' de nodo {from_id}")
			break
		# ignorar otros mensajes
	# recibir chunks
	chunks = []
	while True:
		from_id, msg = receive_message(node)
		if msg.get("type") == "DATA" and msg.get("resource") == "file_chunk":
			data = msg.get("body", {}).get("data")
			raw = base64.b64decode(data)
			print(f"[Service] Recibido chunk de {len(raw)} bytes")
			chunks.append(raw)
		elif msg.get("type") == "DATA" and msg.get("resource") == "file_end":
			print(f"[Service] Recibida señal de fin para '{filename}'")
			break
		# ignorar mensajería no relacionada
	os.makedirs(save_dir, exist_ok=True)
	out_path = os.path.join(save_dir, filename)
	print(f"[Service] Ensamblando y guardando en '{out_path}'")
	with open(out_path, 'wb') as f:
		for c in chunks:
			f.write(c)
	return out_path
