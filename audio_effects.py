
import numpy as np
import noisereduce as nr
import scipy.io.wavfile as wavfile
from scipy.fft import rfft, irfft, rfftfreq


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

def apply_gate(audio_data, threshold_db=-35.0):
    """
    Înlocuiește cu zero toate valorile sub pragul în dB.
    """
    # Convertim dB în amplitudine (0–1)
    threshold = 10 ** (threshold_db / 20.0)
    gated = np.copy(audio_data)

    gated[np.abs(audio_data) < threshold] = 0.0
    return gated
"""
def apply_eq(data, sample_rate, preset):
    print("apply_eq called with preset:", preset)
    return data
"""
def apply_eq(audio_data, sample_rate=44100, preset="flat"):
    import numpy as np
    from scipy.fft import rfft, irfft, rfftfreq

    presets = {
        "flat":     [1, 1, 1, 1, 1, 1, 1],
        "vocal":    [0.8, 0.9, 1, 1.2, 1.3, 1.2, 1.1],
        "broadcast": [0.7, 0.8, 1, 1.1, 1.2, 1.2, 1.3]
    }
    gains = presets.get(preset.lower(), presets["flat"])

    # Convert int16 input to float in range [-1, 1]
    if audio_data.dtype == np.int16:
        audio_data = audio_data.astype(np.float32) / 32768.0

    freqs = rfftfreq(len(audio_data), d=1/sample_rate)
    spectrum = rfft(audio_data)

    bands = [60, 170, 310, 600, 1000, 3000, 6000, sample_rate//2]

    for i in range(7):
        band_start = bands[i]
        band_end = bands[i+1]
        idx = np.where((freqs >= band_start) & (freqs < band_end))[0]
        spectrum[idx] *= gains[i]

    processed = irfft(spectrum)
    processed = np.clip(processed, -1.0, 1.0)

    # Return float, let the main pipeline convert to int16 if needed
    return processed