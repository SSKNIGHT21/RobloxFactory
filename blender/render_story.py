"""
RobloxFactory vertical Shorts renderer.
Builds a stylised block-character kitchen story with animated acting, prop beats,
camera cuts, readable camera-locked captions, and a 45-second frame sequence.
Run: blender -b -t 2 --python blender/render_story.py
"""
import bpy
import json
import math
import os
import textwrap
from mathutils import Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
with open(os.path.join(ROOT, "story.json"), "r", encoding="utf-8") as handle:
    STORY = json.load(handle)
SCENES = STORY.get("scenes", [])
if len(SCENES) < 1:
    raise RuntimeError("story.json must contain at least one scene")

OUT = os.path.join(ROOT, "output")
FRAMES = os.path.join(OUT, "frames")
os.makedirs(FRAMES, exist_ok=True)

# Reset the file to a predictable starting state.
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
for collection in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.cameras):
    for block in list(collection):
        if block.users == 0:
            collection.remove(block)

scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
shade = scene.display.shading
shade.light = "STUDIO"
shade.studio_light = "paint.sl"
shade.color_type = "MATERIAL"
shade.show_shadows = True
shade.show_cavity = True
shade.cavity_type = "WORLD"
shade.background_type = "WORLD"
shade.background_color = (0.018, 0.025, 0.045)
shade.show_specular_highlight = True

DURATION = int(STORY.get("duration_seconds", 45))
FPS = 12
scene.render.resolution_x = 540
scene.render.resolution_y = 960
scene.render.resolution_percentage = 100
scene.render.fps = FPS
scene.frame_start = 1
scene.frame_end = DURATION * FPS
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGB"
scene.render.image_settings.color_depth = "8"
scene.render.film_transparent = False
scene.render.filepath = os.path.join(FRAMES, "frame_")
scene.render.use_file_extension = True
scene.render.image_settings.compression = 20

def mat(name, color):
    material = bpy.data.materials.new(name)
    material.diffuse_color = (*color, 1.0)
    return material

BLUE = mat("Toby | ocean blue", (0.08, 0.28, 0.78))
SKIN = mat("Toby | warm skin", (0.88, 0.56, 0.38))
HAIR = mat("Toby | dark hair", (0.035, 0.045, 0.07))
DARK = mat("Details | charcoal", (0.025, 0.035, 0.055))
RED = mat("Toaster | cherry red", (0.78, 0.075, 0.09))
SILVER = mat("Appliances | brushed silver", (0.46, 0.52, 0.60))
GOLD = mat("Magic | warm gold", (1.0, 0.56, 0.06))
TOAST = mat("Toast | golden brown", (0.72, 0.36, 0.12))
CREAM = mat("Toast | inner crumb", (0.95, 0.72, 0.38))
ORANGE = mat("Cat | bright orange", (0.96, 0.34, 0.045))
WHITE = mat("Caption | white", (1.0, 1.0, 1.0))
FLOOR = mat("Kitchen | floor", (0.12, 0.16, 0.22))
WALL = mat("Kitchen | midnight blue", (0.035, 0.065, 0.12))
CABINET = mat("Kitchen | cabinet", (0.18, 0.25, 0.36))
TEAL = mat("Kitchen | teal accent", (0.04, 0.48, 0.52))
PURPLE = mat("Confetti | purple", (0.48, 0.16, 0.86))
PINK = mat("Confetti | pink", (0.95, 0.16, 0.38))
GREEN = mat("Confetti | green", (0.12, 0.72, 0.36))

def cube(name, location, dimensions, material, bevel=0.045):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if material:
        obj.data.materials.append(material)
    if bevel:
        mod = obj.modifiers.new("Rounded toy edges", "BEVEL")
        mod.width = bevel
        mod.segments = 2
    return obj

def sphere(name, location, scale, material):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    obj.data.materials.append(material)
    return obj

def keep_parent(obj, parent):
    world = obj.matrix_world.copy()
    obj.parent = parent
    obj.matrix_world = world

