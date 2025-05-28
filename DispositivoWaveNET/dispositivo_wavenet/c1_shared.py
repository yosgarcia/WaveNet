import os
import numpy as np
from scipy.io.wavfile import write
import sounddevice as sd
import argparse
import zlib
import time
import logging

# ------------------------------------------------------------------------------------------------------------
# Parte de parametros globales
# ------------------------------------------------------------------------------------------------------------

# Audio
SAMPLE_RATE = 44100           # Hz
BYTE_DURATION = 0.18*3/2       # Segundos
SILENCE_DURATION = 0.36       # Segundos
BASE_FREQ = 350               # Frecuencia para byte 0
SILENCE_FREQ = 200
FREQ_STEP = 50

# silencio freq 20
# frecuencia base 440

# Tipos de tramas
TIPO_PING = 0x01
TIPO_TRAMA_ARCHIVO_INFO = 0x02
TIPO_TRAMA_ARCHIVO = 0x03
TIPO_TRAMA_FINAL_ARCHIVO = 0x04
TIPO_ERROR = 0x05
TIPO_OK = 0x06

# Protocolo
VERSION = 1

TIME_TO_SAY_OK = 10
TIMES_TO_COMUNICATE_OK = 3

TIME_TO_SAY_128_BYTES = 113
TIMES_TO_COMUNICATE_128_BYTES = 3

# Frecuencias especiales
PING_FREQ = 250
FREQ_EOF = 300


# ------------------------------------------------------------------------------------------------------------
# Parte de la clase Trama
# ------------------------------------------------------------------------------------------------------------


"""
    Formato trama:
    [versión][MAC_org][MAC_dest][tipo][longitud][payload][checksum][eof]
"""

class Trama:
    """
    Clase para representar la estructura de las tramas que se van a enviar
    """
    def __init__(self, bytes_trama=None, version=None, mac_origen=None, mac_destino=None, tipo=None, payload=None):
        """
        Constructor de la clase que construye las partes de la trama

        @param bytes_trama Son los bytes que forman parte de la trama
        @param version Version del protocolo que se está usando
        @param mac_origen MAC address del origen de la trama
        @param mac_destino MAC address del destino de la trama
        @param tipo Indica el tipo de trama que se esta enviando
        @param payload Cuerpo del mensaje a transmitir
        """
        if bytes_trama:
            self.bytes_trama = bytearray(bytes_trama)
            self._parse()
        else:
            if None in (version, mac_origen, mac_destino, tipo, payload):
                raise ValueError("Faltan argumentos para crear la trama")
            self.version = version
            self.mac_origen = mac_origen
            self.mac_destino = mac_destino
            self.tipo = tipo
            self.payload = payload
            self.length = len(payload)
            self._build()

    def _parse(self):
        """
        Función para separar los bytes de la trama en los diferentes headers y cuerpo del mensaje
        """
        if len(self.bytes_trama) < 15:
            raise ValueError("Trama muy corta")

        self.version = self.bytes_trama[0]
        self.mac_origen = self.bytes_trama[1:7]
        self.mac_destino = self.bytes_trama[7:13]
        self.tipo = self.bytes_trama[13]
        self.length = self.bytes_trama[14]

        if len(self.bytes_trama) < 15 + self.length + 4:
            raise ValueError("La trama no contiene suficiente longitud según el campo 'length'")

        self.payload = self.bytes_trama[15:15+self.length]
        self.checksum = self.bytes_trama[15+self.length:15+self.length+4]

    def _build(self):
        """
        Función para construir la trama con su checksum
        """
        header = bytearray([self.version]) + self.mac_origen + self.mac_destino + bytearray([self.tipo, self.length])
        self.checksum = calcular_checksum(header + self.payload)
        self.bytes_trama = header + self.payload + self.checksum

    def get_bytes(self):
        """
        Getter para obtener los bytes de la trama
        """
        return bytes(self.bytes_trama)

    def get_checksum_valido(self):
        """
        Verificar el checksum dado en la trama sea valido
        """
        
        header_y_payload = self.bytes_trama[:15 + self.length]
        return self.checksum == calcular_checksum(header_y_payload)

    def imprimir(self):
        """
        Imprimir la trama
        """
        def mac_to_str(mac_bytes):
            return ':'.join(f'{b:02x}' for b in mac_bytes)

        logging.info("----- TRAMA -----")
        logging.info(f"Versión     : {self.version}")
        logging.info(f"MAC Origen  : {mac_to_str(self.mac_origen)}")
        logging.info(f"MAC Destino : {mac_to_str(self.mac_destino)}")
        logging.info(f"Tipo        : {self.tipo}")
        logging.info(f"Longitud    : {self.length}")
        logging.info(f"Payload     : {self.payload}")
        logging.info(f"Checksum    : {self.checksum.hex()}")
        logging.info(f"Checksum válido: {self.get_checksum_valido()}")
        logging.info("-----------------")


