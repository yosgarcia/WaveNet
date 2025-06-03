import argparse
import logging
from NodeManager import NodeManager

class WaveNetParser:
	def __init__(self, desc, is_hub = False):
		self.is_hub = is_hub
		parser = argparse.ArgumentParser(description=desc)

		parser.add_argument('--verbose', action='store_true', help='Activar modo verbose')

		parser.add_argument('--localp', type=str, help='Especifica el puerto para el protocolo local. El formato esperado es --localp <puerto>')
		parser.add_argument('--ipp', type=str, help='Especifica el IPv4 y el puerto para el protocolo IP. El formato esperado es --ipp <IPv4>,<puerto>')
		parser.add_argument('--soundp',type=str, help='Especifica el MAC para el protocolo de sonido. El formato esperado es --soundp <MAC>')
		if not self.is_hub:
			parser.add_argument('--node-id', '-n', type=int, default=None, help='ID numérico para este nodo mesh (opcional)')
			parser.add_argument('--localc', action='append', help='Añade una conexión local. El formato esperado es --localc <ID>,<puerto>')
			parser.add_argument('--ipc', action='append', help='Añade una conexión sobre IP. El formato esperado es --ipc <ID>,<IP>,<puerto>')
			parser.add_argument('--soundc', action='append', help='Añade una conexión sobre sonido. El formato esperado es --soundc <ID>,<MAC>')
		self.parser = parser
	
	def get_parser(self):
		return self.parser
	
	def parse(self):
		args = self.parser.parse_args()

		if not (args.localp or args.ipp or args.soundp):
			self.parser.error("At least one of --localp, --ipp, or --soundp is required")

		if args.verbose: logging.getLogger().setLevel(logging.INFO)

		self.args = args
	
	def get_args(self):
		return self.args
	
	def get_node(self):
		args = self.args
		protocols = []
		connections = []

		if args.localp:
			port = int(args.localp)
			protocol = NodeManager.get_local_protocol(port)
			protocols.append(protocol)
			if not self.is_hub and args.localc:
				for idport in args.localc:
					ID, port = idport.split(',')
					ID = int(ID)
					port = int(port)
					connections.append((ID, protocol, port,))

		if args.ipp:
			ip, port = args.ipp.split(",")
			port = int(port)
			protocol = NodeManager.get_ip_protocol(ip, port)
			protocols.append(protocol)
			if not self.is_hub and args.ipc:
				for idipport in args.ipc:
					ID, ip, port = idipport.split(",")
					ID = int(ID)
					port = int(port)
					connections.append((ID, protocol, (ip, port,)))

		if args.soundp:
			mac = args.soundp
			protocols = NodeManager.get_sound_protocol(mac)
			protocols.append(protocol)
			if not self.is_hub and args.soundc:
				for idmac in args.soundc:
					ID, mac = idmac.split(',')
					ID = int(ID)
					connections.append((ID, protocol, mac,))

		if not self.is_hub: return NodeManager.get_node(ID=args.node_id, protocols=protocols, connections=connections)

		return NodeManager.get_hub(protocols=protocols)
