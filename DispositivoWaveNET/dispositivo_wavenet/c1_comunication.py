from c1_shared import *

def escuchar_archivo(my_mac_address_str):
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
            print("error")
            pass
        t_arch_info = -1

    if (t_arch_info is None):
        print("No se escucho ninguna trama con la info del archivo inicial")
        return False
    
    print("Info del archivo a recibir:")
    t_arch_info.imprimir()

    try:
        cant_tramas, nombre_archivo = decodificar_payload_archivo_info(t_arch_info.payload)
    except Exception as e:
        print("Error al decodificar el payload:", e)
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
                    print(f"No se pudo escuchar la trama {i+1}")
                    return False
                
                if (trama.get_checksum_valido() == False):
                    print(f"El checksum de la trama {i+1} es invalido")
                    return False
                
                print(f"Trama {i + 1} recibida correctamente")

                trama_ok = crear_trama_ok(
                    bytes_mac_org=my_address_bytes,
                    bytes_mac_dest=trama.mac_origen,
                    bytes_checksum_received=trama.checksum
                )

                f.write(trama.payload)

                for _ in range(TIMES_TO_COMUNICATE_OK):
                    emitir_trama(trama_ok)

    except Exception as e:
        print("Error al escribir el archivo:", e)
        return False

    print("Archivo recibido exitosamente.")
    return True
        
        

#Retorna true si exito
def enviar_archivo_por_sonido(nombre_archivo, mac_org_str, mac_dest_str):
    tramas = obtener_tramas_desde_archivo(nombre_archivo,mac_org_str,mac_dest_str)
    my_origin = mac_str_to_bytes(mac_org_str)
    my_sender = mac_str_to_bytes(mac_dest_str)

    print(f"Enviando archivo info del archivo: {nombre_archivo}...")

    trama_inicial=  crear_trama_archivo_info(my_origin, my_sender, len(tramas), nombre_archivo)
    escuchado = emitir_hasta_respuesta(trama_inicial, my_origin, my_sender)

    if (not escuchado):
        print("No se logro comunicar la informacion inicial del archivo")
        return False
    
    for i in range(len(tramas)):
        print(f"Comunicando la trama numero {i+1}...")
        trama = tramas[i]
        if (i == len(tramas) -1):
            trama.tipo = TIPO_TRAMA_FINAL_ARCHIVO
            trama._build()
        trama_recibida = emitir_hasta_respuesta(trama, my_origin, my_sender)
        if (not trama_recibida):
            print(f"No se comunico correctamente la trama {i+1}")
            return False
        
    print("Archivo enviado")
    return True

def escuchar_string(my_mac_address_str):
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
            print("error")
            pass
        t_arch_info = -1

    if (t_arch_info is None):
        print("No se escucho ninguna trama con la info del string")
        return False
    
    print("Info del string a recibir:")
    t_arch_info.imprimir()

    try:
        cant_tramas, nombre_archivo = decodificar_payload_archivo_info(t_arch_info.payload)
    except Exception as e:
        print("Error al decodificar el payload:", e)
        return False

    # Enviar OK después de verificar y decodificar
    trama_ok_1 = crear_trama_ok(
        bytes_mac_org = my_address_bytes,
        bytes_mac_dest = t_arch_info.mac_origen,
        bytes_checksum_received = t_arch_info.checksum
    )
    
    string_final = b""  # Usamos bytes primero


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
                    print(f"No se pudo escuchar la trama {i+1}")
                    return False
                
                if (trama.get_checksum_valido() == False):
                    print(f"El checksum de la trama {i+1} es invalido")
                    return False
                
                print(f"Trama {i + 1} recibida correctamente")

                string_final += trama.payload


                trama_ok = crear_trama_ok(
                    bytes_mac_org=my_address_bytes,
                    bytes_mac_dest=trama.mac_origen,
                    bytes_checksum_received=trama.checksum
                )

                f.write(trama.payload)

                for _ in range(TIMES_TO_COMUNICATE_OK):
                    emitir_trama(trama_ok)

    except Exception as e:
        print("Error al escribir el archivo:", e)
        return False

    print("Contenido recibido (en bytes):")
    print(string_final.hex())  # cuidado: puede contener bytes no imprimibles

    return string_final


def enviar_string_por_sonido(string, mac_org_str, mac_dest_str):
    tramas = obtener_tramas_desde_string(string,mac_org_str,mac_dest_str)
    my_origin = mac_str_to_bytes(mac_org_str)
    my_sender = mac_str_to_bytes(mac_dest_str)

    print(f"Enviando string...")

    trama_inicial =  crear_trama_archivo_info(my_origin, my_sender, len(tramas), "str")
    escuchado = emitir_hasta_respuesta(trama_inicial, my_origin, my_sender)

    if (not escuchado):
        print("No se logro comunicar la informacion inicial del string")
        return False
    
    for i in range(len(tramas)):
        print(f"Comunicando la trama numero {i+1}...")
        trama = tramas[i]
        if (i == len(tramas) -1):
            trama.tipo = TIPO_TRAMA_FINAL_ARCHIVO
            trama._build()
        trama_recibida = emitir_hasta_respuesta(trama, my_origin, my_sender)
        if (not trama_recibida):
            print(f"No se comunico correctamente la trama {i+1}")
            return False
        
    print("String enviado")
    return True


def emitir_hasta_respuesta(trama, my_origin_bytes, my_sender_bytes):

    for i in range (TIMES_TO_COMUNICATE_128_BYTES):
        print(f"Emitiendo trama por {i +1 } vez")
        emitir_trama(trama)
        trama_recibida = None
        for _ in range(max(TIMES_TO_COMUNICATE_OK-2,1)):
            try:
                trama_recibida = escuchar_y_retornar_trama(timeout = TIME_TO_SAY_OK*2)
                trama_recibida.imprimir()
            except:
                pass

        if (trama_recibida is None):
            continue
        
        #Ver si el payload de la trama_recibida es igual a mi checksum de mi trama

        if (verificar_datos_esperados(trama_recibida, TIPO_OK, my_sender_bytes, my_origin_bytes) and trama_recibida.payload == trama.checksum):
            return True

    return False