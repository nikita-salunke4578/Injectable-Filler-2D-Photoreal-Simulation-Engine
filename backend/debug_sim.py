import cv2
import numpy as np
import traceback
from app.simulations.lips.pipeline import run_lips_pipeline

def main():
    try:
        img = np.ones((512, 512, 3), dtype=np.uint8) * 128
        print(f'Image loaded. Shape: {img.shape}')
        res = run_lips_pipeline(
            img,
            philtral_shortening=100,
            vermilion_show=100,
            cupids_bow=100,
            philtral_column=100,
            dental_show=100,
            show_outline=False
        )
        diff = np.sum(np.abs(img.astype(np.int32) - res.astype(np.int32)))
        print(f'Diff sum: {diff}')
    except Exception as e:
        print('Exception occurred:')
        traceback.print_exc()

if __name__ == '__main__':
    main()
