import urllib.request
import os

def download_model():
    url = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
    dest = "app/common/face_landmarker.task"
    if not os.path.exists(dest):
        print(f"Downloading {url} to {dest}...")
        urllib.request.urlretrieve(url, dest)
        print("Downloaded.")
    else:
        print("Model already exists.")

if __name__ == "__main__":
    download_model()
