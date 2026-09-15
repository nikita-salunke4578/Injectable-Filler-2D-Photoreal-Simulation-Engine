import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
import os

class FaceDetector:
    def __init__(self):
        # We assume the model is downloaded in app/common/face_landmarker.task
        model_path = os.path.join(os.path.dirname(__file__), 'face_landmarker.task')
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found at {model_path}")
            
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            output_face_blendshapes=False,
            output_facial_transformation_matrixes=False,
            num_faces=1
        )
        self.detector = vision.FaceLandmarker.create_from_options(options)

    def get_landmarks(self, img: np.ndarray) -> np.ndarray:
        """
        Returns a (478, 2) numpy array of face landmarks (x, y) in pixel coordinates.
        If no face is found, raises a ValueError.
        """
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)
        
        detection_result = self.detector.detect(mp_image)
        
        if not detection_result.face_landmarks:
            raise ValueError("No face detected in the image.")
            
        h, w = img.shape[:2]
        landmarks = detection_result.face_landmarks[0]
        
        # Convert normalized coordinates to pixel coordinates
        pts = np.array([(int(lm.x * w), int(lm.y * h)) for lm in landmarks])
        return pts