def byte_to_freq(byte):
    """
    Convierte un byte (0-255) a una frecuencia.
    """
    return BASE_FREQ + byte * FREQ_STEP

def freq_to_byte(freq):
    """
    @brief Convierte una frecuencia a un byte (0–255) si es válida y cercana a la ideal.
    @param freq Frecuencia en Hz.
    @return Byte correspondiente o None si no es válido.
    """
    byte = int(round((freq - BASE_FREQ) / FREQ_STEP))
    if 0 <= byte <= 255:
        freq_calc = BASE_FREQ + byte * FREQ_STEP
        if abs(freq - freq_calc) < (FREQ_STEP / 2):  # más tolerancia
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
    
def calcular_checksum(trama):
    """
    @brief Calcula el checksum CRC32 de una trama.

    @param trama Bytes de la trama sobre los que se calcula el checksum (bytes o bytearray).

    @return Checksum de 4 bytes en orden big-endian.
    """
    checksum = zlib.crc32(trama)
    return checksum.to_bytes(4, byteorder='big')

def crear_trama(version, bytes_mac_org, bytes_mac_dest, tipo, cur_payload):
    """
    @brief Crea una trama con el formato: [version][MAC_org][MAC_dest][tipo][length][payload][checksum].

    @param version Versión del protocolo (byte).
    @param bytes_mac_org Dirección MAC de origen (bytes).
    @param bytes_mac_dest Dirección MAC de destino (bytes).
    @param tipo Tipo de trama (int o byte).
    @param cur_payload Carga útil (payload) de la trama (bytes).

    @return Trama construida.
    """
    trama = Trama(version=version,
                  mac_origen=bytes_mac_org,
                  mac_destino=bytes_mac_dest,
                  tipo=tipo,
                  payload=cur_payload)
    return trama

def crear_trama_archivo_info(bytes_mac_org, bytes_mac_dest, cantidad_tramas, nombre_archivo):
    """
    @brief Crea una trama de tipo archivo info con cantidad de tramas y nombre de archivo.
    El payload tiene 4 bytes del checksum, y el resto del nombre del archivo
    
    @param bytes_mac_org Dirección MAC de origen (bytes).
    @param bytes_mac_dest Dirección MAC de destino (bytes).
    @param cantidad_tramas Número total de tramas del archivo (int).
    @param nombre_archivo Nombre del archivo (str).
    
    @return Trama con el payload codificado.
     
    """
    payload_cant = cantidad_tramas.to_bytes(4, byteorder='big')
    payload_nombre = nombre_archivo.encode('utf-8')  # convierte string a bytes
    payload = payload_cant + payload_nombre

    return crear_trama(
        version=VERSION,
        bytes_mac_org=bytes_mac_org,
        bytes_mac_dest=bytes_mac_dest,
        tipo=TIPO_TRAMA_ARCHIVO_INFO,
        cur_payload=payload
    )

def decodificar_payload_archivo_info(payload: bytes):
    """
    @brief Decodifica el payload de una trama de tipo ARCHIVO_INFO.

    @param payload Bytes que contienen los datos del payload. Los primeros 4 bytes representan la cantidad de tramas, el resto es el nombre del archivo.

    @return Una tupla (cantidad_tramas, nombre_archivo), donde:
        - cantidad_tramas (int): Número total de tramas que se esperan.
        - nombre_archivo (str): Nombre del archivo transmitido.
    """
    # Extraer los primeros 4 bytes para la cantidad de tramas
    cantidad_tramas = int.from_bytes(payload[:4], byteorder='big')

    # El resto es el nombre del archivo
    nombre_archivo = payload[4:].decode('utf-8')

    return cantidad_tramas, nombre_archivo

def verificar_datos_esperados(trama: Trama, tipo_esperado, org_esperado, dst_esperado):
    """
    @brief Verifica si una trama tiene los datos esperados.

    @param trama Trama a verificar.
    @param tipo_esperado Tipo de trama esperado.
    @param org_esperado Dirección MAC de origen esperada (6 bytes).
    @param dst_esperado Dirección MAC de destino esperada (6 bytes).

    @return True si todos los valores coinciden, False en caso contrario.
    """
    if (trama.tipo == tipo_esperado and trama.mac_origen == org_esperado and trama.mac_destino == dst_esperado):
        return True
    return False

