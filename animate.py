"""Render a 2.5D parallax animation from an image and its depth map with Blender (bpy).

The image is mapped onto a finely subdivided plane, each vertex is pushed
toward the camera by the depth map, and a camera slowly pushes in while
drifting side to side, so near and far parts of the picture separate.

Usage:
    python animate.py image.png depth.png frames/
Then encode with ffmpeg (see README.md).
"""

import argparse
import math
import sys
import tempfile
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from PIL import Image

# ---------------------------------------------------------------- settings
FPS = 24
SECONDS = 10
RESOLUTION = 1080          # output height in pixels; width follows image aspect
GRID = 600                 # plane subdivisions per side (more = crisper depth edges)
DEPTH_STRENGTH = 0.32      # how far (in plane-widths/2) near pixels pop toward camera
FOCAL_MM = 50.0
START_DISTANCE = 3.4       # camera distance from the plane at frame 1
END_DISTANCE = 3.05        # ... and at the last frame (push-in)
SWAY_X = 0.08              # side-to-side camera drift amplitude
SWAY_Y = 0.03              # vertical drift amplitude
LOOK_AT = (0.0, 0.0)       # point on the plane the camera aims at (x, y), ~the portal
OVERSCAN = 1.0             # fraction of the plane visible at frame 1 (<1 hides edges)
CYCLES_SAMPLES = 24
# --------------------------------------------------------------------------


def ease_in_out(t: float) -> float:
    return 0.5 - 0.5 * math.cos(math.pi * t)


def reset_scene() -> bpy.types.Scene:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    return bpy.context.scene


def prefilter_texture(image_path: str) -> str:
    """Downscale big images to 2x the output height before Blender sees them.

    Cycles samples textures without mipmaps, so fine line art shrunk by much
    more than 2x shimmers as the camera moves. A Lanczos downscale to ~2x the
    render size keeps edges crisp and stable.
    """
    src = Image.open(image_path).convert("RGB")
    target_h = RESOLUTION * 2
    if src.height <= target_h:
        return image_path
    target_w = round(src.width * target_h / src.height)
    out = Path(tempfile.gettempdir()) / f"{Path(image_path).stem}_{target_h}.png"
    src.resize((target_w, target_h), Image.LANCZOS).save(out)
    return str(out)


def build_plane(image_path: str, depth_path: str) -> tuple[bpy.types.Object, float]:
    img = bpy.data.images.load(prefilter_texture(image_path))
    w, h = img.size
    aspect = w / h

    bpy.ops.mesh.primitive_grid_add(x_subdivisions=GRID, y_subdivisions=GRID, size=2.0, calc_uvs=True)
    plane = bpy.context.active_object
    plane.name = "ParallaxPlane"
    mesh = plane.data

    # Stretch to the image's aspect ratio, then bake the scale into the vertices.
    n = len(mesh.vertices)
    co = np.empty(n * 3, dtype=np.float32)
    mesh.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    co[:, 0] *= aspect

    # Sample the depth map at each vertex's position (vertex UV == grid position).
    depth_img = bpy.data.images.load(depth_path)
    dw, dh = depth_img.size
    px = np.array(depth_img.pixels[:], dtype=np.float32).reshape(dh, dw, depth_img.channels)[:, :, 0]
    u = (co[:, 0] / aspect + 1.0) / 2.0
    v = (co[:, 1] + 1.0) / 2.0  # Blender image pixels start at the bottom row
    ix = np.clip((u * (dw - 1)).round().astype(int), 0, dw - 1)
    iy = np.clip((v * (dh - 1)).round().astype(int), 0, dh - 1)
    co[:, 2] = px[iy, ix] * DEPTH_STRENGTH

    mesh.vertices.foreach_set("co", co.ravel())
    mesh.update()
    bpy.ops.object.shade_smooth()

    # Stand the plane upright facing -Y (depth now points toward -Y, image up is +Z).
    # The camera sits on the -Y side so world Z is a well-defined "up" for Track To.
    plane.rotation_euler = (math.radians(90), 0.0, 0.0)

    # Emission-only material: colours come out exactly as in the source image.
    mat = bpy.data.materials.new("ImageEmission")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.interpolation = "Cubic"
    tex.extension = "EXTEND"
    emit = nt.nodes.new("ShaderNodeEmission")
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(tex.outputs["Color"], emit.inputs["Color"])
    nt.links.new(emit.outputs["Emission"], out.inputs["Surface"])
    mesh.materials.append(mat)
    return plane, aspect


def build_camera(scene: bpy.types.Scene, aspect: float) -> None:
    cam_data = bpy.data.cameras.new("Camera")
    cam_data.lens = FOCAL_MM
    cam_data.sensor_fit = "VERTICAL"
    cam = bpy.data.objects.new("Camera", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam

    # Pick the sensor height so the frame-1 view covers OVERSCAN of the plane height.
    # Visible half-height at distance d: d * (sensor/2) / lens.
    cam_data.sensor_height = 2.0 * OVERSCAN * FOCAL_MM / START_DISTANCE

    target = bpy.data.objects.new("LookAt", None)
    target.location = (LOOK_AT[0], 0.0, LOOK_AT[1])
    scene.collection.objects.link(target)
    track = cam.constraints.new("TRACK_TO")
    track.target = target
    track.track_axis = "TRACK_NEGATIVE_Z"
    track.up_axis = "UP_Y"

    frames = FPS * SECONDS
    for f in range(1, frames + 1):
        t = (f - 1) / (frames - 1)
        e = ease_in_out(t)
        dist = START_DISTANCE + (END_DISTANCE - START_DISTANCE) * e
        # One slow left-to-right sweep plus a gentle vertical bob.
        x = -SWAY_X * math.cos(math.pi * e)
        y = LOOK_AT[1] + SWAY_Y * math.sin(2 * math.pi * t)
        cam.location = Vector((x, -dist, y))
        cam.keyframe_insert("location", frame=f)


def configure_render(scene: bpy.types.Scene, aspect: float, out_dir: str) -> None:
    scene.frame_start = 1
    scene.frame_end = FPS * SECONDS
    scene.render.fps = FPS
    scene.render.resolution_y = RESOLUTION
    scene.render.resolution_x = int(round(RESOLUTION * aspect / 2) * 2)  # even width for H.264
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = out_dir.rstrip("/") + "/frame_"
    scene.view_settings.view_transform = "Standard"  # keep source colours untouched
    scene.world = bpy.data.worlds.new("World")
    scene.world.color = (0, 0, 0)

    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = CYCLES_SAMPLES
    scene.cycles.use_denoising = False
    scene.cycles.max_bounces = 0  # emission only: no light transport needed
    scene.render.use_persistent_data = True  # don't rebuild the mesh BVH every frame


def main() -> None:
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("image")
    parser.add_argument("depth")
    parser.add_argument("out_dir")
    parser.add_argument("--frames", type=int, default=0, help="render only the first N frames (preview)")
    parser.add_argument("--step", type=int, default=1, help="render every Nth frame (preview)")
    args = parser.parse_args(argv)

    scene = reset_scene()
    _, aspect = build_plane(args.image, args.depth)
    build_camera(scene, aspect)
    configure_render(scene, aspect, args.out_dir)
    if args.frames:
        scene.frame_end = args.frames
    scene.frame_step = args.step
    bpy.ops.render.render(animation=True)


if __name__ == "__main__":
    main()
