# Archivo: WaveNetAplicacion/tests/test_filere gister.py
import os
import pytest
from WaveNetAplicacion.FileRegister import announce_files


def test_announce_files(monkeypatch, tmp_path):
    # Crear directorio compartido con archivos y un subdirectorio
    shared_dir = tmp_path / "shared"
    shared_dir.mkdir()
    file_names = ["a.txt", "b.bin"]
    for fname in file_names:
        (shared_dir / fname).write_text("contenido")
    # Crear subdirectorio para probar filtrado
    (shared_dir / "subdir").mkdir()

    sent = []
    # Stub para capturar send_message
    def stub_send_message(dest_id, msg_type, resource, body):
        sent.append((dest_id, msg_type, resource, body))

    # Monkeypatch para reemplazar send_message interno
    import WaveNetAplicacion.FileRegister as fr_mod
    monkeypatch.setattr(fr_mod, 'send_message', stub_send_message)

    # Llamada a la función bajo prueba
    hub_id = 42
    announce_files(hub_id, str(shared_dir))

    # Debe haberse enviado exactamente 1 mensaje
    assert len(sent) == 1
    dest_id, msg_type, resource, body = sent[0]

    # Verificaciones
    assert dest_id == hub_id
    assert msg_type == 'DATA'
    assert resource == 'file_register'
    # El body debe contener la lista de archivos sin incluir subdirectorios
    assert sorted(body.get('files', [])) == sorted(file_names)
