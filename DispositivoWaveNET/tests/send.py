import logging
logging.getLogget().setLevel(logging.INFO)
from dispositivo_wavenet.dispositivo_wavenet import DispositivoWaveNet as wn

def send():
	w = wn("1:1:1:1:1:1", "0:0:0:0:0:0")
	w.send("wikir", timeout=20)

send()
