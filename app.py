
from flask import Flask, render_template, request, send_from_directory
import os
from werkzeug.utils import secure_filename
from audio_segment import AudioSegment
from audio_effects import reduce_noise, normalize_audio, auto_trim_silence, manual_trim

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
ALLOWED_EXTENSIONS = {'wav', 'mp3'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'audio_file' not in request.files:
        return "Nu ai selectat niciun fișier.", 400

    file = request.files['audio_file']
    if file.filename == '':
        return "Nume fișier invalid.", 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(input_path)

        # Procesare audio
        audio = AudioSegment.from_file(input_path)
        rate, data = audio.to_numpy()

        # Aplică efecte
        data = reduce_noise(data, rate)
        data = normalize_audio(data)
        data = auto_trim_silence(data, rate)

        # Extrage trim manual dacă există
        try:
            start_sec = float(request.form.get('start_sec', 0))
        except ValueError:
            start_sec = 0.0
        try:
            end_sec = float(request.form.get('end_sec')) if request.form.get('end_sec') else None
        except ValueError:
            end_sec = None

        data = manual_trim(data, rate, start_sec=start_sec, end_sec=end_sec)

        # Reconstruim fișierul audio
        audio = AudioSegment.from_numpy(rate, data)

        # Salvăm rezultatul
        base_name = filename.rsplit('.', 1)[0]
        output_filename = base_name + "_processed.wav"
        output_path = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)
        audio.export(output_path, format="wav")

        return render_template('result.html', original=filename, processed=output_filename)

    else:
        return "Format fișier neacceptat. Doar .wav sau .mp3.", 400

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['PROCESSED_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
