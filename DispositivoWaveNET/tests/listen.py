import logging
logging.getLogger().setLevel(logging.INFO)
from dispositivo_wavenet.dispositivo_wavenet import DispositivoWaveNet as wn

def listen():
	w = wn("0:0:0:0:0:0", "1:1:1:1:1:1")
	w.listen(timeout=30)

print(listen())
