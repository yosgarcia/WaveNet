import pytest
import time
from wavenetcore.WaveNetNode import *
from wavenetcore.WaveNetProtocols import *
from wavenetcore.WaveNetCrypto import *

def test_nodeinfo_neighbor_addition():

	node_id = 1
	priv_key = PrivateKey()
	node_info = NodeInfo(node_id, priv_key)

	proto = LocalProtocol(9000)
	link = Link("9001", proto)

	node_info.add_neighbor(link)
	neighbors = node_info.get_neighbors()

	assert link in neighbors

@pytest.fixture
def setup_nodes():
	keys = [PrivateKey() for i in range(4)]
	infos = [NodeInfo(i, keys[i]) for i in range(4)]
	protocols = [LocalProtocol(9000 + i) for i in range(4)]
	queues = [[] for i in range(4)]
	calls = []
	calls.append(lambda p: (queues[0].append(p)) != 1)
	calls.append(lambda p: (queues[1].append(p)) != 1)
	calls.append(lambda p: (queues[2].append(p)) != 1)
	calls.append(lambda p: (queues[3].append(p)) != 1)
	nodes = [Node(infos[i], [protocols[i]], calls[i]) for i in range(4)]
	nodes[0].info.add_neighbor(Link("9001", protocols[0]))
	nodes[0].info.add_neighbor(Link("9002", protocols[0]))
	nodes[1].info.add_neighbor(Link("9000", protocols[1]))
	nodes[1].info.add_neighbor(Link("9002", protocols[1]))
	nodes[2].info.add_neighbor(Link("9000", protocols[2]))
	nodes[2].info.add_neighbor(Link("9001", protocols[2]))
	nodes[2].info.add_neighbor(Link("9003", protocols[2]))
	nodes[3].info.add_neighbor(Link("9002", protocols[3]))
	for node in nodes: node.listen()

	yield nodes, keys, queues

	time.sleep(1.0)
	for node in nodes: node.kill()
	time.sleep(1.0)


def test_plain_packet_propagation(setup_nodes):
	nodes, _, queues = setup_nodes

	nodes[0].send(3, "ping", "fishmaster199")

	time.sleep(1)

	assert any(p.body == "fishmaster199" for p in queues[3])


def test_encrypted_packet_propagation(setup_nodes):
	nodes, keys, queues = setup_nodes

	public_key_C = keys[2].public_key()
	nodes[1].send(2, "data", "lulakibab", public_key=public_key_C)

	time.sleep(1)

	assert any(p.body == "lulakibab" for p in queues[2])
