from dispositivo_wavenet.c1_shared import *
import time
import logging

def escuchar_archivo(my_mac_address_str):
    """
    Método para recibir un archivo por medio de audio

    @param my_mac_address_str Mi MAC address para saber si el archivo me corresponde
    @return True si se recibió correctamente el archivo, False si hubo un error en la transmisión del archivo
    """
    my_address_bytes = mac_str_to_bytes(my_mac_address_str)
    sndr_mac = 0x0
    nombre_archivo = ""
    cant_tramas = -1

    #Vamos a intentar escuchar algun ping de crear archivo como por 5 veces
    t_arch_info = None
    for i in range(TIMES_TO_COMUNICATE_128_BYTES):
        try:
            t_arch_info = escuchar_y_retornar_trama(timeout = TIME_TO_SAY_128_BYTES+10)
            t_arch_info.imprimir()
            if (t_arch_info.tipo == TIPO_TRAMA_ARCHIVO_INFO and
                t_arch_info.mac_destino == my_address_bytes ): break
        except:
            logging.warning("error")
        t_arch_info = -1

    if (t_arch_info is None):
        logging.info("No se escucho ninguna trama con la info del archivo inicial")
        return False
    
    logging.info("Info del archivo a recibir:")
    t_arch_info.imprimir()

    try:
        cant_tramas, nombre_archivo = decodificar_payload_archivo_info(t_arch_info.payload)
    except Exception as e:
        logging.warning(f"Error al decodificar el payload: {str(e)}")
        return False

    # Enviar OK después de verificar y decodificar
    trama_ok_1 = crear_trama_ok(
        bytes_mac_org = my_address_bytes,
        bytes_mac_dest = t_arch_info.mac_origen,
        bytes_checksum_received = t_arch_info.checksum
    )
    nombre_archivo = "new_" + nombre_archivo

    for _ in range (TIMES_TO_COMUNICATE_OK):
        emitir_trama(trama_ok_1)

    sndr_mac = t_arch_info.mac_origen

    try:
        with open(nombre_archivo, 'wb') as f:
            for i in range(cant_tramas):
                trama = None
                for _ in range(TIMES_TO_COMUNICATE_128_BYTES):
                    try:
                        trama = escuchar_y_retornar_trama(TIME_TO_SAY_128_BYTES + 10)
                        tipo_esperado = (TIPO_TRAMA_FINAL_ARCHIVO if i == cant_tramas - 1 else TIPO_TRAMA_ARCHIVO)
                        trama.imprimir()
                        if verificar_datos_esperados(trama, tipo_esperado, sndr_mac, my_address_bytes):
                            break
                    except:
                        continue

                if trama is None:
                    logging.warning(f"No se pudo escuchar la trama {i+1}")
                    return False
                
                if (trama.get_checksum_valido() == False):
                    logging.warning(f"El checksum de la trama {i+1} es invalido")
                    return False
                
                logging.info(f"Trama {i + 1} recibida correctamente")

                trama_ok = crear_trama_ok(
                    bytes_mac_org=my_address_bytes,
                    bytes_mac_dest=trama.mac_origen,
                    bytes_checksum_received=trama.checksum
                )

                f.write(trama.payload)

                for _ in range(TIMES_TO_COMUNICATE_OK):
                    emitir_trama(trama_ok)
                    if (escuchar_ping(5)): break

    except Exception as e:
        logging.warning("Error al escribir el archivo:", e)
        return False

    logging.info("Archivo recibido exitosamente.")
    return True
        
        

