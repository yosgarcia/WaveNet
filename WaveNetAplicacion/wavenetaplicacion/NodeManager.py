# NodeManager.py

from typing import Optional
from wavenetcore.WaveNetAdaptors import WaveNetBasicMeshNode
from wavenetcore.WaveNetProtocols import LocalProtocol

class NodeManager:
    """
    Singleton para WaveNetBasicMeshNode en Capa 4.
    Arranca un nodo local y se conecta/join al mesh‐hub automáticamente.
    """

    _instance: Optional[WaveNetBasicMeshNode] = None
    DEFAULT_PORT: int = 8000
    HUB_PORT:    int = 9000

    @classmethod
    def get_node(cls, ID: int = None) -> WaveNetBasicMeshNode:
        """
        Devuelve la instancia única de WaveNetBasicMeshNode.
        Si no existe, la crea con el protocolo LocalProtocol en DEFAULT_PORT,
        opcionalmente usando el ID que se pase, la arranca, conecta al hub y hace join.
        """
        if cls._instance is None:
            # 1) Arrancar nodo local con ID opcional
            protocol = LocalProtocol(port=cls.DEFAULT_PORT)
            cls._instance = WaveNetBasicMeshNode([protocol], ID=ID)
            cls._instance.run()

            # 2) Conectar y join al mesh‐hub de capa 3
            hub_proto = LocalProtocol(port=cls.DEFAULT_PORT)
            cls._instance.connect(0, hub_proto, str(cls.HUB_PORT))
            cls._instance.join()

        return cls._instance

    @classmethod
    def shutdown(cls) -> None:
        """
        Detiene y elimina la instancia única del nodo.
        """
        if cls._instance is not None:
            cls._instance.kill()
            cls._instance = None
