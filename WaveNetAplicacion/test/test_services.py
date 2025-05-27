# WaveNetAplicacion/tests/test_service.py

import pytest
import time
import threading

from wavenetcore.WaveNetAdaptors import WaveNetBasicMeshHub, WaveNetBasicMeshNode
from wavenetcore.WaveNetProtocols import LocalProtocol
from WaveNetAplicacion.Protocol import Protocol

def test_send_and_receive_via_hub(capfd):
    # 1) Creamos el hub en el puerto 8200 y dos nodos en 8201 y 8202
    hub    = WaveNetBasicMeshHub([LocalProtocol(port=8200)])
    node_a = WaveNetBasicMeshNode([LocalProtocol(port=8201)], ID=1)
    node_b = WaveNetBasicMeshNode([LocalProtocol(port=8202)], ID=2)

    # 2) Arrancamos hub y nodos
    hub.run()
    node_a.run()
    node_b.run()

    try:
        # 3) Conectamos ambos nodos al hub
        node_a.connect(0, LocalProtocol(port=8201), "8200")
        node_b.connect(0, LocalProtocol(port=8202), "8200")

        # Damos tiempo para intercambio de claves y estabilización
        time.sleep(0.5)
        node_a.join()
        node_b.join()
        time.sleep(0.5)

        # 4) Preparamos listener en hilo separado sobre node_b
        results = {}
        def listener():
            from_id, raw = node_b.listen()
            results['received'] = (from_id, Protocol.decode(raw))

        listener_thread = threading.Thread(target=listener, daemon=True)
        listener_thread.start()

        # Asegurar que listener ya está activo
        time.sleep(0.1)

        # 5) Enviamos mensaje desde A a B
        payload = {"type": "DATA", "resource": "file1", "body": "hello"}
        raw_msg = Protocol.encode(payload)
        node_a.send(dest=2, message=raw_msg)

        # 6) Esperamos a que el listener reciba (hasta 2s)
        listener_thread.join(timeout=2.0)
        assert 'received' in results, "El listener no recibió ningún mensaje"

        from_id, received = results['received']
        print(f"Mensaje recibido de {from_id}: {received}")

        # 7) Verificaciones finales
        assert from_id == 1, "El ID del emisor no coincide"
        assert received == payload, "El contenido del mensaje no coincide"

    finally:
        # 8) Limpiar recursos
        node_a.kill()
        node_b.kill()
        hub.kill()
