#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FileDownloader.py

Cliente de búsqueda y descarga de archivos en WaveNET (Capa 4), adaptado para usar MedioFisicoChannel.

Funciones principales:
- query_file: envía QUERY_FILE al Hub y devuelve lista de node_id.
- download_file: conecta al FileServer de un nodo, solicita el archivo
  por nombre y reconstruye localmente recibiendo FILE_CHUNK.
"""

import os
import struct
import argparse
from typing import List, Tuple

from protocol import Packet, MessageType
from MedioFisicoChannel import MedioFisicoChannel


def query_file(hub_addr: Tuple[str, int], filename: str) -> List[str]:
    """
    Envía QUERY_FILE al FileHub y devuelve la lista de node_id separados por comas.
    """
    pkt = Packet(MessageType.QUERY_FILE, filename.encode())
    chan = MedioFisicoChannel()
    chan.connect(hub_addr)
    chan.send(pkt.to_bytes())
    data = chan.recv(4096)
    chan.close()

    resp = Packet.from_bytes(data)
    if resp.msg_type != MessageType.FILE_OFFER:
        raise RuntimeError(f"Respuesta inesperada del Hub: {resp.msg_type}")
    payload = resp.payload.decode()
    return payload.split(',') if payload else []


def download_file(node_addr: Tuple[str, int],
                  filename: str,
                  output_dir: str) -> None:
    """
    Se conecta al FileServer en node_addr, solicita 'filename' y
    escribe los chunks recibidos en output_dir/filename.
    """
    chan = MedioFisicoChannel()
    chan.connect(node_addr)
    # 1) Enviar nombre de archivo (línea terminada en '\n')
    chan.send(filename.encode() + b'\n')

    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, filename)
    with open(out_path, 'wb') as f_out:
        while True:
            # Leer header completo
            header = chan.recv(Packet.HEADER_SIZE)
            if not header:
                raise RuntimeError("Conexión cerrada inesperadamente")
            msg_val, payload_len = struct.unpack(
                Packet.HEADER_FORMAT,
                header
            )
            # Leer payload exacto
            payload = b''
            while len(payload) < payload_len:
                payload += chan.recv(payload_len - len(payload))
            msg_type = MessageType(msg_val)

            if msg_type == MessageType.FILE_CHUNK:
                f_out.write(payload)
            elif msg_type == MessageType.TRANSFER_COMPLETE:
                print(f"[Downloader] Transferencia completa: {filename}")
                break
            else:
                print(f"[Downloader] Mensaje inesperado: {msg_type}")
    chan.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Cliente para buscar y descargar archivos en WaveNET"
    )
    parser.add_argument('--file', '-f', required=True,
                        help='Nombre del archivo a descargar')
    parser.add_argument('--hub-host', default='127.0.0.1',
                        help='IP del File Hub (por defecto 127.0.0.1)')
    parser.add_argument('--hub-port', type=int, default=9000,
                        help='Puerto del File Hub (por defecto 9000)')
    parser.add_argument('--server-port', type=int, default=9001,
                        help='Puerto del FileServer en los nodos (por defecto 9001)')
    parser.add_argument('--output', '-o', default='./downloads',
                        help='Directorio donde guardar el archivo descargado')
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    hub_addr = (args.hub_host, args.hub_port)

    nodes = query_file(hub_addr, args.file)
    if not nodes or nodes == ['']:
        print(f"[Downloader] El archivo '{args.file}' no está registrado en el Hub.")
        return

    node = nodes[0]
    node_addr = (node, args.server_port)
    print(f"[Downloader] Descargando '{args.file}' desde nodo {node_addr}")
    try:
        download_file(node_addr, args.file, args.output)
    except Exception as e:
        print(f"[Downloader][Error] {e}")


if __name__ == '__main__':
    main()