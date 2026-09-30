"""Garbage-photo check (CNN: MobileNetV2, trained in ml/train.py).

Two interchangeable back-ends, same model, same result:
  * ONNX Runtime  (ml_model/waste_model.onnx)  - tiny and fast, used in production (free 512 MB hosts)
  * PyTorch       (ml_model/waste_model.pth)   - fallback for local development

Create the .onnx file once with:  python ml/export_onnx.py
"""
import logging
from pathlib import Path

import numpy as np
from django.conf import settings
from PIL import Image, ImageOps

logger = logging.getLogger(__name__)

ONNX_PATH = Path(settings.BASE_DIR) / 'ml_model' / 'waste_model.onnx'
MODEL_PATH = Path(settings.BASE_DIR) / 'ml_model' / 'waste_model.pth'
THRESHOLD = 0.5   # waste probability at or above this = verified

_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32).reshape(3, 1, 1)
_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32).reshape(3, 1, 1)
_backend = None   # callable: float32 array (1,3,224,224) -> waste probability


def _load_onnx():
    import onnxruntime as ort
    opts = ort.SessionOptions()
    opts.intra_op_num_threads = 1
    sess = ort.InferenceSession(str(ONNX_PATH), opts, providers=['CPUExecutionProvider'])
    name = sess.get_inputs()[0].name

    def run(x):
        logit = float(sess.run(None, {name: x})[0].reshape(-1)[0])
        return float(1.0 / (1.0 + np.exp(-logit)))
    return run


def _load_torch():
    import torch
    import torch.nn as nn
    from torchvision import models
    m = models.mobilenet_v2(weights=None)
    m.classifier = nn.Sequential(nn.Dropout(0.3), nn.Linear(m.last_channel, 1))
    m.load_state_dict(torch.load(MODEL_PATH, map_location='cpu')['state_dict'])
    m.eval()

    def run(x):
        with torch.no_grad():
            return torch.sigmoid(m(torch.from_numpy(x))).item()
    return run


def _load_model():
    """Load the CNN once and reuse it for every request."""
    global _backend
    if _backend is None:
        try:
            if not ONNX_PATH.exists():
                raise FileNotFoundError(ONNX_PATH)
            _backend = _load_onnx()
            logger.info('CNN loaded (ONNX Runtime)')
        except Exception as exc:
            logger.info('ONNX backend not used (%s) - trying PyTorch', exc)
            _backend = _load_torch()
            logger.info('CNN loaded (PyTorch)')
    return _backend


def warm_up():
    """First inference is the slowest - call once at start-up."""
    _load_model()(np.zeros((1, 3, 224, 224), dtype=np.float32))


def _preprocess(image_path):
    img = ImageOps.exif_transpose(Image.open(image_path)).convert('RGB')
    arr = np.asarray(img.resize((224, 224), Image.BILINEAR), dtype=np.float32) / 255.0
    return ((arr.transpose(2, 0, 1) - _MEAN) / _STD)[None].astype(np.float32)


def verify_image(image_path):
    """
    Returns (ai_verified, waste_probability_percent).
    If anything goes wrong, returns (None, None) so the complaint is still saved.
    """
    try:
        p = float(_load_model()(_preprocess(image_path)))
        return bool(p >= THRESHOLD), round(p * 100, 1)
    except Exception:
        logger.exception('AI verification failed')
        return None, None
