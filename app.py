from flask import Flask, render_template, request, jsonify, url_for
import os
from werkzeug.utils import secure_filename
from config import Config
from model.DogBreedDetector import DogBreedDetector
import logging
import gdown
def download_model():
    model_path = "model/final_model.keras"
    if not os.path.exists(model_path):
        print("📥 Скачивание модели из Google Drive...")
        file_id = "1CpLyj-vzXyA8WhStQHRib-lbBVgS0Yn_"
        url = f"https://drive.google.com/uc?id={file_id}"
        os.makedirs("model", exist_ok=True)
        gdown.download(url, model_path, quiet=False)
    else:
        print("✅ Модель уже загружена.")


app = Flask(__name__)
app.config.from_object(Config)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
logging.basicConfig(level=logging.DEBUG)



try:
    download_model()
    detector = DogBreedDetector()
except Exception as e:
    raise RuntimeError(f"Model initialization failed: {str(e)}")

def allowed_file(filename):
    """Проверяет, что файл имеет допустимое расширение"""
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def home():
    return render_template('index.html',
                          js_url=url_for('static', filename='main.js'),
                          css_url=url_for('static', filename='styles.css'))

@app.route('/detect', methods=['POST'])
def detect():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type'}), 400

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        if not os.path.exists(filepath):
            return jsonify({'error': 'File save failed'}), 500

        result = detector.predict_breed(filepath)
        os.remove(filepath)

        return jsonify(result)

    except Exception as e:
        app.logger.error(f"Error: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0')