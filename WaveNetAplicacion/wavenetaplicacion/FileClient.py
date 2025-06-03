#!/usr/bin/env python3
"""
WaveNetAplicacion/FileClient.py

Cliente que solicita un fichero:
1) Pregunta al FileHub qué nodos lo tienen (file_query).
2) Solicita la transferencia al primer owner (file_transfer_init).
3) Recibe y guarda el fichero.
"""
import os
import time

from wavenetaplicacion.Service import send_message, receive_message, receive_file
from wavenetaplicacion.GeneralParser import WaveNetParser

def main():
	parser = WaveNetParser("FileClient: solicita y descarga un archivo de WaveNet")

	parser.get_parser().add_argument(
		'--filename', '-f',
		required=True,
		help='Nombre del archivo a descargar'
	)
	parser.get_parser().add_argument(
		'--out-dir', '-o',
		default='downloads',
		help='Directorio donde guardar el archivo'
	)

	parser.get_parser().add_argument(
		'--hub-id', '-H',
		type=int, required=True,
		help='ID del nodo FileHub'
	)

	parser.parse()

	args = parser.get_args()

	# Inicializar nodo mesh
	node = parser.get_node()
	print(f"[FileClient] Nodo mesh iniciado con ID={node.my_id()}")

	# 1) Preguntar al FileHub quién tiene el archivo
	print(f"[FileClient] Solicitando file_query a hub {args.hub_id} para '{args.filename}'...")
	send_message(
		node=node,
		dest_id=args.hub_id,
		msg_type="REQUEST",
		resource="file_query",
		body={"filename": args.filename}
	)

	# 2) Esperar RESPONSE con file_query_response
	owners = []
	start = time.time()
	timeout = 5.0
	while True:
		if time.time() - start > timeout:
			print(f"[FileClient] Timeout esperando respuesta de file_query_response")
			return
		try:
			from_id, msg = receive_message(node)
		except Exception as e:
			# ignorar timeouts internos del mesh
			if 'Timeout' in str(e):
				continue
			print(f"[FileClient][Error] al recibir respuesta: {e}")
			return
		if from_id == args.hub_id and msg.get('type') == 'RESPONSE' and msg.get('resource') == 'file_query_response':
			owners = msg.get('body', {}).get('nodes', [])
			break

	if not owners:
		print(f"[FileClient] Ningún nodo ofrece '{args.filename}'. Abortando.")
		return

	owner = owners[0]
	print(f"[FileClient] Empezando descarga desde nodo {owner}...")

	# 3) Solicitar transferencia al owner
	send_message(
		node=node,
		dest_id=owner,
		msg_type="REQUEST",
		resource="file_transfer_init",
		body={"filename": args.filename}
	)

	# 4) Recibir fichero completo y guardarlo
	try:
		saved_path = receive_file(node, args.out_dir)
		print(f"[FileClient] Descarga completa. Guardado en: {saved_path}")
	except Exception as e:
		print(f"[FileClient][Error] al recibir fichero: {e}")

# python3 FileClient.py --verbose --localp 9003 -n 3 --localc 0,9000 --hub-id 1 --out-dir ./descargas -f unga_bunga.md
if __name__ == "__main__":
	main()
