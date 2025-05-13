import os
import secrets

class Config:
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(32))
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}
    MODEL_CONFIG = {
        'yolo_model': 'model/yolov8n.pt',
        'breed_model': 'model/final_model.keras',
        'breed_map': 'model/breed_map.json'
    }