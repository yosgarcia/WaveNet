#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FileHub.py

Módulo principal para el File Hub de WaveNET (Capa 4).
Recibe registros de archivos desde nodos y responde consultas
con la lista de nodos que disponen de cada archivo.
"""

import threading
import argparse
from typing import Dict, Set, Tuple
from protocol import Packet, MessageType
from MedioFisicoChannel import MedioFisicoChannel

class FileHub:
    """
    Servidor centralizado que gestiona registros y consultas de archivos.
    index: Dict[str, Set[str]]  → mapea filename a conjunto de node_id
    lock: threading.Lock        → protege el acceso concurrente a index
    """
    def __init__(self, host: str = '0.0.0.0', port: int = 9000) -> None:
        self.address: Tuple[str, int] = (host, port)
        self.index: Dict[str, Set[str]] = {}
        self.lock: threading.Lock = threading.Lock()

    def start(self) -> None:
        """Inicia el canal físico y acepta conexiones entrantes."""
        canal = MedioFisicoChannel()
        canal.bind_and_listen(self.address)
        print(f"[Hub] Escuchando en {self.address[0]}:{self.address[1]}")
        while True:
            conn, addr = canal.accept()
            threading.Thread(
                target=self.handle_client,
                args=(conn, addr),
                daemon=True
            ).start()

    def handle_client(self, conn: MedioFisicoChannel, addr: Tuple[str, int]) -> None:
        """
        Procesa un único mensaje desde un cliente.
        Espera un único Packet por conexión, luego cierra el canal.
        """
        try:
            data = conn.recv(4096)
            packet = Packet.from_bytes(data)
        except Exception as e:
            print(f"[Hub][Error] al leer paquete de {addr}: {e}")
            conn.close()
            return

        # Registro de archivo
        if packet.msg_type == MessageType.REGISTER_FILE:
            filename, node_id = packet.payload.decode().split('|', 1)
            with self.lock:
                node_set = self.index.setdefault(filename, set())
                node_set.add(node_id)
            print(f"[Hub] Registro: '{filename}' desde nodo '{node_id}'")
            # Imprimir estado completo del índice
            print("[Hub] Estado actual del índice:")
            for fname, nodes in self.index.items():
                print(f"  Archivo: '{fname}' → Nodos: {sorted(nodes)}")

        # Consulta de archivo
        elif packet.msg_type == MessageType.QUERY_FILE:
            filename = packet.payload.decode()
            with self.lock:
                nodes = self.index.get(filename, set())
            offer_payload = ','.join(nodes).encode()
            response = Packet(MessageType.FILE_OFFER, offer_payload)
            try:
                conn.send(response.to_bytes())
                print(f"[Hub] Consulta: '{filename}' → nodos {nodes}")
            except Exception as e:
                print(f"[Hub][Error] al enviar oferta a {addr}: {e}")

        else:
            print(f"[Hub] Ignorado msg_type={packet.msg_type} de {addr}")

        conn.close()


def parse_args() -> argparse.Namespace:
    """Parsea argumentos de línea de comando para host y puerto."""
    parser = argparse.ArgumentParser(description="Inicia el File Hub de WaveNET")
    parser.add_argument(
        '--host', '-H',
        default='0.0.0.0',
        help='IP donde escuchar (por defecto 0.0.0.0)'
    )
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=9000,
        help='Puerto TCP donde escuchar (por defecto 9000)'
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    hub = FileHub(host=args.host, port=args.port)
    try:
        hub.start()
    except KeyboardInterrupt:
        print("\n[Hub] Detenido por usuario.")
    except Exception as e:
        print(f"[Hub][Fatal] {e}")

if __name__ == '__main__':
    main()