def key(obj, frame, prop="location"):
    obj.keyframe_insert(data_path=prop, frame=frame)


# Stage: a compact, colourful kitchen set with a deep background.
cube("Stage floor", (0, 0, -0.22), (12, 12, 0.42), FLOOR, 0)
cube("Back wall", (0, 3.5, 3.0), (12, 0.3, 6.0), WALL, 0)
cube("Back cabinet", (0.35, 3.25, 4.0), (4.8, 0.22, 1.6), CABINET, 0.07)
for x in (-1.55, -0.35, 0.85, 2.05):
    cube("Cabinet door", (x, 3.10, 4.0), (1.05, 0.08, 1.34), SILVER, 0.035)
    cube("Cabinet handle", (x + 0.34, 3.02, 4.0), (0.055, 0.06, 0.35), DARK, 0.02)
cube("Window frame", (-2.7, 3.28, 3.0), (1.55, 0.12, 1.42), TEAL, 0.04)
cube("Window glass", (-2.7, 3.19, 3.0), (1.35, 0.035, 1.22), BLUE, 0.02)
cube("Counter top", (0.55, 0.12, 0.96), (3.7, 1.2, 0.22), SILVER, 0.07)
for x in (-0.85, 1.95):
    for y in (-0.26, 0.48):
        cube("Counter leg", (x, y, 0.46), (0.12, 0.12, 0.82), CABINET, 0.025)
cube("Counter front trim", (0.55, -0.48, 0.78), (3.62, 0.08, 0.13), TEAL, 0.02)
cube("Wall shelf", (0.9, 2.55, 2.55), (3.5, 0.65, 0.12), SILVER, 0.035)
for x, color in ((-0.1, GOLD), (0.65, ORANGE), (1.35, GREEN)):
    cube("Shelf canister", (x, 2.48, 2.86), (0.35, 0.34, 0.52), color, 0.06)

# Toby: block-built character with shoulder/hip pivots so he can act.
toby = bpy.data.objects.new("Toby | character root", None)
scene.collection.objects.link(toby)
toby.location = (-1.0, -0.42, 0)

def part(name, loc, dims, material, parent, bevel=0.04):
    obj = cube(name, loc, dims, material, bevel)
    keep_parent(obj, parent)
    return obj

part("Toby | torso", (-1.0, -0.42, 1.46), (0.84, 0.48, 1.0), BLUE, toby, 0.11)
part("Toby | shirt badge", (-1.0, -0.675, 1.58), (0.16, 0.035, 0.18), GOLD, toby, 0.025)
part("Toby | head", (-1.0, -0.42, 2.31), (0.72, 0.62, 0.72), SKIN, toby, 0.10)
part("Toby | hair cap", (-1.0, -0.41, 2.69), (0.77, 0.66, 0.19), HAIR, toby, 0.045)
part("Toby | hair fringe", (-1.0, -0.75, 2.56), (0.72, 0.12, 0.18), HAIR, toby, 0.03)
for x in (-1.16, -0.84):
    obj = sphere("Toby | eye", (x, -0.744, 2.35), (0.045, 0.03, 0.06), DARK)
    keep_parent(obj, toby)
mouth = cube("Toby | smile", (-1.0, -0.755, 2.17), (0.13, 0.025, 0.025), DARK, 0.01)
keep_parent(mouth, toby)

arm_pivots = []
for side, x in (("left", -1.49), ("right", -0.51)):
    pivot = bpy.data.objects.new("Toby | " + side + " arm pivot", None)
    scene.collection.objects.link(pivot)
    pivot.location = (x, -0.42, 1.83)
    keep_parent(pivot, toby)
    arm = cube("Toby | " + side + " sleeve", (x, -0.42, 1.49), (0.27, 0.34, 0.72), BLUE, 0.075)
    keep_parent(arm, pivot)
    hand = sphere("Toby | " + side + " hand", (x, -0.43, 1.11), (0.16, 0.15, 0.16), SKIN)
    keep_parent(hand, pivot)
    arm_pivots.append(pivot)

