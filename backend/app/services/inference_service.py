"""
Real inference service using Thiyagu's ONNX models.

Models available:
  lm_staff_convnext_atto  — Staff vs Customer (98.75% acc, 14MB, recommended)
  lm_staff_convnext_pico  — Staff vs Customer (98.75% acc, 34MB)
  lm_id_convnext_pico     — ID Card Visible vs Not (98.25% acc, 34MB)

ONNX contract (from README):
  Input:  float32 (N, 3, 224, 224) — RGB, shortest-edge resize to 256,
          center-crop 224x224, /255, ImageNet mean/std normalize
  Output: float32 (N, 2) — softmax probabilities [customer/not_visible, staff/visible]
  Classes: index 0 = customer/not_visible, index 1 = staff/visible
"""
from __future__ import annotations
import io
from pathlib import Path
from typing import Optional

import numpy as np
from PIL import Image

try:
    import onnxruntime as ort
    ORT_AVAILABLE = True
except ImportError:
    ORT_AVAILABLE = False

# ── Model paths ───────────────────────────────────────────────
MODELS_DIR = Path(__file__).parent.parent.parent / 'models'

MODEL_PATHS = {
    'staff':  MODELS_DIR / 'lm_staff_convnext_atto'  / 'best_model.onnx',  # recommended
    'staff_pico': MODELS_DIR / 'lm_staff_convnext_pico' / 'best_model.onnx',
    'id':     MODELS_DIR / 'lm_id_convnext_pico'    / 'best_model.onnx',
}

# ImageNet normalisation constants
MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
STD  = np.array([0.229, 0.224, 0.225], dtype=np.float32)

# Cache loaded sessions
_sessions: dict[str, 'ort.InferenceSession'] = {}


def _load_session(model_key: str) -> Optional['ort.InferenceSession']:
    """Load and cache an ONNX session."""
    if not ORT_AVAILABLE:
        return None
    if model_key in _sessions:
        return _sessions[model_key]

    path = MODEL_PATHS.get(model_key)
    if not path or not path.exists():
        return None

    try:
        sess = ort.InferenceSession(
            str(path),
            providers=['CPUExecutionProvider'],  # GPU: add CUDAExecutionProvider first
        )
        _sessions[model_key] = sess
        print(f'[inference] Loaded {model_key} model from {path.name}')
        return sess
    except Exception as e:
        print(f'[inference] Failed to load {model_key}: {e}')
        return None


def preprocess_image(image_bytes: bytes) -> np.ndarray:
    """
    Preprocess a raw image bytes → (1, 3, 224, 224) float32 array.
    Matches evaluate_onnx.py::preprocess_image from Thiyagu's package.
    """
    img = Image.open(io.BytesIO(image_bytes)).convert('RGB')

    # Resize shortest edge to 256 (bicubic)
    w, h    = img.size
    scale   = 256 / min(w, h)
    new_w   = int(round(w * scale))
    new_h   = int(round(h * scale))
    img     = img.resize((new_w, new_h), Image.BICUBIC)

    # Center crop 224x224
    left    = (new_w - 224) // 2
    top     = (new_h - 224) // 2
    img     = img.crop((left, top, left + 224, top + 224))

    # To float32 array, /255, normalize
    arr     = np.array(img, dtype=np.float32) / 255.0          # (224,224,3)
    arr     = (arr - MEAN) / STD                                # normalize
    arr     = arr.transpose(2, 0, 1)[np.newaxis, ...]           # (1,3,224,224)
    return arr.astype(np.float32)


def run_inference(model_key: str, image_bytes: bytes) -> dict:
    """
    Run ONNX inference on raw image bytes.
    Returns prediction dict with label, confidence and probabilities.
    Falls back to a placeholder if model is unavailable.
    """
    sess = _load_session(model_key)

    if sess is None:
        # Fallback if model not loaded (no GPU, missing file etc.)
        return _fallback(model_key)

    try:
        x      = preprocess_image(image_bytes)
        probs  = sess.run(['output'], {'input': x})[0][0]  # (2,)

        if model_key in ('staff', 'staff_pico'):
            labels = ['customer', 'staff']
            pred_idx = int(np.argmax(probs))
            return {
                'model':       model_key,
                'label':       labels[pred_idx],
                'confidence':  round(float(probs[pred_idx]) * 100, 1),
                'is_staff':    pred_idx == 1,
                'p_staff':     round(float(probs[1]) * 100, 1),
                'p_customer':  round(float(probs[0]) * 100, 1),
                'source':      'onnx',
            }
        else:  # id
            labels   = ['not_visible', 'visible']
            pred_idx = int(np.argmax(probs))
            return {
                'model':       model_key,
                'label':       labels[pred_idx],
                'confidence':  round(float(probs[pred_idx]) * 100, 1),
                'is_visible':  pred_idx == 1,
                'p_visible':   round(float(probs[1]) * 100, 1),
                'p_not_visible': round(float(probs[0]) * 100, 1),
                'source':      'onnx',
            }

    except Exception as e:
        print(f'[inference] Error running {model_key}: {e}')
        return _fallback(model_key)


def _fallback(model_key: str) -> dict:
    """Return a placeholder when model is unavailable."""
    if model_key in ('staff', 'staff_pico'):
        return {
            'model':       model_key,
            'label':       'unknown',
            'confidence':  0.0,
            'is_staff':    None,
            'p_staff':     0.0,
            'p_customer':  0.0,
            'source':      'fallback — model not loaded',
        }
    return {
        'model':       model_key,
        'label':       'unknown',
        'confidence':  0.0,
        'is_visible':  None,
        'p_visible':   0.0,
        'p_not_visible': 0.0,
        'source':      'fallback — model not loaded',
    }


def model_status() -> dict:
    """Return status of all ONNX models."""
    status = {}
    for key, path in MODEL_PATHS.items():
        exists = path.exists()
        loaded = key in _sessions
        status[key] = {
            'path':    str(path.name) if exists else 'not found',
            'exists':  exists,
            'loaded':  loaded,
            'size_mb': round(path.stat().st_size / 1_048_576, 1) if exists else 0,
        }
    return status
