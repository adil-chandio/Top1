#!/usr/bin/env python3
"""
Thermal Shock V5 — Exact Zack D. Films 3D Parity (Blender 4.2 LTS Cycles).
Matches all 8 panels of our approved AI Contact Sheet:
  - Razor-sharp focus (NO blurry DoF!)
  - Bright Sunlit Calacatta Marble Kitchen + Warm Oak Cabinets + Posed 3D Character (S1, S2, S6, S7, S8)
  - High-Contrast Dark-Navy Scientific Cutaway Studio (S3 FLIR X-Ray, S4 Atomic Shear, S5 Inner Core)
  - Light-Path transparent-shadow crystal glass & water (zero muddy black glass!)
"""
import argparse
import json
import math
import os
import random
import sys

import bpy
import bmesh
from mathutils import Euler, Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
parser = argparse.ArgumentParser()
parser.add_argument("--start", type=int, default=0)
parser.add_argument("--end", type=int, default=35)
parser.add_argument("--frames", type=str, default="")
parser.add_argument("--out", type=str, default="/tmp/v5_frames")
parser.add_argument("--lock", type=str, default="tools/thermal-shock/voice-lock.json")
parser.add_argument("--samples", type=int, default=28)
parser.add_argument("--res-x", type=int, default=720)
parser.add_argument("--res-y", type=int, default=1280)
args = parser.parse_args(argv)

os.makedirs(args.out, exist_ok=True)
with open(args.lock, "r", encoding="utf-8") as f:
    LOCK = json.load(f)

TOTAL_FRAMES = LOCK["total_frames"]
FPS = LOCK.get("fps", 30)
VAC = LOCK["vacuum_window"]
SHATTER_F = LOCK["shatter_frame"]

# ==============================================================================
# 1. CYCLES + OIDN + AgX CRISP STUDIO ENGINE (ZERO BLUR!)
# ==============================================================================
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = args.samples
scene.cycles.use_adaptive_sampling = True
scene.cycles.adaptive_threshold = 0.025
scene.cycles.use_denoising = True
scene.cycles.denoiser = "OPENIMAGEDENOISE"
scene.cycles.max_bounces = 12
scene.cycles.diffuse_bounces = 3
scene.cycles.glossy_bounces = 6
scene.cycles.transmission_bounces = 12
scene.cycles.transparent_max_bounces = 8
scene.cycles.sample_clamp_indirect = 10.0

scene.render.resolution_x = args.res_x
scene.render.resolution_y = args.res_y
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGB"
scene.render.fps = FPS

scene.view_settings.view_transform = "AgX"
try:
    scene.view_settings.look = "AgX - Medium High Contrast"
except Exception:
    pass
scene.view_settings.exposure = -1.10

world = bpy.data.worlds.new("ZackDWorld")
scene.world = world
world.use_nodes = True
bg_node = world.node_tree.nodes.get("Background")
bg_node.inputs[0].default_value = (0.28, 0.30, 0.34, 1.0)
bg_node.inputs[1].default_value = 0.25

# ==============================================================================
# 2. DUAL LIGHTING RIG (Balanced Cinema Exposure — ZERO White Blowout!)
# ==============================================================================
def add_area_light(name, loc, rot_deg, energy, sx, sy, color):
    ld = bpy.data.lights.new(name=name, type="AREA")
    ld.energy = energy
    ld.shape = "RECTANGLE"
    ld.size = sx
    ld.size_y = sy
    ld.color = color
    lo = bpy.data.objects.new(name=name, object_data=ld)
    lo.location = loc
    lo.rotation_euler = tuple(math.radians(a) for a in rot_deg)
    scene.collection.objects.link(lo)
    return lo

l_sun   = add_area_light("KitchenSunWindow", (-0.55, -0.25, 0.45), (52, 0, -58), 9.0, 0.55, 0.45, (1.0, 0.92, 0.82))
l_fill  = add_area_light("KitchenFill",      ( 0.50, -0.35, 0.38), (58, 0,  52), 4.0, 0.50, 0.40, (0.78, 0.88, 1.0))
l_rim   = add_area_light("StudioRimBack",    ( 0.00,  0.42, 0.34), (-52, 0,  0), 6.5, 0.45, 0.26, (1.0, 0.96, 0.90))

