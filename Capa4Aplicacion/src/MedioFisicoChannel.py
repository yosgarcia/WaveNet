#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedioFisicoChannel.py

Define la interfaz de canal de bytes y su implementación actual sobre sockets.
En el futuro, reemplazaremos aquí por audio + framing + corrección de errores.
"""

import socket
from typing import Tuple, Optional

class MedioFisicoChannel:
    """
    Canal de bytes genérico. API:
      - connect(addr)        : abre conexión
      - bind_and_listen(addr): inicia escucha
      - accept()             : acepta conexión entrante -> (canal, addr)
      - send(data)           : envía bytes
      - recv(n)              : recibe hasta n bytes
      - close()              : cierra el canal
    """

    def __init__(self) -> None:
        self._sock: Optional[socket.socket] = None

    def connect(self, addr: Tuple[str, int]) -> None:
        """Crea y conecta el socket al addr dado."""
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.connect(addr)

    def bind_and_listen(self, addr: Tuple[str, int]) -> None:
        """Crea un socket, lo vincula a addr y comienza a escuchar."""
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.bind(addr)
        self._sock.listen()

    def accept(self) -> Tuple["MedioFisicoChannel", Tuple[str, int]]:
        """Acepta una conexión entrante y devuelve un nuevo canal y la dirección."""
        assert self._sock is not None, "El socket no está inicializado. Llama a bind_and_listen primero."
        conn, addr = self._sock.accept()
        canal = MedioFisicoChannel()
        canal._sock = conn
        return canal, addr

    def send(self, data: bytes) -> None:
        """Envía todos los bytes proporcionados a través del canal."""
        assert self._sock is not None, "El canal no está conectado. Llama a connect o accept primero."
        self._sock.sendall(data)

    def recv(self, n: int) -> bytes:
        """Recibe hasta n bytes del canal."""
        assert self._sock is not None, "El canal no está conectado. Llama a connect o accept primero."
        return self._sock.recv(n)

    def close(self) -> None:
        """Cierra el socket interno, si existe."""
        if self._sock:
            self._sock.close()
            self._sock = None
