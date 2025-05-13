from flask import Flask, render_template, request, jsonify, send_from_directory, url_for
import os
from flask_cors import CORS
from werkzeug.utils import secure_filename
from config import Config
from model.DogBreedDetector import DogBreedDetector
import logging
import gdown
import tempfile
import requests
from io import BytesIO
from PIL import Image

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
app.config.from_object(Config)  # Включение CORS

# Используем временную папку на Render
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True) # Создаем папку, если она не существует
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = {'jpg', 'jpeg', 'png'}  # Расширения для проверки
CORS(app)
logging.basicConfig(level=logging.DEBUG)

try:
    download_model()
    detector = DogBreedDetector()
except Exception as e:
    raise RuntimeError(f"Model initialization failed: {str(e)}")

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def download_image_from_url(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; DogBreedClassifier/1.0; +https://your-site.com)"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return Image.open(BytesIO(response.content))
    except Exception as e:
        raise ValueError(f"Ошибка загрузки изображения: {str(e)}")


@app.route('/')
def home():
    return render_template('index.html', js_url=url_for('static', filename='main.js'), css_url=url_for('static', filename='styles.css'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/detect', methods=['POST'])
def detect():
    print("📥 detect вызван")

    try:
        # проверка типа
        print(f"Content-Type: {request.content_type}")
        if request.content_type == 'application/json':
            data = request.get_json()
            if 'image_url' not in data:
                return jsonify({'error': 'No URL provided'}), 400

            img = download_image_from_url(data['image_url'])
            filename = secure_filename(os.path.basename(data['image_url'])[:255]) or 'uploaded_image.jpg'
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            img.save(filepath)

        # Обработка файла из формы
        elif 'file' in request.files:
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'No selected file'}), 400

            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

        else:
            return jsonify({'error': 'No image provided'}), 400

        # Общая обработка
        result = detector.predict_breed(filepath)
        result['image_url'] = url_for('uploaded_file', filename=filename, _external=True)

        return jsonify(result)

    except Exception as e:
        app.logger.error(f"Error: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/proxy_image', methods=['POST'])
def proxy_image():
    try:
        data = request.get_json()
        image_url = data['image_url']
        response = requests.get(image_url)
        response.raise_for_status()  # Check if the request was successful
        return (response.content, 200, {'Content-Type': response.headers['Content-Type']})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/clear_uploads', methods=['POST'])
def clear_uploads():
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
