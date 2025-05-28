from dispositivo_wavenet.c1_communication import *

#python3 -m venv nombre_del_entorno
#source nombre_del_entorno/bin/activate
#pip install scipy numpy sounddevice

# python3 dispositivo_wavenet.py -a prueba.txt -b aa:bb:cc:dd:ee:ff -c 11:22:33:44:55:66 -d 3
# Ver nombre para ver donde sale el audio   
# for i, device in enumerate(sd.query_devices()):
#        if device['max_output_channels'] > 0:
#            print(f"{i}: {device['name']}")


# python3 dispositivo_wavenet.py -a prueba.txt -b aa:bb:cc:dd:ee:ff -c 11:22:33:44:55:66 -d 5
# python3 dispositivo_wavenet.py -a prueba.txt -b 11:22:33:44:55:66 -d 6

class DispositivoWaveNet:
	"""
	Clase que maneja el dispositivo WaveNet en capa 1
	"""

	def __init__(self, mac_origen, mac_destino=None):
		"""
		Constructor del DispositivoWaveNet.

		@param mac_origen El mac_origen
		@param mac_destino El mac_destino
		"""
		self.mac_origen = mac_origen
		self.mac_destino = mac_destino

	def send(self, string, timeout=None):
		"""
		Envía un string a través de sonido.

		@param string: Mensaje en string a enviar.
		"""

		if not enviar_string_por_sonido(string, self.mac_origen, self.mac_destino, timeout=timeout):
			raise Exception("Failed to send string through layer 1")

	def listen(self, timeout=None, init_timeout=None):
		"""
		Escucha un string a través de sonido.

		@return: True si la escucha fue exitosa, False en caso contrario.
		"""

		ret = escuchar_string(self.mac_origen, timeout=timeout, init_timeout=init_timeout)
		if ret == False:
			raise Exception("Failed to get string from layer 1")
		return ret

def main():
    parser = argparse.ArgumentParser(description="Parser de archivo y direcciones MAC")
    parser.add_argument('-a', '--archivo', required=True, help="Ruta al archivo (ej: archivo.txt)")
    parser.add_argument('-b', '--mac_origen', required=True, help="MAC Address de origen (ej: aa:bb:cc:dd:ee:ff)")
    parser.add_argument('-c', '--mac_destino', required=False, help="MAC Address de destino (ej: 11:22:33:44:55:66)")
    parser.add_argument('-d', '--modo', required=True)


    args = parser.parse_args()
    ruta = args.archivo
    
    if (args.modo=="1" or args.modo=="3") and not os.path.exists(ruta):
        print(f"El archivo {ruta} no existe.")
        return

    match (args.modo):
        case "1":
            guardar_archivo_en_tramas_wav(ruta, args.mac_origen, args.mac_destino)
        case "2":
            try:
                tramita = escuchar_y_retornar_trama(TIME_TO_SAY_128_BYTES)
                tramita.imprimir()
                #trama_ok = crear_trama_ok(tramita.mac_origen, tramita.mac_destino, tramita.checksum)
                #guardar_trama_como_wav(trama_ok, "Trama_ok.wav")
            except:
                print("No se escuho ninguna trama en el tiempo establecido.")

        case "3":
            exito = enviar_archivo_por_sonido(ruta, args.mac_origen, args.mac_destino)
            if (not exito): print("No se envio el archivo correctamente")
        case "4":
            exito = escuchar_archivo(args.mac_origen)
            if (not exito): print("No se escucho el archivo correctamente")
        case "5":
            exito = enviar_string_por_sonido(ruta, args.mac_origen, args.mac_destino)
            if (not exito): print("No se envio el archivo correctamente")
        case "6":
            exito = escuchar_string(args.mac_origen)
            if (not exito): print("No se escucho el archivo correctamente")

    #enviar_ping(args.mac_origen)

    #send_file_as_sound(ruta, args.mac_origen, args.mac_destino)

    #guardar_archivo_en_tramas_wav(ruta, args.mac_origen, args.mac_destino)

if __name__ == '__main__':
    main()
