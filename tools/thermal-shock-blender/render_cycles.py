#!/usr/bin/env python3
"""
Thermal Shock V2 — Next-Level Blender 4.2 LTS Cycles Path-Traced 3D Film (Zack D. Films Standard).
Full Modern Sunlit Kitchen + Rigged 3D Human (homeowner.glb) + Real Refracting Glass & Water +
Covalent Atomic SiO2 Lattice Cutaway + Glowing Fracture Web + 80-Shard Bullet-Time Shatter!
"""
import argparse
import json
import math
import os
import sys

import bpy
import bmesh
from mathutils import Euler, Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
parser = argparse.ArgumentParser()
parser.add_argument("--start", type=int, default=0)
parser.add_argument("--end", type=int, default=35)
parser.add_argument("--out", type=str, default="/tmp/blender_frames")
parser.add_argument("--lock", type=str, default="tools/thermal-shock/voice-lock.json")
parser.add_argument("--samples", type=int, default=20)
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
# 1. CYCLES + OIDN + AgX FILMIC (Fast & Crystal-Clear)
# ==============================================================================
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = args.samples
scene.cycles.use_adaptive_sampling = True
scene.cycles.adaptive_threshold = 0.04
scene.cycles.use_denoising = True
scene.cycles.denoiser = "OPENIMAGEDENOISE"
scene.cycles.max_bounces = 6
scene.cycles.diffuse_bounces = 2
scene.cycles.glossy_bounces = 3
scene.cycles.transmission_bounces = 6
scene.cycles.transparent_max_bounces = 4

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
scene.view_settings.exposure = 0.30

world = bpy.data.worlds.new("KitchenWorld")
scene.world = world
world.use_nodes = True
bg_node = world.node_tree.nodes.get("Background")
bg_node.inputs[0].default_value = (0.82, 0.78, 0.72, 1.0)
bg_node.inputs[1].default_value = 0.70

# ==============================================================================
# 2. CINEMA STUDIO LIGHTING (Warm Window Sun + Cool Fill + Overhead Rim)
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

add_area_light("SunWindow", (-0.52, -0.38, 0.52), (50, 0, -52), 34.0, 0.65, 0.50, (1.0, 0.94, 0.86))
add_area_light("SkyFill", (0.52, -0.28, 0.38), (58, 0, 56), 16.0, 0.65, 0.45, (0.84, 0.93, 1.0))
add_area_light("RimSoftbox", (0.0, 0.42, 0.50), (-48, 0, 0), 22.0, 0.50, 0.30, (1.0, 0.98, 0.94))

# ==============================================================================
# 3. MATERIALS
# ==============================================================================
def make_glass_mat(name, ior=1.52, roughness=0.015, tint=(0.98, 0.995, 1.0, 1.0)):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = tint
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["IOR"].default_value = ior
    bsdf.inputs["Transmission Weight"].default_value = 1.0
    if "Coat Weight" in bsdf.inputs:
        bsdf.inputs["Coat Weight"].default_value = 0.6
    return mat

def make_quartz_mat():
    mat = bpy.data.materials.new("QuartzCounter")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.14
    if "Coat Weight" in bsdf.inputs:
        bsdf.inputs["Coat Weight"].default_value = 0.45
    tc = nt.nodes.new("ShaderNodeTexCoord")
    ns = nt.nodes.new("ShaderNodeTexNoise")
    ns.inputs["Scale"].default_value = 70.0
    ns.inputs["Detail"].default_value = 8.0
    rmp = nt.nodes.new("ShaderNodeValToRGB")
    rmp.color_ramp.elements[0].position = 0.35
    rmp.color_ramp.elements[0].color = (0.72, 0.69, 0.65, 1.0)
    rmp.color_ramp.elements[1].position = 0.70
    rmp.color_ramp.elements[1].color = (0.90, 0.88, 0.84, 1.0)
    nt.links.new(tc.outputs["Object"], ns.inputs["Vector"])
    nt.links.new(ns.outputs["Fac"], rmp.inputs["Fac"])
    nt.links.new(rmp.outputs["Color"], bsdf.inputs["Base Color"])
    return mat

def make_pbr(name, color, roughness=0.35, metallic=0.0, emission=0.0):
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

