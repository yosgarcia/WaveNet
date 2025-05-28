Network Working Group                                       S. Ramos
Request for Comments: XXXX                                  Y. García
Category: Experimental                                      M. Latysh
                                                            J. Cordero
                                                            ITCR
                                                            Mayo 2025

                Protocolo de Comunicación Acústica
                WaveNet


Status of this Memo

   This memo defines an Experimental Protocol for the Internet community.
   It does not specify an Internet standard of any kind. Distribution of
   this memo is unlimited.

Abstract

   Este documento describe un protocolo de comunicación experimental
   basado en la transmisión de datos utilizando sonido. El protocolo se
   divide en capas funcionales, siendo cada una abordada en su sección
   respectiva. Este RFC documenta la capa física (Capa 1) XXXXX Y LAS OTRAS,
   diseñada para codificar bytes en frecuencias audibles y enviar tramas
   de datos entre dispositivos.

Table of Contents

   1. Introducción ................................................. 2  
   2. Terminología ................................................. 2  
   3. Visión general del protocolo ................................ 3  
   4. Capa 1: Capa Física Acústica ................................ 4  
      4.1 Formato de Trama ........................................ 4  
      4.2 Asignación de Frecuencias ............................... 5  
      4.3 Comunicación de tramas .................................. 6  
      4.4 Comunicación de mensaje ................................. 7  
      4.5 Consideraciones y Problemas Comunes ..................... 8  
   5. Referencias ................................................. 9  

1. Introducción

   El presente documento forma parte de un sistema de comunicación
   modular por capas, donde se utiliza la transmisión acústica de
   datos como medio. Este RFC describe la capa física (Capa 1), la
   cual define cómo se estructuran, codifican y transmiten las tramas
   de datos mediante sonidos.

2. Terminología

   - Emisor: dispositivo que transmite los datos.
   - Receptor: dispositivo que escucha y decodifica los datos.
   - Trama: paquete de datos con formato estructurado.
   - Byte: unidad de 8 bits.
   - Ping: señal de inicio o confirmación de comunicación.
   - EOF: señal de fin de trama.
   - Checksum: verificación de integridad.

3. Visión general del protocolo

   El protocolo define una comunicación unidireccional o bidireccional
   mediante sonido. Un emisor convierte bytes en frecuencias, las emite
   junto con silencios, y el receptor escucha, interpreta y responde.

4. Capa 1: Capa Física Acústica

4.1 Formato de Trama

   Cada trama tiene un tamaño máximo de 128 bytes, distribuidos de la
   siguiente manera:

      [versión][MAC_org][MAC_dest][tipo][longitud][payload][checksum][eof]

   - versión: 1 byte
   - MAC_org: 6 bytes
   - MAC_dest: 6 bytes
   - tipo: 1 byte
   - longitud: 1 byte
   - payload: 0–107 bytes
   - checksum: 4 bytes
   - eof: señal final (frecuencia especial)

   Tipos definidos para la versión 1:
     - TIPO_PING = 0x01
     - TIPO_TRAMA_ARCHIVO_INFO = 0x02
     - TIPO_TRAMA_ARCHIVO = 0x03
     - TIPO_TRAMA_FINAL_ARCHIVO = 0x04
     - TIPO_ERROR = 0x05
     - TIPO_OK = 0x06
     
     Parametros definidos para la sinconización
     - VERSION = 0x01  
     - TIME_TO_SAY_OK = 10 segundos
     - TIMES_TO_COMUNICATE_OK = 3  
     - TIME_TO_SAY_128_BYTES = 113 segundos  
     - TIMES_TO_COMUNICATE_128_BYTES = 3  

 4.2 Asignación de Frecuencias

   - BASE_FREQ = 550 Hz (para el byte 0)
   - FREQ_STEP = 70 Hz
     (byte N se representa como BASE_FREQ + N * FREQ_STEP)

   Frecuencias especiales:
     - SILENCE_FREQ = 200
     - PING_FREQ = 250 Hz
     - FREQ_EOF = 300 Hz


 4.3 Comunicación de tramas
 
   
   Proceso de emisión de trama única:  
     1. Emitir PING_FREQ.  
     2. Emitir SILENCE_FREQ.  
     3. Emitir cada byte del mensaje convertido a su frecuencia correspondiente,  
        intercalando silencios entre bytes para evitar superposición.  
     4. Emitir FREQ_EOF.
     
   
   Proceso del escucha de trama única:
   	1. Recibir un tiempo ajustable TIMEOUT, que suele ser 
   	TIME_TO_SAY_128 bytes más un margen de tolerancia.
   	1. Espera hasta escuchar PING_FREQ
   	2. Alterna entre frecuencias de silencio y de bytes, decodificando cada byte
   	recibido
   	3. Repite este proceso hasta alguna de estas condiciones
   		- Escuchar FREQ_EOF
   		- Pase TIMEOUT segundos y no escuche ningun ping
   		- Pase TIMEOUT segundos desde que escuchó el ping inicial
   		
   El proceso de comunicación de una trama:
   	1. Emitir la trama
   	2. Se intenta TIMES_TO_COMUNICATE_OK veces escuchar un PING_FREQ en 3 segundos
   		-Si se escucha un PING_FREQ del receptor, se indica que la trama fue recibida
   		correctamente, y se termina este ciclo
   		-Si no se escucha un PING_FREQ en todo el ciclo, se indica que la trama
   		no fue recibida correctamente
 
   Proceso de recepción de una trama:
   	1. Se escucha una trama
   	2. Se valida la trama de la siguiente manera
   	  - Se verifica que su checksum sea válido
   	  - Se verifica que su destinatario sea mi MAC ADDRESS
   	  - Si no es una trama TIPO_TRAMA_ARCHIVO_INFO, se verifica que
   	  su origen sea el indicado inicialmente
   	3. Si la trama es valida, se emite un PING 2 veces y se indica la recepción correcta,
        si no, se repite el proceso TIMES_TO_COMUNICATE_128_BYTES veces
   		
 4.4 Comunicación de mensaje
 	
   Proceso de emisión de mensaje:
        1. El emisor recibe:
   		- MAC ADDRESS de sí mismo 
   		- MAC ADDRESS del destinatario
   		- El mensaje a transmitir como bytes  
   	2. Divide el mensaje en bloques de máximo 107 bytes
   	3. Crea la trama inicial del tipo TIPO_TRAMA_ARCHIVO_INFO, cuyo payload
   	comienza con 4 bytes que indican la cantidad total de tramas a emitir,
   	seguido opcionalmente por un nombre o descripción del mensaje
   	4. El emisor comunica la trama de información
   	5. El emisor comunica cada trama con la información del mensaje
   Si no se llega a cumplir correctamente el proceso de comunicación correcta del mensaje,
   se cierra la conexión
   
   Proceso de recepción de mensaje:
        1. El receptor recibe la trama de TIPO_TRAMA_ARCHIVO_INFO inicial
        2. El receptor decodifica esta trama y recibe las tramas del mensaje
        3. El receptor junta los payloads de las tramas del mensaje y lo retorna
   Si no se llega a cumplir correctamente el proceso de recepción del mensaje,
   se cierra la conexión.


4.5 Consideraciones y Problemas Comunes

   - El uso de silencio entre bytes es crucial para evitar mezcla de señales.
   - Se podrían recibir bytes erróneos por ruido, aunque el checksum
     reduce el riesgo de aceptar tramas inválidas.

5. Referencias

   [1] Fielding, R., et al. "Hypertext Transfer Protocol -- HTTP/1.1",
       RFC 2616, June 1999.


