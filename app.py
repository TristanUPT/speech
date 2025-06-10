
from flask import Flask, render_template, request, send_from_directory, url_for
import os
from werkzeug.utils import secure_filename
from shutil import copyfile
from audio_segment import AudioSegment
from audio_effects import reduce_noise, normalize_audio, auto_trim_silence, manual_trim

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
STATIC_ORIGINALS = 'static/originals'
STATIC_PROCESSED = 'static/processed'
ALLOWED_EXTENSIONS = {'wav', 'mp3'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)
os.makedirs(STATIC_ORIGINALS, exist_ok=True)
os.makedirs(STATIC_PROCESSED, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower().lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'audio_file' not in request.files:
        return "Nu ai selectat niciun fișier.", 400

    file = request.files['audio_file']
    print('Fișier primit:', file.filename)
    print('Extensie validă:', allowed_file(file.filename))
    if file.filename == '':
        return "Nume fișier invalid.", 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(input_path)

        # Procesare audio
        audio = AudioSegment.from_file(input_path)
        rate, data = audio.to_numpy()

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
        audio = AudioSegment.from_numpy(rate, data)

        # Salvare în static pentru previzualizare
        base_name = filename.rsplit('.', 1)[0]
        output_filename = base_name + "_processed.wav"
        output_path = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)

        static_original_path = os.path.join(STATIC_ORIGINALS, filename)
        static_processed_path = os.path.join(STATIC_PROCESSED, output_filename)

        copyfile(input_path, static_original_path)
        audio.export(static_processed_path, format="wav")

        return render_template(
            'result.html',
            original=filename,
            processed=output_filename,
            original_path=static_original_path,
            processed_path=static_processed_path
        )

    else:
        return "Format fișier neacceptat. Doar .wav sau .mp3.", 400

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(STATIC_PROCESSED, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
