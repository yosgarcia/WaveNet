from c1_shared import *
from c1_send import enviar_archivo_por_sonido, emitir_trama
from c1_listen import escuchar_y_retornar_trama

#python3 -m venv nombre_del_entorno
#source nombre_del_entorno/bin/activate
#pip install scipy numpy sounddevice

#python3 dispositivo_wavenet.py -a prueba.txt -b aa:bb:cc:dd:ee:ff -c 11:22:33:44:55:66 -d 2

def main():
    parser = argparse.ArgumentParser(description="Parser de archivo y direcciones MAC")
    
    parser.add_argument('-a', '--archivo', required=True, help="Ruta al archivo (ej: archivo.txt)")
    parser.add_argument('-b', '--mac_origen', required=True, help="MAC Address de origen (ej: aa:bb:cc:dd:ee:ff)")
    parser.add_argument('-c', '--mac_destino', required=True, help="MAC Address de destino (ej: 11:22:33:44:55:66)")
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
            tramita = escuchar_y_retornar_trama()
            imprimir_trama(tramita)
        case "3":
            tramas = obtener_tramas_desde_archivo(ruta, args.mac_origen, args.mac_destino)
            emitir_trama(tramas[0])

    #enviar_ping(args.mac_origen)

    #send_file_as_sound(ruta, args.mac_origen, args.mac_destino)

    #guardar_archivo_en_tramas_wav(ruta, args.mac_origen, args.mac_destino)


if __name__ == '__main__':
    main()