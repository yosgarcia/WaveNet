from wavenetcore.WaveNetAdaptors import WaveNetBasicMeshHub as MeshHub
from wavenetcore.WaveNetAdaptors import WaveNetBasicMeshNode as MeshNode
from wavenetcore.WaveNetProtocols import *
from threading import Thread
import signal
import time

A = "0:0:0:0:0:0"
B = "1:1:1:1:1:1"

def run():
	p = SoundProtocol(mac=B)
	node = MeshNode([p], ID=1, encrypt=False)
	node.run()
	return node, p

if __name__ == "__main__": 
	import logging
	logging.getLogger().setLevel(logging.INFO)
	node, p = run()
	time.sleep(10)
	node.connect(0, p, A)
	time.sleep(10)
	signal.signal(signal.SIGINT, lambda s, f: None)
	signal.pause()
	node.kill()