# ==============================================================================
# 3. MATERIALS (Light-Path Glass, White Calacatta Marble, Warm Oak, FLIR Glow)
# ==============================================================================
def make_real_glass_mat(name, ior=1.52, roughness=0.008, tint=(0.98, 0.995, 1.0, 1.0)):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    mix = nt.nodes.new("ShaderNodeMixShader")
    lp = nt.nodes.new("ShaderNodeLightPath")
    trans = nt.nodes.new("ShaderNodeBsdfTransparent")
    trans.inputs["Color"].default_value = (0.94, 0.98, 1.0, 1.0)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = tint
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["IOR"].default_value = ior
    bsdf.inputs["Transmission Weight"].default_value = 1.0
    if "Coat Weight" in bsdf.inputs:
        bsdf.inputs["Coat Weight"].default_value = 0.90
    nt.links.new(lp.outputs["Is Shadow Ray"], mix.inputs["Fac"])
    nt.links.new(bsdf.outputs["BSDF"], mix.inputs[1])
    nt.links.new(trans.outputs["BSDF"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    return mat

def make_calacatta_marble():
    mat = bpy.data.materials.new("CalacattaMarble")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.08
    if "Coat Weight" in bsdf.inputs:
        bsdf.inputs["Coat Weight"].default_value = 0.75
    tc = nt.nodes.new("ShaderNodeTexCoord")
    ns = nt.nodes.new("ShaderNodeTexNoise")
    ns.inputs["Scale"].default_value = 14.0
    ns.inputs["Detail"].default_value = 10.0
    ns.inputs["Distortion"].default_value = 2.6
    rmp = nt.nodes.new("ShaderNodeValToRGB")
    rmp.color_ramp.elements[0].position = 0.42
    rmp.color_ramp.elements[0].color = (0.58, 0.60, 0.64, 1.0)
    rmp.color_ramp.elements[1].position = 0.56
    rmp.color_ramp.elements[1].color = (0.95, 0.95, 0.94, 1.0)
    nt.links.new(tc.outputs["Object"], ns.inputs["Vector"])
    nt.links.new(ns.outputs["Fac"], rmp.inputs["Fac"])
    nt.links.new(rmp.outputs["Color"], bsdf.inputs["Base Color"])
    return mat

def make_oak_mat():
    mat = bpy.data.materials.new("SunlitOak")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.36
    tc = nt.nodes.new("ShaderNodeTexCoord")
    ns = nt.nodes.new("ShaderNodeTexNoise")
    ns.inputs["Scale"].default_value = 30.0
    ns.inputs["Detail"].default_value = 6.0
    rmp = nt.nodes.new("ShaderNodeValToRGB")
    rmp.color_ramp.elements[0].position = 0.3
    rmp.color_ramp.elements[0].color = (0.44, 0.28, 0.14, 1.0)
    rmp.color_ramp.elements[1].position = 0.7
    rmp.color_ramp.elements[1].color = (0.64, 0.44, 0.24, 1.0)
    nt.links.new(tc.outputs["Object"], ns.inputs["Vector"])
    nt.links.new(ns.outputs["Fac"], rmp.inputs["Fac"])
    nt.links.new(rmp.outputs["Color"], bsdf.inputs["Base Color"])
    return mat

def make_steam_mat():
    mat = bpy.data.materials.new("CrispSteam")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    mix = nt.nodes.new("ShaderNodeMixShader")
    trans = nt.nodes.new("ShaderNodeBsdfTransparent")
    emis = nt.nodes.new("ShaderNodeEmission")
    emis.inputs["Color"].default_value = (0.95, 0.97, 1.0, 1.0)
    emis.inputs["Strength"].default_value = 1.1
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.45
    mth = nt.nodes.new("ShaderNodeMath")
    mth.operation = "MULTIPLY"
    mth.inputs[1].default_value = 0.22
    nt.links.new(lw.outputs["Facing"], mth.inputs[0])
    nt.links.new(mth.outputs["Value"], mix.inputs["Fac"])
    nt.links.new(trans.outputs["BSDF"], mix.inputs[1])
    nt.links.new(emis.outputs["Emission"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    return mat

def make_pbr(name, color, roughness=0.22, metallic=0.0, emission=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if emission > 0 and "Emission Color" in bsdf.inputs:
        bsdf.inputs["Emission Color"].default_value = color
        bsdf.inputs["Emission Strength"].default_value = emission
    return mat

mat_glass      = make_real_glass_mat("RealGlass", ior=1.52, roughness=0.006)
mat_water      = make_real_glass_mat("RealWater", ior=1.333, roughness=0.012, tint=(0.90, 0.97, 1.0, 1.0))
mat_cold_water = make_real_glass_mat("ColdWater", ior=1.333, roughness=0.012, tint=(0.35, 0.80, 1.0, 1.0))
mat_marble     = make_calacatta_marble()
mat_oak        = make_oak_mat()
mat_wall       = make_pbr("KitchenWall", (0.92, 0.91, 0.88, 1.0), roughness=0.55)
mat_steel      = make_pbr("BrushedSteel", (0.85, 0.88, 0.92, 1.0), roughness=0.14, metallic=0.96)
mat_black      = make_pbr("MatteBlack", (0.05, 0.05, 0.06, 1.0), roughness=0.40)
mat_steam      = make_steam_mat()
mat_flir_cold  = make_real_glass_mat("FLIR_Cold", ior=1.45, roughness=0.04, tint=(0.05, 0.72, 1.0, 1.0))
mat_flir_hot   = make_real_glass_mat("FLIR_Hot",  ior=1.45, roughness=0.04, tint=(1.0, 0.28, 0.03, 1.0))
mat_arrow_cold = make_pbr("ArrowCold", (0.04, 0.68, 1.0, 1.0), roughness=0.12, emission=1.6)
mat_arrow_hot  = make_pbr("ArrowHot",  (1.0, 0.32, 0.02, 1.0), roughness=0.12, emission=1.8)
mat_bond_cold  = make_pbr("BondCold",  (0.08, 0.62, 0.95, 1.0), roughness=0.18, metallic=0.4, emission=0.4)
mat_bond_hot   = make_pbr("BondHot",   (0.95, 0.30, 0.05, 1.0), roughness=0.18, metallic=0.4, emission=0.5)
mat_bond_snap  = make_pbr("BondSnap",  (1.0, 0.78, 0.12, 1.0), roughness=0.12, emission=2.2)
mat_crack      = make_pbr("CrackGlow", (0.15, 0.75, 1.0, 1.0), roughness=0.08, emission=2.5)

# ==============================================================================
# 4. GEOMETRY HELPERS
# ==============================================================================
def build_lathe(name, profile_rz, segs, mat, col, arc_rad=6.2831853, start_ang=0.0, cap_ends=True):
    bm = bmesh.new()
    rings = []
    steps = segs if arc_rad >= 6.28 else segs + 1
    for r, z in profile_rz:
        ring = []
        for s in range(steps):
            a = start_ang + (s / segs) * arc_rad
            ring.append(bm.verts.new((math.cos(a) * r, math.sin(a) * r, z)))
        rings.append(ring)
    for i in range(len(rings) - 1):
        for s in range(segs):
            s2 = (s + 1) % steps if arc_rad >= 6.28 else s + 1
            bm.faces.new((rings[i][s], rings[i][s2], rings[i + 1][s2], rings[i + 1][s]))
    if cap_ends and arc_rad >= 6.28:
        bm.faces.new(rings[0][::-1])
        bm.faces.new(rings[-1])
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    for p in mesh.polygons:
        p.use_smooth = True
    obj = bpy.data.objects.new(name, mesh)
    obj.data.materials.append(mat)
    col.objects.link(obj)
    return obj

def add_box(name, loc, scale, mat, col):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = scale
    o.data.materials.append(mat)
    scene.collection.objects.unlink(o)
    col.objects.link(o)
    return o

def add_3d_arrow(name, p_start, p_end, mat, col, radius=0.0020):
    v = Vector(p_end) - Vector(p_start)
    dist = v.length
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=radius, depth=dist * 0.66)
    shaft = bpy.context.active_object
    shaft.location = Vector(p_start) + v * 0.33
    shaft.rotation_euler = v.to_track_quat("Z", "Y").to_euler()
    shaft.data.materials.append(mat)
    scene.collection.objects.unlink(shaft)
    col.objects.link(shaft)

    bpy.ops.mesh.primitive_cone_add(vertices=12, radius1=radius * 2.4, radius2=0.0, depth=dist * 0.36)
    head = bpy.context.active_object
    head.location = Vector(p_start) + v * 0.82
    head.rotation_euler = v.to_track_quat("Z", "Y").to_euler()
    head.data.materials.append(mat)
    scene.collection.objects.unlink(head)
    col.objects.link(head)
    return [shaft, head]

# ==============================================================================
# 5. SET A: BRIGHT SUNLIT MODERN KITCHEN + POSED 3D CHARACTER (S1, S2, S6, S7, S8)
# ==============================================================================
kitchen_col = bpy.data.collections.new("SunlitKitchen")
scene.collection.children.link(kitchen_col)

# White Calacatta Marble Countertop + Clean Kitchen Wall + Sunlit Oak Cabinets
add_box("CalacattaCounter", (0, 0.04, -0.02), (1.8, 0.85, 0.04), mat_marble, kitchen_col)
add_box("KitchenBackWall",  (0, 0.78,  0.42), (2.2, 0.04, 1.10), mat_wall,   kitchen_col)
add_box("LeftOakCabinet",  (-0.36, 0.68, 0.48), (0.36, 0.22, 0.42), mat_oak, kitchen_col)
add_box("RightOakCabinet", ( 0.38, 0.68, 0.48), (0.38, 0.22, 0.42), mat_oak, kitchen_col)
add_box("LowerOakBase",    ( 0.00, 0.68, 0.02), (1.60, 0.24, 0.26), mat_oak, kitchen_col)

# Import & Pose Rigged 3D Human (`homeowner.glb`) — Natural Stance (NOT T-pose!)
human_root = None
human_armature = None
glb_path = os.path.abspath("tools/monarch-cockroach/v4/assets/homeowner.glb")
if os.path.exists(glb_path):
    bpy.ops.import_scene.gltf(filepath=glb_path)
    imported = [o for o in bpy.context.selected_objects]
    human_root = bpy.data.objects.new("HumanRoot", None)
    kitchen_col.objects.link(human_root)
    human_root.location = (0.04, 0.38, -0.40)
    human_root.rotation_euler = (0, 0, math.radians(180))
    human_root.scale = (0.48, 0.48, 0.48)
    for o in imported:
        if o.type == "ARMATURE":
            human_armature = o
        if o.parent is None:
            o.parent = human_root
        if o.name in scene.collection.objects:
            scene.collection.objects.unlink(o)
        if o.name not in kitchen_col.objects:
            kitchen_col.objects.link(o)

def pose_human(mode="curious"):
    if human_armature is None:
        return
    pb = human_armature.pose.bones
    for b in pb:
        b.rotation_mode = "XYZ"
        b.rotation_euler = (0, 0, 0)
    def set_b(substr, rx, ry, rz):
        for name, b in pb.items():
            if substr in name:
                b.rotation_euler = (math.radians(rx), math.radians(ry), math.radians(rz))
    if mode == "curious":
        set_b("LeftArm",  18, 0,  62)
        set_b("RightArm", 18, 0, -62)
        set_b("LeftForeArm", 15, 0, 0)
        set_b("RightForeArm", 15, 0, 0)
        set_b("Head", 12, 0, 0)
    elif mode == "shock":
        set_b("LeftArm", -45, 0,  28)
        set_b("RightArm", -45, 0, -28)
        set_b("LeftForeArm", -65, 0, 0)
        set_b("RightForeArm", -65, 0, 0)
        set_b("Spine", -12, 0, 0)
    elif mode == "outro":
        set_b("LeftArm",  28, 0,  55)
        set_b("RightArm", 28, 0, -55)
        set_b("Head", 22, 0, 0)

# Hero Glass + Boiling Water + Bubbles + Steam + Pitcher
glass_obj = build_lathe("HeroGlass", [
    (0.029, 0.0002), (0.033, 0.003), (0.038, 0.016), (0.041, 0.058), (0.039, 0.105),
    (0.0380, 0.108), (0.0358, 0.108), (0.0364, 0.101), (0.0372, 0.058), (0.0332, 0.020), (0.0278, 0.014),
], 72, mat_glass, kitchen_col)

water_obj = build_lathe("BoilingWater", [
    (0.0275, 0.0145), (0.0328, 0.020), (0.0368, 0.058), (0.0362, 0.086),
], 56, mat_water, kitchen_col)

bubbles = []
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.0017)
bub_mesh = bpy.context.active_object.data
bub_mesh.materials.append(mat_glass)
bpy.data.objects.remove(bpy.context.active_object, do_unlink=True)
for i in range(65):
    bo = bpy.data.objects.new(f"Bubble_{i}", bub_mesh)
    kitchen_col.objects.link(bo)
    bubbles.append((bo, (i * 2.39996) % 6.283, 0.004 + ((i * 0.013) % 0.027), 0.32 + (i % 7) * 0.08, (i * 0.37) % 1.0))

steam_wisps = []
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.014)
steam_mesh = bpy.context.active_object.data
for p in steam_mesh.polygons:
    p.use_smooth = True
steam_mesh.materials.append(mat_steam)
bpy.data.objects.remove(bpy.context.active_object, do_unlink=True)
for i in range(18):
    so = bpy.data.objects.new(f"Steam_{i}", steam_mesh)
    kitchen_col.objects.link(so)
    steam_wisps.append((so, (i * 1.9) % 6.283, i / 18.0))

# Brushed Steel Pitcher + Handle + Pour Stream
pitcher_root = bpy.data.objects.new("PitcherRoot", None)
kitchen_col.objects.link(pitcher_root)
p_body = build_lathe("PitcherBody", [
    (0.036, -0.052), (0.040, -0.044), (0.038, 0.035), (0.032, 0.062),
], 48, mat_steel, kitchen_col)
p_body.parent = pitcher_root
bpy.ops.curve.primitive_bezier_curve_add()
p_handle = bpy.context.active_object
p_handle.data.bevel_depth = 0.0048
p_handle.data.splines[0].bezier_points[0].co = Vector((-0.034, 0, 0.048))
p_handle.data.splines[0].bezier_points[0].handle_right = Vector((-0.078, 0, 0.048))
p_handle.data.splines[0].bezier_points[1].co = Vector((-0.038, 0, -0.032))
p_handle.data.splines[0].bezier_points[1].handle_left = Vector((-0.078, 0, -0.032))
p_handle.data.materials.append(mat_steel)
scene.collection.objects.unlink(p_handle)
kitchen_col.objects.link(p_handle)
p_handle.parent = pitcher_root

bpy.ops.curve.primitive_bezier_curve_add()
pour_curve = bpy.context.active_object
pour_curve.data.bevel_depth = 0.0046
pour_curve.data.bevel_resolution = 8
pour_curve.data.materials.append(mat_cold_water)
scene.collection.objects.unlink(pour_curve)
kitchen_col.objects.link(pour_curve)

# ==============================================================================
# 6. SET B: DARK-NAVY FLIR THERMAL X-RAY CUTAWAY (S3 & S5)
# ==============================================================================
flir_col = bpy.data.collections.new("ThermalCutawaySet")
scene.collection.children.link(flir_col)

build_lathe("FLIR_OuterCold", [(0.039, 0.014), (0.042, 0.058), (0.040, 0.106)],
            48, mat_flir_cold, flir_col, arc_rad=math.pi * 1.15, start_ang=-0.25, cap_ends=False)
build_lathe("FLIR_InnerHot",  [(0.033, 0.014), (0.036, 0.058), (0.034, 0.104)],
            48, mat_flir_hot,  flir_col, arc_rad=math.pi * 1.15, start_ang=-0.25, cap_ends=False)

for az in [0.032, 0.058, 0.084]:
    add_3d_arrow(f"CompL_{az}", (-0.068, -0.005, az), (-0.043, -0.005, az), mat_arrow_cold, flir_col, 0.0019)
    add_3d_arrow(f"CompR_{az}", ( 0.068, -0.005, az), ( 0.043, -0.005, az), mat_arrow_cold, flir_col, 0.0019)
    add_3d_arrow(f"ExpL_{az}",  (-0.012, -0.008, az), (-0.033, -0.008, az), mat_arrow_hot,  flir_col, 0.0019)
    add_3d_arrow(f"ExpR_{az}",  ( 0.012, -0.008, az), ( 0.033, -0.008, az), mat_arrow_hot,  flir_col, 0.0019)

# ==============================================================================
# 7. SET C: MICROSCOPIC SiO2 ATOMIC SHEAR LATTICE (S4)
# ==============================================================================
mol_col = bpy.data.collections.new("MolecularSet")
scene.collection.children.link(mol_col)
bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=16, radius=0.0068)
atom_mesh = bpy.context.active_object.data
for p in atom_mesh.polygons:
    p.use_smooth = True
bpy.data.objects.remove(bpy.context.active_object, do_unlink=True)

bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.0016, depth=1.0)
bond_mesh = bpy.context.active_object.data
for p in bond_mesh.polygons:
    p.use_smooth = True
