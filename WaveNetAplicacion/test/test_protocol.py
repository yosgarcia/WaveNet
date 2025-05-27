# Archivo: WaveNetAplicacion/tests/test_protocol.py
import pytest
from WaveNetAplicacion.Protocol import Protocol


def test_encode_decode_roundtrip(capfd):
    # Mensaje de ejemplo
    original = {
        "type": "REQUEST",
        "resource": "test.txt",
        "body": {"key": "value"}
    }
    # Encode
    encoded = Protocol.encode(original)
    print(f"Encoded message: {encoded}")
    # Decode
    decoded = Protocol.decode(encoded)
    print(f"Decoded message: {decoded}")

    # Comprobaciones
    assert isinstance(encoded, str)
    assert decoded == original


def test_decode_invalid_json():
    bad_json = "{not valid json}"
    with pytest.raises(ValueError) as excinfo:
        Protocol.decode(bad_json)
    print(f"Expected error: {excinfo.value}")
    assert "Error al decodificar" in str(excinfo.value)

