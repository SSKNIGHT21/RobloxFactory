"""
RobloxFactory: fast vertical story renderer.
Run: blender -b --python blender/render_story.py
Input: story.json at repository root.
Optional voice track: audio/audio.wav (mixed into the final MP4 when present).
"""
import bpy
import json
import math
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
STORY_PATH = os.path.join(ROOT, "story.json")
OUTPUT_DIR = os.path.join(ROOT, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)
OUTPUT_VIDEO = os.path.join(OUTPUT_DIR, "roblox_story.mp4")

with open(STORY_PATH, "r", encoding="utf-8") as f:
    story = json.load(f)
scenes = story.get("scenes", [])
if not scenes:
    raise RuntimeError("story.json must contain at least one scene")

# Reset the default scene.
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
    for block in list(datablocks):
        if block.users == 0:
            datablocks.remove(block)

scene = bpy.context.scene

# Workbench avoids slow software-Eevee rendering on GitHub's CPU-only runners.
# It keeps the block-built Roblox-inspired look while rendering much faster.
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.studio_light = "paint.sl"
scene.display.shading.color_type = "MATERIAL"
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
scene.display.shading.cavity_type = "WORLD"
scene.display.shading.background_type = "WORLD"
scene.display.shading.background_color = (0.025, 0.035, 0.06)

# Vertical Shorts output. 12 fps is intentional: half the old frame count,
# still smooth enough for this stylised, story-driven animation.
scene.render.resolution_x = 540
scene.render.resolution_y = 960
scene.render.resolution_percentage = 100
scene.render.fps = 12
scene.frame_start = 1
fps = scene.render.fps
total_seconds = int(story.get("duration_seconds", 45))
scene.frame_end = total_seconds * fps

FRAMES_DIR = os.path.join(OUTPUT_DIR, "frames")
os.makedirs(FRAMES_DIR, exist_ok=True)
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGB"
scene.render.filepath = os.path.join(FRAMES_DIR, "frame_")
scene.render.film_transparent = False

def material(name, color, roughness=0.8, emission=0.0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    return m

blue = material("Toby blue", (0.12, 0.35, 0.85))
skin = material("Warm skin", (0.92, 0.62, 0.42))
dark = material("Dark details", (0.035, 0.045, 0.07))
red = material("Toaster red", (0.8, 0.12, 0.12))
silver = material("Toaster silver", (0.45, 0.5, 0.58))
gold = material("Magic gold", (1.0, 0.62, 0.08))
toast_mat = material("Toast", (0.75, 0.42, 0.16))
cat_mat = material("Cat orange", (0.95, 0.42, 0.08))
floor_mat = material("Floor", (0.12, 0.16, 0.23))

def cube(name, loc, scale, mat, bevel=0.08):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if mat:
        obj.data.materials.append(mat)
    if bevel:
        mod = obj.modifiers.new("Soft block edges", "BEVEL")
        mod.width = bevel
        mod.segments = 1
    return obj

def sphere(name, loc, scale, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=6, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    obj.data.materials.append(mat)
    return obj

# Kitchen set
cube("Kitchen floor", (0, 0, -0.25), (12, 12, 0.5), floor_mat, 0)
cube("Back wall", (0, 3.5, 3), (12, 0.3, 6), dark, 0)

# Toby
cube("Toby torso", (-1.2, 0, 1.45), (0.85, 0.5, 1.0), blue)
cube("Toby head", (-1.2, 0, 2.25), (0.72, 0.62, 0.72), skin)
cube("Toby hair", (-1.2, 0, 2.64), (0.75, 0.64, 0.18), dark)
for x in (-1.38, -1.02):
    sphere("Toby eye", (x, -0.32, 2.3), (0.045, 0.035, 0.06), dark)
for x in (-1.42, -0.98):
    cube("Toby leg", (x, 0, 0.65), (0.28, 0.35, 0.75), dark)

# Toaster and toast
cube("Counter", (0.8, 0.2, 0.65), (3.4, 1.1, 0.25), silver)
cube("Magic toaster", (0.8, 0, 1.35), (1.1, 0.8, 1.0), red)
cube("Toast slice", (0.8, -0.02, 2.0), (0.55, 0.12, 0.7), toast_mat)
sphere("Magic glow", (0.8, -0.55, 1.65), (0.18, 0.08, 0.18), gold)

# Cat
cube("Cat body", (2.0, -0.1, 0.85), (0.65, 0.35, 0.42), cat_mat)
sphere("Cat head", (2.0, -0.2, 1.2), (0.28, 0.25, 0.27), cat_mat)
for x in (1.82, 2.18):
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0.13, radius2=0, depth=0.3, location=(x, -0.2, 1.48))
    bpy.context.object.data.materials.append(cat_mat)
for x in (1.91, 2.09):
    sphere("Cat eye", (x, -0.43, 1.22), (0.035, 0.025, 0.045), dark)

# Camera
bpy.ops.object.camera_add(location=(0, -10, 3.1))
camera = bpy.context.object
camera.name = "Story camera"
camera.data.lens = 48
camera.rotation_euler = (math.radians(78), 0, 0)
scene.camera = camera
camera.location = (0, -10.8, 3.2)
camera.keyframe_insert(data_path="location", frame=1)
camera.location = (0, -9.7, 3.0)
camera.keyframe_insert(data_path="location", frame=scene.frame_end)

# Captions, one at a time.
segment = max(1, scene.frame_end // len(scenes))
for i, item in enumerate(scenes):
    curve = bpy.data.curves.new("Caption", "FONT")
    curve.body = item.get("caption", "")
    curve.align_x = "CENTER"
    curve.size = 0.42
    text_obj = bpy.data.objects.new("Caption %02d" % (i + 1), curve)
    scene.collection.objects.link(text_obj)
    text_obj.location = (0, -1.1, 4.35)
    text_obj.rotation_euler = (math.radians(90), 0, 0)
    curve.materials.append(material("Caption material %02d" % i, (1, 1, 1)))
    start = i * segment + 1
    end = scene.frame_end if i == len(scenes) - 1 else (i + 1) * segment
    text_obj.hide_render = True
    text_obj.keyframe_insert(data_path="hide_render", frame=max(1, start - 1))
    text_obj.hide_render = False
    text_obj.keyframe_insert(data_path="hide_render", frame=start)
    text_obj.keyframe_insert(data_path="hide_render", frame=end)
    text_obj.hide_render = True
    text_obj.keyframe_insert(data_path="hide_render", frame=min(scene.frame_end, end + 1))

# Animate the magic glow gently.
glow = bpy.data.objects.get("Magic glow")
if glow:
    for frame in range(1, scene.frame_end + 1, 12):
        pulse = 0.15 + 0.05 * (1 + math.sin(frame / 4))
        glow.scale = (pulse, 0.08, pulse)
        glow.keyframe_insert(data_path="scale", frame=frame)

scene.frame_set(1)
scene.render.filepath = os.path.join(FRAMES_DIR, "frame_")
print("Rendering:", story.get("title", "RobloxFactory story"), "to", OUTPUT_VIDEO)
bpy.ops.render.render(animation=True)
print("Render complete:", OUTPUT_VIDEO)