bpy.data.objects.remove(bpy.context.active_object, do_unlink=True)

def place_rod(obj, p1, p2):
    v = p2 - p1
    dist = v.length
    if dist < 1e-5:
        obj.hide_render = True
        return
    obj.location = (p1 + p2) * 0.5
    obj.scale = (1.0, 1.0, dist)
    obj.rotation_euler = v.to_track_quat("Z", "Y").to_euler()

mat_atom_cold  = make_pbr("AtomCold",  (0.03, 0.65, 1.0, 1.0), roughness=0.14, metallic=0.2, emission=0.8)
mat_atom_hot   = make_pbr("AtomHot",   (1.0, 0.22, 0.02, 1.0), roughness=0.14, metallic=0.2, emission=1.1)
cold_atoms, hot_atoms = [], []
for iz in range(4):
    for iy in range(3):
        for ix in range(3):
            x = -0.018 - ix * 0.023
            y = (iy - 1) * 0.025
            z = (iz - 1.5) * 0.025
            ca = bpy.data.objects.new(f"Cold_{ix}_{iy}_{iz}", atom_mesh.copy())
            ca.data.materials.append(mat_atom_cold)
            mol_col.objects.link(ca)
            cold_atoms.append((ca, x, y, z, (ix + iy * 3 + iz * 9) * 0.71, ix, iy, iz))

            ha = bpy.data.objects.new(f"Hot_{ix}_{iy}_{iz}", atom_mesh.copy())
            ha.data.materials.append(mat_atom_hot)
            mol_col.objects.link(ha)
            hot_atoms.append((ha, -x, y, z, (ix + iy * 3 + iz * 9) * 0.93, ix, iy, iz))

