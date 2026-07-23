"""
Steganography Detection Engine
================================
Architecture:
  1. SRNet-inspired Noise Extractor  –  strips image content, isolates HF noise residuals
  2. EfficientNet-B2 Classifier      –  classifies clean vs stego from noise feature maps

The full model is loaded once at worker startup (singleton via module-level variable).
All inference runs on in-memory numpy / PIL objects — nothing is written to disk.
"""
import io
import time
import base64
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image
import timm
from config import get_settings
from utils.logger import logger

settings = get_settings()

# --------------------------------------------------------------------------- #
#  Noise Extractor (SRNet front-end)                                          #
# --------------------------------------------------------------------------- #
class SRNetNoiseExtractor(nn.Module):
    """
    Simplified SRNet-style noise extraction front-end.
    Learns to suppress image content and retain noise residuals.
    """
    def __init__(self):
        super().__init__()
        # High-pass filter initialised with fixed Laplacian kernel (SRM-style)
        self.hpf = nn.Conv2d(3, 3, kernel_size=5, padding=2, groups=3, bias=False)
        self._init_hpf_weights()

        self.layer1 = self._make_block(3, 16)
        self.layer2 = self._make_block(16, 32)
        self.layer3 = self._make_block(32, 64)
        self.layer4 = self._make_block(64, 64)

    def _init_hpf_weights(self):
        # Laplacian high-pass filter to bias toward residuals
        kernel = torch.tensor([
            [-1, -1, -1, -1, -1],
            [-1,  2,  2,  2, -1],
            [-1,  2,  8,  2, -1],
            [-1,  2,  2,  2, -1],
            [-1, -1, -1, -1, -1],
        ], dtype=torch.float32) / 8.0
        kernel = kernel.unsqueeze(0).unsqueeze(0).repeat(3, 1, 1, 1)
        self.hpf.weight = nn.Parameter(kernel, requires_grad=True)

    def _make_block(self, in_c, out_c):
        return nn.Sequential(
            nn.Conv2d(in_c, out_c, 3, padding=1, bias=False),
            nn.BatchNorm2d(out_c),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_c, out_c, 3, padding=1, bias=False),
            nn.BatchNorm2d(out_c),
            nn.ReLU(inplace=True),
        )

    def forward(self, x):
        x = self.hpf(x)
        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)
        return x   # (B, 64, H, W) noise feature maps


# --------------------------------------------------------------------------- #
#  Full Model: Noise Extractor + EfficientNet-B2 Backbone                    #
# --------------------------------------------------------------------------- #
class InstaGuardModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.noise_extractor = SRNetNoiseExtractor()

        # Project noise channels into 3 channels so EfficientNet-B2 can ingest them
        self.channel_proj = nn.Conv2d(64, 3, kernel_size=1, bias=False)

        # EfficientNet-B2 backbone (no pretrained weights needed — trained from scratch)
        self.backbone = timm.create_model(
            "efficientnet_b2",
            pretrained=False,
            num_classes=2,
            in_chans=3,
        )

    def forward(self, x):
        noise = self.noise_extractor(x)
        noise = self.channel_proj(noise)
        logits = self.backbone(noise)
        return logits


# --------------------------------------------------------------------------- #
#  Singleton model loader                                                     #
# --------------------------------------------------------------------------- #
_model: InstaGuardModel = None


def load_model() -> InstaGuardModel:
    global _model
    if _model is not None:
        return _model

    device = torch.device(settings.MODEL_DEVICE)
    model = InstaGuardModel()

    try:
        state = torch.load(settings.MODEL_PATH, map_location=device)
        # Support both raw state_dict and {"model_state_dict": ...} checkpoints
        if isinstance(state, dict) and "model_state_dict" in state:
            state = state["model_state_dict"]
        model.load_state_dict(state)
        logger.info(f"Model loaded from {settings.MODEL_PATH} on {device}")
    except FileNotFoundError:
        logger.warning(
            f"Model file not found at {settings.MODEL_PATH}. "
            "Running with random weights — replace with trained model for production."
        )

    model.to(device)
    model.eval()
    _model = model
    return _model


# --------------------------------------------------------------------------- #
#  Pre-processing                                                              #
# --------------------------------------------------------------------------- #
_IMG_SIZE = 224
_MEAN = torch.tensor([0.485, 0.456, 0.406])
_STD  = torch.tensor([0.229, 0.224, 0.225])


def _preprocess(image_bytes: bytes) -> torch.Tensor:
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img = img.resize((_IMG_SIZE, _IMG_SIZE), Image.LANCZOS)
    arr = np.array(img, dtype=np.float32) / 255.0
    tensor = torch.from_numpy(arr).permute(2, 0, 1)           # (3, H, W)
    tensor = (tensor - _MEAN[:, None, None]) / _STD[:, None, None]
    return tensor.unsqueeze(0)                                  # (1, 3, H, W)


def _make_thumbnail_b64(image_bytes: bytes, size: int = 120) -> str:
    """Create a small base64-encoded JPEG thumbnail for DB storage."""
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img.thumbnail((size, size))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=60)
    return base64.b64encode(buf.getvalue()).decode()


# --------------------------------------------------------------------------- #
#  Inference                                                                   #
# --------------------------------------------------------------------------- #
def analyze_image(image_bytes: bytes) -> dict:
    """
    Analyze a single image in memory.

    Returns:
        {
            "is_suspicious": bool,
            "confidence_score": float,   # 0.0–1.0
            "scan_duration_ms": float,
            "thumbnail_b64": str,
        }
    """
    t0 = time.perf_counter()
    model = load_model()
    device = next(model.parameters()).device

    thumbnail_b64 = _make_thumbnail_b64(image_bytes)
    tensor = _preprocess(image_bytes).to(device)

    with torch.no_grad():
        logits = model(tensor)
        probs = F.softmax(logits, dim=1)[0]   # [clean_prob, stego_prob]

    stego_prob = probs[1].item()
    is_suspicious = stego_prob >= settings.CONFIDENCE_THRESHOLD
    duration_ms = (time.perf_counter() - t0) * 1000

    return {
        "is_suspicious": is_suspicious,
        "confidence_score": round(stego_prob if is_suspicious else probs[0].item(), 4),
        "scan_duration_ms": round(duration_ms, 2),
        "thumbnail_b64": thumbnail_b64,
    }
