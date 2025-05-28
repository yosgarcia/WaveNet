import pytest
import time
from wavenetcore.WaveNetProtocols import *
from wavenetcore.WaveNetPacketeering import Packet

A = "0:0:0:0:0:0"
B = "1:1:1:1:1:1"
pkt = Packet(src=1, dest=2, mtype="msg", body="ahu, ahua")

def manual_test_link_sending_packet_sound():
	time.sleep(0.5)

	sender = SoundProtocol(mac=A)

	time.sleep(0.5)

	link = Link(B, sender)
	link.send(pkt).join()

	time.sleep(0.5)

	assert True

if __name__ == "__main__":
	import logging
	logging.getLogger().setLevel(logging.INFO)
	manual_test_link_sending_packet_sound()
