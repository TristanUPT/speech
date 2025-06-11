
import subprocess
import os
import tempfile
import scipy.io.wavfile as wavfile

class AudioSegment:
    def __init__(self, raw_data: bytes):
        self.raw_data = raw_data

    @classmethod
    def from_file(cls, file_path):
        # Convertim orice fișier audio în WAV PCM 16-bit mono folosind ffmpeg
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp_path = tmp.name

        try:
            subprocess.run([
                "ffmpeg", "-y",
                "-i", file_path,
                "-ac", "1",               # mono
                "-ar", "44100",           # 44.1kHz
                "-f", "wav",
                "-acodec", "pcm_s16le",
                tmp_path
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

            with open(tmp_path, "rb") as f:
                data = f.read()

            return cls(data)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def to_numpy(self):
        # Returnează sample rate și array audio din self.raw_data
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(self.raw_data)
            tmp.flush()
            rate, data = wavfile.read(tmp.name)
        os.remove(tmp.name)
        return rate, data

    @classmethod
    def from_numpy(cls, rate, data):
        import numpy as np
        import tempfile
        import scipy.io.wavfile as wavfile

        # Asigură-te că e PCM 16-bit (int16)
        if data.dtype != np.int16:
            data = np.clip(data, -1.0, 1.0)
            # Normalizează la intervalul [-1, 1]
            data = (data * 32767).astype(np.int16)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            wavfile.write(tmp.name, rate, data)
            tmp.seek(0)
            raw = tmp.read()
        os.remove(tmp.name)
        return cls(raw)

    def export(self, out_f, format="wav"):
        with open(out_f, 'wb') as f:
            f.write(self.raw_data)
