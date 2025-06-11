
from flask import Flask, render_template, request, send_from_directory, url_for
import os
from werkzeug.utils import secure_filename
from shutil import copyfile
from audio_segment import AudioSegment
from audio_effects import reduce_noise, normalize_audio, auto_trim_silence, manual_trim, compress_audio, apply_gate, apply_eq

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
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
        
        effects_selected = (
            'use_reduce_noise' in request.form or
            'use_normalize' in request.form or
            'use_auto_trim' in request.form or
            'use_compressor' in request.form or
            'use_gate' in request.form or
            'use_eq' in request.form
        )
        if not effects_selected:
            error_message = "Please select at least one effect."
            return render_template(
                'result.html',
                error=error_message,
                original=filename,
                processed=None
            )
        
        # Procesare audio
        audio = AudioSegment.from_file(input_path)
        rate, data = audio.to_numpy()
        audio_duration_sec = len(data) / rate
        
        try:
            threshold_db = float(request.form.get('threshold_db', -20.0))
        except (TypeError, ValueError):
            threshold_db = -20.0
        try:
            ratio = float(request.form.get('ratio', 4.0))
        except (TypeError, ValueError):
            ratio = 4.0
            
        if 'use_reduce_noise' in request.form:
            print(f"Reducere zgomot activată, rate: {rate}")
            data = reduce_noise(data, rate)
        else:
            print("Reducere zgomot nu este activată.")
        if 'use_normalize' in request.form:
            print("Normalizare activată.")
            data = normalize_audio(data)
        else:
            print("Normalizare nu este activată.")
        if 'use_auto_trim' in request.form:
            print("Auto-trim activat.")
            data = auto_trim_silence(data, rate)
        else:
            print("Auto-trim nu este activat.")

        use_compressor = 'use_compressor' in request.form
        print(f"Compressor activat: {use_compressor}, threshold_db: {threshold_db}, ratio: {ratio}")
        # Aplică compresor dacă este activat
        if use_compressor:
            data = compress_audio(data, threshold_db=threshold_db, ratio=ratio)
            #data = compress_audio(data, threshold_db=threshold_db, ratio=ratio)
            
        data = compress_audio(data, threshold_db=-20.0, ratio=4.0)
        try:
            gate_threshold_db = float(request.form.get('gate_threshold_db', -35.0))
        except (TypeError, ValueError):
            gate_threshold_db = -35.0
        use_gate = 'use_gate' in request.form
        print(f"Gate activat: {use_gate}, gate_threshold_db: {gate_threshold_db}")
        if use_gate:
            data = apply_gate(data, threshold_db=gate_threshold_db)

        # ...after gate logic...
        use_eq = 'use_eq' in request.form
        if use_eq:
            eq_preset = request.form.get('eq_preset', 'flat')
            print(f"EQ preset selectat: {eq_preset}")
            data = apply_eq(data, sample_rate=rate, preset=eq_preset)
            print("EQ output min/max:", data.min(), data.max(), "dtype:", data.dtype)
        else:
            print("EQ nu este activat.")
# ...continue with print('Durată audio (sec):', audio_duration_sec)...

        print('Durată audio (sec):', audio_duration_sec)
        print('Dimensiune date audio:', data.shape)

        # Extrage și validează trim manual
        error_message = None
        try:
            start_sec = float(request.form.get('start_sec', 0))
        except ValueError:
            start_sec = 0.0
        try:
            end_sec_raw = request.form.get('end_sec')
            end_sec = float(end_sec_raw) if end_sec_raw else None
        except ValueError:
            end_sec = None

        if start_sec < 0 or (end_sec is not None and (end_sec < 0 or end_sec > audio_duration_sec or start_sec >= end_sec)):
            error_message = "Intervalul de trim este invalid. Te rugăm să alegi un interval valid în secunde."

        if error_message:
            return render_template(
                'result.html',
                error=error_message,
                original=filename,
                processed=None
            )
        print(f"Start sec: {start_sec}, End sec: {end_sec}")
        # Aplică trim manual
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