leg_pivots = []
for side, x in (("left", -1.23), ("right", -0.77)):
    pivot = bpy.data.objects.new("Toby | " + side + " leg pivot", None)
    scene.collection.objects.link(pivot)
    pivot.location = (x, -0.42, 0.98)
    keep_parent(pivot, toby)
    leg = cube("Toby | " + side + " leg", (x, -0.42, 0.63), (0.29, 0.36, 0.72), DARK, 0.045)
    keep_parent(leg, pivot)
    shoe = cube("Toby | " + side + " shoe", (x, -0.54, 0.29), (0.34, 0.48, 0.18), HAIR, 0.04)
    keep_parent(shoe, pivot)
    leg_pivots.append(pivot)

# Cat with a tail and expressive head.
cat = bpy.data.objects.new("Miso | character root", None)
scene.collection.objects.link(cat)
cat.location = (1.52, -0.10, 0)
cat_body = cube("Cat | body", (1.52, -0.10, 0.43), (0.68, 0.38, 0.40), ORANGE, 0.13)
keep_parent(cat_body, cat)
cat_head = sphere("Cat | head", (1.52, -0.25, 0.82), (0.31, 0.29, 0.30), ORANGE)
keep_parent(cat_head, cat)
for x in (1.31, 1.73):
    ear = bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0.13, radius2=0, depth=0.30, location=(x, -0.22, 1.08))
    keep_parent(bpy.context.object, cat)
for x in (1.42, 1.62):
    eye = sphere("Cat | eye", (x, -0.515, 0.85), (0.036, 0.024, 0.05), DARK)
    keep_parent(eye, cat)
nose = sphere("Cat | nose", (1.52, -0.548, 0.75), (0.045, 0.025, 0.03), PINK)
keep_parent(nose, cat)
tail = cube("Cat | tail", (1.88, 0.0, 0.62), (0.16, 0.18, 0.72), ORANGE, 0.07)
tail.rotation_euler[1] = math.radians(-28)
keep_parent(tail, cat)

# Toaster, toast, and the magic button.
toaster_x = 0.62
toaster = cube("Magic toaster", (toaster_x, 0.0, 1.57), (1.05, 0.78, 1.10), RED, 0.11)
cube("Toaster | top slot", (toaster_x, -0.02, 2.135), (0.58, 0.48, 0.035), DARK, 0.025)
button = sphere("Toaster | magic button", (toaster_x, -0.42, 1.56), (0.14, 0.07, 0.14), GOLD)
lever = cube("Toaster | side lever", (toaster_x + 0.59, 0.0, 1.57), (0.11, 0.12, 0.38), SILVER, 0.025)
toast = cube("Toast | slice", (toaster_x, -0.02, 2.42), (0.48, 0.14, 0.64), TOAST, 0.08)
toast_face = cube("Toast | crumb face", (toaster_x, -0.105, 2.42), (0.34, 0.025, 0.47), CREAM, 0.055)
glow = sphere("Magic | glow", (toaster_x, -0.60, 1.58), (0.18, 0.065, 0.18), GOLD)

# Camera with scene-specific framing and a stable on-screen caption panel.
bpy.ops.object.camera_add(location=(0, -10, 3.6))
camera = bpy.context.object
camera.name = "Story camera"
camera.data.lens = 48
camera.data.sensor_fit = "VERTICAL"
camera.data.sensor_height = 24
scene.camera = camera

def camera_pose(location, target):
    camera.location = location
    direction = Vector(target) - camera.location
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()

shot_map = {
    "wide": ((0.0, -12.2, 3.65), (0.1, 0.1, 1.55)),
    "toby": ((-1.0, -8.2, 3.05), (-1.0, 0.0, 1.75)),
    "toaster": ((0.62, -7.3, 2.95), (0.62, 0.0, 1.75)),
    "cat": ((1.5, -7.3, 2.65), (1.5, 0.0, 1.0)),
    "action": ((0.30, -9.0, 4.15), (0.25, 0.0, 1.65)),
}

