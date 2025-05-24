import pytest
from wavenetcore.WaveNetAdaptors import WaveNetBasicMeshHub as MeshHub
from wavenetcore.WaveNetAdaptors import WaveNetBasicMeshNode as MeshNode
from wavenetcore.WaveNetProtocols import LocalProtocol
import time
from threading import Thread

@pytest.fixture
def setup_mesh_1():
	ports = [9000, 9001, 9002, 9003]
	protocols = [[LocalProtocol(ports[i])] for i in range(4)]
	nodes = [MeshHub(protocols[0])] + [MeshNode(protocols[i], ID=i) for i in range(1, 4)]

	for node in nodes: node.run()

	yield nodes, protocols, ports

	time.sleep(0.5)
	for node in nodes: node.kill()
	time.sleep(1)

@pytest.fixture
def setup_mesh_2(setup_mesh_1):
	nodes, protocols, ports = setup_mesh_1
	hub, node1, node2, node3 = nodes

	node1.connect(0, protocols[1][0], str(ports[0]))
	node2.connect(1, protocols[2][0], str(ports[1]))
	node2.connect(3, protocols[2][0], str(ports[3]))

	time.sleep(0.5)

	yield nodes[0], nodes[1:]

@pytest.fixture
def setup_mesh_3(setup_mesh_2):
	hub, nodes = setup_mesh_2

	for node in nodes:
		node.join()

	time.sleep(0.5)
	
	return hub, nodes


def test_mutual_connection_after_connect(setup_mesh_1):
	def get_link_dests(node):
		return set(link.dest for link in node.node.info.get_neighbors())

	nodes, protocols, ports = setup_mesh_1
	hub, node1, node2, node3 = nodes

	node1.connect(0, protocols[1][0], str(ports[0]))
	node2.connect(1, protocols[2][0], str(ports[1]))

	time.sleep(0.5)

	hub_dests = get_link_dests(hub)
	node1_dests = get_link_dests(node1)
	node2_dests = get_link_dests(node2)

	assert str(ports[1]) in hub_dests
	assert str(ports[0]) in node1_dests
	assert str(ports[2]) in node1_dests
	assert str(ports[1]) in node2_dests

	time.sleep(1)

def test_all_nodes_can_join_network(setup_mesh_2):
	hub, nodes = setup_mesh_2

	for node in nodes:
		node.join()

	for node in nodes:
		assert node.hub_key is not None
		assert node.my_id() in hub.nodes

def test_hub_can_ping_node(setup_mesh_3):
	hub, nodes = setup_mesh_3
	for node in nodes:
		assert hub.ping(node.my_id())

def test_node_can_ping_hub(setup_mesh_3):
	hub, nodes = setup_mesh_3
	for node in nodes:
		assert node.ping(0)

def test_node_can_ping_node(setup_mesh_3):
	_, nodes = setup_mesh_3
	assert nodes[0].ping(nodes[1].my_id())
	assert nodes[1].ping(nodes[0].my_id())

def test_recv_data_from_any(setup_mesh_3):
	hub, nodes = setup_mesh_3
	receiver = nodes[0]
	sender = nodes[1]

	msg = "I like hotdogs and police"
	result = {}

	def recv_thread():
		result["from_id"], result["data"] = receiver.listen()

	t = Thread(target=recv_thread)
	t.start()
	time.sleep(0.5)
	sender.send_data(receiver.my_id(), msg)
	t.join(timeout=2)

	assert result.get("data") == msg

def test_recv_data_from_specific_id(setup_mesh_3):
	hub, nodes = setup_mesh_3
	receiver = nodes[0]
	target_sender = nodes[1]
	other_sender = nodes[2]

	msg = "rararraarrarraraMIAUW"
	result = {}

	def recv_thread():
		result["from_id"], result["data"] = receiver.recv(ID=target_sender.my_id())

	t = Thread(target=recv_thread)
	t.start()
	time.sleep(0.1)

	other_sender.send_data(receiver.my_id(), "Shalam alakum")
	time.sleep(0.1)

	target_sender.send_data(receiver.my_id(), msg)
	t.join(timeout=2)

	assert result.get("data") == msg
	assert result.get("from_id") == target_sender.my_id()
