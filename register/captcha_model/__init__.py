"""
Captcha model package — exports recognize_captcha_local for use by signup.py.
"""

import os

ONNX_MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "captcha.onnx")


def recognize_captcha_local(png_base64: str) -> str | None:
    """
    Recognize captcha text from a base64-encoded PNG using the local ONNX model.

    Args:
        png_base64: Base64-encoded PNG image of the captcha.

    Returns:
        Recognized captcha text (6 chars), or None if model is unavailable.
    """
    if not os.path.exists(ONNX_MODEL_PATH):
        print("    [local] ONNX model not found, skipping local recognition")
        return None

    try:
        from .predict import predict_from_png_base64
        result = predict_from_png_base64(png_base64, ONNX_MODEL_PATH)
        print(f"    [local] Recognized: {result}")
        return result
    except Exception as e:
        print(f"    [local] Recognition failed: {e}")
        return None
