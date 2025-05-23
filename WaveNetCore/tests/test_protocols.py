import pytest
import time
from wavenetcore.WaveNetProtocols import *
from wavenetcore.WaveNetPacketeering import Packet

def test_empty_protocol_from_str_matches_enum():
	for name in ProtocolType.__members__:
		proto = empty_protocol_from_str(name)
		assert isinstance(proto, Protocol)
		assert proto.protocol_type == ProtocolType[name]

def test_link_str_eq_hash():
	protocol = LocalProtocol()
	link1 = Link("9000", protocol)
	link2 = Link("9000", protocol)
	link3 = Link("9001", protocol)

	assert str(link1) == "|LOCAL|9000"
	assert link1 == link2
	assert link1 != link3
	assert hash(link1) == hash(link2)
	assert hash(link1) != hash(link3)

def test_link_sending_and_receiving_packet_local():
	time.sleep(0.5)
	recv_port = 9100
	receiver = LocalProtocol(port=recv_port)
	received = []

	thread = receiver.listen(lambda packet: received.append(packet))

	time.sleep(0.5)

	link = Link(str(recv_port), LocalProtocol())
	pkt = Packet(src=1, dest=2, mtype="msg", body="hello")
	link.send(pkt)

	time.sleep(0.5)
	receiver.kill()

	assert len(received) == 1
	assert pkt == received[0]

def test_link_sending_and_receiving_packet_ip():
	time.sleep(0.5)
	recv_ip = "127.0.0.1"
	recv_port = 9100
	receiver = IPProtocol(ip=recv_ip, port=recv_port)
	received = []

	thread = receiver.listen(lambda packet: received.append(packet))

	time.sleep(0.5)

	data = {
			"ip" : recv_ip,
			"port" : recv_port
			}
	dest = json.dumps(data)

	link = Link(dest, IPProtocol())
	pkt = Packet(src=1, dest=2, mtype="msg", body="hello")
	link.send(pkt)

	time.sleep(0.5)
	receiver.kill()

	assert len(received) == 1
	assert pkt == received[0]

