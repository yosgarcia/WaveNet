#!/usr/bin/env python3
"""
WaveNetAplicacion/FileHub.py

Nodo FileHub de Capa 4: mantiene un catálogo de archivos registrados
por nodos y responde consultas sobre qué nodos tienen un archivo.
"""
import threading
import time
from typing import Dict, Set, List

from wavenetaplicacion.Service import receive_message, send_message
from wavenetaplicacion.NodeManager import NodeManager
from wavenetaplicacion.GeneralParser import WaveNetParser


class FileHub:
	"""
	Nodo centralizado que gestiona registros y consultas de archivos.
	_registry: Dict[str, Set[int]] mapea filename a conjunto de node IDs.
	"""

	def __init__(self, node) -> None:
		self._registry: Dict[str, Set[int]] = {}
		self._running = False
		self._thread: threading.Thread = None  # type: ignore
		self.node = node

	def start(self) -> None:
		"""
		Inicializa el nodo mesh y arranca el loop de escucha.
		"""
		print(f"[FileHub] Nodo mesh iniciado con ID={(self.node.my_id())}")

		self._running = True
		self._thread = threading.Thread(target=self._run_loop, daemon=True)
		self._thread.start()

	def stop(self) -> None:
		"""
		Detiene el loop de escucha y apaga el nodo mesh.
		"""
		self._running = False
		if self._thread:
			self._thread.join(timeout=1.0)

	def _run_loop(self) -> None:
		"""
		Bucle que recibe mensajes via receive_message() y procesa:
		- DATA/file_register
		- REQUEST/file_query
		"""
		while self._running:
			try:
				from_id, msg = receive_message(self.node)
			except Exception:
				time.sleep(0.1)
				continue

			mtype = msg.get('type')
			resource = msg.get('resource')
			body = msg.get('body', {})

			if mtype == 'DATA' and resource == 'file_register':
				files: List[str] = body.get('files', [])
				for fname in files:
					self._registry.setdefault(fname, set()).add(from_id)
				print(f"[FileHub] Registro de nodo {from_id}: {files}")

				# 2Print: Mostrar todos los nodos y sus archivos
				from typing import Dict, Set
				node_files: Dict[int, Set[str]] = {}
				for archivo, nodos in self._registry.items():
					for nodo in nodos:
						if nodo not in node_files:
							node_files[nodo] = set()
						node_files[nodo].add(archivo)
				print("="*10)
				for nodo, archivos in node_files.items():
					print(f"Nodo {nodo}: {sorted(list(archivos))}")
				print("="*10)

			elif mtype == 'REQUEST' and resource == 'file_query':
				filename: str = body.get('filename')
				owners = list(self._registry.get(filename, set()))
				print(f"[FileHub] Consulta '{filename}' de nodo {from_id} -> owners: {owners}")
				send_message(
					node=self.node,
					dest_id=from_id,
					msg_type='RESPONSE',
					resource='file_query_response',
					body={'nodes': owners}
				)
			elif mtype == 'REQUEST' and resource == 'list_files':
			   files = sorted(self._registry.keys())
			   send_message(
				node=self.node,
				dest_id=from_id,
				msg_type='RESPONSE',
				resource='list_files_response',
				body={'files': files}
			   )

	def lookup(self, filename: str) -> List[int]:
		"""
		Consulta local del catálogo.
		"""
		return list(self._registry.get(filename, []))


# python3 FileHub.py --verbose --localp 9001 --localc 0,9000 -n 1
if __name__ == '__main__':
	parser = WaveNetParser("FileHub: Crea un file hub")
	parser.parse()

	hub = FileHub(parser.get_node())
	hub.start()
	print('[FileHub] Ejecutando. Ctrl+C para detener...')
	try:
		while True:
			time.sleep(1)
	except KeyboardInterrupt:
		print('\n[FileHub] Parando...')
		NodeManager.shutdown()  # Asegura que el nodo mesh se apague correctamente
		hub.stop()
