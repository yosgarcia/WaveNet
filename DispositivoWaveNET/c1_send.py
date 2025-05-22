import os
import numpy as np
from scipy.io.wavfile import write
import sounddevice as sd
import argparse
import zlib

from c1_shared import *
from c1_listen import escuchar_y_retornar_trama

def transmite_freq(freq, duration=BYTE_DURATION):
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
    tono = 0.5 * np.sin(2 * np.pi * freq * t)
    sd.play(tono, samplerate=SAMPLE_RATE)
    sd.wait()

def transmitir_silencio(freq = SILENCE_FREQ, duration=SILENCE_DURATION):
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
    tono = 0.5 * np.sin(2 * np.pi * freq * t)
    sd.play(tono, samplerate=SAMPLE_RATE)
    sd.wait()


def emitir_trama(trama_bytes):
    for byte in trama_bytes:
        freq = byte_to_freq(byte)
        print(f"Enviando byte {byte} → {freq:.1f} Hz")
        transmite_freq(freq)
        transmitir_silencio()
    transmite_freq(FREQ_EOF)  # Frecuencia especial para EOF
    print("Trama transmitida.")
        
def send_file_as_sound(file_path, str_org_mac, str_dest_mac):
    """
    Divide el archivo en bloques de 107 bytes, crea una trama por cada uno y la emite como sonido.
    """
    version = 1
    bytes_mac_org = mac_str_to_bytes(str_org_mac)
    bytes_mac_dest = mac_str_to_bytes(str_dest_mac)
    tipo = TIPO_ENVIO_ARCHIVO

    with open(file_path, 'rb') as f:
        while True:
            block = f.read(107)
            if not block:
                break
            trama = crear_trama(version, bytes_mac_org, bytes_mac_dest, tipo, block)
            imprimir_trama(trama)
            print(f"Enviando trama de {len(trama)} bytes...")
            emitir_trama(trama)

def enviar_ping(mac_origin):
    version = VERSION
    tipo = TIPO_PING
    payload = b''
    mac_origin = mac_str_to_bytes(mac_origin)
    dest_mac_broadcast = mac_str_to_bytes("ff:ff:ff:ff:ff:ff")

    trama = crear_trama(version, mac_origin, dest_mac_broadcast, tipo, payload)

    print(f"Enviando PING desde {mac_origin}...")
    emitir_trama(trama)


def enviar_archivo_por_sonido(nombre_archivo, mac_org_str, mac_dest_str):
    tramas = obtener_tramas_desde_archivo(nombre_archivo,mac_org_str,mac_dest_str)
    my_origin = mac_str_to_bytes(mac_org_str)
    my_sender = mac_str_to_bytes(mac_dest_str)
    print(f"Enviando archivo {nombre_archivo}...")
    for i in len(tramas):
        print(f"Comunicando la trama numero {i+1}...")
        trama = tramas[i]
        my_length = trama[14]
        my_checksum = trama[15+my_length:15+my_length+4]
        while (True):
            emitir_trama(trama)
            trama_recibida = escuchar_y_retornar_trama()
            sender_mac_origin = trama_recibida[1:7]
            sender_mac_dest = trama_recibida[7:13]
            sender_length = trama[14]
            sender_checksum = trama[15+sender_length:15+sender_length+4]
            #Manejo de macs distintas a las esperadas
            if (sender_mac_origin != my_sender or sender_mac_dest != my_origin): continue
            # Manejo cuando trama es diferente
            if (my_checksum != sender_checksum): continue
            break
        print(f"Trama {i+1} recibida correctamente por el destinatario")
    print("Archivo enviado")

def recibir_archivo_por_sonido():
    pass