def crear_trama_ok(bytes_mac_org, bytes_mac_dest, bytes_checksum_received):
    """
    @brief Crea una trama OK con un checksum como payload.
    @param bytes_mac_org Dirección MAC de origen (6 bytes).
    @param bytes_mac_dest Dirección MAC de destino (6 bytes).
    @param bytes_checksum_received Checksum recibido en bytes (4 bytes).
    @return Trama codificada con tipo OK.
    """
    return crear_trama(
        version=VERSION,
        bytes_mac_org=bytes_mac_org,
        bytes_mac_dest=bytes_mac_dest,
        tipo=TIPO_OK,
        cur_payload=bytes_checksum_received  # debe ser un bytearray o bytes de 4 bytes
    )

# ------------------------------------------------------------------------------------------------------------
# Parte de soniditos
# ------------------------------------------------------------------------------------------------------------

def detectar_frecuencia(audio, sample_rate):
    """
    @brief Detecta la frecuencia dominante en una señal de audio.

    @param audio Arreglo NumPy unidimensional con muestras de audio.
    @param sample_rate Frecuencia de muestreo del audio en Hz.

    @return Frecuencia dominante detectada en Hz (float).
    """
    fft = np.fft.fft(audio)
    freqs = np.fft.fftfreq(len(audio), 1/sample_rate)
    magnitudes = np.abs(fft)
    peak_idx = np.argmax(magnitudes[:len(magnitudes)//2])
    return abs(freqs[peak_idx])

def escuchar_y_retornar_trama(timeout):
    """
    Escucha frecuencias de audio y reconstruye una trama por un tiempo determinado
    Si escucha un ping inicial, el conteo de tiempo se reinicia
    @param timeout Tiempo en segundos que va a tardar para escuchar la trama.
    @return Trama correspondiente escuchada, que puede ser incorrecta.

    """
    bytes_recibidos = []
    logging.info("Escuchando... (esperando datos hasta EOF 7000 Hz)")

    expect_silence = True
    heard_ping = False
    start_time = time.time()

    while True:

        # Verificar si se superó el timeout
        if (time.time() - start_time > timeout):
            logging.info("Timeout alcanzado. Terminando escucha.")
            break
            
        duracion_muestra = int(SAMPLE_RATE * (BYTE_DURATION-0.08))
        audio = sd.rec(duracion_muestra, samplerate=SAMPLE_RATE, channels=1, dtype='float64')
        sd.wait()

        audio = audio.flatten()
        freq = detectar_frecuencia(audio, SAMPLE_RATE)
        
        if (not heard_ping):
            if (abs(freq - PING_FREQ) < 10):
                heard_ping = True
                logging.info("Escuche el ping")
                start_time = time.time() # Reset start time
            continue

        if abs(freq - FREQ_EOF) < 10:  # Frecuencia EOF detectada
            logging.info("EOF detectado.")
            break

        byte = freq_to_byte(freq)
        if byte is not None:
            if (expect_silence):
                logging.info(f"?------------?")
                continue
            logging.info(f"BYTE <- {byte}")
            bytes_recibidos.append(byte)
            expect_silence = True
        else:
            expect_silence = False
            logging.info(f"--------------")

    logging.info(f"{bytes_recibidos}")
    trama = Trama(bytes_trama=bytes_recibidos)
    return trama

def escuchar_ping(timeout):
    """
    Escucha un sonido de ping durante un tiempo determinado.
    @return False si no se escucha un ping, True si sí se escucha
    """
    bytes_recibidos = []
    logging.info("Escuchando ping... (esperando datos hasta EOF 7000 Hz)")

    heard_ping = False
    start_time = time.time()

    while True:
        # Verificar si se superó el timeout
        if time.time() - start_time > timeout:
            logging.info("Timeout alcanzado. Terminando escucha.")
            return False

        # Leer bloque de audio del tamaño de un byte
        duracion_muestra = int(SAMPLE_RATE * (BYTE_DURATION-0.08))
        audio = sd.rec(duracion_muestra, samplerate=SAMPLE_RATE, channels=1, dtype='float64')
        sd.wait()

        audio = audio.flatten()
        freq = detectar_frecuencia(audio, SAMPLE_RATE)
        
        if (abs(freq - PING_FREQ) < 10):
            logging.info("Escuche el ping")
            return True

def transmite_freq(freq, duration=BYTE_DURATION):
    """
    Reproduce una frecuencia de audio por cierta duración.
    """
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
    tono = 0.5 * np.sin(2 * np.pi * freq * t)
    tono = tono*1.95
    tono = np.clip(tono, -1.0, 1.0)
    sd.play(tono, samplerate=SAMPLE_RATE)
    sd.wait()

def transmitir_silencio(freq = SILENCE_FREQ, duration=SILENCE_DURATION):
    """
    Reproduce una frecuencia de silencio para separación entre bytes.
    """
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
    tono = 0.5 * np.sin(2 * np.pi * freq * t)
    tono = tono*1.95
    tono = np.clip(tono, -1.0, 1.0)
    sd.play(tono, samplerate=SAMPLE_RATE)
    sd.wait()

def ejecutar_ping():
    """
    Ejecuta un ping
    """
    time.sleep(2)
    transmite_freq(PING_FREQ, duration=BYTE_DURATION*2)
    #transmitir_silencio()

def emitir_trama(trama):
    """
    Transmite una trama byte por byte como audio.
    Para iniciar la transmicion, empieza con un ping, seguido de un silencio
    """
    transmite_freq(PING_FREQ, duration=BYTE_DURATION*2)
    transmitir_silencio()

    for byte in trama.bytes_trama:
        freq = byte_to_freq(byte)
        logging.info(f"Enviando byte {byte} -> {freq:.1f} Hz")
        transmite_freq(freq)
        transmitir_silencio()
    
    transmite_freq(FREQ_EOF, duration=BYTE_DURATION*2)
    #transmitir_silencio()
    logging.info("Trama transmitida.")
        
# ------------------------------------------------------------------------------------------------------------
# Parte de la clase Pruebas
# ------------------------------------------------------------------------------------------------------------

def guardar_trama_como_wav(trama, nombre_archivo):
    """
    Guarda una trama (secuencia de bytes) como un archivo .wav,
    codificando cada byte como una frecuencia de audio.
    """
    t = np.linspace(0, BYTE_DURATION, int(SAMPLE_RATE * BYTE_DURATION), endpoint=False)
    t_silence = np.linspace(0, SILENCE_DURATION, int(SAMPLE_RATE * SILENCE_DURATION), False)

    onda_silencio = 0.5 * np.sin(2 * np.pi * SILENCE_FREQ * t_silence)
    onda_ping = 0.5 * np.sin(2 * np.pi * PING_FREQ * t_silence)

    audio = []
    audio.append(onda_ping)
    audio.append(onda_silencio)
    
    for byte in trama.bytes_trama:
        freq = byte_to_freq(byte)
        onda = 0.5 * np.sin(2 * np.pi * freq * t)
        audio.append(onda)
        audio.append(onda_silencio)

    # Agregar frecuencia EOF al final
    onda_eof = 0.5 * np.sin(2 * np.pi * FREQ_EOF * t)
    audio.append(onda_eof)
    audio.append(onda_silencio)

    audio_signal = np.concatenate(audio)
    audio_int16 = np.int16(audio_signal * 32767)

    write(nombre_archivo, SAMPLE_RATE, audio_int16)
    trama.imprimir()
    logging.info(f"Trama guardada como archivo WAV: {nombre_archivo}")

def obtener_tramas_desde_archivo(file_path, mac_origen_str, mac_destino_str):
    """
    Lee un archivo binario y lo divide en tramas de acuerdo al formato:
    [versión][MAC_origen][MAC_destino][tipo][longitud][payload][checksum]
    Retorna una lista de tramas (listas de bytes).
    """
    lista_tramas = []
    bytes_mac_org = mac_str_to_bytes(mac_origen_str)
    bytes_mac_dest = mac_str_to_bytes(mac_destino_str)
    tipo = TIPO_TRAMA_ARCHIVO

    with open(file_path, 'rb') as f:
        while True:
            bloque = f.read(107)
            if not bloque:
                break
            trama = crear_trama(VERSION, bytes_mac_org, bytes_mac_dest, tipo, bloque)
            lista_tramas.append(trama)

    return lista_tramas

def obtener_tramas_desde_string(string, mac_origen_str, mac_destino_str):
    """
    Lee un string y lo divide en tramas de acuerdo al formato:
    [versión][MAC_origen][MAC_destino][tipo][longitud][payload][checksum]
    Retorna una lista de tramas (listas de bytes).
    """
    lista_tramas = []
    bytes_mac_org = mac_str_to_bytes(mac_origen_str)
    bytes_mac_dest = mac_str_to_bytes(mac_destino_str)
    tipo = TIPO_TRAMA_ARCHIVO

    # Asegúrate de que el string sea bytes (por si acaso)
    if isinstance(string, str): string = string.encode()

    for i in range(0, len(string), 107):
        bloque = string[i:i+107]
        trama = crear_trama(VERSION, bytes_mac_org, bytes_mac_dest, tipo, bloque)
        lista_tramas.append(trama)

    return lista_tramas

def guardar_archivo_en_tramas_wav(nombre_archivo, mac_org_str, mac_dest_str):
    """
    Guarda una lista de tramas como archivos WAV individuales,
    cada una representando una trama diferente.
    """
    lista_tramas = obtener_tramas_desde_archivo(nombre_archivo,mac_org_str, mac_dest_str)
    silencio = np.zeros(int(SAMPLE_RATE * SILENCE_DURATION))

    for i, trama in enumerate(lista_tramas):
        nombre_trama = f"{nombre_archivo}_trama_{i+1}.wav"
        guardar_trama_como_wav(trama, nombre_trama)
