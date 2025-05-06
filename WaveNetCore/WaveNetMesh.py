from WaveNetNode import *
from WaveNetCommunication import *
from random import randint

"""
ping
pong
data
add
attach
"""

class MeshHub(Node):
	def __init__(self):
		info = NodeInfo(0)
		self.node = Node(info, [LocalProtocol(8000)], self.delegate)
		self.node.listen()
		self.nodes = {0: info}
	
	def delegate(self, packet):
		pass

class MeshNode(Node):
	def __init__(self, protocols, neighbors=dict()):
		info = NodeInfo(randint(1, (1 << 64) - 1), neighbors)
		self.node = Node(info, protocols, self.delegate)

	def delegate(self, packet):
		pass

