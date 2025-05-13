import cv2
import numpy as np
import json
from tensorflow.keras.models import load_model

class DogBreedDetector:
    def __init__(self, breed_model_path="model/final_model.keras", breed_map_path="model/breed_map.json"):
        self.breed_model = load_model(breed_model_path, compile=False)

        with open(breed_map_path, "r") as f:
            self.breed_map = json.load(f)

    def preprocess_image(self, img, target_size=(350, 350)):
        """Подготовка изображения для Keras-модели"""
        img = cv2.resize(img, target_size)
        img = img / 255.0  # Нормализация
        return np.expand_dims(img, axis=0)

    def predict_breed(self, img_path):
        img = cv2.imread(img_path)
        if img is None:
            return {"error": "Не удалось загрузить изображение"}

        try:
            img_processed = self.preprocess_image(img)
            preds = self.breed_model.predict(img_processed)[0]
            top_class_idx = int(np.argmax(preds))
            confidence = float(preds[top_class_idx] * 100)

            return {
                "breed": self.breed_map.get(str(top_class_idx), "Unknown"),
                "confidence": confidence
            }
        except Exception as e:
            return {"error": f"Ошибка при предсказании: {str(e)}"}
