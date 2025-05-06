from WaveNetNode import *
from WaveNetCommunication import *

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
		self.nodes = [info]
	
	def delegate(self, packet):
		pass

class MeshNode(Node):
	def __init__(self):
		pass

	def delegate(self, packet):
		pass

