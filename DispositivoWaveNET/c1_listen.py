from c1_shared  import *

def detectar_frecuencia(audio, sample_rate):
    fft = np.fft.fft(audio)
    freqs = np.fft.fftfreq(len(audio), 1/sample_rate)
    magnitudes = np.abs(fft)
    peak_idx = np.argmax(magnitudes[:len(magnitudes)//2])
    return abs(freqs[peak_idx])

def escuchar_y_retornar_trama():
    bytes_recibidos = []
    print("Escuchando... (esperando datos hasta EOF 7000 Hz)")

    expect_silence = True
    heard_ping = False

    while True:
        # Leer bloque de audio del tamaño de un byte
        duracion_muestra = int(SAMPLE_RATE * (BYTE_DURATION-0.06))
        audio = sd.rec(duracion_muestra, samplerate=SAMPLE_RATE, channels=1, dtype='float64')
        sd.wait()

        audio = audio.flatten()
        freq = detectar_frecuencia(audio, SAMPLE_RATE)
        
        if (not heard_ping):
            if (abs(freq - PING_FREQ) < 10):
                heard_ping = True
                print("Escuche el ping")
            continue

        if abs(freq - FREQ_EOF) < 10:  # Frecuencia EOF detectada
            print("EOF detectado.")
            break

        byte = freq_to_byte(freq)
        if byte is not None:
            if (expect_silence):
                continue
            #print(f"Frecuencia detectada: {freq:.1f} Hz → Byte: {byte} | ASCII: {chr(byte) if 32 <= byte<= 126 else 'No printable character'}")
            bytes_recibidos.append(byte)
            expect_silence = True
        else:
            expect_silence = False
            #print(f"Frecuencia fuera de rango: {freq:.1f} Hz")

    print(bytes_recibidos)
    return bytes_recibidos