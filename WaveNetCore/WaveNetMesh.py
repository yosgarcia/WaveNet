from WaveNetNode import *
from WaveNetCommunication import *
from random import randint

"""
data...
join
leave[crypto]
report[crypto]
"""

class MeshHistory:
	def __init__(self, ID, time):
		self.ID = ID
		self.time = time

class MeshHub(Node):
	def __init__(self):
		info = NodeInfo(0)
		self.node = Node(info, [LocalProtocol(8000)], self.delegate)
		self.node.listen()
		self.nodes = {0: MeshHistory(0, get_time())}
	
	def delegate(self, message):
		prefix = message[:5]

class MeshNode(Node):
	def __init__(self, protocols, neighbors=set()):
		info = NodeInfo(randint(1, (1 << 64) - 1), neighbors)
		self.node = Node(info, protocols, self.delegate)

	def delegate(self, packet):
		pass

