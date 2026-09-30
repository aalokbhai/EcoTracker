import glob
import random
import shutil
from pathlib import Path

import kagglehub

BASE = Path(__file__).resolve().parent
DATA = BASE / 'data'
N = 1500
random.seed(42)


def collect(dataset, out_dir, prefix):
    out_dir.mkdir(parents=True, exist_ok=True)
    if len(list(out_dir.glob(f'{prefix}_*.jpg'))) >= N:
        print(f'{out_dir.name}: already done, skipping')
        return
    path = kagglehub.dataset_download(dataset)
    imgs = glob.glob(str(Path(path) / '**' / '*.jpg'), recursive=True)
    print(len(imgs), 'images found in', dataset)
    for i, p in enumerate(random.sample(imgs, min(N, len(imgs)))):
        shutil.copy(p, out_dir / f'{prefix}_{i}.jpg')


# 1) WASTE images (already downloaded, will be skipped)
collect("mostafaabla/garbage-classification", DATA / 'waste', 'w')

# 2) NOT WASTE images (streets, buildings, nature, sea, mountains)
collect("puneet6060/intel-image-classification", DATA / 'not_waste', 'n')

print('Done ->', len(list((DATA / 'waste').iterdir())), 'waste,',
      len(list((DATA / 'not_waste').iterdir())), 'not_waste')