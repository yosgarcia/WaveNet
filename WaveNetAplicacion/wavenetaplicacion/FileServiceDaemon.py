"""
Servicio combinado: registra nuevos archivos y atiende descargas.
Se ejecuta con un solo nodo mesh (mismo ID).
"""
import os
import time
import threading
import argparse

from wavenetaplicacion.Service import send_message, receive_message, send_file
from wavenetaplicacion.NodeManager import NodeManager
from wavenetaplicacion.GeneralParser import WaveNetParser


def watch_and_register(node, hub_id: int, shared_dir: str, interval: float) -> None:
	"""
	Escanea shared_dir cada 'interval' segundos y registra archivos nuevos.
	"""
	seen = set()
	while True:
		try:
			current = {f for f in os.listdir(shared_dir)
					   if os.path.isfile(os.path.join(shared_dir, f))}
			new = current - seen
			if new:
				send_message(
					node=node,
					dest_id=hub_id,
					msg_type="DATA",
					resource="file_register",
					body={"files": list(new)}
				)
				print(f"[FileServiceDaemon] Registró archivos: {list(new)}")
				seen = current
			time.sleep(interval)
		except Exception as e:
			print(f"[FileServiceDaemon][Error register] {e}")
			time.sleep(interval)


def serve_requests(node, shared_dir: str) -> None:
	"""
	Atiende peticiones de transferencia y envía chunks.
	"""
	while True:
		try:
			from_id, msg = receive_message(node)
		except Exception as e:
			if 'Timeout' in str(e):
				continue
			print(f"[FileServiceDaemon][Error receive] {e}")
			continue

		if msg.get("type") == "REQUEST" and msg.get("resource") == "file_transfer_init":
			filename = msg.get("body", {}).get("filename")
			filepath = os.path.join(shared_dir, filename)
			print(f"[FileServiceDaemon] Petición de '{filename}' desde nodo {from_id}")
			try:
				send_file(node, from_id, filepath)
				print(f"[FileServiceDaemon] Envío de '{filename}' completado.")
			except Exception as e:
				print(f"[FileServiceDaemon][Error send_file] {e}")


def main() -> None:
	parser = WaveNetParser("Daemon: registro y servicio de archivos en WaveNet")
	parser.get_parser().add_argument(
		'--hub-id', '-H', type=int, required=True,
		help='ID del nodo FileHub'
	)
	parser.get_parser().add_argument(
		'--dir', '-d', required=True,
		help='Directorio compartido'
	)
	parser.get_parser().add_argument(
		'--interval', '-t', type=float, default=5.0,
		help='Segs. entre escaneos'
	)

	parser.parse()

	args = parser.get_args()

	# Inicializar el nodo mesh (mismo ID de nodo-hub si ya registrado)
	node = parser.get_node()
	print(f"[FileServiceDaemon] Nodo mesh ID={node.my_id()}")

	# Hilo de registro de archivos
	reg_thread = threading.Thread(
		target=watch_and_register,
		args=(node, args.hub_id, args.dir, args.interval,),
		daemon=True
	)
	reg_thread.start()

	# Hilo de atención a peticiones
	srv_thread = threading.Thread(
		target=serve_requests,
		args=(node, args.dir,),
		daemon=True
	)
	srv_thread.start()

	print("[FileServiceDaemon] Corriendo... Ctrl+C para detener")
	try:
		while True:
			time.sleep(1)
	except KeyboardInterrupt:
		print("[FileServiceDaemon] Parando...")
		NodeManager.shutdown()

# python3 FileServiceDaemon.py --verbose --localp 9002 --localc 1,9001 -n 2 --hub-id 1 --dir ./carpeta_compartida
if __name__ == '__main__':
	main()
