#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FileServer.py

Servidor de transferencia de archivos para WaveNET (Capa 4).
Atiende peticiones entrantes y envía FILE_CHUNK + TRANSFER_COMPLETE.
"""

import os
import threading
import argparse
from typing import Tuple

from protocol import Packet, MessageType
from MedioFisicoChannel import MedioFisicoChannel

CHUNK_SIZE = 107  # Bytes máximos de payload por Packet

class FileServer:
    """
    Servidor que comparte los archivos de shared_dir.
    Cada conexión recibe un filename y luego se envían trozos.
    """
    def __init__(self, shared_dir: str, host: str = '0.0.0.0', port: int = 9001) -> None:
        self.shared_dir = shared_dir
        self.address: Tuple[str, int] = (host, port)

    def start(self) -> None:
        """Inicia el canal físico y acepta conexiones concurrentes."""
        canal = MedioFisicoChannel()
        canal.bind_and_listen(self.address)
        print(f"[Server] Escuchando en {self.address[0]}:{self.address[1]}")
        while True:
            conn, addr = canal.accept()
            threading.Thread(
                target=self.handle_client,
                args=(conn, addr),
                daemon=True
            ).start()

    def handle_client(self, conn: MedioFisicoChannel, addr: Tuple[str, int]) -> None:
        """
        Tras recibir el nombre de archivo (bytes UTF-8), envía FILE_CHUNK y luego TRANSFER_COMPLETE.
        """
        try:
            # 1. Leer nombre de archivo
            raw = conn.recv(1024)
            filename = raw.decode().strip()
            filepath = os.path.join(self.shared_dir, filename)
            print(f"[Server] Petición de '{filename}' desde {addr}")
            # 2. Verificar existencia
            if not os.path.isfile(filepath):
                print(f"[Server][Error] Archivo no encontrado: {filepath}")
                conn.close()
                return
            # 3. Enviar trozos
            with open(filepath, 'rb') as f:
                while True:
                    chunk = f.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    pkt = Packet(MessageType.FILE_CHUNK, chunk)
                    conn.send(pkt.to_bytes())
            # 4. Indicar fin de transferencia
            end_pkt = Packet(MessageType.TRANSFER_COMPLETE, b'')
            conn.send(end_pkt.to_bytes())
            print(f"[Server] Transferencia completa de '{filename}' a {addr}")
        except Exception as e:
            print(f"[Server][Error] {e} al atender {addr}")
        finally:
            conn.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inicia el File Server de WaveNET"
    )
    parser.add_argument(
        '--dir', '-d',
        required=True,
        help='Directorio de archivos a compartir'
    )
    parser.add_argument(
        '--host', '-H',
        default='0.0.0.0',
        help='IP donde escuchar (por defecto 0.0.0.0)'
    )
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=9001,
        help='Puerto TCP donde escuchar (por defecto 9001)'
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    server = FileServer(shared_dir=args.dir, host=args.host, port=args.port)
    try:
        server.start()
    except KeyboardInterrupt:
        print("\n[Server] Detenido por usuario.")
    except Exception as e:
        print(f"[Server][Fatal] {e}")

if __name__ == '__main__':
    main()
