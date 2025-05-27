
# Archivo: WaveNetAplicacion/tests/test_node_manager.py
import pytest
from WaveNetAplicacion.NodeManager import NodeManager


def test_singleton_behavior():
    # Obtener dos instancias
    node1 = NodeManager.get_node()
    node2 = NodeManager.get_node()
    print(f"Node1 ID: {id(node1)}")
    print(f"Node2 ID: {id(node2)}")
    assert node1 is node2
    
    # Shutdown y recreación
    NodeManager.shutdown()
    new_node = NodeManager.get_node()
    print(f"New node ID: {id(new_node)}")
    assert new_node is not node1
    
    # Limpiar
    NodeManager.shutdown()