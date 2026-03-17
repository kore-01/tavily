"""
Captcha Recognition CNN — Lightweight position-aware model

6-character captcha (a-z, A-Z, 0-9 = 62 classes per position).

Architecture (~335K params, designed for small datasets):
- Input: 1x60x160 (grayscale)
- 3 VGG-style blocks (double conv + pool):
    Block1: 1->32, 60x160 -> 32x30x80
    Block2: 32->64, 30x80 -> 64x15x40
    Block3: 64->128, 15x40 -> 128x7x20
- AdaptiveAvgPool2d(1, 6): maps 128x7x20 -> 128x1x6
  (pools height, maps width to 6 character positions)
- Dropout(0.3) -> 6 heads: Linear(128, 62)
- No large FC layer — position-aware pooling replaces it.
"""

import string

# Character set: 0-9 + A-Z + a-z = 62 classes
CHARSET = string.digits + string.ascii_uppercase + string.ascii_lowercase
NUM_CLASSES = len(CHARSET)  # 62
NUM_CHARS = 6  # captcha length
IMG_H, IMG_W = 60, 160  # input image size


def char_to_index(c: str) -> int:
    idx = CHARSET.find(c)
    if idx == -1:
        raise ValueError(f"Character '{c}' not in charset")
    return idx


def index_to_char(i: int) -> str:
    return CHARSET[i]


def label_to_indices(label: str) -> list[int]:
    return [char_to_index(c) for c in label]


def indices_to_label(indices: list[int]) -> str:
    return "".join(index_to_char(i) for i in indices)


def _build_model():
    """Build and return the CaptchaCNN model. Requires torch."""
    import torch
    import torch.nn as nn

    class CaptchaCNN(nn.Module):
        def __init__(self):
            super().__init__()

            self.features = nn.Sequential(
                # Block 1: 1x60x160 -> 32x30x80
                nn.Conv2d(1, 32, 3, padding=1), nn.BatchNorm2d(32), nn.ReLU(inplace=True),
                nn.Conv2d(32, 32, 3, padding=1), nn.BatchNorm2d(32), nn.ReLU(inplace=True),
                nn.MaxPool2d(2, 2),

                # Block 2: 32x30x80 -> 64x15x40
                nn.Conv2d(32, 64, 3, padding=1), nn.BatchNorm2d(64), nn.ReLU(inplace=True),
                nn.Conv2d(64, 64, 3, padding=1), nn.BatchNorm2d(64), nn.ReLU(inplace=True),
                nn.MaxPool2d(2, 2),

                # Block 3: 64x15x40 -> 128x7x20
                nn.Conv2d(64, 128, 3, padding=1), nn.BatchNorm2d(128), nn.ReLU(inplace=True),
                nn.Conv2d(128, 128, 3, padding=1), nn.BatchNorm2d(128), nn.ReLU(inplace=True),
                nn.MaxPool2d(2, 2),

                # Block 4: 128x7x20 -> 256x7x20 (no pool — preserve spatial resolution)
                nn.Conv2d(128, 256, 3, padding=1), nn.BatchNorm2d(256), nn.ReLU(inplace=True),
            )

            # Position-aware pooling (ONNX-compatible):
            # Height 7→1: mean; Width 20→6: AvgPool1d(kernel=5, stride=3)
            # covers [0:5],[3:8],[6:11],[9:14],[12:17],[15:20] — full width
            self.width_pool = nn.AvgPool1d(kernel_size=5, stride=3)

            self.dropout = nn.Dropout(0.4)

            # 6 parallel output heads — one per character position
            self.heads = nn.ModuleList(
                [nn.Linear(256, NUM_CLASSES) for _ in range(NUM_CHARS)]
            )

        def forward(self, x):
            x = self.features(x)          # (batch, 256, 7, 20)
            x = torch.mean(x, dim=2)      # (batch, 256, 20) — pool height
            x = self.width_pool(x)        # (batch, 256, 6)  — pool width to 6 chars
            x = x.permute(0, 2, 1)        # (batch, 6, 256)
            x = self.dropout(x)
            return [self.heads[i](x[:, i]) for i in range(NUM_CHARS)]

    return CaptchaCNN
