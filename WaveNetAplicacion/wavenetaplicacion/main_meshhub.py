#!/usr/bin/env python3
"""
main_meshhub.py

Arranca un WaveNetBasicMeshHub escuchando en el puerto 9000.
"""
from wavenetcore.WaveNetAdaptors import WaveNetBasicMeshHub
from wavenetcore.WaveNetProtocols import LocalProtocol
import time

def main():
	PORT = 9000
	hub = WaveNetBasicMeshHub([LocalProtocol(port=PORT)])
	print(f"[MeshHub] Arrancando en puerto {PORT}...")
	hub.run()  # Inicializa listeners en background

	# Mantener el proceso vivo
	print("[MeshHub] Ejecutando. Ctrl+C para detener...")
	try:
		while True:
			time.sleep(1)
	except KeyboardInterrupt:
		print("\n[MeshHub] Parando...")
		hub.kill()  # Finaliza el hub y cierra sockets


# python3 main_meshhub.py
if __name__ == "__main__":
	main()