bridge_bonds = []
for iz in range(4):
    for iy in range(3):
        bo = bpy.data.objects.new(f"Bridge_{iy}_{iz}", bond_mesh.copy())
        bo.data.materials.append(mat_bond_snap)
        mol_col.objects.link(bo)
        bridge_bonds.append((bo, iy, iz))

internal_bonds = []
for side, mat_b in [("C", mat_bond_cold), ("H", mat_bond_hot)]:
    for iz in range(4):
        for iy in range(3):
            for ix in range(3):
                if ix < 2:
                    bo = bpy.data.objects.new(f"Bond_{side}_x_{ix}_{iy}_{iz}", bond_mesh.copy())
                    bo.data.materials.append(mat_b)
                    mol_col.objects.link(bo)
                    internal_bonds.append((bo, side, (ix, iy, iz), (ix + 1, iy, iz)))
                if iz < 3:
                    bo = bpy.data.objects.new(f"Bond_{side}_z_{ix}_{iy}_{iz}", bond_mesh.copy())
                    bo.data.materials.append(mat_b)
                    mol_col.objects.link(bo)
                    internal_bonds.append((bo, side, (ix, iy, iz), (ix, iy, iz + 1)))

# ==============================================================================
# 8. BRANCHING CRACK WEB (S6) + 80 SHARDS + 50 DROPLETS + PUDDLE (S7, S8)
# ==============================================================================
cracks_col = bpy.data.collections.new("BranchingCracks")
scene.collection.children.link(cracks_col)
crack_curves = []
rng = random.Random(42)
for b_idx in range(18):
    cd = bpy.data.curves.new(f"Crack_{b_idx}", type="CURVE")
    cd.dimensions = "3D"
    cd.bevel_depth = 0.00055 if b_idx < 10 else 0.00035
    cd.bevel_resolution = 3
    spl = cd.splines.new("POLY")
    steps = 7
    spl.points.add(steps - 1)
    dir_ang = (b_idx / 18.0) * math.pi * 2.0 + rng.uniform(-0.18, 0.18)
    cur_a, cur_z = -math.pi * 0.5, 0.062
    for s in range(steps):
        if s > 0:
            cur_a += math.cos(dir_ang) * 0.15 + rng.uniform(-0.04, 0.04)
            cur_z = max(0.015, min(0.102, cur_z + math.sin(dir_ang) * 0.009 + rng.uniform(-0.003, 0.003)))
        spl.points[s].co = (math.cos(cur_a) * 0.0394, math.sin(cur_a) * 0.0394, cur_z, 1.0)
    co = bpy.data.objects.new(f"CrackObj_{b_idx}", cd)
    co.data.materials.append(mat_crack)
    cracks_col.objects.link(co)
    crack_curves.append(cd)

