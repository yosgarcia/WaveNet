#!/usr/bin/env python3
"""
WaveNetAplicacion/irc_bot.py

Bot IRC para WaveNet:
 - !list	   → lista todos los archivos disponibles
 - !get <file> → descarga el archivo y notifica la ruta local
"""
import argparse
import irc.client
import os

from Service import send_message, receive_message, receive_file
from NodeManager import NodeManager

class WaveNetBot:
	def __init__(self, reactor, connection, channel, hub_id, out_dir):
		self.reactor  = reactor
		self.conn	 = connection
		self.channel  = channel
		self.hub_id   = hub_id
		self.out_dir  = out_dir

		# Handlers
		self.conn.add_global_handler("welcome", self.on_welcome)
		self.conn.add_global_handler("pubmsg",  self.on_pubmsg)

	def on_welcome(self, conn, event):
		print(f"[irc_bot] on_welcome: uniéndome a {self.channel}")
		conn.join(self.channel)
		print(f"[irc_bot] on_welcome: enviando mensaje de bienvenida")
		conn.privmsg(self.channel, "WaveNetBot listo. !list | !get <archivo>")

	def on_pubmsg(self, conn, event):
		print(f"[irc_bot] on_pubmsg: recibí {event.arguments[0]!r} de {event.source}")
		msg  = event.arguments[0].strip()
		nick = irc.client.NickMask(event.source).nick

		# !list → lista archivos
		if msg == "!list":
			send_message(self.hub_id, "REQUEST", "list_files", {})
			# Esperar respuesta
			while True:
				from_id, resp = receive_message()
				if from_id == self.hub_id and resp.get("resource") == "list_files_response":
					files = resp.get("body", {}).get("files", [])
					break
			text = ", ".join(files) if files else "<vacío>"
			conn.privmsg(self.channel, f"Archivos disponibles: {text}")

		# !get <archivo> → descarga
		elif msg.startswith("!get "):
			filename = msg.split(" ",1)[1]
			conn.privmsg(self.channel, f"{nick}: descargando '{filename}'…")
			# 1) quién lo tiene
			send_message(self.hub_id, "REQUEST", "file_query", {"filename": filename})
			while True:
				from_id, resp = receive_message()
				if from_id == self.hub_id and resp.get("resource") == "file_query_response":
					owners = resp.get("body", {}).get("nodes", [])
					break
			if not owners:
				conn.privmsg(self.channel, f"{nick}: '{filename}' no encontrado")
				return
			owner = owners[0]
			# 2) pedir transferencia
			send_message(owner, "REQUEST", "file_transfer_init", {"filename": filename})
			# 3) recibir y guardar
			try:
				path = receive_file(self.out_dir)
				conn.privmsg(self.channel, f"{nick}: completado → {path}")
			except Exception as e:
				conn.privmsg(self.channel, f"{nick}: error → {e}")

	def start(self):
		self.reactor.process_forever()

# python3 irc_bot.py   --hub-id <> --node-port 8004   --hub-port 9000   --server 127.0.0.1   --port 6667   --channel "#wavenet"   --nick "WaveBot"   --out-dir "./descargas"
if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="Bot IRC para WaveNet")
	parser.add_argument("--server",   default="127.0.0.1", help="Host IRC")
	parser.add_argument("--port",	 type=int, default=6667,   help="Puerto IRC")
	parser.add_argument("--channel",  default="#wavenet",	help="Canal IRC")
	parser.add_argument("--nick",	 default="WaveNetBot",  help="Nickname del bot")
	parser.add_argument("--hub-id",   type=int, required=True,  help="ID del nodo FileHub")
	parser.add_argument("--node-port",type=int, default=None,   help="Puerto local mesh (evitar choques)")
	parser.add_argument("--hub-port", type=int, default=None,   help="Puerto mesh-hub (capa3), por defecto 9000")
	parser.add_argument("--out-dir",  default="downloads",   help="Carpeta para descargas")
	args = parser.parse_args()

	# Ajustar puertos en NodeManager antes de instanciar nodo
	if args.node_port:
		NodeManager.DEFAULT_PORT = args.node_port
	else:
		NodeManager.DEFAULT_PORT = 1
	if args.hub_port:
		NodeManager.HUB_PORT = args.hub_port

	# Crear y arrancar el nodo mesh
	node = NodeManager.get_node()
	print(f"[irc_bot] Nodo mesh ID={node.my_id()} en puerto {NodeManager.DEFAULT_PORT}")

	# Crear conexión IRC
	reactor   = irc.client.Reactor()
	connection= reactor.server().connect(args.server, args.port, args.nick)

	# Instanciar bot y arrancar
	bot = WaveNetBot(
		reactor   = reactor,
		connection= connection,
		channel   = args.channel,
		hub_id	= args.hub_id,
		out_dir   = args.out_dir
	)
	bot.start()
