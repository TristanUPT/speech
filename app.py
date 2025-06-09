from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import os
from werkzeug.utils import secure_filename
from audio_segment import AudioSegment



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

        # Procesare dummy: încărcăm fișierul cu pydub și îl salvăm în formatul opus
        ext = filename.rsplit('.', 1)[1].lower()
        base_name = filename.rsplit('.', 1)[0]

        audio = AudioSegment.from_file(input_path)
        output_filename = base_name + ('.mp3' if ext == 'wav' else '.wav')
        output_path = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)
        audio.export(output_path, format=output_filename.rsplit('.', 1)[1])

        return render_template('result.html', original=filename, processed=output_filename)

    else:
        return "Format fișier neacceptat.", 400

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['PROCESSED_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