#Retorna true si exito
def enviar_archivo_por_sonido(nombre_archivo, mac_org_str, mac_dest_str):
    """
    Función para enviar un archivo por medio de un sonido

    @param nombre_archivo Ruta del archivo a enviar
    @param mac_org_str String de la MAC address de origen
    @param mac_dest_str String de la MAC address de destino

    @return True si el archivo es enviado correctamente, False si ocurre un error en el envío del archivo
    """
    tramas = obtener_tramas_desde_archivo(nombre_archivo,mac_org_str,mac_dest_str)
    my_origin = mac_str_to_bytes(mac_org_str)
    my_sender = mac_str_to_bytes(mac_dest_str)

    logging.info(f"Enviando archivo info del archivo: {nombre_archivo}...")

    trama_inicial=  crear_trama_archivo_info(my_origin, my_sender, len(tramas), nombre_archivo)
    escuchado = emitir_hasta_respuesta(trama_inicial, my_origin, my_sender)

    if (not escuchado):
        logging.warning("No se logro comunicar la informacion inicial del archivo")
        return False
    
    for i in range(len(tramas)):
        logging.info(f"Comunicando la trama numero {i+1}...")
        trama = tramas[i]
        if (i == len(tramas) -1):
            trama.tipo = TIPO_TRAMA_FINAL_ARCHIVO
            trama._build()
        trama_recibida = emitir_hasta_respuesta(trama, my_origin, my_sender)
        if (not trama_recibida):
            logging.warning(f"No se comunico correctamente la trama {i+1}")
            return False
        time.sleep(0.5)
        for _ in range(5):
            transmite_freq(PING_FREQ)
        time.sleep(1)
        
    logging.info("Archivo enviado")
    return True

