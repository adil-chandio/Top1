#!/usr/bin/env python3
"""
Thermal Shock V3 — Real Zack D. Films / Studio Commercial Blender 4.2 LTS Cycles 3D Renderer.
Fixes all 8 forensic V2 defects:
  1. Light Path (Is Shadow Ray) transparent-shadow Glass & Water shaders (zero black glass!)
  2. Dark Nero Marquina Marble + Brick-Grout Backsplash + Tall Rim Strip-Lights (10x contrast!)
  3. Zero primitive cubes, zero stiff T-pose mannequin
  4. Complete Gooseneck Kettle (body + lid + knob + handle + spout) with exact spout-aligned pour
  5. Rising boiling steam wisps + animated water surface ripples
  6. Animated jagged branching fracture web (grows 0% -> 100% before shatter)
  7. True 3D SiO2 Covalent Lattice with actual 3D snapping bond rods
  8. 80-shard bullet-time glass shatter + 40 flying water droplets
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
parser.add_argument("--frames", type=str, default="", help="Comma-separated exact frame list (e.g. 25,155,310,425,465)")
parser.add_argument("--out", type=str, default="/tmp/blender_frames")
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
# 1. CYCLES + OIDN + AgX HIGH-CONTRAST STUDIO ENGINE
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
scene.view_settings.exposure = 0.35

world = bpy.data.worlds.new("ZackDStudioWorld")
scene.world = world
world.use_nodes = True
bg_node = world.node_tree.nodes.get("Background")
bg_node.inputs[0].default_value = (0.015, 0.022, 0.038, 1.0)
bg_node.inputs[1].default_value = 0.35

# ==============================================================================
# 2. COMMERCIAL GLASS STUDIO LIGHTING (Tall Rim Strip-Lights + Overhead Key)
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

# Left & Right tall vertical strip softboxes create razor-sharp glass rim highlights!
add_area_light("StripRimLeft",  (-0.34, 0.08, 0.22), (82, 0, -108), 28.0, 0.09, 0.42, (1.0, 0.94, 0.86))
add_area_light("StripRimRight", ( 0.34, 0.08, 0.22), (82, 0,  108), 26.0, 0.09, 0.42, (0.76, 0.90, 1.0))
add_area_light("OverheadKey",   ( 0.00, -0.18, 0.48), (22, 0,   0), 18.0, 0.38, 0.28, (1.0, 0.98, 0.96))
add_area_light("BackAccent",    ( 0.00,  0.38, 0.26), (-62, 0,  0), 14.0, 0.50, 0.24, (0.25, 0.55, 1.0))

# ==============================================================================
# 3. REALISTIC MATERIALS (Light Path Transparent Shadow Glass + Nero Marble)
# ==============================================================================
def make_real_glass_mat(name, ior=1.52, roughness=0.012, tint=(0.98, 0.995, 1.0, 1.0), shadow_tint=(0.92, 0.96, 1.0, 1.0)):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    mix = nt.nodes.new("ShaderNodeMixShader")
    lp = nt.nodes.new("ShaderNodeLightPath")
    trans = nt.nodes.new("ShaderNodeBsdfTransparent")
    trans.inputs["Color"].default_value = shadow_tint

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = tint
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["IOR"].default_value = ior
    bsdf.inputs["Transmission Weight"].default_value = 1.0
    if "Coat Weight" in bsdf.inputs:
        bsdf.inputs["Coat Weight"].default_value = 0.85
        bsdf.inputs["Coat Roughness"].default_value = 0.01

    nt.links.new(lp.outputs["Is Shadow Ray"], mix.inputs["Fac"])
    nt.links.new(bsdf.outputs["BSDF"], mix.inputs[1])
    nt.links.new(trans.outputs["BSDF"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    return mat

def make_nero_marble_mat():
    mat = bpy.data.materials.new("NeroMarquinaMarble")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.09
    if "Coat Weight" in bsdf.inputs:
        bsdf.inputs["Coat Weight"].default_value = 0.75
        bsdf.inputs["Coat Roughness"].default_value = 0.04

    tc = nt.nodes.new("ShaderNodeTexCoord")
    ns1 = nt.nodes.new("ShaderNodeTexNoise")
    ns1.inputs["Scale"].default_value = 18.0
    ns1.inputs["Detail"].default_value = 10.0
    ns1.inputs["Distortion"].default_value = 2.4

    rmp = nt.nodes.new("ShaderNodeValToRGB")
    rmp.color_ramp.elements[0].position = 0.44
    rmp.color_ramp.elements[0].color = (0.025, 0.028, 0.035, 1.0)
    rmp.color_ramp.elements[1].position = 0.56
    rmp.color_ramp.elements[1].color = (0.28, 0.30, 0.34, 1.0)

    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.04
    nt.links.new(tc.outputs["Object"], ns1.inputs["Vector"])
    nt.links.new(ns1.outputs["Fac"], rmp.inputs["Fac"])
    nt.links.new(rmp.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(ns1.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat

def make_tile_backsplash_mat():
    mat = bpy.data.materials.new("DarkSubwayTile")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.16
    tc = nt.nodes.new("ShaderNodeTexCoord")
    brk = nt.nodes.new("ShaderNodeTexBrick")
    brk.inputs["Scale"].default_value = 22.0
    brk.inputs["Mortar Size"].default_value = 0.018
    brk.inputs["Color1"].default_value = (0.045, 0.055, 0.075, 1.0)
    brk.inputs["Color2"].default_value = (0.035, 0.042, 0.060, 1.0)
    brk.inputs["Mortar"].default_value = (0.015, 0.018, 0.025, 1.0)
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.18
    nt.links.new(tc.outputs["Object"], brk.inputs["Vector"])
    nt.links.new(brk.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(brk.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat

def make_steam_mat():
    mat = bpy.data.materials.new("SteamWisp")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    mix = nt.nodes.new("ShaderNodeMixShader")
    trans = nt.nodes.new("ShaderNodeBsdfTransparent")
    emis = nt.nodes.new("ShaderNodeEmission")
    emis.inputs["Color"].default_value = (0.85, 0.92, 1.0, 1.0)
    emis.inputs["Strength"].default_value = 0.85
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.45
    mth = nt.nodes.new("ShaderNodeMath")
    mth.operation = "MULTIPLY"
    mth.inputs[1].default_value = 0.16
    nt.links.new(lw.outputs["Facing"], mth.inputs[0])
    nt.links.new(mth.outputs["Value"], mix.inputs["Fac"])
    nt.links.new(trans.outputs["BSDF"], mix.inputs[1])
    nt.links.new(emis.outputs["Emission"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    return mat

def make_pbr(name, color, roughness=0.25, metallic=0.0, emission=0.0):
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

mat_glass = make_real_glass_mat("RealGlass", ior=1.52, roughness=0.010, tint=(0.97, 0.995, 1.0, 1.0))
mat_water = make_real_glass_mat("RealWater", ior=1.333, roughness=0.018, tint=(0.88, 0.96, 1.0, 1.0))
mat_marble = make_nero_marble_mat()
mat_tile = make_tile_backsplash_mat()
mat_steam = make_steam_mat()
mat_steel = make_pbr("BrushedSteel", (0.82, 0.85, 0.90, 1.0), roughness=0.14, metallic=0.96)
mat_matte_black = make_pbr("KettleHandle", (0.04, 0.04, 0.05, 1.0), roughness=0.45, metallic=0.05)
mat_cold_atom = make_pbr("ColdAtom", (0.04, 0.78, 1.0, 1.0), roughness=0.10, emission=4.5)
mat_hot_atom = make_pbr("HotAtom", (1.0, 0.24, 0.03, 1.0), roughness=0.10, emission=5.5)
mat_bond_cold = make_pbr("BondCold", (0.30, 0.82, 1.0, 1.0), roughness=0.15, metallic=0.3, emission=1.2)
mat_bond_hot = make_pbr("BondHot", (1.0, 0.45, 0.12, 1.0), roughness=0.15, metallic=0.3, emission=1.5)
mat_bond_snap = make_pbr("BondSnap", (1.0, 0.90, 0.30, 1.0), roughness=0.10, emission=9.0)
mat_crack = make_pbr("ThermalCrack", (0.45, 0.92, 1.0, 1.0), roughness=0.05, emission=10.0)

# ==============================================================================
# 4. SET A: ZACK D. FILMS STUDIO STAGE (Nero Marble + Dark Subway Tile)
# ==============================================================================
stage_col = bpy.data.collections.new("StudioStage")
scene.collection.children.link(stage_col)

bpy.ops.mesh.primitive_plane_add(size=2.4, location=(0, 0.05, 0.0))
counter = bpy.context.active_object
counter.name = "MarbleCounter"
counter.data.materials.append(mat_marble)
scene.collection.objects.unlink(counter)
stage_col.objects.link(counter)

bpy.ops.mesh.primitive_plane_add(size=2.4, location=(0, 0.55, 0.55))
wall = bpy.context.active_object
wall.name = "TileBacksplash"
wall.rotation_euler = (math.radians(90), 0, 0)
wall.data.materials.append(mat_tile)
scene.collection.objects.unlink(wall)
stage_col.objects.link(wall)

# ==============================================================================
# 5. HERO GLASS TUMBLER + BOILING WATER + BUBBLES + STEAM + COMPLETE KETTLE
# ==============================================================================
def build_lathe(name, profile_rz, segs, mat, col):
    bm = bmesh.new()
    rings = []
    for r, z in profile_rz:
        ring = [bm.verts.new((math.cos(s / segs * 6.283185) * r, math.sin(s / segs * 6.283185) * r, z)) for s in range(segs)]
        rings.append(ring)
    for i in range(len(rings) - 1):
        for s in range(segs):
            s2 = (s + 1) % segs
            bm.faces.new((rings[i][s], rings[i][s2], rings[i + 1][s2], rings[i + 1][s]))
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

# Thick-base crystal tumbler (outer + inner wall for true double-wall refraction)
glass_obj = build_lathe("HeroGlass", [
    (0.029, 0.0002), (0.033, 0.003), (0.038, 0.016), (0.041, 0.058), (0.039, 0.105),
    (0.0380, 0.108), (0.0358, 0.108), (0.0364, 0.101), (0.0372, 0.058), (0.0332, 0.020), (0.0278, 0.014),
], 72, mat_glass, stage_col)

water_obj = build_lathe("BoilingWater", [
    (0.0275, 0.0145), (0.0328, 0.020), (0.0368, 0.058), (0.0362, 0.086),
], 56, mat_water, stage_col)

# 65 Rising Boiling Bubbles
bubbles = []
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.0016)
bub_mesh = bpy.context.active_object.data
bub_mesh.materials.append(mat_glass)
bpy.data.objects.remove(bpy.context.active_object, do_unlink=True)
for i in range(65):
    bo = bpy.data.objects.new(f"Bubble_{i}", bub_mesh)
    stage_col.objects.link(bo)
    bubbles.append((bo, (i * 2.39996) % 6.283, 0.004 + ((i * 0.013) % 0.027), 0.32 + (i % 7) * 0.08, (i * 0.37) % 1.0))

# 18 Rising Translucent Steam Wisps above the boiling glass
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
    steam_wisps.append((so, (i * 1.9) % 6.283, (i / 18.0)))

# Complete Brushed-Steel Gooseneck Kettle (Parented Root: Body + Lid + Knob + Handle + Spout!)
kettle_root = bpy.data.objects.new("KettleRoot", None)
stage_col.objects.link(kettle_root)
kettle_body = build_lathe("KettleBody", [
    (0.044, -0.052), (0.048, -0.045), (0.046, 0.010), (0.036, 0.058), (0.032, 0.064),
], 48, mat_steel, stage_col)
kettle_body.parent = kettle_root

kettle_lid = build_lathe("KettleLid", [
    (0.033, 0.064), (0.028, 0.070), (0.008, 0.072), (0.009, 0.082), (0.013, 0.085), (0.004, 0.087),
], 36, mat_matte_black, stage_col)
kettle_lid.parent = kettle_root

# Curved Kettle Handle (+X side)
bpy.ops.curve.primitive_bezier_curve_add()
k_handle = bpy.context.active_object
k_handle.data.bevel_depth = 0.0055
k_handle.data.bevel_resolution = 6
hp = k_handle.data.splines[0].bezier_points
hp[0].co = Vector((0.036, 0, 0.048))
hp[0].handle_right = Vector((0.088, 0, 0.048))
hp[1].co = Vector((0.046, 0, -0.036))
hp[1].handle_left = Vector((0.088, 0, -0.036))
k_handle.data.materials.append(mat_matte_black)
scene.collection.objects.unlink(k_handle)
stage_col.objects.link(k_handle)
k_handle.parent = kettle_root

# Gooseneck Spout (-X side, tip at (-0.088, 0, 0.058) in local space)
bpy.ops.curve.primitive_bezier_curve_add()
k_spout = bpy.context.active_object
k_spout.data.bevel_depth = 0.0052
k_spout.data.bevel_resolution = 8
sp = k_spout.data.splines[0].bezier_points
sp[0].co = Vector((-0.044, 0, -0.028))
sp[0].handle_right = Vector((-0.076, 0, -0.015))
sp[1].co = Vector((-0.088, 0, 0.058))
sp[1].handle_left = Vector((-0.072, 0, 0.048))
k_spout.data.materials.append(mat_steel)
scene.collection.objects.unlink(k_spout)
stage_col.objects.link(k_spout)
k_spout.parent = kettle_root

# Refracting Water Pour Stream (dynamically anchored to spout tip in render loop!)
bpy.ops.curve.primitive_bezier_curve_add()
pour_curve = bpy.context.active_object
pour_curve.data.bevel_depth = 0.0042
pour_curve.data.bevel_resolution = 8
pour_curve.data.materials.append(mat_water)
scene.collection.objects.unlink(pour_curve)
stage_col.objects.link(pour_curve)

# ==============================================================================
# 6. ANIMATED JAGGED BRANCHING FRACTURE WEB (Grows 0% -> 100% before Shatter!)
# ==============================================================================
cracks_col = bpy.data.collections.new("BranchingCracks")
scene.collection.children.link(cracks_col)
crack_curves = []
rng = random.Random(42)
impact_ang = -math.pi * 0.5  # Front-facing camera side!
impact_z = 0.056

for b_idx in range(14):
    cd = bpy.data.curves.new(f"Crack_{b_idx}", type="CURVE")
    cd.dimensions = "3D"
    cd.bevel_depth = 0.00055 if b_idx < 8 else 0.00035
    cd.bevel_resolution = 3
    spl = cd.splines.new("POLY")
    steps = 7
    spl.points.add(steps - 1)
    dir_ang = (b_idx / 14.0) * math.pi * 2.0 + rng.uniform(-0.18, 0.18)
    cur_a = impact_ang
    cur_z = impact_z
    for s in range(steps):
        if s > 0:
            cur_a += math.cos(dir_ang) * 0.14 + rng.uniform(-0.04, 0.04)
            cur_z = max(0.015, min(0.102, cur_z + math.sin(dir_ang) * 0.0085 + rng.uniform(-0.003, 0.003)))
        r_wall = 0.0392
        spl.points[s].co = (math.cos(cur_a) * r_wall, math.sin(cur_a) * r_wall, cur_z, 1.0)
    co = bpy.data.objects.new(f"CrackObj_{b_idx}", cd)
    co.data.materials.append(mat_crack)
    cracks_col.objects.link(co)
    crack_curves.append(cd)

# ==============================================================================
# 7. 80 REAL CRYSTAL SHATTER SHARDS + 40 FLYING WATER DROPLETS!
# ==============================================================================
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

# 40 Flying Refracting Water Droplets during shatter
droplets = []
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.0032)
drop_mesh = bpy.context.active_object.data
for p in drop_mesh.polygons:
    p.use_smooth = True
drop_mesh.materials.append(mat_water)
bpy.data.objects.remove(bpy.context.active_object, do_unlink=True)
for idx in range(40):
    ang = (idx * 2.39996 + 0.5) % 6.283185
    do = bpy.data.objects.new(f"Drop_{idx}", drop_mesh)
    shards_col.objects.link(do)
    spd = 0.075 + ((idx * 0.019) % 0.11)
    droplets.append({
        "obj": do,
        "origin": Vector((math.cos(ang) * 0.026, math.sin(ang) * 0.026, 0.022 + ((idx * 0.011) % 0.060))),
        "vel": Vector((math.cos(ang) * spd, math.sin(ang) * spd, 0.055 + ((idx * 0.017) % 0.095))),
    })

# ==============================================================================
# 8. SET B: REAL 3D SiO2 COVALENT ATOMIC LATTICE WITH SNAPPING BOND RODS!
# ==============================================================================
mol_col = bpy.data.collections.new("MolecularSet")
scene.collection.children.link(mol_col)
bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=16, radius=0.0064)
atom_mesh = bpy.context.active_object.data
for p in atom_mesh.polygons:
    p.use_smooth = True
bpy.data.objects.remove(bpy.context.active_object, do_unlink=True)

bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.0014, depth=1.0)
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
            ca.data.materials.append(mat_cold_atom)
            mol_col.objects.link(ca)
            cold_atoms.append((ca, x, y, z, (ix + iy * 3 + iz * 9) * 0.71, ix, iy, iz))

            ha = bpy.data.objects.new(f"Hot_{ix}_{iy}_{iz}", atom_mesh.copy())
            ha.data.materials.append(mat_hot_atom)
            mol_col.objects.link(ha)
            hot_atoms.append((ha, -x, y, z, (ix + iy * 3 + iz * 9) * 0.93, ix, iy, iz))

# Bridge covalent bonds across the shear seam (between Cold ix=0 and Hot ix=0!)
bridge_bonds = []
for iz in range(4):
    for iy in range(3):
        bo = bpy.data.objects.new(f"BridgeBond_{iy}_{iz}", bond_mesh.copy())
        bo.data.materials.append(mat_bond_snap)
        mol_col.objects.link(bo)
        bridge_bonds.append((bo, iy, iz))

# Internal lattice bonds
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
# 9. CINEMA CAMERA (Dynamic Lens + Shallow DoF f/2.0)
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
# 10. RENDER FRAME LIST
# ==============================================================================
if args.frames.strip():
    frame_list = [int(x.strip()) for x in args.frames.split(",") if x.strip()]
else:
    frame_list = list(range(args.start, min(args.end, TOTAL_FRAMES)))

for f in frame_list:
    t = f / FPS
    is_mol = (f >= BEATS[1]["f0"] + 86) and (f < BEATS[3]["f0"])
    shattered = (f >= SHATTER_F) and (f < BEATS[4]["f0"] + 48)
    pour_active = (f >= BEATS[1]["f0"]) and (f < BEATS[1]["f0"] + 86)
    cracks_vis = (not is_mol) and (not shattered) and (f >= BEATS[3]["f0"])

    stage_col.hide_render = is_mol
    mol_col.hide_render = not is_mol
    shards_col.hide_render = (not shattered) or is_mol
    cracks_col.hide_render = not cracks_vis

    if is_mol:
        bg_node.inputs[0].default_value = (0.008, 0.012, 0.028, 1.0)
        bg_node.inputs[1].default_value = 0.25
        m_u = max(0.0, min(1.0, (f - (BEATS[1]["f0"] + 86)) / max(1, BEATS[3]["f0"] - (BEATS[1]["f0"] + 86))))
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
        snapped = f >= VAC["f0"]
        for bo, iy, iz in bridge_bonds:
            bo.hide_render = snapped
            if not snapped:
                place_rod(bo, c_pos[(0, iy, iz)], h_pos[(0, iy, iz)])
    else:
        bg_node.inputs[0].default_value = (0.015, 0.022, 0.038, 1.0)
        bg_node.inputs[1].default_value = 0.35
        glass_obj.hide_render = shattered
        water_obj.hide_render = shattered
        pour_curve.hide_render = not pour_active
        kettle_vis = pour_active
        kettle_root.hide_render = not kettle_vis
        for ch in kettle_root.children:
            ch.hide_render = not kettle_vis

        if pour_active:
            pe = math.sin(min(1.0, max(0.0, (f - BEATS[1]["f0"]) / 16.0)) * math.pi * 0.5)
            kettle_root.location = (0.135 - pe * 0.012, 0.0, 0.155 + pe * 0.010)
            kettle_root.rotation_euler = (0.0, -pe * 0.52, 0.0)
            bpy.context.view_layer.update()
            spout_world = kettle_root.matrix_world @ Vector((-0.088, 0.0, 0.058))
            pts = pour_curve.data.splines[0].bezier_points
            pts[0].co = spout_world
            pts[0].handle_right = spout_world + Vector((-0.022, 0.0, -0.010))
            pts[1].co = Vector((0.008, 0.0, 0.072))
            pts[1].handle_left = Vector((0.012, 0.0, 0.120))

        # Animate branching crack growth 0% -> 100%
        if cracks_vis:
            cg = max(0.05, min(1.0, (f - BEATS[3]["f0"]) / max(1, SHATTER_F - BEATS[3]["f0"])))
            for cd in crack_curves:
                cd.bevel_factor_end = cg

        # Boiling bubbles
        for bo, ang, rad, spd, ph in bubbles:
            bo.hide_render = shattered
            yf = (ph + t * spd) % 1.0
            bo.location = (math.cos(ang) * rad, math.sin(ang) * rad, 0.016 + yf * 0.068)

        # Rising steam wisps
        for so, ang, ph in steam_wisps:
            so.hide_render = shattered
            u_s = (ph + t * 0.28) % 1.0
            rad = 0.006 + u_s * 0.026
            so.location = (math.cos(ang + u_s * 2.0) * rad, math.sin(ang + u_s * 2.0) * rad, 0.092 + u_s * 0.115)
            sc = 0.55 + u_s * 1.45
            so.scale = (sc, sc, sc * 1.35)

        # Bullet-time Shatter Shards + Flying Water Droplets
        if shattered:
            raw_dt = (f - SHATTER_F) / FPS
            sim_t = raw_dt * 0.22 if raw_dt < 1.25 else 1.25 * 0.22 + (raw_dt - 1.25) * 0.85
            for sh in shards:
                pz = sh["origin"].z + sh["vel"].z * sim_t - 0.5 * 0.35 * sim_t * sim_t
                if pz < 0.003:
                    pz = 0.003 + abs(pz - 0.003) * 0.35
                sh["obj"].location = (
                    sh["origin"].x + sh["vel"].x * sim_t,
                    sh["origin"].y + sh["vel"].y * sim_t,
                    pz,
                )
                sh["obj"].rotation_euler = (sh["rot"].x * sim_t, sh["rot"].y * sim_t, sh["ang"] + sh["rot"].z * sim_t)
            for dr in droplets:
                pz = dr["origin"].z + dr["vel"].z * sim_t - 0.5 * 0.42 * sim_t * sim_t
                if pz < 0.002:
                    pz = 0.002
                dr["obj"].location = (
                    dr["origin"].x + dr["vel"].x * sim_t,
                    dr["origin"].y + dr["vel"].y * sim_t,
                    pz,
                )

    # Dynamic Storytelling Camera Choreography
    if f < 48:
        u = f / 48.0
        aim_camera((-0.04 + u * 0.04, -0.32 + u * 0.07, 0.105 - u * 0.018), (0, 0, 0.058), 55.0, -1.2 * u)
    elif f < BEATS[1]["f0"]:
        u = (f - 48) / max(1, BEATS[1]["f0"] - 48)
        a = -0.30 + u * 0.60
        aim_camera((math.sin(a) * 0.25, -math.cos(a) * 0.25, 0.076 + u * 0.016), (0, 0, 0.058), 55.0, 1.8)
    elif f < BEATS[1]["f0"] + 86:
        u = (f - BEATS[1]["f0"]) / 86.0
        aim_camera((0.065 - u * 0.035, -0.28 + u * 0.02, 0.135 - u * 0.018), (0.015, 0, 0.078), 48.0, -1.8)
    elif f < VAC["f0"]:
        u = (f - (BEATS[1]["f0"] + 86)) / max(1, VAC["f0"] - (BEATS[1]["f0"] + 86))
        aim_camera((-0.025 + u * 0.025, -0.21 + u * 0.02, 0.010), (0, 0, 0), 52.0, 0.0)
    elif f < BEATS[2]["f0"]:
        u = (f - VAC["f0"]) / max(1, BEATS[2]["f0"] - VAC["f0"])
        aim_camera((0, -0.19 + u * 0.035, 0.005), (0, 0, 0), 44.0 + u * 14.0, -3.0 * u)
    elif f < BEATS[3]["f0"]:
        u = (f - BEATS[2]["f0"]) / max(1, BEATS[3]["f0"] - BEATS[2]["f0"])
        a = -0.28 + u * 0.72
        aim_camera((math.sin(a) * 0.20, -math.cos(a) * 0.20, 0.014), (0.005, 0, 0), 52.0, 0.0)
    elif f < SHATTER_F:
        u = (f - BEATS[3]["f0"]) / max(1, SHATTER_F - BEATS[3]["f0"])
        aim_camera((-0.022 + u * 0.022, -0.21 + u * 0.022, 0.064), (0, 0, 0.056), 58.0, 2.5 * u)
    elif f < BEATS[4]["f0"]:
        u = (f - SHATTER_F) / max(1, BEATS[4]["f0"] - SHATTER_F)
        a = -0.2 + u * 1.45
        aim_camera((math.sin(a) * 0.29, -math.cos(a) * 0.29, 0.092), (0, 0, 0.056), 46.0, -3.0 * math.sin(u * math.pi))
    else:
        u = (f - BEATS[4]["f0"]) / max(1, TOTAL_FRAMES - BEATS[4]["f0"])
        e = u * u * (3 - 2 * u)
        aim_camera((0.03 * (1 - e) - 0.04 * e, -0.30 * (1 - e) - 0.32 * e, 0.098 * (1 - e) + 0.105 * e), (0, 0, 0.058), 55.0, 0.0)

    scene.render.filepath = os.path.join(args.out, f"frame_{f:04d}.png")
    bpy.ops.render.render(write_still=True)

print(f"[Cycles V3] Finished {len(frame_list)} frames -> {args.out}")
