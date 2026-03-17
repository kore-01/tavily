"""
ONNX-based captcha inference.

Requires only: onnxruntime, Pillow, numpy (no torch needed at runtime).

Usage:
    python -m captcha_model.predict --test data/captchas/sample.png
    python -m captcha_model.predict --base64 <png_base64_string>
"""

import argparse
import base64
import io
import os

import numpy as np
from PIL import Image

from .model import IMG_H, IMG_W, NUM_CHARS, indices_to_label

ONNX_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "captcha.onnx")

_session = None


def _get_session(onnx_path: str = None):
    """Lazy-load ONNX runtime session."""
    global _session
    if _session is None:
        import onnxruntime as ort
        path = onnx_path or ONNX_PATH
        _session = ort.InferenceSession(path, providers=["CPUExecutionProvider"])
    return _session


def preprocess_image(img: Image.Image) -> np.ndarray:
    """Preprocess PIL Image to model input tensor."""
    img = img.convert("L").resize((IMG_W, IMG_H))
    arr = np.array(img, dtype=np.float32) / 255.0
    return arr.reshape(1, 1, IMG_H, IMG_W)


def predict_from_image(img: Image.Image, onnx_path: str = None) -> str:
    """Predict captcha text from a PIL Image."""
    session = _get_session(onnx_path)
    input_tensor = preprocess_image(img)
    outputs = session.run(None, {"image": input_tensor})

    indices = [int(np.argmax(outputs[i], axis=1)[0]) for i in range(NUM_CHARS)]
    return indices_to_label(indices)


def predict_from_png_base64(png_base64: str, onnx_path: str = None) -> str:
    """Predict captcha text from a base64-encoded PNG."""
    png_data = base64.b64decode(png_base64)
    img = Image.open(io.BytesIO(png_data))
    return predict_from_image(img, onnx_path)


def predict_from_file(filepath: str, onnx_path: str = None) -> str:
    """Predict captcha text from an image file."""
    img = Image.open(filepath)
    return predict_from_image(img, onnx_path)


def main():
    parser = argparse.ArgumentParser(description="Predict captcha from image")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--test", help="Path to a captcha image file")
    group.add_argument("--base64", help="Base64-encoded PNG string")
    parser.add_argument("--model", default=ONNX_PATH, help="Path to ONNX model")
    args = parser.parse_args()

    if not os.path.exists(args.model):
        print(f"Error: ONNX model not found: {args.model}")
        print("Run export_onnx.py first.")
        return

    if args.test:
        result = predict_from_file(args.test, args.model)
        print(f"File: {args.test}")
    else:
        result = predict_from_png_base64(args.base64, args.model)
        print(f"Base64 input")

    print(f"Prediction: {result}")


if __name__ == "__main__":
    main()
