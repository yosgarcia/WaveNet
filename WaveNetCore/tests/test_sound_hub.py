from wavenetcore.WaveNetAdaptors import WaveNetBasicMeshHub as MeshHub
from wavenetcore.WaveNetAdaptors import WaveNetBasicMeshNode as MeshNode
from wavenetcore.WaveNetProtocols import *
from threading import Thread
import signal

A = "0:0:0:0:0:0"
B = "1:1:1:1:1:1"

def run():
	p = SoundProtocol(mac=A)
	hub = MeshHub([p])
	hub.run()
	return hub

if __name__ == "__main__": 
	import logging
	logging.getLogger().setLevel(logging.INFO)
	hub = run()
	signal.signal(signal.SIGINT, lambda s, f: None)
	signal.pause()
	hub.kill()
