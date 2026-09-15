import base64
import cv2
import numpy as np

def decode_image_base64(b64_str: str) -> np.ndarray:
    """Decodes a base64 image (with or without data URI prefix) into a cv2 BGR image."""
    if "," in b64_str:
        b64_str = b64_str.split(",")[1]
    
    img_data = base64.b64decode(b64_str)
    np_arr = np.frombuffer(img_data, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not decode image.")
    return img

def encode_image_base64(img: np.ndarray, ext: str = ".jpg") -> str:
    """Encodes a cv2 BGR image into a base64 string with data URI prefix."""
    success, buffer = cv2.imencode(ext, img)
    if not success:
        raise ValueError("Could not encode image.")
    
    b64_str = base64.b64encode(buffer).decode("utf-8")
    mime = "image/jpeg" if ext.lower() in [".jpg", ".jpeg"] else "image/png"
    return f"data:{mime};base64,{b64_str}"
