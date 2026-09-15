import asyncio
import cv2
import numpy as np
from app.services.simulation_service import SimulationService
from app.common.schemas import SimulationRequest, ZoneSimulationRequest, TreatmentZone
from app.simulations.lips.pipeline import run_lips_pipeline

def test_pipeline():
    # 1. Create a dummy image (e.g. 500x500 black image)
    # MediaPipe needs a real face to not raise ValueError. 
    # Let's download a small sample face image.
    pass

import urllib.request
import traceback

async def main():
    try:
        url = "https://raw.githubusercontent.com/opencv/opencv/master/samples/data/lena.jpg"
        req = urllib.request.urlopen(url)
        arr = np.asarray(bytearray(req.read()), dtype=np.uint8)
        img = cv2.imdecode(arr, -1)
        
        print("Image loaded. Shape:", img.shape)
        
        # Run pipeline
        res = run_lips_pipeline(img, volume_ml=1.0, intensity=1.0)
        print("Pipeline ran successfully. Output shape:", res.shape)
    except Exception as e:
        print("Exception occurred:")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