shards_col = bpy.data.collections.new("ShatterShards")
scene.collection.children.link(shards_col)
shards = []
for idx in range(80):
    ang = (idx * 2.39996) % 6.283185
    z0 = 0.015 + ((idx * 0.013) % 0.088)
    bm = bmesh.new()
    w = 0.0055 + ((idx * 0.0029) % 0.009)
    h = 0.010 + ((idx * 0.0049) % 0.014)
    v0 = bm.verts.new((0, 0, h * 0.6))
    v1 = bm.verts.new((w * 0.55, 0, -h * 0.15))
    v2 = bm.verts.new((w * 0.2, 0, -h * 0.55))
    v3 = bm.verts.new((-w * 0.48, 0, -h * 0.35))
    f = bm.faces.new((v0, v1, v2, v3))
    ret = bmesh.ops.extrude_face_region(bm, geom=[f])
    bmesh.ops.translate(bm, verts=[g for g in ret["geom"] if isinstance(g, bmesh.types.BMVert)], vec=(0, 0.0024, 0))
    m = bpy.data.meshes.new(f"ShardMesh_{idx}")
    bm.to_mesh(m)
    bm.free()
    so = bpy.data.objects.new(f"Shard_{idx}", m)
    so.data.materials.append(mat_glass)
    shards_col.objects.link(so)
    spd = 0.10 + ((idx * 0.023) % 0.14)
    shards.append({
        "obj": so,
        "origin": Vector((math.cos(ang) * 0.038, math.sin(ang) * 0.038, z0)),
        "vel": Vector((math.cos(ang) * spd, math.sin(ang) * spd, 0.042 + ((idx * 0.013) % 0.085))),
        "rot": Vector((((idx % 3) - 1) * 6.8 + 2.0, ((idx % 5) - 2) * 5.4, ((idx % 4) - 1.5) * 7.2)),
        "ang": ang,
    })

