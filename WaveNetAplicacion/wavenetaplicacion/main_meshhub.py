#!/usr/bin/env python3
"""
main_meshhub.py

Arranca un WaveNetBasicMeshHub escuchando en el puerto 9000.
"""
from wavenetcore.WaveNetAdaptors import WaveNetBasicMeshHub
from wavenetcore.WaveNetProtocols import LocalProtocol
from wavenetaplicacion.GeneralParser import WaveNetParser
import time

def main():

	parser = WaveNetParser("MeshHub: Crea una instancia del MeshHub", is_hub=True)
	parser.parse()

	hub = parser.get_node()

	print(f"[MeshHub] Arrancando..")

	# Mantener el proceso vivo
	print("[MeshHub] Ejecutando. Ctrl+C para detener...")
	try:
		while True:
			time.sleep(1)
	except KeyboardInterrupt:
		print("\n[MeshHub] Parando...")
		hub.kill()  # Finaliza el hub y cierra sockets


# python3 main_meshhub.py --verbose --localp 9000
if __name__ == "__main__":
	main()
