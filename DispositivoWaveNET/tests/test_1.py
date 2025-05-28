import logging
import pytest
from dispositivo_wavenet.dispositivo_wavenet import DispositivoWaveNet as wn

def test_listen():
	with pytest.raises(Exception) as e_info:
		w = wn("0:0:0:0:0:0", "1:1:1:1:1:1")
		w.listen(timeout=10)
	logging.info(f"{e_info}")

def test_send():
	with pytest.raises(Exception) as e_info:
		w = wn("0:0:0:0:0:0", "1:1:1:1:1:1")
		w.send("wikir", timeout=10)
	logging.info(f"{e_info}")
