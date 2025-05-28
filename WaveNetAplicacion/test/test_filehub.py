# Archivo: WaveNetAplicacion/tests/test_filehub.py
import pytest

import WaveNetAplicacion.FileHub as filehub_mod


def test_filehub_register_and_query(monkeypatch):
    # Preparar FileHub
    hub = filehub_mod.FileHub()

    # Mensajes simulados: registro y consulta
    messages = [
        (10, {  # Nodo 10 registra archivos a.txt y b.txt
            "type": "DATA",
            "resource": "file_register",
            "body": {"files": ["a.txt", "b.txt"]}
        }),
        (20, {  # Nodo 20 consulta b.txt
            "type": "REQUEST",
            "resource": "file_query",
            "body": {"filename": "b.txt"}
        }),
    ]
    sent = []

    # Stub de receive_message
    def stub_receive_message():
        from_id, msg = messages.pop(0)
        # Después del segundo mensaje, detener el hub
        if not messages:
            hub.stop()
        return from_id, msg

    # Stub de send_message para capturar respuestas
    def stub_send_message(dest_id, msg_type, resource, body):
        sent.append((dest_id, msg_type, resource, body))

    # Monkeypatch en el módulo FileHub
    monkeypatch.setattr(filehub_mod, 'receive_message', stub_receive_message)
    monkeypatch.setattr(filehub_mod, 'send_message', stub_send_message)

    # Ejecutar bucle de procesamiento
    hub._running = True
    hub._run_loop()

    # Tras procesar, el registro debe contener los archivos registrados
    assert sorted(hub.lookup('a.txt')) == [10]
    assert sorted(hub.lookup('b.txt')) == [10]

    # Debe haberse enviado una respuesta a la consulta
    assert len(sent) == 1
    dest_id, msg_type, resource, body = sent[0]
    assert dest_id == 20
    assert msg_type == 'RESPONSE'
    assert resource == 'file_query_response'
    assert body == {'nodes': [10]}
