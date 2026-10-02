import os
import urllib.request


def download_model(url: str, dest: str):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    if not os.path.exists(dest):
        print(f"Downloading {url} to {dest}...")
        urllib.request.urlretrieve(url, dest)
        print("Downloaded.")
    else:
        print("Model already exists.")


def download_face_landmarker():
    download_model(
        "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task",
        "app/common/face_landmarker.task",
    )


def download_selfie_segmenter():
    download_model(
        "https://storage.googleapis.com/mediapipe-models/image_segmenter/selfie_segmenter/float16/latest/selfie_segmenter.tflite",
        "app/common/selfie_segmenter.tflite",
    )


def download_face_parsing_model():
    download_model(
        "https://github.com/opencv/opencv_zoo/raw/main/models/face_parsing_bisenet/face_parsing_bisenet.onnx",
        "app/common/face_parsing_bisenet.onnx",
    )


def download_face_parsing_labels():
    labels = """background
skin
l_brow
r_brow
l_eye
r_eye
eye_g
l_ear
r_ear
nose
mouth
upper_lip
lower_lip
neck
hair
hat
ear_ring
necklace
cloth
"""
    os.makedirs("app/common", exist_ok=True)
    dest = "app/common/face_parsing_labels.txt"
    if not os.path.exists(dest):
        with open(dest, "w", encoding="utf-8") as f:
            f.write(labels)
        print(f"Saved labels to {dest}")
    else:
        print("Face parsing labels already exist.")


if __name__ == "__main__":
    download_face_landmarker()
    download_selfie_segmenter()
    download_face_parsing_model()
    download_face_parsing_labels()