mat_glass = make_glass_mat("RealGlass", ior=1.52, roughness=0.015)
mat_water = make_glass_mat("RealWater", ior=1.333, roughness=0.025, tint=(0.94, 0.985, 1.0, 1.0))
mat_quartz = make_quartz_mat()
mat_steel = make_pbr("BrushedSteel", (0.84, 0.87, 0.90, 1.0), roughness=0.14, metallic=0.96)
mat_oak = make_pbr("WarmOak", (0.48, 0.30, 0.17, 1.0), roughness=0.42)
mat_walnut = make_pbr("WalnutBoard", (0.28, 0.16, 0.09, 1.0), roughness=0.38)
mat_tile = make_pbr("SubwayTile", (0.90, 0.89, 0.86, 1.0), roughness=0.18)
mat_ceramic = make_pbr("CeramicMug", (0.76, 0.28, 0.16, 1.0), roughness=0.12)
mat_leaf = make_pbr("PlantLeaf", (0.14, 0.42, 0.16, 1.0), roughness=0.35)
mat_led = make_pbr("WarmLED", (1.0, 0.86, 0.65, 1.0), roughness=0.2, emission=6.0)
mat_cold_atom = make_pbr("ColdAtom", (0.04, 0.76, 1.0, 1.0), roughness=0.10, emission=5.0)
mat_hot_atom = make_pbr("HotAtom", (1.0, 0.22, 0.02, 1.0), roughness=0.10, emission=6.0)
mat_bond = make_pbr("CovalentBond", (0.75, 0.85, 0.95, 1.0), roughness=0.2, metallic=0.6)
mat_crack = make_pbr("ThermalCrack", (1.0, 0.84, 0.28, 1.0), roughness=0.1, emission=12.0)

# ==============================================================================
# 4. SET A: FULL MODERN SUNLIT KITCHEN + PROPS + RIGGED 3D HUMAN
# ==============================================================================
kitchen_col = bpy.data.collections.new("KitchenSet")
scene.collection.children.link(kitchen_col)

def add_box(name, loc, scale, mat, col):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = scale
    o.data.materials.append(mat)
    scene.collection.objects.unlink(o)
    col.objects.link(o)
    return o

# Quartz Countertop + Subway Tile Backsplash + Oak Cabinets + Under-Cabinet LED
add_box("QuartzCounter", (0, 0.05, -0.02), (1.8, 1.0, 0.04), mat_quartz, kitchen_col)
add_box("BacksplashWall", (0, 0.56, 0.32), (1.8, 0.04, 0.72), mat_tile, kitchen_col)
add_box("UpperCabinet", (0, 0.44, 0.58), (1.6, 0.24, 0.26), mat_oak, kitchen_col)
add_box("UnderCabinetLED", (0, 0.36, 0.445), (1.4, 0.012, 0.008), mat_led, kitchen_col)
add_box("StainlessFridge", (0.42, 0.50, 0.28), (0.38, 0.18, 0.68), mat_steel, kitchen_col)

# Walnut Cutting Board + Ceramic Coffee Mug + Potted Kitchen Plant (Foreground/Midground Depth!)
add_box("CuttingBoard", (-0.19, 0.10, 0.008), (0.20, 0.14, 0.016), mat_walnut, kitchen_col)

bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.032, depth=0.072, location=(-0.20, 0.08, 0.052))
mug = bpy.context.active_object
mug.data.materials.append(mat_ceramic)
scene.collection.objects.unlink(mug)
kitchen_col.objects.link(mug)

bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.036, depth=0.068, location=(0.24, 0.18, 0.034))
pot = bpy.context.active_object
pot.data.materials.append(mat_tile)
scene.collection.objects.unlink(pot)
kitchen_col.objects.link(pot)
for l_idx in range(6):
    a = (l_idx / 6.0) * math.pi * 2
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.024, location=(0.24 + math.cos(a) * 0.022, 0.18 + math.sin(a) * 0.022, 0.082))
    lf = bpy.context.active_object
    lf.scale = (1.3, 0.6, 0.5)
    lf.rotation_euler = (0.3, 0.2, a)
    lf.data.materials.append(mat_leaf)
    scene.collection.objects.unlink(lf)
    kitchen_col.objects.link(lf)

# Import Rigged 53-Bone 3D Human (`homeowner.glb`) standing behind the kitchen counter!
human_root = None
glb_path = os.path.abspath("tools/monarch-cockroach/v4/assets/homeowner.glb")
if os.path.exists(glb_path):
    bpy.ops.import_scene.gltf(filepath=glb_path)
    imported = [o for o in bpy.context.selected_objects]
    human_root = bpy.data.objects.new("HumanRoot", None)
    kitchen_col.objects.link(human_root)
    human_root.location = (-0.08, 0.30, -0.34)
    human_root.rotation_euler = (0, 0, math.radians(-165))
    human_root.scale = (0.45, 0.45, 0.45)
    for o in imported:
        if o.parent is None:
            o.parent = human_root
        if o.name in scene.collection.objects:
            scene.collection.objects.unlink(o)
        if o.name not in kitchen_col.objects:
            kitchen_col.objects.link(o)