droplets = []
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.0030)
drop_mesh = bpy.context.active_object.data
for p in drop_mesh.polygons:
    p.use_smooth = True
drop_mesh.materials.append(mat_water)
bpy.data.objects.remove(bpy.context.active_object, do_unlink=True)
for idx in range(50):
    ang = (idx * 2.39996 + 0.5) % 6.283185
    do = bpy.data.objects.new(f"Drop_{idx}", drop_mesh)
    shards_col.objects.link(do)
    spd = 0.075 + ((idx * 0.019) % 0.11)
    droplets.append({
        "obj": do,
        "origin": Vector((math.cos(ang) * 0.026, math.sin(ang) * 0.026, 0.022 + ((idx * 0.011) % 0.060))),
        "vel": Vector((math.cos(ang) * spd, math.sin(ang) * spd, 0.055 + ((idx * 0.017) % 0.095))),
    })

bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.11, depth=0.0015, location=(0.0, 0.0, 0.0008))
puddle_obj = bpy.context.active_object
puddle_obj.data.materials.append(mat_water)
scene.collection.objects.unlink(puddle_obj)
shards_col.objects.link(puddle_obj)

# ==============================================================================
# 9. RAZOR-SHARP CINEMA CAMERA (NO BLUR! f/8.0 Crisp Focus)
# ==============================================================================
cam_data = bpy.data.cameras.new("CinemaCam")
cam_data.lens = 50.0
cam_data.dof.use_dof = False  # ZERO BLUR — Razor-sharp Zack D. Films clarity!
cam_obj = bpy.data.objects.new("CinemaCam", cam_data)
scene.collection.objects.link(cam_obj)
scene.camera = cam_obj

