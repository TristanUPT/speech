
import numpy as np
import noisereduce as nr
import scipy.io.wavfile as wavfile

def reduce_noise(audio_data, sample_rate=44100):
    # Reduce zgomotul folosind noisereduce
    reduced = nr.reduce_noise(y=audio_data, sr=sample_rate)
    return reduced

def normalize_audio(audio_data):
    # Normalizează volumul la amplitudinea maximă
    peak = np.max(np.abs(audio_data))
    if peak == 0:
        return audio_data
    return audio_data / peak

def auto_trim_silence(audio_data, sample_rate=44100, threshold_db=-35, padding_ms=300):
    # Transformă pragul dB într-o valoare între 0-1
    threshold = 10 ** (threshold_db / 20.0)
    abs_audio = np.abs(audio_data)

    # Găsește indici unde semnalul este peste prag
    above_thresh = np.where(abs_audio > threshold)[0]

    if len(above_thresh) == 0:
        return audio_data  # nimic de păstrat

    start_index = max(0, above_thresh[0] - int(padding_ms * sample_rate / 1000))
    end_index = min(len(audio_data), above_thresh[-1] + int(padding_ms * sample_rate / 1000))
    

    return audio_data[start_index:end_index]

def manual_trim(audio_data, sample_rate=44100, start_sec=0, end_sec=None):
    start_index = int(start_sec * sample_rate)
    end_index = int(end_sec * sample_rate) if end_sec else len(audio_data)
    
    return audio_data[start_index:end_index]

def compress_audio(audio_data, threshold_db=-20.0, ratio=4.0):
    """
    Aplică o compresie dinamică simplă asupra semnalului.
    threshold_db: pragul peste care se aplică compresia (ex: -20 dB)
    ratio: raportul de compresie (ex: 4.0 = 4:1)
    """
    threshold = 10 ** (threshold_db / 20.0)  # convertim dB în amplitudine (0–1)
    compressed = np.copy(audio_data)

    above_threshold = np.abs(audio_data) > threshold
    compressed[above_threshold] = np.sign(audio_data[above_threshold]) * (
        threshold + (np.abs(audio_data[above_threshold]) - threshold) / ratio
    )

    return compressed