# ==============================================================================
# 5. HERO GLASS TUMBLER + BOILING WATER + BUBBLES + KETTLE + POUR STREAM
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

glass_obj = build_lathe("HeroGlass", [
    (0.030, 0.0002), (0.034, 0.004), (0.039, 0.018), (0.042, 0.055), (0.039, 0.102),
    (0.0378, 0.105), (0.0355, 0.105), (0.0362, 0.098), (0.0372, 0.055), (0.0335, 0.020), (0.0285, 0.014),
], 64, mat_glass, kitchen_col)

water_obj = build_lathe("BoilingWater", [
    (0.028, 0.0145), (0.033, 0.020), (0.0365, 0.055), (0.0358, 0.084),
], 48, mat_water, kitchen_col)

# 60 Refracting Boiling Bubbles
bubbles = []
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.0017)
bub_proto = bpy.context.active_object
bub_mesh = bub_proto.data
bub_mesh.materials.append(mat_glass)
bpy.data.objects.remove(bub_proto, do_unlink=True)
for i in range(60):
    bo = bpy.data.objects.new(f"Bubble_{i}", bub_mesh)
    kitchen_col.objects.link(bo)
    bubbles.append((bo, (i * 2.39996) % 6.283, 0.004 + ((i * 0.013) % 0.026), 0.28 + (i % 7) * 0.08, (i * 0.37) % 1.0))

# Glowing Spiderweb Cracks inside Glass Wall (visible during Beat 4 pre-shatter!)
cracks_col = bpy.data.collections.new("Cracks")
scene.collection.children.link(cracks_col)
for k in range(12):
    ba = (k / 12.0) * 6.283185
    bpy.ops.curve.primitive_bezier_curve_add()
    crv = bpy.context.active_object
    crv.data.bevel_depth = 0.0006
    p = crv.data.splines[0].bezier_points
    p[0].co = Vector((math.cos(ba) * 0.0385, math.sin(ba) * 0.0385, 0.016 + (k % 3) * 0.014))
    p[1].co = Vector((math.cos(ba + 0.18) * 0.0385, math.sin(ba + 0.18) * 0.0385, 0.086 + (k % 2) * 0.012))
    crv.data.materials.append(mat_crack)
    scene.collection.objects.unlink(crv)
    cracks_col.objects.link(crv)

# Brushed Steel Pouring Kettle + Curved Refracting Water Stream
kettle_obj = build_lathe("SteelKettle", [(0.042, -0.05), (0.048, 0.0), (0.036, 0.065), (0.028, 0.075)], 40, mat_steel, kitchen_col)
kettle_obj.location = (0.135, 0.0, 0.165)

bpy.ops.curve.primitive_bezier_curve_add()
pour_curve = bpy.context.active_object
pour_curve.data.bevel_depth = 0.0048
pour_curve.data.bevel_resolution = 8
pts = pour_curve.data.splines[0].bezier_points
pts[0].co = Vector((0.084, 0.0, 0.185))
pts[0].handle_right = Vector((0.046, 0.0, 0.165))
pts[1].co = Vector((0.016, 0.0, 0.075))
pts[1].handle_left = Vector((0.022, 0.0, 0.125))
pour_curve.data.materials.append(mat_water)
scene.collection.objects.unlink(pour_curve)
kitchen_col.objects.link(pour_curve)

# ==============================================================================
# 6. 80 REAL REFRACTING CRYSTAL SHATTER SHARDS + FLYING WATER DROPLETS!
# ==============================================================================
shards_col = bpy.data.collections.new("ShatterShards")
scene.collection.children.link(shards_col)
shards = []
for idx in range(80):
    ang = (idx * 2.39996) % 6.283185
    z0 = 0.014 + ((idx * 0.013) % 0.088)
    bm = bmesh.new()
    w = 0.005 + ((idx * 0.0029) % 0.009)
    h = 0.009 + ((idx * 0.0049) % 0.014)
    v0 = bm.verts.new((0, 0, h * 0.6))
    v1 = bm.verts.new((w * 0.55, 0, -h * 0.15))
    v2 = bm.verts.new((w * 0.2, 0, -h * 0.55))
    v3 = bm.verts.new((-w * 0.48, 0, -h * 0.35))
    f = bm.faces.new((v0, v1, v2, v3))
    ret = bmesh.ops.extrude_face_region(bm, geom=[f])
    bmesh.ops.translate(bm, verts=[g for g in ret["geom"] if isinstance(g, bmesh.types.BMVert)], vec=(0, 0.0022, 0))
    m = bpy.data.meshes.new(f"ShardMesh_{idx}")
    bm.to_mesh(m)
    bm.free()
    so = bpy.data.objects.new(f"Shard_{idx}", m)
    so.data.materials.append(mat_glass)
    shards_col.objects.link(so)
    spd = 0.095 + ((idx * 0.023) % 0.13)
    shards.append({
        "obj": so,
        "origin": Vector((math.cos(ang) * 0.038, math.sin(ang) * 0.038, z0)),
        "vel": Vector((math.cos(ang) * spd, math.sin(ang) * spd, 0.038 + ((idx * 0.013) % 0.082))),
        "rot": Vector((((idx % 3) - 1) * 6.8 + 2.0, ((idx % 5) - 2) * 5.4, ((idx % 4) - 1.5) * 7.2)),
        "ang": ang,
    })

