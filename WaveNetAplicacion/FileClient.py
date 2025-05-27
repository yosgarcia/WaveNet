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
import argparse

from Service import send_message, receive_message, receive_file
from NodeManager import NodeManager


def main():
    parser = argparse.ArgumentParser(
        description="FileClient: solicita y descarga un archivo de WaveNet"
    )
    parser.add_argument(
        '--hub-id', '-H',
        type=int, required=True,
        help='ID del nodo FileHub'
    )
    parser.add_argument(
        '--filename', '-f',
        required=True,
        help='Nombre del archivo a descargar'
    )
    parser.add_argument(
        '--out-dir', '-o',
        default='downloads',
        help='Directorio donde guardar el archivo'
    )
    parser.add_argument(
        '--port', '-p',
        type=int, default=None,
        help='Puerto local para el nodo mesh (evitar choques)'
    )
    parser.add_argument(
        '--node-id', '-n',
        type=int, default=None,
        help='ID numérico para este nodo mesh (opcional)'
    )
    args = parser.parse_args()

    # Ajustar puerto de escucha si se indicó
    if args.port:
        NodeManager.DEFAULT_PORT = args.port

    # Inicializar nodo mesh
    node = NodeManager.get_node(ID=args.node_id)
    print(f"[FileClient] Nodo mesh iniciado con ID={node.my_id()} en puerto {NodeManager.DEFAULT_PORT}")

    # 1) Preguntar al FileHub quién tiene el archivo
    print(f"[FileClient] Solicitando file_query a hub {args.hub_id} para '{args.filename}'...")
    send_message(
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
            from_id, msg = receive_message()
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
        dest_id=owner,
        msg_type="REQUEST",
        resource="file_transfer_init",
        body={"filename": args.filename}
    )

    # 4) Recibir fichero completo y guardarlo
    try:
        saved_path = receive_file(args.out_dir)
        print(f"[FileClient] Descarga completa. Guardado en: {saved_path}")
    except Exception as e:
        print(f"[FileClient][Error] al recibir fichero: {e}")

if __name__ == "__main__":
    main()
