from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Subset
from torchvision import datasets, transforms, models

BASE = Path(__file__).resolve().parent
DATA = BASE / 'data'
OUT = BASE.parent / 'ml_model'
OUT.mkdir(exist_ok=True)

MEAN, STD = [0.485, 0.456, 0.406], [0.229, 0.224, 0.225]

train_tf = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomRotation(10),
    transforms.ColorJitter(0.2, 0.2, 0.2),
    transforms.ToTensor(),
    transforms.Normalize(MEAN, STD),
])
val_tf = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(MEAN, STD),
])


def run_epoch(model, loader, device, criterion, optimizer=None):
    training = optimizer is not None
    model.train(training)
    total_loss, correct, n = 0.0, 0, 0
    with torch.set_grad_enabled(training):
        for x, y in loader:
            x = x.to(device)
            y = y.float().unsqueeze(1).to(device)
            out = model(x)
            loss = criterion(out, y)
            if training:
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
            total_loss += loss.item() * x.size(0)
            correct += ((out > 0).float() == y).sum().item()
            n += x.size(0)
    return total_loss / n, correct / n


def main():
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print('Device:', device)

    full_train = datasets.ImageFolder(DATA, transform=train_tf)
    full_val = datasets.ImageFolder(DATA, transform=val_tf)
    print('Classes:', full_train.classes)          # ['not_waste', 'waste']
    print('Total images:', len(full_train))

    # 80/20 split (same indices for train and validation transforms)
    g = torch.Generator().manual_seed(42)
    perm = torch.randperm(len(full_train), generator=g).tolist()
    split = int(0.8 * len(perm))
    train_dl = DataLoader(Subset(full_train, perm[:split]), batch_size=32,
                          shuffle=True, num_workers=4)
    val_dl = DataLoader(Subset(full_val, perm[split:]), batch_size=32, num_workers=4)

    # MobileNetV2 (pretrained on ImageNet) with a new 1-output head
    model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.DEFAULT)
    model.classifier = nn.Sequential(nn.Dropout(0.3), nn.Linear(model.last_channel, 1))
    model.to(device)
    criterion = nn.BCEWithLogitsLoss()

    best = 0.0
    phases = [('head only', 3, 1e-3), ('fine-tune', 4, 1e-4)]
    for name, epochs, lr in phases:
        if name == 'head only':
            for p in model.features.parameters():
                p.requires_grad = False
        else:
            for p in model.features[-6:].parameters():
                p.requires_grad = True
        optimizer = torch.optim.Adam(
            [p for p in model.parameters() if p.requires_grad], lr=lr)

        for ep in range(1, epochs + 1):
            tl, ta = run_epoch(model, train_dl, device, criterion, optimizer)
            vl, va = run_epoch(model, val_dl, device, criterion)
            print(f'[{name}] epoch {ep}/{epochs}  '
                  f'train_acc={ta:.3f}  val_acc={va:.3f}  val_loss={vl:.3f}')
            if va > best:
                best = va
                torch.save({'state_dict': model.state_dict(),
                            'classes': full_train.classes},
                           OUT / 'waste_model.pth')
                print('   -> best model saved')

    print(f'Best val accuracy: {best:.3f}')


if __name__ == '__main__':      # Required on Windows for DataLoader workers
    main()