# Caption backing and text stay locked to the camera, well inside the safe area.
panel = cube("Caption | dark panel", (0, 0, 0), (2.42, 0.42, 0.018), DARK, 0.045)
panel.parent = camera
panel.location = (0, -0.91, -5.15)
panel.rotation_euler = (0, 0, 0)
caption_objects = []
scene_count = len(SCENES)
segment = max(1, scene.frame_end // scene_count)
for index, item in enumerate(SCENES):
    curve = bpy.data.curves.new("Caption text %02d" % (index + 1), "FONT")
    curve.body = textwrap.fill(str(item.get("caption", "")), width=27)
    curve.align_x = "CENTER"
    curve.align_y = "CENTER"
    curve.size = 0.068
    curve.extrude = 0
    text_obj = bpy.data.objects.new("Caption %02d" % (index + 1), curve)
    scene.collection.objects.link(text_obj)
    text_obj.parent = camera
    text_obj.location = (0, -0.91, -5.125)
    text_obj.rotation_euler = (0, 0, 0)
    curve.materials.append(WHITE)
    start = index * segment + 1
    end = scene.frame_end if index == scene_count - 1 else min(scene.frame_end, (index + 1) * segment)
    text_obj.hide_render = True
    text_obj.keyframe_insert(data_path="hide_render", frame=max(1, start - 1))
    text_obj.hide_render = False
    text_obj.keyframe_insert(data_path="hide_render", frame=start)
    text_obj.keyframe_insert(data_path="hide_render", frame=end)
    text_obj.hide_render = True
    text_obj.keyframe_insert(data_path="hide_render", frame=min(scene.frame_end, end + 1))
    caption_objects.append(text_obj)

# Animate the characters according to each story beat.
for index, item in enumerate(SCENES):
    start = index * segment + 1
    end = scene.frame_end if index == scene_count - 1 else min(scene.frame_end, (index + 1) * segment)
    mid = (start + end) // 2
    action = item.get("action", ["walk", "surprise", "point", "jump", "panic", "fix", "celebrate"][index % 7])
    camera_name = item.get("camera", ["wide", "toaster", "toby", "cat", "action", "toby", "wide"][index % 7])
    location, target = shot_map.get(camera_name, shot_map["wide"])
    camera_pose(location, target)
    camera.keyframe_insert(data_path="location", frame=start)
    camera.keyframe_insert(data_path="rotation_euler", frame=start)
    camera_pose((location[0] + 0.05, location[1] + 0.25, location[2] + 0.04), target)
    camera.keyframe_insert(data_path="location", frame=end)
    camera.keyframe_insert(data_path="rotation_euler", frame=end)

    # Reset both arms and legs, then play one clear action per scene.
    for pivot in arm_pivots:
        pivot.rotation_euler = (0, 0, 0)
        key(pivot, start, "rotation_euler")
        key(pivot, end, "rotation_euler")
    for pivot in leg_pivots:
        pivot.rotation_euler = (0, 0, 0)
        key(pivot, start, "rotation_euler")
        key(pivot, end, "rotation_euler")

    if action == "walk":
        for side, pivot in enumerate(arm_pivots):
            pivot.rotation_euler.x = (-0.48 if side == 0 else 0.48)
            key(pivot, start + 1, "rotation_euler")
            pivot.rotation_euler.x *= -1
            key(pivot, mid, "rotation_euler")
        for side, pivot in enumerate(leg_pivots):
            pivot.rotation_euler.x = (0.48 if side == 0 else -0.48)
            key(pivot, start + 1, "rotation_euler")
            pivot.rotation_euler.x *= -1
            key(pivot, mid, "rotation_euler")
    elif action in ("surprise", "panic"):
        for pivot in arm_pivots:
            pivot.rotation_euler.y = -0.9
            pivot.rotation_euler.x = -0.35
            key(pivot, mid, "rotation_euler")
            pivot.rotation_euler.y = 0.0
            pivot.rotation_euler.x = 0.0
            key(pivot, end, "rotation_euler")
        toby.rotation_euler.z = -0.10 if action == "panic" else 0.06
        key(toby, mid, "rotation_euler")
        toby.rotation_euler.z = 0
        key(toby, end, "rotation_euler")
    elif action == "point":
        arm_pivots[1].rotation_euler.x = -1.35
        arm_pivots[1].rotation_euler.y = -0.25
        key(arm_pivots[1], mid, "rotation_euler")
    elif action == "jump":
        toby.location.z = 0.24
        key(toby, mid, "location")
        toby.location.z = 0
        key(toby, end, "location")
    elif action == "fix":
        toby.location.x = -0.28
        key(toby, mid, "location")
        arm_pivots[1].rotation_euler.x = -1.0
        key(arm_pivots[1], mid, "rotation_euler")
    elif action == "celebrate":
        toby.location.z = 0.28
        key(toby, mid, "location")
        toby.location.z = 0
        key(toby, end, "location")
        for pivot in arm_pivots:
            pivot.rotation_euler.y = 0.95
            key(pivot, mid, "rotation_euler")
            pivot.rotation_euler.y = 0
            key(pivot, end, "rotation_euler")

# The cat jumps up onto the counter during the cat beat and reacts to the magic.
cat_start = min(scene.frame_end, 3 * segment + 1)
cat_mid = min(scene.frame_end, cat_start + segment // 2)
cat_end = min(scene.frame_end, cat_start + segment)
cat.location.z = 0
key(cat, cat_start)
cat.location.z = 0.72
key(cat, cat_mid)
cat.location.z = 0.72
key(cat, cat_end)
cat.rotation_euler.y = -0.12
key(cat, cat_mid, "rotation_euler")

# Toast pops, rewinds, then lands back in the toaster.
toast_events = [
    (1, 2.42), (2 * segment, 2.42), (2 * segment + 12, 3.1),
    (3 * segment, 2.42), (4 * segment, 2.42),
    (4 * segment + 10, 3.35), (5 * segment, 2.42),
    (6 * segment, 2.42), (scene.frame_end, 2.42)
]
for frame, z in toast_events:
    toast.location.z = z
    toast_face.location.z = z
    key(toast, frame)
    key(toast_face, frame)
for frame in range(1, scene.frame_end + 1, max(1, FPS // 2)):
    pulse = 0.15 + 0.045 * (1 + math.sin(frame / 4.8))
    glow.scale = (pulse, 0.065, pulse)
    key(glow, frame, "scale")
button.location.z = 1.56
key(button, 1)
button.location.z = 1.49
key(button, min(scene.frame_end, 2 * segment + 12))
button.location.z = 1.56
key(button, min(scene.frame_end, 3 * segment))

# Small coloured confetti at the ending.
for i in range(12):
    x = -1.5 + (i % 6) * 0.58
    y = -0.2 + (i % 3) * 0.32
    color = (PURPLE, PINK, GOLD, GREEN)[i % 4]
    piece = cube("Ending | confetti %02d" % i, (x, y, 3.7 + (i % 4) * 0.2), (0.11, 0.07, 0.15), color, 0.02)
    piece.rotation_euler = (i * 0.2, i * 0.3, i * 0.4)
    key(piece, max(1, scene.frame_end - 2 * FPS))
    piece.location.z = 1.8 + (i % 3) * 0.2
    piece.rotation_euler.x += 1.5
    key(piece, scene.frame_end)

# Keep default Blender keyframe interpolation for compatibility across Blender 4/5.

scene.frame_set(1)
print("Rendering story:", STORY.get("title", "RobloxFactory"), "at", FPS, "fps for", DURATION, "seconds")
bpy.ops.render.render(animation=True)
print("Rendered", scene.frame_end, "frames into", FRAMES)
