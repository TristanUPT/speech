
import subprocess
import io
import os
import tempfile

class AudioSegment:
    def __init__(self, raw_data: bytes):
        self.raw_data = raw_data

    @classmethod
    def from_file(cls, file_path):
        # Convertim la WAV PCM 16-bit mono cu ffmpeg
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

    def export(self, out_f, format="wav"):
        with open(out_f, 'wb') as f:
            f.write(self.raw_data)
