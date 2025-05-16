#!/usr/bin/env python3
"""
protocol.py

Define los tipos de mensaje de Capa 4 y la serialización/deserialización
de los packets de intercambio de archivos en WaveNET.
"""

from enum import Enum
import struct

class MessageType(Enum):
    """Tipos de mensaje de Capa 4."""
    REGISTER_FILE       = 1  # Nodo anuncia un archivo disponible
    QUERY_FILE          = 2  # Cliente solicita disponibilidad de un archivo
    FILE_OFFER          = 3  # Hub responde con lista de nodos que tienen el archivo
    FILE_CHUNK          = 4  # Fragmento de archivo (payload ≤ 107 bytes)
    TRANSFER_COMPLETE   = 5  # Indica fin de la transferencia

class Packet:
    """
    Packet de Capa 4 para WaveNET.
    Estructura de header:
      - msg_type:     1 byte  (MessageType.value)
      - payload_len:  2 bytes (unsigned short, big-endian)
    payload: bytes de longitud variable.
    """
    HEADER_FORMAT = '!BH'  # B=unsigned char, H=unsigned short
    HEADER_SIZE   = struct.calcsize(HEADER_FORMAT)

    def __init__(self, msg_type: MessageType, payload: bytes):
        self.msg_type = msg_type
        self.payload  = payload

    def to_bytes(self) -> bytes:
        """Serializa el Packet a bytes (header + payload)."""
        header = struct.pack(self.HEADER_FORMAT,
                             self.msg_type.value,
                             len(self.payload))
        return header + self.payload

    @classmethod
    def from_bytes(cls, data: bytes) -> 'Packet':
        """
        Deserializa un array de bytes en un Packet.
        Asume que `data` contiene al menos HEADER_SIZE + payload_len bytes.
        """
        # Extraer tipo de mensaje y longitud de payload
        msg_val, payload_len = struct.unpack(
            cls.HEADER_FORMAT,
            data[:cls.HEADER_SIZE]
        )
        # Extraer payload según la longitud indicada
        payload = data[cls.HEADER_SIZE : cls.HEADER_SIZE + payload_len]
        msg_type = MessageType(msg_val)
        return cls(msg_type=msg_type, payload=payload)
