import pytest
import time
from wavenetcore.WaveNetProtocols import *
from wavenetcore.WaveNetPacketeering import Packet

A = "0:0:0:0:0:0"
B = "1:1:1:1:1:1"
pkt = Packet(src=1, dest=2, mtype="msg", body="ahu, ahua")

def __test_link_sending_packet_sound():
	time.sleep(0.5)

	sender = SoundProtocol(mac=A)

	time.sleep(0.5)

	link = Link(B, sender)
	link.send(pkt).join()

	time.sleep(0.5)

	assert True

def __test_link_receiving_packet_sound():
	time.sleep(0.5)
	receiver = SoundProtocol(mac=B)
	received = []

	thread = receiver.listen(lambda packet: received.append(packet))

	time.sleep(60*4)

	receiver.kill()

	assert len(received) == 1
	assert pkt == received[0]
