from flask import Flask, render_template, request, jsonify, send_from_directory, url_for
import os
from flask_cors import CORS
from werkzeug.utils import secure_filename
from model.DogBreedDetector import DogBreedDetector
import logging
import requests
from io import BytesIO
from PIL import Image
import tempfile
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
app.config['UPLOAD_FOLDER'] = os.path.join(tempfile.gettempdir(), 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
CORS(app)
logging.basicConfig(level=logging.DEBUG)

download_model()
detector = DogBreedDetector()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ['jpg', 'jpeg', 'png']

def download_image_from_url(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Проверка успешности загрузки
        img = Image.open(BytesIO(response.content))
        return img
    except Exception as e:
        raise ValueError(f"Ошибка загрузки изображения: {str(e)}")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/detect', methods=['POST'])
def detect():
    try:
        # Обработка URL изображения
        if request.content_type == 'application/json':
            data = request.get_json()
            if 'image_url' not in data:
                return jsonify({'error': 'No URL provided'}), 400
            img = download_image_from_url(data['image_url'])
            filename = secure_filename(os.path.basename(data['image_url'])[:255]) or 'uploaded_image.jpg'
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            img.save(filepath)

        # Обработка изображения из формы
        elif 'file' in request.files:
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'No selected file'}), 400
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
        else:
            return jsonify({'error': 'No image provided'}), 400

        # Общая обработка изображения
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
        # Скачивание изображения по URL
        img = download_image_from_url(image_url)
        filename = secure_filename(os.path.basename(image_url)) or 'image.jpg'
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        img.save(filepath)
        return jsonify({'image_url': url_for('uploaded_file', filename=filename, _external=True)})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0')
