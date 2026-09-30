import sys
from pathlib import Path

import torch
import torch.nn as nn
from PIL import Image
from torchvision import transforms, models

MODEL = Path(__file__).resolve().parent.parent / 'ml_model' / 'waste_model.pth'

tf = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])


def load_model():
    m = models.mobilenet_v2(weights=None)
    m.classifier = nn.Sequential(nn.Dropout(0.3), nn.Linear(m.last_channel, 1))
    ckpt = torch.load(MODEL, map_location='cpu')
    m.load_state_dict(ckpt['state_dict'])
    m.eval()
    return m


if __name__ == '__main__':
    model = load_model()
    for path in sys.argv[1:]:
        img = Image.open(path).convert('RGB')
        with torch.no_grad():
            p = torch.sigmoid(model(tf(img).unsqueeze(0))).item()
        label = 'WASTE' if p > 0.5 else 'NOT WASTE'
        print(f'{Path(path).name}: {label}  ({p*100:.1f}% waste)')