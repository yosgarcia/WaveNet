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
byte_duration = 0.1     # Duración de cada byte en segundos
silence_duration = 0.2
base_freq = 350            # Frecuencia base para el primer byte
silence_freq = 200
freq_step = 70             # Incremento de frecuencia por valor de byte (0-127)
tipo_envio_archivo = 0x02
tipo_ping = 0x01
version = 1

freq_eof = 16000


def byte_to_freq(byte):
    """
    Convierte un byte (0-255) a una frecuencia.
    """
    return base_freq + byte * freq_step


def freq_to_byte(freq):
    byte = int(round((freq - base_freq) / freq_step))
    if 0 <= byte <= 255:
        freq_calc = base_freq + byte * freq_step
        if abs(freq - freq_calc) < (freq_step / 2):  # más tolerancia
            return byte
    return None


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

def transmite_freq(freq, duration=byte_duration):
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    tono = 0.5 * np.sin(2 * np.pi * freq * t)
    sd.play(tono, samplerate=sample_rate)
    sd.wait()

def transmitir_silencio(freq = silence_freq, duration=silence_duration):
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    tono = 0.5 * np.sin(2 * np.pi * freq * t)
    sd.play(tono, samplerate=sample_rate)
    sd.wait()


def emitir_trama(trama_bytes):
    for byte in trama_bytes:
        freq = byte_to_freq(byte)
        print(f"Enviando byte {byte} → {freq:.1f} Hz")
        transmite_freq(freq)
        transmitir_silencio()
    transmite_freq(freq_eof)  # Frecuencia especial para EOF
    print("Trama transmitida.")
        
    
def recibir_trama():
    tipo_trama = 2
    if (tipo_trama == 2):
        recibir_archivo
    pass

def calcular_checksum(trama):
    """
    Calcula el checksum de una trama.
    """
    checksum = zlib.crc32(trama)
    return checksum.to_bytes(4, byteorder='big')



def crear_trama(version, bytes_mac_org, bytes_mac_dest, tipo, cur_payload):
    """
    Crea una trama con el formato: [version][MAC_org][MAC_dest][tipo][length][payload][checksum]
    """
    length = len(cur_payload)
    header = bytearray([version]) + bytes_mac_org + bytes_mac_dest + bytearray([tipo,length])
    checksum = calcular_checksum(header + cur_payload)
    trama = header + cur_payload + checksum
    return trama

def imprimir_trama(trama):
    """
    Imprime el contenido de una trama en formato legible.
    Formato esperado:
    [versión][MAC_org][MAC_dest][tipo][longitud][payload][checksum][eof]
    """
    if len(trama) < 15:
        print("Trama demasiado corta para ser válida.")
        return

    version = trama[0]
    mac_org = trama[1:7]
    mac_dest = trama[7:13]
    tipo = trama[13]
    length = trama[14]

    if len(trama) < 15 + length + 4:
        print("Longitud declarada no coincide con datos reales.")
        return

    payload = trama[15:15+length]
    checksum = trama[15+length:15+length+4]

    def mac_to_str(mac_bytes):
        return ':'.join(f'{b:02x}' for b in mac_bytes)

    print("----- TRAMA -----")
    print(f"Versión     : {version}")
    print(f"MAC Origen : {mac_to_str(mac_org)}")
    print(f"MAC Destino  : {mac_to_str(mac_dest)}")
    print(f"Tipo        : {tipo}")
    print(f"Longitud    : {length}")
    print(f"Payload     : {payload}")
    print(f"Checksum    : {checksum.hex()}")
    print("-----------------")

