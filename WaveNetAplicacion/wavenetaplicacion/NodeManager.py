# NodeManager.py

from typing import Optional
from wavenetcore.WaveNetAdaptors import WaveNetBasicMeshHub
from wavenetcore.WaveNetAdaptors import WaveNetBasicMeshNode
from wavenetcore.WaveNetProtocols import LocalProtocol, IPProtocol, SoundProtocol

class NodeManager:
	"""
	Singleton para WaveNetBasicMeshNode en Capa 4.
	Arranca un nodo local y se conecta/join al mesh‐hub automáticamente.
	"""

	encrypt = False
	nodes = []

	def get_hub(protocols):
		hub = WaveNetBasicMeshHub(protocols, encrypt=encrypt)

		hub.run()

		NodeManager.nodes.append(hub)

		return hub

	def get_node(ID=None, protocols, connections):
		node = WaveNetBasicMeshNode(protocols, ID=ID, encrypt=encrypt)

		node.run()

		for ID, protocol, data in connections:
			if type(protocol) == LocalProtocol: node.connect(ID, protocol, str(data))
			if type(protocol) == IPProtocol: node.connect(ID, protocol, IPProtocol.ip_to_json(data[0], data[1]))
			if type(protocol) == SoundProtocol: node.connect(ID, protocol, data)

		node.join()

		NodeManager.nodes.append(node)

		return node
	
	def shutdown():
		for node in nodes: node.kill()
