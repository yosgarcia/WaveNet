from c1_shared import *

def escuchar_archivo(my_mac_address_str):
    my_address_bytes = mac_str_to_bytes(my_mac_address_str)
    sndr_mac = 0x0
    nombre_archivo = ""
    cant_tramas = -1

    #Vamos a intentar escuchar algun ping de crear archivo como por 5 veces
    t_arch_info = -1
    for i in range(TIMES_TO_COMUNICATE_128_BYTES):
        try:
            t_arch_info = escuchar_y_retornar_trama(timeout = TIME_TO_SAY_128_BYTES+10)
            if (t_arch_info.tipo == TIPO_TRAMA_ARCHIVO_INFO and
                t_arch_info.mac_destino == my_address_bytes ): break
        except:
            pass
        t_arch_info = -1

    if (t_arch_info == -1):
        print("No se escucho ninguna trama con la info del archivo inicial")
        return
    
    print("Info del archivo a recibir:")
    t_arch_info.imprimir()
    trama_ok_1 = crear_trama_ok(
        bytes_mac_org = my_address_bytes,
        bytes_mac_dest = t_arch_info.mac_origen,
        bytes_checksum_received = t_arch_info.checksum
    )

    for i in range (TIMES_TO_COMUNICATE_OK):
        emitir_trama(trama_ok_1)

    cant_tramas, nombre_archivo = decodificar_payload_archivo_info(t_arch_info.payload)
    sndr_mac = t_arch_info.mac_origen

    #sacar cuantas tramas voy a recibir
    tramas_recibidas = []
    for i in range(cant_tramas):
        trama  = -1
        for _ in range(TIMES_TO_COMUNICATE_128_BYTES):
            try:
                trama = escuchar_y_retornar_trama(TIME_TO_SAY_128_BYTES+10)
                tipo_esperado = TIPO_TRAMA_ARCHIVO
                if (i == cant_tramas - 1): tipo_esperado = TIPO_TRAMA_FINAL_ARCHIVO
                if (verificar_datos_esperados(trama = trama,
                                              tipo_esperado = tipo_esperado,
                                              org_esperado = sndr_mac,
                                              dst_esperado = my_address_bytes)):break
            except:
                continue
        
        if (trama == -1):
            print("No se pudo escuchar la trama ", i+1)
            return
        
        trama_ok = crear_trama_ok(
            bytes_mac_org = my_address_bytes,
            bytes_mac_dest = trama.mac_origen,
            bytes_checksum_received = trama.checksum)
        
        for i in range (TIMES_TO_COMUNICATE_OK):
            emitir_trama(trama_ok)
        
        tramas_recibidas.append(trama)
    return tramas_recibidas
        
        

#Retorna true si exito
def enviar_archivo_por_sonido(nombre_archivo, mac_org_str, mac_dest_str):
    tramas = obtener_tramas_desde_archivo(nombre_archivo,mac_org_str,mac_dest_str)
    my_origin = mac_str_to_bytes(mac_org_str)
    my_sender = mac_str_to_bytes(mac_dest_str)

    print(f"Enviando archivo info del archivo: {nombre_archivo}...")

    trama_inicial=  crear_trama_archivo_info(my_origin, my_sender, len(tramas), nombre_archivo)
    escuchado = emitir_hasta_respuesta(trama_inicial)

    if (not escuchado):
        return False
    
    for i in len(tramas):
        print(f"Comunicando la trama numero {i+1}...")
        trama = tramas[i]
        trama_recibida = emitir_hasta_respuesta(trama, my_origin, my_sender)
        if (not trama_recibida):
            return False
        
    print("Archivo enviado")
    return True

def emitir_hasta_respuesta(trama, my_origin_bytes, my_sender_bytes):
    my_length = trama[14]
    my_checksum = trama[15 + my_length: 15 + my_length + 4]
    start_time = time.time()
    
    for i in range (TIMES_TO_HEAR_OK):
        emitir_trama(trama)
        trama_recibida = escuchar_y_retornar_trama(timeout = TIME_TO_SAY_OK*2)

        if (trama_recibida == -1):
            continue

        sender_type = trama_recibida[0]
        if (sender_type != TIPO_OK):
            continue

        sender_mac_origin = trama_recibida[1:7]
        sender_mac_dest = trama_recibida[7:13]

        if (sender_mac_origin != my_sender_bytes or sender_mac_dest != my_origin_bytes): continue

        sender_length = trama[14]

        #payload should be my checksum
        sender_payload = trama_recibida[15 + sender_length : 15 + sender_length + 4]
        if (my_checksum != sender_payload): continue

        return True
    return False