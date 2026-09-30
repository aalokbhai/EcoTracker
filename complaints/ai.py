import logging
from pathlib import Path

import torch
import torch.nn as nn
from django.conf import settings
from PIL import Image, ImageOps
from torchvision import models, transforms

logger = logging.getLogger(__name__)

MODEL_PATH = Path(settings.BASE_DIR) / 'ml_model' / 'waste_model.pth'
THRESHOLD = 0.5   # waste probability at or above this = verified

_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])
_model = None


def _load_model():
    """Load the CNN once and reuse it for every request."""
    global _model
    if _model is None:
        m = models.mobilenet_v2(weights=None)
        m.classifier = nn.Sequential(nn.Dropout(0.3), nn.Linear(m.last_channel, 1))
        ckpt = torch.load(MODEL_PATH, map_location='cpu')
        m.load_state_dict(ckpt['state_dict'])
        m.eval()
        _model = m
    return _model


def verify_image(image_path):
    """
    Returns (ai_verified, waste_probability_percent).
    If anything goes wrong, returns (None, None) so the complaint is still saved.
    """
    try:
        model = _load_model()
        img = ImageOps.exif_transpose(Image.open(image_path)).convert('RGB')
        with torch.no_grad():
            p = torch.sigmoid(model(_transform(img).unsqueeze(0))).item()
        return p >= THRESHOLD, round(p * 100, 1)
    except Exception:
        logger.exception('AI verification failed')
        return None, None