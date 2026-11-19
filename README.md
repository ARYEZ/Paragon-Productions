# Paragon Productions: 2.5D parallax animation

Turns a still image into a 10-second camera-move animation using Blender (`bpy`).

1. `depth_map.py` estimates a depth map with the MiDaS v2.1 small model (ONNX, CPU).
2. `animate.py` builds a plane in Blender, pushes each vertex toward the camera by
   its depth, and renders a slow push-in with a side-to-side drift (Cycles, CPU).
3. ffmpeg encodes the frames to MP4.

## Setup (Python 3.13)

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
mkdir -p models && curl -L -o models/midas_small.onnx https://github.com/isl-org/MiDaS/releases/download/v2_1/model-small.onnx
```

## Run

```bash
python depth_map.py input.png depth.png
python animate.py input.png depth.png frames/
ffmpeg -framerate 24 -i frames/frame_%04d.png -c:v libx264 -pix_fmt yuv420p -crf 18 output.mp4
```

Preview a few frames first with `python animate.py input.png depth.png frames/ --step 60`.
Camera path, depth strength, length and resolution are constants at the top of `animate.py`.