# ==============================================================================
# 7. SET B: COVALENT ATOMIC SiO2 LATTICE CUTAWAY (Cold Cyan vs Molten Red)
# ==============================================================================
mol_col = bpy.data.collections.new("MolecularSet")
scene.collection.children.link(mol_col)
bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=14, radius=0.0068)
atom_proto = bpy.context.active_object
atom_mesh = atom_proto.data
for p in atom_mesh.polygons:
    p.use_smooth = True
bpy.data.objects.remove(atom_proto, do_unlink=True)

cold_atoms, hot_atoms = [], []
for i in range(48):
    gx = (i % 3) * 0.026
    gz = (int(i / 3) % 4) * 0.026 - 0.039
    gy = (int(i / 12) % 4) * 0.026 - 0.039
    ca = bpy.data.objects.new(f"ColdAtom_{i}", atom_mesh.copy())
    ca.data.materials.append(mat_cold_atom)
    mol_col.objects.link(ca)
    cold_atoms.append((ca, -0.024 - gx, gy, gz, i * 0.71))

    ha = bpy.data.objects.new(f"HotAtom_{i}", atom_mesh.copy())
    ha.data.materials.append(mat_hot_atom)
    mol_col.objects.link(ha)
    hot_atoms.append((ha, 0.024 + gx, gy, gz, i * 0.93))

# Multi-bolt Golden Shear-Fracture Lightning Seam
shear_bolts = []
for b in range(3):
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.0016, depth=0.19, location=((b - 1) * 0.004, (b - 1) * 0.012, 0))
    sb = bpy.context.active_object
    sb.rotation_euler = (0.08 * (b - 1), 0.05 * (b - 1), 0)
    sb.data.materials.append(mat_crack)
    scene.collection.objects.unlink(sb)
    mol_col.objects.link(sb)
    shear_bolts.append(sb)

# ==============================================================================
# 8. CINEMA CAMERA (Dynamic Lens + Cycles DoF f/2.8)
# ==============================================================================
cam_data = bpy.data.cameras.new("CinemaCam")
cam_data.lens = 50.0
cam_data.dof.use_dof = True
cam_data.dof.aperture_fstop = 2.8
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
    cam_data.dof.focus_distance = direction.length