def detectar_frecuencia(audio, sample_rate):
    fft = np.fft.fft(audio)
    freqs = np.fft.fftfreq(len(audio), 1/sample_rate)
    magnitudes = np.abs(fft)
    peak_idx = np.argmax(magnitudes[:len(magnitudes)//2])
    return abs(freqs[peak_idx])

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
            imprimir_trama(trama)
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

def recibir_archivo(bytes_mac_myself, bytes_mac_sender, longitud):
    pass

def escuchar_y_reconstruir_trama():
    bytes_recibidos = []
    print("Escuchando... (esperando datos hasta EOF 7000 Hz)")

    expect_silence = False

    while True:
        # Leer bloque de audio del tamaño de un byte
        duracion_muestra = int(sample_rate * (byte_duration-0.06))
        audio = sd.rec(duracion_muestra, samplerate=sample_rate, channels=1, dtype='float64')
        sd.wait()

        audio = audio.flatten()
        freq = detectar_frecuencia(audio, sample_rate)

        if abs(freq - freq_eof) < 10:  # Frecuencia EOF detectada
            print("EOF detectado.")
            break

        byte = freq_to_byte(freq)
        if byte is not None:
            if (expect_silence):
                continue
            print(f"Frecuencia detectada: {freq:.1f} Hz → Byte: {byte} | ASCII: {chr(byte) if 32 <= byte <= 126 else 'No printable character'}")
            bytes_recibidos.append(byte)
            expect_silence = True
        else:
            expect_silence = False
            print(f"Frecuencia fuera de rango: {freq:.1f} Hz")

    return bytes_recibidos


def procesar_trama_recibida(trama):
    if len(trama) < 15:
        print("Trama demasiado corta para ser válida.")
        return
    version = trama[0]
    bytes_mac_org = trama[1:7]
    bytes_mac_dest = trama[7:13]
    tipo = trama[13]
    longitud = trama[14]
    payload = trama[15:15+longitud]
    checksum_recibido = trama[15+longitud:15+longitud+4]


    # Verificar checksum
    header = bytearray([version]) + bytes_mac_org + bytes_mac_dest + bytearray([tipo, longitud])
    checksum_calculado = calcular_checksum(header + payload)

    if checksum_recibido != checksum_calculado:
        print("Checksum inválido. Trama corrupta.")
        return

    print("Trama válida recibida:")
    imprimir_trama(trama)
 
    """
    Convierte el contenido de un archivo en una señal de audio codificada por frecuencia
    y guarda dicha señal como archivo WAV.
    """

    bytes_mac_org = mac_str_to_bytes(mac_origen_str)
    bytes_mac_dest = mac_str_to_bytes(mac_destino_str)
    tipo = tipo_envio_archivo

    audio_signal = []

    with open(file_path, 'rb') as f:
        while True:
            block = f.read(107)
            if not block:
                break

            trama = crear_trama(version, bytes_mac_org, bytes_mac_dest, tipo, block)

            for byte in trama:
                freq = byte_to_freq(byte)
                t = np.linspace(0, byte_duration, int(sample_rate * byte_duration), endpoint=False)
                tono = 0.5 * np.sin(2 * np.pi * freq * t)
                audio_signal.append(tono)

    # Añadir tono EOF al final
    t_eof = np.linspace(0, byte_duration, int(sample_rate * byte_duration), endpoint=False)
    tono_eof = 0.5 * np.sin(2 * np.pi * freq_eof * t_eof)
    audio_signal.append(tono_eof)

    # Unir, convertir y guardar
    full_audio = np.concatenate(audio_signal)
    audio_int16 = np.int16(full_audio * 32767)
    write(output_wav_path, sample_rate, audio_int16)
    print(f"Archivo WAV generado en: {output_wav_path}")

def guardar_trama_como_wav(trama_bytes, nombre_archivo):
    """
    Guarda una trama (secuencia de bytes) como un archivo .wav,
    codificando cada byte como una frecuencia de audio.
    """
    t = np.linspace(0, byte_duration, int(sample_rate * byte_duration), endpoint=False)
    silencio = np.zeros(int(sample_rate * silence_duration))
    #definir silencio
    t_silence = np.linspace(0, silence_duration, int(sample_rate * silence_duration), False)
    onda_silencio = 0.5 * np.sin(2 * np.pi * silence_freq * t_silence)

    audio = []

    for byte in trama_bytes:
        freq = byte_to_freq(byte)
        onda = 0.5 * np.sin(2 * np.pi * freq * t)
        audio.append(onda)
        audio.append(onda_silencio)

    # Agregar frecuencia EOF al final
    onda_eof = 0.5 * np.sin(2 * np.pi * freq_eof * t)
    audio.append(onda_eof)
    audio.append(onda_silencio)


    audio_signal = np.concatenate(audio)
    audio_int16 = np.int16(audio_signal * 32767)

    write(nombre_archivo, sample_rate, audio_int16)
    print(f"Trama guardada como archivo WAV: {nombre_archivo}")

def obtener_tramas_desde_archivo(file_path, mac_origen_str, mac_destino_str):
    """
    Lee un archivo binario y lo divide en tramas de acuerdo al formato:
    [versión][MAC_origen][MAC_destino][tipo][longitud][payload][checksum]
    Retorna una lista de tramas (listas de bytes).
    """
    lista_tramas = []
    bytes_mac_org = mac_str_to_bytes(mac_origen_str)
    bytes_mac_dest = mac_str_to_bytes(mac_destino_str)
    tipo = tipo_envio_archivo

    with open(file_path, 'rb') as f:
        while True:
            bloque = f.read(107)
            if not bloque:
                break
            trama = crear_trama(version, bytes_mac_org, bytes_mac_dest, tipo, bloque)
            lista_tramas.append(trama)

    return lista_tramas

def guardar_archivo_en_tramas_wav(nombre_archivo, mac_org_str, mac_dest_str):
    """
    Guarda una lista de tramas como archivos WAV individuales,
    cada una representando una trama diferente.
    """
    lista_tramas = obtener_tramas_desde_archivo(nombre_archivo,mac_org_str, mac_dest_str)
    silencio = np.zeros(int(sample_rate * silence_duration))

    for i, trama_bytes in enumerate(lista_tramas):
        nombre_trama = f"{nombre_archivo}_trama_{i+1}.wav"
        guardar_trama_como_wav(trama_bytes, nombre_trama)
    
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
            tramita = escuchar_y_reconstruir_trama()
            imprimir_trama(tramita)
        case "3":
            tramas = obtener_tramas_desde_archivo(ruta, args.mac_origen, args.mac_destino)
            emitir_trama(tramas[0])

    #enviar_ping(args.mac_origen)

    #send_file_as_sound(ruta, args.mac_origen, args.mac_destino)

    #guardar_archivo_en_tramas_wav(ruta, args.mac_origen, args.mac_destino)


if __name__ == '__main__':
    main()