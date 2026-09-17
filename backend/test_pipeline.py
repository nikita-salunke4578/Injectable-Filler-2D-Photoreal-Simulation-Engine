import cv2
import numpy as np
from app.simulations.lips.pipeline import run_lips_pipeline

def main():
    # Create a dummy image
    img = np.ones((512, 512, 3), dtype=np.uint8) * 200
    # Draw something to represent lips
    cv2.circle(img, (256, 256), 40, (100, 100, 250), -1)
    cv2.imwrite("dummy_input.jpg", img)
    
    print("Running pipeline...")
    # Mock face detector
    class MockFaceDetector:
        def get_landmarks(self, image):
            # Return mock landmarks
            pts = np.zeros((478, 2), dtype=np.int32)
            # Center at 256, 256
            outer = [[206, 256], [226, 236], [256, 236], [286, 236], [306, 256], [286, 276], [256, 276], [226, 276]]
            inner = [[216, 256], [236, 246], [256, 246], [276, 246], [296, 256], [276, 266], [256, 266], [236, 266]]
            nose = [[236, 206], [256, 206], [276, 206]]
            from app.simulations.lips.landmarks import OUTER_LIP_INDICES, INNER_LIP_INDICES, NOSE_BASE_INDICES
            for i, p in enumerate(outer): pts[OUTER_LIP_INDICES[i % len(OUTER_LIP_INDICES)]] = p
            for i, p in enumerate(inner): pts[INNER_LIP_INDICES[i % len(INNER_LIP_INDICES)]] = p
            for i, p in enumerate(nose): pts[NOSE_BASE_INDICES[i % len(NOSE_BASE_INDICES)]] = p
            return pts

    res = run_lips_pipeline(
        img, 
        vermilion_show=100, 
        philtral_shortening=100,
        face_detector=MockFaceDetector()
    )
    cv2.imwrite("dummy_output.jpg", res)
    print("Done")

if __name__ == "__main__":
    main()
