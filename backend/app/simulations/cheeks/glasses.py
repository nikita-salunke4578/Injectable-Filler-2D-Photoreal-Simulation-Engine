"""
Eyeglasses detection and hard protection mask generation for midface simulations.

Detection uses the OpenCV Zoo 19-class BiSeNet face parser. Class `eye_g` is
treated as the eyeglasses mask. The downstream protected-mask pipeline remains
unchanged and consumes the complete glass region mask directly.
"""

from __future__ import annotations

import logging
import os

import cv2
import numpy as np
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.vision.core import image as mp_image_module

from app.simulations.cheeks.landmarks import CheekLandmarks

logger = logging.getLogger(__name__)

_BASE_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
    )
)

SEGMENTATION_MODEL_PATH = os.path.abspath(
    os.path.join(
        _BASE_DIR,
        "common",
        "selfie_segmenter.tflite",
    )
)

FACE_PARSING_MODEL_PATH = os.path.abspath(
    os.path.join(
        _BASE_DIR,
        "common",
        "face_parsing_bisenet.onnx",
    )
)
FACE_PARSING_LABELS_PATH = os.path.abspath(
    os.path.join(
        _BASE_DIR,
        "common",
        "face_parsing_labels.txt",
    )
)

# OpenCV Zoo BiSeNet / CelebAMask-HQ preprocessing.
_BISENET_INPUT_SIZE = (512, 512)
_BISENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
_BISENET_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)
_DEFAULT_EYE_G_INDEX = 6
_MIN_GLASSES_PIXELS = 40

_FACE_PARSING_SESSION = None
_FACE_PARSING_INPUT_NAME: str | None = None
_FACE_PARSING_INPUT_SHAPE: tuple | None = None
_FACE_PARSING_LABELS: list[str] | None = None


