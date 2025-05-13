from flask import Flask, render_template, request, jsonify, url_for, send_from_directory
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

# Создаем папки, если они не существуют
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

logging.basicConfig(level=logging.DEBUG)

try:
    download_model()
    detector = DogBreedDetector()
except Exception as e:
    raise RuntimeError(f"Model initialization failed: {str(e)}")


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route('/')
def home():
    return render_template('index.html',
                           js_url=url_for('static', filename='main.js'),
                           css_url=url_for('static', filename='styles.css'))


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """GET метод для отдачи загруженных изображений"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/detect', methods=['GET', 'POST'])
def detect():
    if request.method == 'GET':
        # Пример GET запроса - можно вернуть форму или инструкции
        return jsonify({
            'message': 'Send POST request with image file to detect breed',
            'allowed_extensions': app.config['ALLOWED_EXTENSIONS']
        })

    # POST обработка
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

        # Добавляем URL для доступа к изображению
        result['image_url'] = url_for('uploaded_file', filename=filename, _external=True)

        # Не удаляем файл сразу, чтобы можно было получить его по GET
        # os.remove(filepath)

        return jsonify(result)

    except Exception as e:
        app.logger.error(f"Error: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/clear_uploads', methods=['POST'])
def clear_uploads():
    """Очистка папки с загруженными файлами"""
    try:
        for filename in os.listdir(app.config['UPLOAD_FOLDER']):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if os.path.isfile(file_path):
                os.unlink(file_path)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == "__main__":
    app.run(host='0.0.0.0')