"""Convert the trained PyTorch model to ONNX (runs on 'onnxruntime': ~10x lighter than PyTorch).

    python ml/export_onnx.py        ->  ml_model/waste_model.onnx
Needs: torch, torchvision, onnx (only for this one-time conversion).
"""
from pathlib import Path

import torch
import torch.nn as nn
from torchvision import models

ROOT = Path(__file__).resolve().parent.parent
SRC, DST = ROOT / 'ml_model' / 'waste_model.pth', ROOT / 'ml_model' / 'waste_model.onnx'

m = models.mobilenet_v2(weights=None)
m.classifier = nn.Sequential(nn.Dropout(0.3), nn.Linear(m.last_channel, 1))
m.load_state_dict(torch.load(SRC, map_location='cpu')['state_dict'])
m.eval()
torch.onnx.export(m, torch.zeros(1, 3, 224, 224), str(DST), input_names=['input'], output_names=['logit'],
                  dynamic_axes={'input': {0: 'batch'}, 'logit': {0: 'batch'}}, opset_version=17,
                  dynamo=False)
print('saved', DST, f'{DST.stat().st_size / 1e6:.1f} MB')