# ==============================================================================
# 9. RENDER CHUNK [args.start .. args.end)
# ==============================================================================
for f in range(args.start, min(args.end, TOTAL_FRAMES)):
    t = f / FPS
    is_mol = (f >= BEATS[1]["f0"] + 86) and (f < BEATS[3]["f0"])
    shattered = (f >= SHATTER_F) and (f < BEATS[4]["f0"] + 48)
    pour_active = (f >= BEATS[1]["f0"]) and (f < BEATS[1]["f0"] + 86)
    cracks_vis = (not is_mol) and (not shattered) and (f >= BEATS[3]["f0"])

    kitchen_col.hide_render = is_mol
    mol_col.hide_render = not is_mol
    shards_col.hide_render = (not shattered) or is_mol
    cracks_col.hide_render = not cracks_vis

    if is_mol:
        bg_node.inputs[0].default_value = (0.012, 0.018, 0.042, 1.0)
        bg_node.inputs[1].default_value = 0.25
        m_u = max(0.0, min(1.0, (f - (BEATS[1]["f0"] + 86)) / max(1, BEATS[3]["f0"] - (BEATS[1]["f0"] + 86))))
        for obj, x, y, z, ph in cold_atoms:
            obj.location = (x - m_u * 0.015 + math.sin(t * 28 + ph) * 0.001, y, z * (1 - m_u * 0.08))
        for obj, x, y, z, ph in hot_atoms:
            obj.location = (x + m_u * 0.017 + math.sin(t * 48 + ph) * 0.0032, y, z * (1 + m_u * 0.12))
        for sb in shear_bolts:
            sb.hide_render = f < VAC["f0"]
    else:
        bg_node.inputs[0].default_value = (0.82, 0.78, 0.72, 1.0)
        bg_node.inputs[1].default_value = 0.70
        glass_obj.hide_render = shattered
        water_obj.hide_render = shattered
        pour_curve.hide_render = not pour_active
        kettle_obj.hide_render = not (pour_active or f < BEATS[1]["f0"])
        pe = math.sin(min(1.0, max(0.0, (f - BEATS[1]["f0"]) / 16.0)) * math.pi * 0.5) if pour_active else 0.0
        kettle_obj.location = (0.135 - pe * 0.02, 0.0, 0.165 + pe * 0.018)
        kettle_obj.rotation_euler = (0.0, -pe * 0.65, 0.0)

        # Human recoil backward on glass shatter!
        if human_root is not None:
            recoil = min(1.0, (f - SHATTER_F) / 14.0) if shattered else 0.0
            human_root.location = (-0.08 - recoil * 0.04, 0.30 + recoil * 0.08, -0.34)

        for bo, ang, rad, spd, ph in bubbles:
            bo.hide_render = shattered
            yf = (ph + t * spd) % 1.0
            bo.location = (math.cos(ang) * rad, math.sin(ang) * rad, 0.016 + yf * 0.065)

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

    # Dynamic Storytelling Camera Choreography
    if f < 48:
        u = f / 48.0
        aim_camera((-0.05 + u * 0.05, -0.34 + u * 0.08, 0.115 - u * 0.022), (0, 0, 0.058), 50.0, -1.5 * u)
    elif f < BEATS[1]["f0"]:
        u = (f - 48) / max(1, BEATS[1]["f0"] - 48)
        a = -0.32 + u * 0.64
        aim_camera((math.sin(a) * 0.25, -math.cos(a) * 0.25, 0.078 + u * 0.018), (0, 0, 0.058), 52.0, 2.0)
    elif f < BEATS[1]["f0"] + 86:
        u = (f - BEATS[1]["f0"]) / 86.0
        aim_camera((0.085 - u * 0.045, -0.26 + u * 0.02, 0.140 - u * 0.020), (0.015, 0, 0.075), 46.0, -2.0)
    elif f < VAC["f0"]:
        u = (f - (BEATS[1]["f0"] + 86)) / max(1, VAC["f0"] - (BEATS[1]["f0"] + 86))
        aim_camera((-0.03 + u * 0.03, -0.21 + u * 0.02, 0.012), (0, 0, 0), 50.0, 0.0)
    elif f < BEATS[2]["f0"]:
        u = (f - VAC["f0"]) / max(1, BEATS[2]["f0"] - VAC["f0"])
        aim_camera((0, -0.19 + u * 0.04, 0.006), (0, 0, 0), 42.0 + u * 16.0, -3.5 * u)
    elif f < BEATS[3]["f0"]:
        u = (f - BEATS[2]["f0"]) / max(1, BEATS[3]["f0"] - BEATS[2]["f0"])
        a = -0.3 + u * 0.78
        aim_camera((math.sin(a) * 0.20, -math.cos(a) * 0.20, 0.016), (0.006, 0, 0), 50.0, 0.0)
    elif f < SHATTER_F:
        u = (f - BEATS[3]["f0"]) / max(1, SHATTER_F - BEATS[3]["f0"])
        aim_camera((-0.028 + u * 0.028, -0.22 + u * 0.025, 0.068), (0, 0, 0.056), 54.0, 3.0 * u)
    elif f < BEATS[4]["f0"]:
        u = (f - SHATTER_F) / max(1, BEATS[4]["f0"] - SHATTER_F)
        a = -0.2 + u * 1.55
        aim_camera((math.sin(a) * 0.30, -math.cos(a) * 0.30, 0.098), (0, 0, 0.056), 44.0, -3.5 * math.sin(u * math.pi))
    else:
        u = (f - BEATS[4]["f0"]) / max(1, TOTAL_FRAMES - BEATS[4]["f0"])
        e = u * u * (3 - 2 * u)
        aim_camera((0.04 * (1 - e) - 0.05 * e, -0.32 * (1 - e) - 0.34 * e, 0.105 * (1 - e) + 0.115 * e), (0, 0, 0.058), 50.0, 0.0)

    scene.render.filepath = os.path.join(args.out, f"frame_{f:04d}.png")
    bpy.ops.render.render(write_still=True)

print(f"[Cycles V2] Finished chunk [{args.start}..{args.end}) -> {args.out}")
