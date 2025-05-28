import os
import numpy as np
from scipy.io.wavfile import write
import sounddevice as sd
import argparse
import zlib
#python3 -m venv nombre_del_entorno
#source nombre_del_entorno/bin/activate
#pip install scipy numpy sounddevice

# Parámetros
sample_rate = 44100        # Frecuencia de muestreo en Hz
byte_duration = 0.05       # Duración de cada byte en segundos
base_freq = 500            # Frecuencia base para el primer byte
freq_step = 20             # Incremento de frecuencia por valor de byte (0-127)
tipo_envio_archivo = 0x02
tipo_ping = 0x01
version = 1

def byte_to_freq(byte):
    """
    Convierte un byte (0-127) a una frecuencia.
    """
    return base_freq + byte * freq_step

def freq_to_byte(freq):
    byte = round((freq - base_freq) / freq_step)
    if 0 <= byte <= 127:
        return byte
    return None


def transmite_freq(freq, duration=byte_duration):
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    tono = 0.5 * np.sin(2 * np.pi * freq * t)
    sd.play(tono, samplerate=sample_rate)
    sd.wait()


def emitir_trama(trama_bytes):
    for byte in trama_bytes:
        freq = byte_to_freq(byte)
        print(f"Enviando byte {byte} → {freq:.1f} Hz")
        transmite_freq(freq)
    transmite_freq(900)  # Frecuencia especial para EOF
    print("Trama transmitida.")

def recibir_trama():
    
    if (tipo_trama == 2):
        recibir_archivo
    pass

def detectar_frecuencia(audio, sample_rate):
    fft = np.fft.fft(audio)
    freqs = np.fft.fftfreq(len(audio), 1/sample_rate)
    magnitudes = np.abs(fft)
    peak_idx = np.argmax(magnitudes[:len(magnitudes)//2])
    return abs(freqs[peak_idx])


def recibir_archivo(bytes_mac_myself, bytes_mac_sender, longitud):
    pass
    

def mac_str_to_bytes(mac_str):
    """
    Convierte una dirección MAC en formato string (aa:bb:cc:dd:ee:ff)
    a un objeto bytes b'\xaa\xbb\xcc\xdd\xee\xff'.
    """
    try:
        parts = mac_str.split(":")
        if len(parts) != 6:
            raise ValueError
        return bytes(int(part, 16) for part in parts)
    except Exception:
        raise argparse.ArgumentTypeError(f"MAC inválida: {mac_str}")


def crear_trama(version, bytes_mac_org, bytes_mac_dest, tipo, cur_payload):
    """
    Crea una trama con el formato: [version][MAC_org][MAC_dest][tipo][length][payload][checksum]
    """


    length = len(cur_payload)

    header = bytearray([version]) + bytes_mac_org + bytes_mac_dest + bytearray([tipo,length])
    checksum = zlib.crc32(header + cur_payload).to_bytes(4, byteorder='big')
    trama = header + cur_payload + checksum
    return trama


def send_file_as_sound(file_path, str_org_mac, str_dest_mac):
    """
    Divide el archivo en bloques de 107 bytes, crea una trama por cada uno y la emite como sonido.
    """
    version = 1
    bytes_mac_org = mac_str_to_bytes(str_org_mac)
    bytes_mac_dest = mac_str_to_bytes(str_dest_mac)
    tipo = tipo_envio_archivo

    with open(file_path, 'rb') as f:
        while True:
            block = f.read(107)
            if not block:
                break
            trama = crear_trama(version, bytes_mac_org, bytes_mac_dest, tipo, block)
            print(f"Enviando trama de {len(trama)} bytes...")
            emitir_trama(trama)



def enviar_ping(mac_origin):
    version = 1
    tipo = tipo_ping
    payload = b''
    mac_origin = mac_str_to_bytes(mac_origin)
    dest_mac_broadcast = mac_str_to_bytes("ff:ff:ff:ff:ff:ff")

    trama = crear_trama(version, mac_origin, dest_mac_broadcast, tipo, payload)

    print(f"Enviando PING desde {mac_origin}...")
    emitir_trama(trama)

#python3 capa1.py -a archivo.txt -b aa:bb:cc:dd:ee:ff -c 11:22:33:44:55:66

def main():
    parser = argparse.ArgumentParser(description="Parser de archivo y direcciones MAC")
    
    parser.add_argument('-a', '--archivo', required=True, help="Ruta al archivo (ej: archivo.txt)")
    parser.add_argument('-b', '--mac_origen', required=True, help="MAC Address de origen (ej: aa:bb:cc:dd:ee:ff)")
    parser.add_argument('-c', '--mac_destino', required=True, help="MAC Address de destino (ej: 11:22:33:44:55:66)")

    args = parser.parse_args()
    ruta = args.archivo
    
    enviar_ping(args.mac_origen)

    if not os.path.exists(ruta):
        print(f"El archivo {ruta} no existe.")
        return

    send_file_as_sound(ruta, args.mac_origen, args.mac_destino)

    # Mensaje de 128 bytes (valores de 0x00 a 0x7F)
    message = bytes(range(128))

    trama = bytearray([
            1,                          # Versión
            *b'\xaa\xbb\xcc\xdd\xee\xff',  # MAC origen
            *b'\x11\x22\x33\x44\x55\x66',  # MAC destino
            1,                          # Longitud
            42,                         # Payload (1 byte)
            0x12, 0x34                  # CRC16 (ejemplo)
        ])
    emitir_trama(trama)
 

 

    # Tiempo para una "nota"
    t = np.linspace(0, byte_duration, int(sample_rate * byte_duration), endpoint=False)

    # Generar señal de audio: cada byte como un tono único
    audio = [
        0.5 * np.sin(2 * np.pi * (base_freq + byte * freq_step) * t)
        for byte in message
    ]

    # Concatenar las ondas y convertir a formato int16 para WAV
    audio_signal = np.concatenate(audio)
    audio_int16 = np.int16(audio_signal * 32767)

    # Guardar el archivo de audio
    file_path_bytes = "trama_128bytes_por_byte.wav"
    write(file_path_bytes, sample_rate, audio_int16)

    print("Archivo guardado en: ", file_path_bytes)

if __name__ == '__main__':
    main()