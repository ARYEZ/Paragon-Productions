"""Estimate a depth map for an image using the MiDaS v2.1 small ONNX model.

Output is a 16-bit grayscale PNG the same size as the input, where
white = near the camera and black = far away. animate.py uses it to
displace a plane for the 2.5D parallax effect.

Usage:
    python depth_map.py input.png depth.png --model models/midas_small.onnx
"""

import argparse

import cv2
import numpy as np
import onnxruntime as ort
from PIL import Image

MODEL_SIZE = 256  # MiDaS small expects 256x256 input
IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
IMAGENET_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)


def estimate_depth(image_rgb: np.ndarray, model_path: str) -> np.ndarray:
    """Return a float32 depth map in [0, 1] (1 = nearest) at the image's size."""
    h, w = image_rgb.shape[:2]
    session = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])

    x = cv2.resize(image_rgb, (MODEL_SIZE, MODEL_SIZE), interpolation=cv2.INTER_AREA)
    x = (x.astype(np.float32) / 255.0 - IMAGENET_MEAN) / IMAGENET_STD
    x = x.transpose(2, 0, 1)[None]  # HWC -> NCHW

    inv_depth = session.run(None, {session.get_inputs()[0].name: x})[0][0]

    # Upscale back to the source resolution.
    depth = cv2.resize(inv_depth, (w, h), interpolation=cv2.INTER_CUBIC)

    # Normalise using percentiles so a few outlier pixels don't squash the range.
    lo, hi = np.percentile(depth, [1, 99])
    depth = np.clip((depth - lo) / max(hi - lo, 1e-6), 0.0, 1.0).astype(np.float32)
    return depth


def smooth_depth(depth: np.ndarray, image_rgb: np.ndarray) -> np.ndarray:
    """Soften depth edges so the displaced mesh doesn't tear or stretch harshly.

    A bilateral filter keeps the big depth boundaries (figure vs. background)
    while removing the blocky artifacts from upscaling a 256px prediction.
    A final light Gaussian blur rounds off whatever stair-steps remain.
    """
    scale = max(image_rgb.shape[:2]) / 1000.0
    d = cv2.bilateralFilter(depth, d=int(9 * scale) | 1, sigmaColor=0.1, sigmaSpace=8 * scale)
    k = int(7 * scale) | 1
    return cv2.GaussianBlur(d, (k, k), 0)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input", help="source image")
    parser.add_argument("output", help="where to write the 16-bit depth PNG")
    parser.add_argument("--model", default="models/midas_small.onnx", help="path to MiDaS small ONNX model")
    args = parser.parse_args()

    image = np.array(Image.open(args.input).convert("RGB"))
    depth = smooth_depth(estimate_depth(image, args.model), image)
    cv2.imwrite(args.output, (depth * 65535).astype(np.uint16))
    print(f"wrote {args.output} ({depth.shape[1]}x{depth.shape[0]})")


if __name__ == "__main__":
    main()