def aim_camera(pos, target, lens=50.0, roll_deg=0.0):
    cam_obj.location = Vector(pos)
    direction = Vector(target) - cam_obj.location
    rot = direction.to_track_quat("-Z", "Y").to_euler()
    rot.rotate_axis("Z", math.radians(roll_deg))
    cam_obj.rotation_euler = rot
    cam_data.lens = lens

# ==============================================================================
# 10. RENDER LOOP
# ==============================================================================
if args.frames.strip():
    frame_list = [int(x.strip()) for x in args.frames.split(",") if x.strip()]
else:
    frame_list = list(range(args.start, min(args.end, TOTAL_FRAMES)))

for f in frame_list:
    t = f / FPS
    is_flir = (195 <= f < 270) or (326 <= f < 405)
    is_mol  = (270 <= f < 326)
    is_pour = (117 <= f < 195)
    is_crack = (405 <= f < SHATTER_F)
    is_shatter = (f >= SHATTER_F)
    is_aftermath = (f >= 559)

    dark_cutaway = is_flir or is_mol
    kitchen_col.hide_render = dark_cutaway
    flir_col.hide_render = not is_flir
    mol_col.hide_render = not is_mol
    cracks_col.hide_render = not is_crack
    shards_col.hide_render = not is_shatter

    if dark_cutaway:
        bg_node.inputs[0].default_value = (0.008, 0.014, 0.028, 1.0)
        bg_node.inputs[1].default_value = 0.20
        l_sun.data.energy = 8.0
        l_fill.data.energy = 5.0
        l_rim.data.energy = 12.0
    else:
        bg_node.inputs[0].default_value = (0.28, 0.30, 0.34, 1.0)
        bg_node.inputs[1].default_value = 0.25
        l_sun.data.energy = 9.0
        l_fill.data.energy = 4.0
        l_rim.data.energy = 6.5

    if is_mol:
        m_u = max(0.0, min(1.0, (f - 270) / 55.0))
        c_pos, h_pos = {}, {}
        for obj, x, y, z, ph, ix, iy, iz in cold_atoms:
            p = Vector((x - m_u * 0.016 + math.sin(t * 28 + ph) * 0.001, y, z * (1.0 - m_u * 0.10)))
            obj.location = p
            c_pos[(ix, iy, iz)] = p
        for obj, x, y, z, ph, ix, iy, iz in hot_atoms:
            p = Vector((x + m_u * 0.018 + math.sin(t * 50 + ph) * 0.003, y, z * (1.0 + m_u * 0.14)))
            obj.location = p
            h_pos[(ix, iy, iz)] = p
        for bo, side, k1, k2 in internal_bonds:
            d = c_pos if side == "C" else h_pos
            bo.hide_render = False
            place_rod(bo, d[k1], d[k2])
        snapped = f >= VAC["f0"] + 3
        for bo, iy, iz in bridge_bonds:
            bo.hide_render = snapped
            if not snapped:
                place_rod(bo, c_pos[(0, iy, iz)], h_pos[(0, iy, iz)])
        aim_camera((-0.012 + m_u * 0.025, -0.185, 0.006), (0, 0, 0), 50.0, -2.0 * m_u)

    elif is_flir:
        if f < 270:
            u = (f - 195) / 75.0
            aim_camera((-0.02 + u * 0.04, -0.24, 0.064), (0, 0, 0.058), 54.0, 0.0)
        else:
            u = (f - 326) / 79.0
            aim_camera((0.028 - u * 0.04, -0.155, 0.060), (0, 0, 0.058), 66.0, 0.0)

    else:
        glass_obj.hide_render = is_shatter
        water_obj.hide_render = is_shatter
        pour_curve.hide_render = not is_pour
        pitcher_root.hide_render = not is_pour
        for ch in pitcher_root.children:
            ch.hide_render = not is_pour
        puddle_obj.hide_render = not is_aftermath

        if human_root is not None:
            human_root.hide_render = is_pour or is_crack
            if is_aftermath:
                pose_human("outro")
                human_root.location = (0.04, 0.42, -0.28)
            elif is_shatter:
                pose_human("shock")
                human_root.location = (0.06, 0.46, -0.28)
            else:
                pose_human("curious")
                human_root.location = (0.04, 0.40, -0.28)

        if is_pour:
            pitcher_root.location = (-0.095, 0.0, 0.175)
            pitcher_root.rotation_euler = (0.0, math.radians(42), 0.0)
            bpy.context.view_layer.update()
            lip_world = pitcher_root.matrix_world @ Vector((0.032, 0.0, 0.062))
            pts = pour_curve.data.splines[0].bezier_points
            pts[0].co = lip_world
            pts[0].handle_right = lip_world + Vector((0.025, 0.0, -0.015))
            pts[1].co = Vector((0.005, 0.0, 0.072))
            pts[1].handle_left = Vector((-0.005, 0.0, 0.125))

        if is_crack:
            cg = max(0.25, min(1.0, (f - 405) / max(1, SHATTER_F - 405)))
            for cd in crack_curves:
                cd.bevel_factor_end = cg

        for bo, ang, rad, spd, ph in bubbles:
            bo.hide_render = is_shatter
            yf = (ph + t * spd) % 1.0
            bo.location = (math.cos(ang) * rad, math.sin(ang) * rad, 0.016 + yf * 0.068)

        for so, ang, ph in steam_wisps:
            so.hide_render = True  # Remove ugly low-poly steam spheres!
            u_s = (ph + t * 0.28) % 1.0
            rad = 0.006 + u_s * 0.026
            so.location = (math.cos(ang + u_s * 2.0) * rad, math.sin(ang + u_s * 2.0) * rad, 0.092 + u_s * 0.115)
            sc = 0.55 + u_s * 1.45
            so.scale = (sc, sc, sc * 1.35)

        if is_shatter:
            raw_dt = (f - SHATTER_F) / FPS
            sim_t = raw_dt * 0.22 if raw_dt < 1.25 else 1.25 * 0.22 + (raw_dt - 1.25) * 0.85
            if is_aftermath:
                sim_t = 1.65
            for sh in shards:
                pz = max(0.003, sh["origin"].z + sh["vel"].z * sim_t - 0.5 * 0.35 * sim_t * sim_t)
                sh["obj"].location = (
                    sh["origin"].x + sh["vel"].x * min(sim_t, 1.1),
                    sh["origin"].y + sh["vel"].y * min(sim_t, 1.1),
                    pz,
                )
                sh["obj"].rotation_euler = (sh["rot"].x * sim_t, sh["rot"].y * sim_t, sh["ang"] + sh["rot"].z * sim_t)
            for dr in droplets:
                dr["obj"].hide_render = is_aftermath
                pz = max(0.002, dr["origin"].z + dr["vel"].z * sim_t - 0.5 * 0.42 * sim_t * sim_t)
                dr["obj"].location = (dr["origin"].x + dr["vel"].x * sim_t, dr["origin"].y + dr["vel"].y * sim_t, pz)

        if f < 117:
            aim_camera((-0.02, -0.34, 0.115), (0.01, 0.05, 0.085), 48.0, 0.0)
        elif is_pour:
            aim_camera((-0.03, -0.30, 0.135), (-0.01, 0, 0.095), 48.0, 0.0)
        elif is_crack:
            aim_camera((0.0, -0.19, 0.062), (0, 0, 0.058), 60.0, 0.0)
        elif not is_aftermath:
            aim_camera((0.02, -0.32, 0.105), (0.02, 0.05, 0.075), 46.0, 0.0)
        else:
            aim_camera((-0.02, -0.32, 0.105), (0.01, 0.05, 0.055), 48.0, 0.0)

    scene.render.filepath = os.path.join(args.out, f"frame_{f:04d}.png")
    bpy.ops.render.render(write_still=True)

print(f"[Cycles V5 ZackD] Finished {len(frame_list)} frames -> {args.out}")
