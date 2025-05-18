#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FileRegistrar.py

Cliente que registra archivos en el File Hub de WaveNET (Capa 4).
Al iniciar, recorre la carpeta de archivos compartidos y envía
REGISTER_FILE(filename|node_id) por cada archivo nuevo. Luego
vuelve a comprobar cada intervalo para detectar añadidos, usando
automáticamente la IP local como node_id.
"""

import os
import time
import argparse
from typing import Set, Tuple

from protocol import Packet, MessageType
from MedioFisicoChannel import MedioFisicoChannel

CHUNK_INTERVAL_DEFAULT = 5.0


def register_file(hub_addr: Tuple[str, int], filename: str, node_id: str) -> None:
    """
    Envía un paquete REGISTER_FILE al Hub con payload "filename|node_id".
    """
    payload = f"{filename}|{node_id}".encode()
    packet = Packet(MessageType.REGISTER_FILE, payload)
    chan = MedioFisicoChannel()
    chan.connect(hub_addr)
    chan.send(packet.to_bytes())
    chan.close()
    print(f"[Registrar] Enviado REGISTER_FILE para '{filename}' desde nodo '{node_id}'")


def watch_and_register(shared_dir: str,
                       hub_addr: Tuple[str, int],
                       node_id: str,
                       interval: float = CHUNK_INTERVAL_DEFAULT) -> None:
    """
    Escanea shared_dir cada interval segundos. Para todo archivo que
    no estuviera ya registrado, llama a register_file().
    """
    seen: Set[str] = set()
    while True:
        try:
            for entry in os.listdir(shared_dir):
                path = os.path.join(shared_dir, entry)
                if os.path.isfile(path) and entry not in seen:
                    register_file(hub_addr, entry, node_id)
                    seen.add(entry)
            time.sleep(interval)
        except Exception as e:
            print(f"[Registrar][Error] {e}")
            time.sleep(interval)


def parse_args() -> argparse.Namespace:
    """Parsea argumentos: directorio compartido, host/puerto del Hub y opcional interval."""
    parser = argparse.ArgumentParser(
        description="Cliente para registrar archivos en File Hub"
    )
    parser.add_argument(
        '--dir', '-d',
        required=True,
        help='Ruta al directorio de archivos compartidos'
    )
    parser.add_argument(
        '--host', '-H',
        default='127.0.0.1',
        help='IP del File Hub (por defecto 127.0.0.1)'
    )
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=9000,
        help='Puerto del File Hub (por defecto 9000)'
    )
    parser.add_argument(
        '--interval', '-t',
        type=float,
        default=CHUNK_INTERVAL_DEFAULT,
        help='Segundos entre escaneos de directorio (por defecto 5s)'
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        # Detectar automáticamente la IP local para usar como node_id
        import socket
        node_id = socket.gethostbyname(socket.gethostname())
    except Exception:
        node_id = 'unknown'
    hub_addr = (args.host, args.port)
    print(f"[Registrar] Observando '{args.dir}', registrando en {hub_addr} como nodo '{node_id}'")
    watch_and_register(args.dir, hub_addr, node_id, args.interval)


if __name__ == '__main__':
    main()