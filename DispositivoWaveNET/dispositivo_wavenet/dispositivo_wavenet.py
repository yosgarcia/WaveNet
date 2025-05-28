from c1_comunication import *

#python3 -m venv nombre_del_entorno
#source nombre_del_entorno/bin/activate
#pip install scipy numpy sounddevice

# python3 dispositivo_wavenet.py -a prueba.txt -b aa:bb:cc:dd:ee:ff -c 11:22:33:44:55:66 -d 3
# Ver nombre para ver donde sale el audio   
# for i, device in enumerate(sd.query_devices()):
#        if device['max_output_channels'] > 0:
#            print(f"{i}: {device['name']}")


# python3 dispositivo_wavenet.py -a prueba.txt -b 11:22:33:44:55:66 -d 4
'''
class DispositivoWaveNET:
    def __init__(self, mac_origen, mac_destino=None):
        self.mac_origen = mac_origen
        self.mac_destino = mac_destino
    
    def enviar_archivo(self, ruta_archivo):
        """
        Envía un archivo a través de sonido.
        :param ruta_archivo: Ruta del archivo a enviar.
        :return: True si el envío fue exitoso, False en caso contrario.
        """
        if not os.path.exists(ruta_archivo):
            raise FileNotFoundError(f"El archivo {ruta_archivo} no existe.")
        return enviar_archivo_por_sonido(ruta_archivo, self.mac_origen, self.mac_destino)
    
    def escuchar_archivo(self):
        """
        Escucha un archivo a través de sonido.
        :return: True si la escucha fue exitosa, False en caso contrario.
        """
        return escuchar_archivo(self.mac_origen)

    def guardar_archivo_en_tramas_wav(self, ruta_archivo):
        guardar_archivo_en_tramas_wav(ruta_archivo, self.mac_origen, self.mac_destino)


    def escuchar_y_obtener_trama(self, tiempo_espera=TIME_TO_SAY_128_BYTES):
        """
        Escucha y retorna una trama.
        :param tiempo_espera: Tiempo máximo para esperar la trama.
        :return: Trama recibida.
        """
        try:
            trama = escuchar_y_retornar_trama(tiempo_espera)
            return trama
        except Exception as e:
            print(f"No se escuchó ninguna trama: {e}")
            return None

'''
def main():
    parser = argparse.ArgumentParser(description="Parser de archivo y direcciones MAC")
    parser.add_argument('-a', '--archivo', required=True, help="Ruta al archivo (ej: archivo.txt)")
    parser.add_argument('-b', '--mac_origen', required=True, help="MAC Address de origen (ej: aa:bb:cc:dd:ee:ff)")
    parser.add_argument('-c', '--mac_destino', required=False, help="MAC Address de destino (ej: 11:22:33:44:55:66)")
    parser.add_argument('-d', '--modo', required=True)


    args = parser.parse_args()
    ruta = args.archivo
    
    if not os.path.exists(ruta):
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



    #enviar_ping(args.mac_origen)

    #send_file_as_sound(ruta, args.mac_origen, args.mac_destino)

    #guardar_archivo_en_tramas_wav(ruta, args.mac_origen, args.mac_destino)


if __name__ == '__main__':
    main()