def escuchar_string(my_mac_address_str, timeout=None):
    """
    Función para recibir un string por medio de audio

    @param my_mac_address_str Mi MAC address para saber si el archivo me corresponde
    @param timeout El timeout asignado externamente
    @return string_final El string recibido si se recibió correctamente el archivo, False si hubo un error en la transmisión del archivo
    """

    my_address_bytes = mac_str_to_bytes(my_mac_address_str)
    if timeout is None: timeout = TIME_TO_SAY_128_BYTES + 2
    sndr_mac = 0x0
    cant_tramas = -1
    logging.info(f"Timeout : {timeout}")
    logging.info(f"Repetitions : {max(TIMES_TO_COMUNICATE_128_BYTES//2, 1)}")

    #Vamos a intentar escuchar algun ping de crear archivo como por 5 veces
    t_arch_info = None
    for i in range(max(TIMES_TO_COMUNICATE_128_BYTES//2, 1)):
        try:
            t_arch_info = escuchar_y_retornar_trama(timeout = timeout)
            t_arch_info.imprimir()
            if (t_arch_info.tipo == TIPO_TRAMA_ARCHIVO_INFO and
                t_arch_info.mac_destino == my_address_bytes ): break
        except:
            logging.warning("error")
        t_arch_info = -1

    if (type(t_arch_info) is not Trama):
        logging.info("No se escucho ninguna trama con la info del string")
        return False
    
    logging.info("Info del string a recibir:")
    t_arch_info.imprimir()

    try:
        cant_tramas, nombre_archivo = decodificar_payload_archivo_info(t_arch_info.payload)
    except Exception as e:
        logging.warning("Error al decodificar el payload:", e)
        return False

    # Enviar OK después de verificar y decodificar
    #trama_ok_1 = crear_trama_ok(
	#bytes_mac_org = my_address_bytes,
	#bytes_mac_dest = t_arch_info.mac_origen,
	#bytes_checksum_received = t_arch_info.checksum
    #)
    
    string_final = b""  # Usamos bytes primero


    #for _ in range (TIMES_TO_COMUNICATE_OK):
    #    emitir_trama(trama_ok_1)
    time.sleep(0.1)
    ejecutar_ping()
    time.sleep(0.1)

    sndr_mac = t_arch_info.mac_origen

    try:
        for i in range(cant_tramas):
            trama = None
            for _ in range(TIMES_TO_COMUNICATE_128_BYTES):
                try:
                    trama = escuchar_y_retornar_trama(timeout=timeout)
                    tipo_esperado = (TIPO_TRAMA_FINAL_ARCHIVO if i == cant_tramas - 1 else TIPO_TRAMA_ARCHIVO)
                    trama.imprimir()
                    if verificar_datos_esperados(trama, tipo_esperado, sndr_mac, my_address_bytes):
                        break
                except:
                    continue

            if trama is None:
                logging.warning(f"No se pudo escuchar la trama {i+1}")
                return False
            
            if (trama.get_checksum_valido() == False):
                logging.warning(f"El checksum de la trama {i+1} es invalido")
                return False
            
            logging.info(f"Trama {i + 1} recibida correctamente")

            string_final += trama.payload

	    #trama_ok = crear_trama_ok(
			    #bytes_mac_org=my_address_bytes,
		#bytes_mac_dest=trama.mac_origen,
		#bytes_checksum_received=trama.checksum
		#)

            time.sleep(0.1)
            ejecutar_ping()
            time.sleep(0.1)
	    #if (escuchar_ping(5)): break

            """
            for _ in range(TIMES_TO_COMUNICATE_OK):
                emitir_trama(trama_ok)
                if (escuchar_ping(5)): break
            """

    except Exception as e:
        logging.warning(f"Error al recibir el string: {e}")
        return False

    logging.info("Contenido recibido (en bytes):")
    logging.info(f"{string_final.hex()}")  # cuidado: puede contener bytes no imprimibles

    return string_final.decode()


def enviar_string_por_sonido(string, mac_org_str, mac_dest_str, timeout=None):
    """
    Función para enviar un string por medio de audio

    @param string El mensaje que se quiere transmitir
    @param mac_org_str String de la MAC address de origen
    @param mac_dest_str String de la MAC address de destino

    @return True si el string es enviado correctamente, False si ocurre un error en el envío del mensaje
    """
    
    if timeout is None: timeout = TIME_TO_SAY_128_BYTES + 10
    tramas = obtener_tramas_desde_string(string,mac_org_str,mac_dest_str)
    my_origin = mac_str_to_bytes(mac_org_str)
    my_sender = mac_str_to_bytes(mac_dest_str)

    logging.info(f"Enviando string...")

    trama_inicial =  crear_trama_archivo_info(my_origin, my_sender, len(tramas), "str")
    escuchado = emitir_hasta_respuesta_ping(trama_inicial, my_origin, my_sender, timeout=timeout)

    if (not escuchado):
        logging.warning("No se logro comunicar la informacion inicial del string")
        return False
    
    for i in range(len(tramas)):
        logging.info(f"Comunicando la trama numero {i+1}...")
        trama = tramas[i]
        if (i == len(tramas) -1):
            trama.tipo = TIPO_TRAMA_FINAL_ARCHIVO
            trama._build()
        trama_recibida = emitir_hasta_respuesta_ping(trama, my_origin, my_sender, timeout=timeout)
        if (not trama_recibida):
            logging.warning(f"No se comunico correctamente la trama {i+1}")
            return False
        time.sleep(0.5)
        for _ in range(6):
            transmite_freq(PING_FREQ)
        time.sleep(1)

    logging.info("String enviado")
    return True


def emitir_hasta_respuesta_ping(trama, my_origin_bytes, my_sender_bytes, timeout=None):
    """"
    Función para emitir una trama y recibir un ping como confirmación
    
    @param trama Mi trama a ser emitada
    @param my_origin_bytes MAC address del origen del mensaje
    @param my_sender_bytes MAC address del destinatario del mensaje

    @return True si la trama es emitida y escuchada correctamente, False si no
    """

    if timeout is None: timeout = TIME_TO_SAY_128_BYTES + 10
    for i in range (TIMES_TO_COMUNICATE_128_BYTES):
        logging.info(f"Emitiendo trama por {i +1 } vez")
        emitir_trama(trama)
        for _ in range(max(TIMES_TO_COMUNICATE_OK-1,1)):
            if escuchar_ping(timeout):
		    time.sleep(0.1)
		    return True
    return False

def emitir_hasta_respuesta(trama, my_origin_bytes, my_sender_bytes, timeout=None):
    """"
    Función para emitir una trama y recibir un OK representado como una trama de 
    que tiene en el payload el checksum de mi trama
    
    @param trama Mi trama a ser emitada
    @param my_origin_bytes MAC address del origen del mensaje
    @param my_sender_bytes MAC address del destinatario del mensaje

    @return True si la trama es emitida y escuchada correctamente, False si no
    """

    if timeout is None: timeout = TIME_TO_SAY_128_BYTES + 10
    for i in range (TIMES_TO_COMUNICATE_128_BYTES):
        logging.info(f"Emitiendo trama por {i +1 } vez")
        emitir_trama(trama)
        trama_recibida = None
        for _ in range(max(TIMES_TO_COMUNICATE_OK-1,1)):
            try:
                trama_recibida = escuchar_y_retornar_trama(timeout = timeout)
                if (trama_recibida is None): continue
                trama_recibida.imprimir()
                #Ver si el payload de la trama_recibida es igual a mi checksum de mi trama
                if (verificar_datos_esperados(trama_recibida, TIPO_OK, my_sender_bytes, my_origin_bytes) and trama_recibida.payload == trama.checksum):
                    return True
            except:
                pass

    return False