def segment_face_region(
    image: np.ndarray,
    model_path: str | None = None,
) -> np.ndarray:
    """Return a binary face/person mask for the image.

    The priority path uses a MediaPipe image segmenter model if available. When the
    model is missing or the runtime fails, the function falls back to a simple face
    region estimate based on the image ROI and is intentionally conservative.
    """
    if image is None or image.ndim != 3 or image.shape[2] != 3:
        if image is not None and image.ndim >= 2:
            return np.zeros(image.shape[:2], dtype=np.uint8)
        return np.zeros((0, 0), dtype=np.uint8)

    target_model = model_path or SEGMENTATION_MODEL_PATH
    h, w = image.shape[:2]

    if os.path.exists(target_model):
        try:
            base_options = python.BaseOptions(model_asset_path=target_model)
            options = vision.ImageSegmenterOptions(
                base_options=base_options,
                output_confidence_masks=True,
                running_mode=vision.RunningMode.IMAGE,
            )
            segmenter = vision.ImageSegmenter.create_from_options(options)
            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            mp_image = mp_image_module.Image(
                image_format=mp_image_module.ImageFormat.SRGB,
                data=rgb,
            )
            result = segmenter.segment(mp_image)
            if result and result.confidence_masks:
                mask_image = result.confidence_masks[0]
                if mask_image is not None:
                    mask = np.asarray(mask_image.numpy_view())
                    if mask.ndim == 3:
                        mask = np.squeeze(mask, axis=-1)
                    mask = mask.astype(np.float32)
                    if mask.shape[:2] == (h, w):
                        binary = (mask >= 0.25).astype(np.uint8) * 255
                        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))
                        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
                        binary = cv2.medianBlur(binary, 9)
                        return binary
        except Exception:
            pass

    mask = np.zeros((h, w), dtype=np.uint8)
    margin_x = int(w * 0.12)
    margin_y = int(h * 0.10)
    cv2.ellipse(
        mask,
        (w // 2, h // 2),
        (max(30, w // 2 - margin_x), max(34, h // 2 - margin_y)),
        0,
        0,
        360,
        255,
        -1,
    )
    return mask


def _load_face_parsing_labels(labels_path: str | None = None) -> list[str]:
    global _FACE_PARSING_LABELS
    if _FACE_PARSING_LABELS is not None and labels_path is None:
        return _FACE_PARSING_LABELS

    target_labels = labels_path or FACE_PARSING_LABELS_PATH
    labels: list[str] = []
    if os.path.exists(target_labels):
        with open(target_labels, "r", encoding="utf-8") as handle:
            labels = [line.strip() for line in handle if line.strip()]

    if labels_path is None:
        _FACE_PARSING_LABELS = labels
    return labels


def _resolve_face_parsing_class_index(labels: list[str] | None = None) -> int:
    """Resolve the eyeglasses class index from a 19-class BiSeNet face parser."""
    label_names = []
    if labels:
        label_names = [label.strip().lower() for label in labels if label and label.strip()]

    aliases = {"eye_g", "eye-g", "eyeglasses", "glasses"}
    for idx, label in enumerate(label_names):
        if label in aliases or label.replace("-", "_") in aliases:
            return idx

    return _DEFAULT_EYE_G_INDEX


def _get_face_parsing_session(model_path: str | None = None):
    global _FACE_PARSING_SESSION, _FACE_PARSING_INPUT_NAME, _FACE_PARSING_INPUT_SHAPE

    target_model = model_path or FACE_PARSING_MODEL_PATH
    if not os.path.exists(target_model):
        logger.warning(
            "BiSeNet face-parsing weights not found at %s; glasses protection will remain disabled.",
            target_model,
        )
        return None, None, None

    if (
        _FACE_PARSING_SESSION is not None
        and model_path is None
        and _FACE_PARSING_INPUT_NAME is not None
        and _FACE_PARSING_INPUT_SHAPE is not None
    ):
        return _FACE_PARSING_SESSION, _FACE_PARSING_INPUT_NAME, _FACE_PARSING_INPUT_SHAPE

    try:
        import onnxruntime as ort
    except Exception:
        logger.warning("onnxruntime is unavailable; glasses protection will remain disabled.")
        return None, None, None

    try:
        session = ort.InferenceSession(
            target_model,
            providers=["CPUExecutionProvider"],
        )
        input_cfg = session.get_inputs()[0]
        input_name = input_cfg.name
        input_shape = tuple(input_cfg.shape)
    except Exception:
        logger.warning(
            "Failed to load BiSeNet face-parsing weights at %s; glasses protection will remain disabled.",
            target_model,
        )
        return None, None, None

    if model_path is None:
        _FACE_PARSING_SESSION = session
        _FACE_PARSING_INPUT_NAME = input_name
        _FACE_PARSING_INPUT_SHAPE = input_shape

    return session, input_name, input_shape


def _static_dim(value, default: int) -> int:
    if isinstance(value, int) and value > 0:
        return value
    return default


def _preprocess_bisenet_input(
    image: np.ndarray,
    input_shape: tuple | None,
) -> np.ndarray:
    """Build an OpenCV Zoo BiSeNet tensor from a BGR face crop."""
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    height, width = _BISENET_INPUT_SIZE[1], _BISENET_INPUT_SIZE[0]
    channels_first = True

    if input_shape is not None and len(input_shape) == 4:
        if input_shape[-1] == 3 and input_shape[1] != 3:
            channels_first = False
            height = _static_dim(input_shape[1], _BISENET_INPUT_SIZE[1])
            width = _static_dim(input_shape[2], _BISENET_INPUT_SIZE[0])
        else:
            channels_first = True
            height = _static_dim(input_shape[2], _BISENET_INPUT_SIZE[1])
            width = _static_dim(input_shape[3], _BISENET_INPUT_SIZE[0])

    resized = cv2.resize(rgb, (width, height), interpolation=cv2.INTER_LINEAR)
    tensor = resized.astype(np.float32) / 255.0
    tensor = (tensor - _BISENET_MEAN) / _BISENET_STD

    if channels_first:
        return np.transpose(tensor, (2, 0, 1))[None, ...].astype(np.float32)
    return tensor[None, ...].astype(np.float32)


def _parsing_map_from_output(output: np.ndarray) -> np.ndarray | None:
    """Convert BiSeNet logits to an HxW class-index map via argmax."""
    if output is None:
        return None

    array = np.asarray(output)
    if array.ndim == 4:
        if array.shape[1] == 19:
            return np.argmax(array[0], axis=0).astype(np.int32)
        if array.shape[-1] == 19:
            return np.argmax(array[0], axis=-1).astype(np.int32)
        return None
    if array.ndim == 3:
        if array.shape[0] == 19:
            return np.argmax(array, axis=0).astype(np.int32)
        if array.shape[-1] == 19:
            return np.argmax(array, axis=-1).astype(np.int32)
        # Already an HxW label map with a singleton channel.
        if 1 in array.shape:
            return np.squeeze(array).astype(np.int32)
        return None
    if array.ndim == 2:
        return array.astype(np.int32)
    return None


def _glasses_mask_from_parsing_map(
    parsing_map: np.ndarray,
    output_size: tuple[int, int],
    eye_index: int,
) -> np.ndarray:
    mask = (parsing_map == eye_index).astype(np.uint8) * 255
    if mask.shape[:2] != output_size:
        mask = cv2.resize(
            mask,
            (output_size[1], output_size[0]),
            interpolation=cv2.INTER_NEAREST,
        )
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    return cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)


def _run_face_parsing_model(
    image: np.ndarray,
    model_path: str | None = None,
    labels_path: str | None = None,
) -> np.ndarray | None:
    """Run BiSeNet and return a binary eye_g mask in the crop's resolution."""
    if image is None or image.ndim != 3 or image.shape[2] != 3:
        return None

    session, input_name, input_shape = _get_face_parsing_session(model_path)
    if session is None or input_name is None:
        return None

    try:
        input_tensor = _preprocess_bisenet_input(image, input_shape)
        output = session.run(None, {input_name: input_tensor})[0]
    except Exception:
        logger.warning("BiSeNet face-parsing inference failed; glasses protection will remain disabled.")
        return None

    parsing_map = _parsing_map_from_output(output)
    if parsing_map is None or parsing_map.size == 0:
        return None

    labels = _load_face_parsing_labels(labels_path)
    eye_index = _resolve_face_parsing_class_index(labels)
    return _glasses_mask_from_parsing_map(
        parsing_map,
        image.shape[:2],
        eye_index,
    )


def _collect_face_points(landmarks: CheekLandmarks) -> np.ndarray | None:
    chunks: list[np.ndarray] = []
    for attr in (
        "anchors",
        "left_all",
        "right_all",
        "left_eye_exclusion",
        "right_eye_exclusion",
        "left_apex",
        "right_apex",
    ):
        value = getattr(landmarks, attr, None)
        if value is None:
            continue
        points = np.asarray(value, dtype=np.float32)
        if points.size == 0:
            continue
        if points.ndim == 1:
            points = points.reshape(1, -1)
        chunks.append(points[:, :2])

    if not chunks:
        return None
    return np.concatenate(chunks, axis=0)


def face_crop_bounds(
    image: np.ndarray,
    landmarks: CheekLandmarks,
) -> tuple[int, int, int, int]:
    """Return inclusive-exclusive face crop bounds that cover frames and temples."""
    h, w = image.shape[:2]
    face_pts = _collect_face_points(landmarks)
    if face_pts is None:
        return 0, 0, w, h

    min_x = max(0, int(np.floor(np.min(face_pts[:, 0]))) - 40)
    min_y = max(0, int(np.floor(np.min(face_pts[:, 1]))) - 50)
    max_x = min(w, int(np.ceil(np.max(face_pts[:, 0]))) + 40)
    max_y = min(h, int(np.ceil(np.max(face_pts[:, 1]))) + 40)

    if max_x <= min_x or max_y <= min_y:
        return 0, 0, w, h
    return min_x, min_y, max_x, max_y


def detect_glasses(
    image: np.ndarray,
    landmarks: CheekLandmarks,
) -> tuple[bool, np.ndarray | None]:
    """Detect eyeglasses using the BiSeNet face-parser `eye_g` class mask."""
    if image is None or image.ndim != 3 or image.shape[2] != 3:
        return False, None

    if landmarks is None or getattr(landmarks, "anchors", None) is None or len(landmarks.anchors) == 0:
        return False, None

    min_x, min_y, max_x, max_y = face_crop_bounds(image, landmarks)
    face_crop = image[min_y:max_y, min_x:max_x]
    if face_crop.size == 0:
        face_crop = image
        min_x, min_y = 0, 0
        max_x, max_y = image.shape[1], image.shape[0]

    crop_mask = _run_face_parsing_model(face_crop)
    if crop_mask is None or crop_mask.size == 0:
        logger.warning(
            "No eyeglasses mask produced by the face-parsing model; no protected glasses region will be applied."
        )
        return False, None

    if crop_mask.ndim == 3:
        crop_mask = np.squeeze(crop_mask, axis=-1)

    crop_mask = crop_mask.astype(np.uint8)
    if crop_mask.max() <= 1:
        crop_mask = (crop_mask > 0).astype(np.uint8) * 255

    crop_h, crop_w = face_crop.shape[:2]
    if crop_mask.shape[:2] != (crop_h, crop_w):
        crop_mask = cv2.resize(crop_mask, (crop_w, crop_h), interpolation=cv2.INTER_NEAREST)

    mask = np.zeros(image.shape[:2], dtype=np.uint8)
    mask[min_y:max_y, min_x:max_x] = crop_mask

    glasses_pixels = int(np.count_nonzero(mask))
    if glasses_pixels < _MIN_GLASSES_PIXELS:
        return False, mask

    return True, mask
