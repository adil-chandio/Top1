#!/usr/bin/env python3
"""
Thermal Shock V4 — Monarch-Cockroach V6 IMAX Standard (Blender 4.2 LTS Cycles).
8 Distinct Storyboarded Cinema Shots:
  S1_HOOK         (f=25)  : Warm Architectural Kitchen + Volumetric Sun God-Rays + Boiling Glass & Steam
  S2_POUR_ACT     (f=145) : Complete Gooseneck Kettle Pouring Cold Water onto Hot Glass + Splash Mist
  S3_THERMAL_IR   (f=215) : FLIR Thermal X-Ray Half-Cutaway (Cold Cyan Outer vs Hot Orange Inner + 3D Force Arrows)
  S4_VACUUM_SHEAR (f=286) : Microscopic SiO2 Covalent Lattice Shear Plane with Stretching/Snapping 3D Bonds
  S5_INNER_HOT    (f=345) : Extreme Macro Inside-Out Thermal Stress View (Hot Core Expanding vs Cold Shell)
  S6_CRACK_WEB    (f=425) : Phantom 500 FPS Macro Jagged Branching Fracture Web Racing Across Glass Wall
  S7_SHATTER_BT   (f=475) : Bullet-Time 500 FPS 80-Shard Crystal Explosion + 45 Flying Water Droplets
  S8_OUTRO_WARN   (f=615) : Cinematic Aftermath — Scattered Glass Shards + Reflective Water Puddle + Volumetric Backlight
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
parser.add_argument("--frames", type=str, default="", help="Comma-separated exact frame list")
parser.add_argument("--out", type=str, default="/tmp/v4_frames")
parser.add_argument("--lock", type=str, default="tools/thermal-shock/voice-lock.json")
parser.add_argument("--samples", type=int, default=24)
parser.add_argument("--res-x", type=int, default=720)
parser.add_argument("--res-y", type=int, default=1280)
args = parser.parse_args(argv)

os.makedirs(args.out, exist_ok=True)
with open(args.lock, "r", encoding="utf-8") as f:
    LOCK = json.load(f)

TOTAL_FRAMES = LOCK["total_frames"]
FPS = LOCK.get("fps", 30)
BEATS = LOCK["beats"]
VAC = LOCK["vacuum_window"]
SHATTER_F = LOCK["shatter_frame"]

# ==============================================================================
# 1. CYCLES + OIDN + AgX IMAX COLOR MANAGEMENT
# ==============================================================================
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = args.samples
scene.cycles.use_adaptive_sampling = True
scene.cycles.adaptive_threshold = 0.03
scene.cycles.use_denoising = True
scene.cycles.denoiser = "OPENIMAGEDENOISE"
scene.cycles.max_bounces = 12
scene.cycles.diffuse_bounces = 3
scene.cycles.glossy_bounces = 6
scene.cycles.transmission_bounces = 12
scene.cycles.transparent_max_bounces = 8
scene.cycles.sample_clamp_indirect = 8.0

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
scene.view_settings.exposure = 0.40

world = bpy.data.worlds.new("ImaxWorld")
scene.world = world
world.use_nodes = True
bg_node = world.node_tree.nodes.get("Background")
bg_node.inputs[0].default_value = (0.014, 0.020, 0.035, 1.0)
bg_node.inputs[1].default_value = 0.35

# ==============================================================================
# 2. MULTI-MOOD IMAX STUDIO LIGHTING
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

l_rim_l = add_area_light("StripRimLeft",  (-0.34, 0.08, 0.22), (82, 0, -108), 32.0, 0.09, 0.44, (1.0, 0.90, 0.76))
l_rim_r = add_area_light("StripRimRight", ( 0.34, 0.08, 0.22), (82, 0,  108), 28.0, 0.09, 0.44, (0.68, 0.88, 1.0))
l_key   = add_area_light("OverheadKey",   ( 0.00, -0.18, 0.48), (22, 0,   0), 20.0, 0.38, 0.28, (1.0, 0.98, 0.95))
l_back  = add_area_light("BackAccent",    ( 0.00,  0.38, 0.26), (-62, 0,  0), 16.0, 0.52, 0.24, (0.28, 0.58, 1.0))

# ==============================================================================
# 3. MATERIALS (Light-Path Glass, Nero Marble, Subway Tile, FLIR Thermal, God-Ray)
# ==============================================================================
def make_real_glass_mat(name, ior=1.52, roughness=0.010, tint=(0.97, 0.995, 1.0, 1.0)):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    mix = nt.nodes.new("ShaderNodeMixShader")
    lp = nt.nodes.new("ShaderNodeLightPath")
    trans = nt.nodes.new("ShaderNodeBsdfTransparent")
    trans.inputs["Color"].default_value = (0.93, 0.97, 1.0, 1.0)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = tint
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["IOR"].default_value = ior
    bsdf.inputs["Transmission Weight"].default_value = 1.0
    if "Coat Weight" in bsdf.inputs:
        bsdf.inputs["Coat Weight"].default_value = 0.85
    nt.links.new(lp.outputs["Is Shadow Ray"], mix.inputs["Fac"])
    nt.links.new(bsdf.outputs["BSDF"], mix.inputs[1])
    nt.links.new(trans.outputs["BSDF"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    return mat

def make_nero_marble_mat():
    mat = bpy.data.materials.new("NeroMarble")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.08
    if "Coat Weight" in bsdf.inputs:
        bsdf.inputs["Coat Weight"].default_value = 0.80
    tc = nt.nodes.new("ShaderNodeTexCoord")
    ns = nt.nodes.new("ShaderNodeTexNoise")
    ns.inputs["Scale"].default_value = 18.0
    ns.inputs["Detail"].default_value = 10.0
    ns.inputs["Distortion"].default_value = 2.4
    rmp = nt.nodes.new("ShaderNodeValToRGB")
    rmp.color_ramp.elements[0].position = 0.44
    rmp.color_ramp.elements[0].color = (0.022, 0.025, 0.032, 1.0)
    rmp.color_ramp.elements[1].position = 0.56
    rmp.color_ramp.elements[1].color = (0.30, 0.32, 0.36, 1.0)
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.04
    nt.links.new(tc.outputs["Object"], ns.inputs["Vector"])
    nt.links.new(ns.outputs["Fac"], rmp.inputs["Fac"])
    nt.links.new(rmp.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(ns.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat

def make_tile_mat():
    mat = bpy.data.materials.new("DarkSubwayTile")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.16
    tc = nt.nodes.new("ShaderNodeTexCoord")
    brk = nt.nodes.new("ShaderNodeTexBrick")
    brk.inputs["Scale"].default_value = 22.0
    brk.inputs["Mortar Size"].default_value = 0.018
    brk.inputs["Color1"].default_value = (0.042, 0.052, 0.072, 1.0)
    brk.inputs["Color2"].default_value = (0.032, 0.040, 0.058, 1.0)
    brk.inputs["Mortar"].default_value = (0.014, 0.016, 0.022, 1.0)
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.18
    nt.links.new(tc.outputs["Object"], brk.inputs["Vector"])
    nt.links.new(brk.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(brk.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat

def make_translucent_glow(name, color, strength=0.9, opacity=0.18):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    mix = nt.nodes.new("ShaderNodeMixShader")
    trans = nt.nodes.new("ShaderNodeBsdfTransparent")
    emis = nt.nodes.new("ShaderNodeEmission")
    emis.inputs["Color"].default_value = color
    emis.inputs["Strength"].default_value = strength
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.42
    mth = nt.nodes.new("ShaderNodeMath")
    mth.operation = "MULTIPLY"
    mth.inputs[1].default_value = opacity
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

mat_glass      = make_real_glass_mat("RealGlass", ior=1.52, roughness=0.008)
mat_water      = make_real_glass_mat("RealWater", ior=1.333, roughness=0.015, tint=(0.86, 0.96, 1.0, 1.0))
mat_cold_water = make_real_glass_mat("ColdWater", ior=1.333, roughness=0.015, tint=(0.55, 0.88, 1.0, 1.0))
mat_marble     = make_nero_marble_mat()
mat_tile       = make_tile_mat()
mat_steam      = make_translucent_glow("SteamWisp", (0.88, 0.94, 1.0, 1.0), 0.95, 0.16)
mat_godray     = make_translucent_glow("VolumetricGodRay", (1.0, 0.84, 0.56, 1.0), 1.4, 0.11)
mat_steel      = make_pbr("BrushedSteel", (0.84, 0.87, 0.92, 1.0), roughness=0.14, metallic=0.96)
mat_black      = make_pbr("MatteBlack", (0.04, 0.04, 0.05, 1.0), roughness=0.42, metallic=0.05)
mat_flir_cold  = make_pbr("FLIR_Cold", (0.02, 0.72, 1.0, 1.0), roughness=0.12, emission=3.6)
mat_flir_hot   = make_pbr("FLIR_Hot",  (1.0, 0.24, 0.02, 1.0), roughness=0.12, emission=4.8)
mat_arrow_cold = make_pbr("ArrowCold", (0.10, 0.88, 1.0, 1.0), roughness=0.10, emission=5.0)
mat_arrow_hot  = make_pbr("ArrowHot",  (1.0, 0.42, 0.04, 1.0), roughness=0.10, emission=6.0)
mat_bond_cold  = make_pbr("BondCold",  (0.28, 0.82, 1.0, 1.0), roughness=0.15, metallic=0.3, emission=1.4)
mat_bond_hot   = make_pbr("BondHot",   (1.0, 0.45, 0.10, 1.0), roughness=0.15, metallic=0.3, emission=1.8)
mat_bond_snap  = make_pbr("BondSnap",  (1.0, 0.92, 0.30, 1.0), roughness=0.08, emission=10.0)
mat_crack      = make_pbr("CrackGlow", (0.55, 0.95, 1.0, 1.0), roughness=0.05, emission=12.0)
mat_mote       = make_pbr("DustMote",  (1.0, 0.90, 0.70, 1.0), roughness=0.10, emission=6.0)

# ==============================================================================
# 4. HELPER GEOMETRY BUILDERS
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

def add_3d_arrow(name, p_start, p_end, mat, col, radius=0.0020):
    v = Vector(p_end) - Vector(p_start)
    dist = v.length
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=radius, depth=dist * 0.68)
    shaft = bpy.context.active_object
    shaft.name = name + "_Shaft"
    shaft.location = Vector(p_start) + v * 0.34
    shaft.rotation_euler = v.to_track_quat("Z", "Y").to_euler()
    shaft.data.materials.append(mat)
    scene.collection.objects.unlink(shaft)
    col.objects.link(shaft)

    bpy.ops.mesh.primitive_cone_add(vertices=12, radius1=radius * 2.4, radius2=0.0, depth=dist * 0.34)
    head = bpy.context.active_object
    head.name = name + "_Head"
    head.location = Vector(p_start) + v * 0.83
    head.rotation_euler = v.to_track_quat("Z", "Y").to_euler()
    head.data.materials.append(mat)
    scene.collection.objects.unlink(head)
    col.objects.link(head)
    return [shaft, head]

# ==============================================================================
# 5. SET A: ARCHITECTURAL STUDIO STAGE + VOLUMETRIC GOD-RAY + TYNDALL MOTES
# ==============================================================================
stage_col = bpy.data.collections.new("StudioStage")
scene.collection.children.link(stage_col)

bpy.ops.mesh.primitive_plane_add(size=2.4, location=(0, 0.05, 0.0))
counter = bpy.context.active_object
counter.data.materials.append(mat_marble)
scene.collection.objects.unlink(counter)
stage_col.objects.link(counter)

bpy.ops.mesh.primitive_plane_add(size=2.4, location=(0, 0.55, 0.55))
wall = bpy.context.active_object
wall.rotation_euler = (math.radians(90), 0, 0)
wall.data.materials.append(mat_tile)
scene.collection.objects.unlink(wall)
stage_col.objects.link(wall)

# Volumetric Warm Morning Sun God-Ray Shafts (Monarch-Cockroach Signature!)
godray_col = bpy.data.collections.new("GodRays")
scene.collection.children.link(godray_col)
for gi in range(3):
    bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=0.14 + gi * 0.03, radius2=0.03, depth=0.52,
                                    location=(-0.12 + gi * 0.04, 0.08, 0.20))
    gr = bpy.context.active_object
    gr.rotation_euler = (math.radians(15), math.radians(-38), 0)
    gr.data.materials.append(mat_godray)
    scene.collection.objects.unlink(gr)
    godray_col.objects.link(gr)

# 45 Floating Tyndall Atmospheric Dust Motes
mote_rng = random.Random(101)
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.00085)
mote_mesh = bpy.context.active_object.data
mote_mesh.materials.append(mat_mote)
bpy.data.objects.remove(bpy.context.active_object, do_unlink=True)
for mi in range(45):
    mo = bpy.data.objects.new(f"Mote_{mi}", mote_mesh)
    mo.location = (mote_rng.uniform(-0.18, 0.18), mote_rng.uniform(-0.10, 0.22), mote_rng.uniform(0.03, 0.24))
    godray_col.objects.link(mo)

# Hero Glass + Boiling Water + Bubbles + Steam + Complete Gooseneck Kettle
glass_obj = build_lathe("HeroGlass", [
    (0.029, 0.0002), (0.033, 0.003), (0.038, 0.016), (0.041, 0.058), (0.039, 0.105),
    (0.0380, 0.108), (0.0358, 0.108), (0.0364, 0.101), (0.0372, 0.058), (0.0332, 0.020), (0.0278, 0.014),
], 72, mat_glass, stage_col)

water_obj = build_lathe("BoilingWater", [
    (0.0275, 0.0145), (0.0328, 0.020), (0.0368, 0.058), (0.0362, 0.086),
], 56, mat_water, stage_col)

bubbles = []
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.0016)
bub_mesh = bpy.context.active_object.data
bub_mesh.materials.append(mat_glass)
bpy.data.objects.remove(bpy.context.active_object, do_unlink=True)
for i in range(65):
    bo = bpy.data.objects.new(f"Bubble_{i}", bub_mesh)
    stage_col.objects.link(bo)
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
    stage_col.objects.link(so)
    steam_wisps.append((so, (i * 1.9) % 6.283, i / 18.0))

# Complete Gooseneck Kettle
kettle_root = bpy.data.objects.new("KettleRoot", None)
stage_col.objects.link(kettle_root)
kettle_body = build_lathe("KettleBody", [
    (0.044, -0.052), (0.048, -0.045), (0.046, 0.010), (0.036, 0.058), (0.032, 0.064),
], 48, mat_steel, stage_col)
kettle_body.parent = kettle_root
kettle_lid = build_lathe("KettleLid", [
    (0.033, 0.064), (0.028, 0.070), (0.008, 0.072), (0.009, 0.082), (0.013, 0.085), (0.004, 0.087),
], 36, mat_black, stage_col)
kettle_lid.parent = kettle_root

bpy.ops.curve.primitive_bezier_curve_add()
k_handle = bpy.context.active_object
k_handle.data.bevel_depth = 0.0055
k_handle.data.splines[0].bezier_points[0].co = Vector((0.036, 0, 0.048))
k_handle.data.splines[0].bezier_points[0].handle_right = Vector((0.088, 0, 0.048))
k_handle.data.splines[0].bezier_points[1].co = Vector((0.046, 0, -0.036))
k_handle.data.splines[0].bezier_points[1].handle_left = Vector((0.088, 0, -0.036))
k_handle.data.materials.append(mat_black)
scene.collection.objects.unlink(k_handle)
stage_col.objects.link(k_handle)
k_handle.parent = kettle_root

bpy.ops.curve.primitive_bezier_curve_add()
k_spout = bpy.context.active_object
k_spout.data.bevel_depth = 0.0052
k_spout.data.splines[0].bezier_points[0].co = Vector((-0.044, 0, -0.028))
k_spout.data.splines[0].bezier_points[0].handle_right = Vector((-0.076, 0, -0.015))
k_spout.data.splines[0].bezier_points[1].co = Vector((-0.088, 0, 0.058))
k_spout.data.splines[0].bezier_points[1].handle_left = Vector((-0.072, 0, 0.048))
k_spout.data.materials.append(mat_steel)
scene.collection.objects.unlink(k_spout)
stage_col.objects.link(k_spout)
k_spout.parent = kettle_root

bpy.ops.curve.primitive_bezier_curve_add()
pour_curve = bpy.context.active_object
pour_curve.data.bevel_depth = 0.0044
pour_curve.data.bevel_resolution = 8
pour_curve.data.materials.append(mat_cold_water)
scene.collection.objects.unlink(pour_curve)
stage_col.objects.link(pour_curve)

# ==============================================================================
# 6. SET B: FLIR THERMAL X-RAY HALF-CUTAWAY + 3D COMPRESSION/EXPANSION ARROWS!
# ==============================================================================
flir_col = bpy.data.collections.new("ThermalCutawaySet")
scene.collection.children.link(flir_col)

# Outer Cold Cyan Shell (Half-cylinder cutaway facing camera!)
build_lathe("FLIR_OuterCold", [
    (0.039, 0.014), (0.042, 0.058), (0.040, 0.106),
], 48, mat_flir_cold, flir_col, arc_rad=math.pi * 1.15, start_ang=-0.25, cap_ends=False)

# Inner Hot Molten-Orange Core (Half-cylinder cutaway!)
build_lathe("FLIR_InnerHot", [
    (0.033, 0.014), (0.036, 0.058), (0.034, 0.104),
], 48, mat_flir_hot, flir_col, arc_rad=math.pi * 1.15, start_ang=-0.25, cap_ends=False)

# 3D Blue Compression Arrows (pushing INWARD on outer wall) + Orange Expansion Arrows (pushing OUTWARD from inner core!)
for az in [0.032, 0.058, 0.084]:
    add_3d_arrow(f"CompL_{az}", (-0.068, -0.005, az), (-0.043, -0.005, az), mat_arrow_cold, flir_col, 0.0018)
    add_3d_arrow(f"CompR_{az}", ( 0.068, -0.005, az), ( 0.043, -0.005, az), mat_arrow_cold, flir_col, 0.0018)
    add_3d_arrow(f"ExpL_{az}",  (-0.012, -0.008, az), (-0.033, -0.008, az), mat_arrow_hot,  flir_col, 0.0018)
    add_3d_arrow(f"ExpR_{az}",  ( 0.012, -0.008, az), ( 0.033, -0.008, az), mat_arrow_hot,  flir_col, 0.0018)

# ==============================================================================
# 7. SET C: MICROSCOPIC SiO2 COVALENT LATTICE + SNAPPING 3D BONDS
# ==============================================================================
mol_col = bpy.data.collections.new("MolecularSet")
scene.collection.children.link(mol_col)
bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=16, radius=0.0064)
atom_mesh = bpy.context.active_object.data
for p in atom_mesh.polygons:
    p.use_smooth = True
bpy.data.objects.remove(bpy.context.active_object, do_unlink=True)

bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.0015, depth=1.0)
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

cold_atoms, hot_atoms = [], []
for iz in range(4):
    for iy in range(3):
        for ix in range(3):
            x = -0.018 - ix * 0.024
            y = (iy - 1) * 0.026
            z = (iz - 1.5) * 0.026
            ca = bpy.data.objects.new(f"Cold_{ix}_{iy}_{iz}", atom_mesh.copy())
            ca.data.materials.append(mat_flir_cold)
            mol_col.objects.link(ca)
            cold_atoms.append((ca, x, y, z, (ix + iy * 3 + iz * 9) * 0.71, ix, iy, iz))

            ha = bpy.data.objects.new(f"Hot_{ix}_{iy}_{iz}", atom_mesh.copy())
            ha.data.materials.append(mat_flir_hot)
            mol_col.objects.link(ha)
            hot_atoms.append((ha, -x, y, z, (ix + iy * 3 + iz * 9) * 0.93, ix, iy, iz))

bridge_bonds = []
for iz in range(4):
    for iy in range(3):
        bo = bpy.data.objects.new(f"BridgeBond_{iy}_{iz}", bond_mesh.copy())
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
# 8. BRANCHING CRACK WEB + 80 SHATTER SHARDS + 45 FLYING DROPLETS + PUDDLE
# ==============================================================================
cracks_col = bpy.data.collections.new("BranchingCracks")
scene.collection.children.link(cracks_col)
crack_curves = []
rng = random.Random(42)
for b_idx in range(16):
    cd = bpy.data.curves.new(f"Crack_{b_idx}", type="CURVE")
    cd.dimensions = "3D"
    cd.bevel_depth = 0.00060 if b_idx < 8 else 0.00038
    cd.bevel_resolution = 3
    spl = cd.splines.new("POLY")
    steps = 7
    spl.points.add(steps - 1)
    dir_ang = (b_idx / 16.0) * math.pi * 2.0 + rng.uniform(-0.18, 0.18)
    cur_a, cur_z = -math.pi * 0.5, 0.056
    for s in range(steps):
        if s > 0:
            cur_a += math.cos(dir_ang) * 0.14 + rng.uniform(-0.04, 0.04)
            cur_z = max(0.015, min(0.102, cur_z + math.sin(dir_ang) * 0.0085 + rng.uniform(-0.003, 0.003)))
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
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.0032)
drop_mesh = bpy.context.active_object.data
for p in drop_mesh.polygons:
    p.use_smooth = True
drop_mesh.materials.append(mat_water)
bpy.data.objects.remove(bpy.context.active_object, do_unlink=True)
for idx in range(45):
    ang = (idx * 2.39996 + 0.5) % 6.283185
    do = bpy.data.objects.new(f"Drop_{idx}", drop_mesh)
    shards_col.objects.link(do)
    spd = 0.075 + ((idx * 0.019) % 0.11)
    droplets.append({
        "obj": do,
        "origin": Vector((math.cos(ang) * 0.026, math.sin(ang) * 0.026, 0.022 + ((idx * 0.011) % 0.060))),
        "vel": Vector((math.cos(ang) * spd, math.sin(ang) * spd, 0.055 + ((idx * 0.017) % 0.095))),
    })

# Reflective Water Puddle for S8 Aftermath
bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.11, depth=0.0015, location=(0.0, 0.0, 0.0008))
puddle_obj = bpy.context.active_object
puddle_obj.data.materials.append(mat_water)
scene.collection.objects.unlink(puddle_obj)
shards_col.objects.link(puddle_obj)

# ==============================================================================
# 9. CINEMA CAMERA (Dynamic Lens + f/2.0 Bokeh)
# ==============================================================================
cam_data = bpy.data.cameras.new("CinemaCam")
cam_data.lens = 55.0
cam_data.dof.use_dof = True
cam_data.dof.aperture_fstop = 2.0
cam_obj = bpy.data.objects.new("CinemaCam", cam_data)
scene.collection.objects.link(cam_obj)
scene.camera = cam_obj

def aim_camera(pos, target, lens=55.0, roll_deg=0.0):
    cam_obj.location = Vector(pos)
    direction = Vector(target) - cam_obj.location
    rot = direction.to_track_quat("-Z", "Y").to_euler()
    rot.rotate_axis("Z", math.radians(roll_deg))
    cam_obj.rotation_euler = rot
    cam_data.lens = lens
    cam_data.dof.focus_distance = direction.length

# ==============================================================================
# 10. 8-SHOT DIRECTOR RENDER LOOP
# ==============================================================================
if args.frames.strip():
    frame_list = [int(x.strip()) for x in args.frames.split(",") if x.strip()]
else:
    frame_list = list(range(args.start, min(args.end, TOTAL_FRAMES)))

for f in frame_list:
    t = f / FPS
    # Shot ranges:
    # S1_HOOK:         0..116   (Kitchen + God-Rays + Boiling Glass)
    # S2_POUR_ACT:   117..194   (Gooseneck Kettle Pouring Cold Water)
    # S3_THERMAL_IR: 195..269   (FLIR Thermal Cutaway + 3D Force Arrows)
    # S4_VACUUM:     270..325   (Microscopic SiO2 Covalent Lattice + Snapping Bonds)
    # S5_INNER_HOT:  326..404   (Macro FLIR Inside-Out Thermal Stress)
    # S6_CRACK_WEB:  405..454   (500 FPS Macro Branching Fracture Web)
    # S7_SHATTER_BT: 455..558   (Bullet-Time 80-Shard + 45-Droplet Explosion)
    # S8_OUTRO_WARN: 559..689   (Aftermath Shards + Reflective Puddle + God-Rays)

    is_flir = (195 <= f < 270) or (326 <= f < 405)
    is_mol  = (270 <= f < 326)
    is_pour = (117 <= f < 195)
    is_crack = (405 <= f < SHATTER_F)
    is_shatter = (f >= SHATTER_F)
    is_aftermath = (f >= 559)

    stage_col.hide_render = is_mol
    flir_col.hide_render = not is_flir
    mol_col.hide_render = not is_mol
    cracks_col.hide_render = not is_crack
    shards_col.hide_render = not is_shatter
    godray_col.hide_render = is_mol or is_flir

    if is_mol:
        bg_node.inputs[0].default_value = (0.006, 0.010, 0.024, 1.0)
        bg_node.inputs[1].default_value = 0.25
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
        aim_camera((-0.015 + m_u * 0.03, -0.195, 0.008), (0, 0, 0), 50.0, -2.5 * m_u)

    elif is_flir:
        bg_node.inputs[0].default_value = (0.008, 0.012, 0.026, 1.0)
        bg_node.inputs[1].default_value = 0.25
        glass_obj.hide_render = True
        water_obj.hide_render = True
        kettle_root.hide_render = True
        for ch in kettle_root.children:
            ch.hide_render = True
        pour_curve.hide_render = True
        for bo, *_ in bubbles:
            bo.hide_render = True
        for so, *_ in steam_wisps:
            so.hide_render = True
        if f < 270:
            u = (f - 195) / 75.0
            aim_camera((-0.02 + u * 0.04, -0.25 + u * 0.02, 0.068), (0, 0, 0.058), 55.0, -1.5)
        else:
            u = (f - 326) / 79.0
            aim_camera((0.035 - u * 0.05, -0.17, 0.062 + u * 0.012), (0, 0, 0.058), 68.0, 2.5)
    else:
        bg_node.inputs[0].default_value = (0.014, 0.020, 0.035, 1.0)
        bg_node.inputs[1].default_value = 0.35
        glass_obj.hide_render = is_shatter
        water_obj.hide_render = is_shatter
        pour_curve.hide_render = not is_pour
        kettle_root.hide_render = not is_pour
        for ch in kettle_root.children:
            ch.hide_render = not is_pour
        puddle_obj.hide_render = not is_aftermath

        if is_pour:
            pe = math.sin(min(1.0, max(0.0, (f - 117) / 16.0)) * math.pi * 0.5)
            kettle_root.location = (0.135 - pe * 0.012, 0.0, 0.155 + pe * 0.010)
            kettle_root.rotation_euler = (0.0, -pe * 0.52, 0.0)
            bpy.context.view_layer.update()
            spout_world = kettle_root.matrix_world @ Vector((-0.088, 0.0, 0.058))
            pts = pour_curve.data.splines[0].bezier_points
            pts[0].co = spout_world
            pts[0].handle_right = spout_world + Vector((-0.022, 0.0, -0.010))
            pts[1].co = Vector((0.008, 0.0, 0.072))
            pts[1].handle_left = Vector((0.012, 0.0, 0.120))

        if is_crack:
            cg = max(0.15, min(1.0, (f - 405) / max(1, SHATTER_F - 405)))
            for cd in crack_curves:
                cd.bevel_factor_end = cg

        for bo, ang, rad, spd, ph in bubbles:
            bo.hide_render = is_shatter
            yf = (ph + t * spd) % 1.0
            bo.location = (math.cos(ang) * rad, math.sin(ang) * rad, 0.016 + yf * 0.068)

        for so, ang, ph in steam_wisps:
            so.hide_render = is_shatter
            u_s = (ph + t * 0.28) % 1.0
            rad = 0.006 + u_s * 0.026
            so.location = (math.cos(ang + u_s * 2.0) * rad, math.sin(ang + u_s * 2.0) * rad, 0.092 + u_s * 0.115)
            sc = 0.55 + u_s * 1.45
            so.scale = (sc, sc, sc * 1.35)

        if is_shatter:
            raw_dt = (f - SHATTER_F) / FPS
            sim_t = raw_dt * 0.22 if raw_dt < 1.25 else 1.25 * 0.22 + (raw_dt - 1.25) * 0.85
            if is_aftermath:
                sim_t = 1.65  # Settled shards on marble counter!
            for sh in shards:
                pz = sh["origin"].z + sh["vel"].z * sim_t - 0.5 * 0.35 * sim_t * sim_t
                if pz < 0.003:
                    pz = 0.003
                sh["obj"].location = (
                    sh["origin"].x + sh["vel"].x * min(sim_t, 1.1),
                    sh["origin"].y + sh["vel"].y * min(sim_t, 1.1),
                    pz,
                )
                sh["obj"].rotation_euler = (sh["rot"].x * sim_t, sh["rot"].y * sim_t, sh["ang"] + sh["rot"].z * sim_t)
            for dr in droplets:
                dr["obj"].hide_render = is_aftermath
                pz = max(0.002, dr["origin"].z + dr["vel"].z * sim_t - 0.5 * 0.42 * sim_t * sim_t)
                dr["obj"].location = (
                    dr["origin"].x + dr["vel"].x * sim_t,
                    dr["origin"].y + dr["vel"].y * sim_t,
                    pz,
                )

        # Camera per shot
        if f < 117:
            u = f / 117.0
            aim_camera((-0.04 + u * 0.06, -0.31 + u * 0.05, 0.105 - u * 0.018), (0, 0, 0.060), 55.0, -1.2)
        elif is_pour:
            u = (f - 117) / 78.0
            aim_camera((0.065 - u * 0.035, -0.29, 0.135 - u * 0.015), (0.018, 0, 0.080), 48.0, -1.8)
        elif is_crack:
            u = (f - 405) / max(1, SHATTER_F - 405)
            aim_camera((-0.018 + u * 0.018, -0.18 + u * 0.015, 0.060), (0, 0, 0.056), 65.0, 2.5)
        elif not is_aftermath:
            u = (f - SHATTER_F) / max(1, 559 - SHATTER_F)
            a = -0.25 + u * 1.45
            aim_camera((math.sin(a) * 0.28, -math.cos(a) * 0.28, 0.092), (0, 0, 0.056), 46.0, -3.0)
        else:
            u = (f - 559) / max(1, TOTAL_FRAMES - 559)
            aim_camera((-0.04 + u * 0.08, -0.28, 0.085), (0, 0, 0.018), 50.0, 0.0)

    scene.render.filepath = os.path.join(args.out, f"frame_{f:04d}.png")
    bpy.ops.render.render(write_still=True)

print(f"[Cycles V4 IMAX] Finished {len(frame_list)} frames -> {args.out}")
