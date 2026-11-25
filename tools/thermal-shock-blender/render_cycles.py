#!/usr/bin/env python3
"""
Thermal Shock — True Blender 4.2 LTS Cycles Path-Traced 3D Renderer (Zack D. Films Quality).
Run inside Blender headless:
  blender --background --python tools/thermal-shock-blender/render_cycles.py -- --start 0 --end 69 --out /tmp/frames
"""
import argparse
import json
import math
import os
import sys

import bpy
import bmesh
from mathutils import Euler, Vector

# Parse args after '--'
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
parser = argparse.ArgumentParser()
parser.add_argument("--start", type=int, default=0)
parser.add_argument("--end", type=int, default=69)
parser.add_argument("--out", type=str, default="/tmp/blender_frames")
parser.add_argument("--lock", type=str, default="tools/thermal-shock/voice-lock.json")
parser.add_argument("--samples", type=int, default=36)
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
# 1. RESET & CONFIGURE CYCLES + OIDN + AgX FILMIC
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
scene.cycles.max_bounces = 8
scene.cycles.diffuse_bounces = 3
scene.cycles.glossy_bounces = 4
scene.cycles.transmission_bounces = 8
scene.cycles.transparent_max_bounces = 6
scene.cycles.caustics_reflective = True
scene.cycles.caustics_refractive = True

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
scene.view_settings.exposure = 0.25

# World background (Warm Bright Modern Kitchen Daylight)
world = bpy.data.worlds.new("KitchenWorld")
scene.world = world
world.use_nodes = True
wnodes = world.node_tree.nodes
wlinks = world.node_tree.links
bg_node = wnodes.get("Background")
bg_node.inputs[0].default_value = (0.78, 0.74, 0.68, 1.0)
bg_node.inputs[1].default_value = 0.65

# ==============================================================================
# 2. STUDIO SOFTBOX LIGHTING (Zack D. Films Bright Tactile 3D Look)
# ==============================================================================
def add_area_light(name, loc, rot_deg, energy, size_x, size_y, color):
    ld = bpy.data.lights.new(name=name, type="AREA")
    ld.energy = energy
    ld.shape = "RECTANGLE"
    ld.size = size_x
    ld.size_y = size_y
    ld.color = color
    lo = bpy.data.objects.new(name=name, object_data=ld)
    lo.location = loc
    lo.rotation_euler = tuple(math.radians(a) for a in rot_deg)
    scene.collection.objects.link(lo)
    return lo

# Warm daylight kitchen window key light (left-front)
add_area_light("KeyWindow", (-0.42, -0.35, 0.45), (52, 0, -48), 26.0, 0.55, 0.45, (1.0, 0.96, 0.90))
# Cool sky fill softbox (right)
add_area_light("CoolFill", (0.48, -0.25, 0.35), (60, 0, 58), 14.0, 0.60, 0.45, (0.86, 0.94, 1.0))
# Overhead crisp rim softbox (gives razor-sharp glass rim highlight!)
add_area_light("RimTop", (0.02, 0.38, 0.46), (-50, 0, 0), 18.0, 0.45, 0.28, (1.0, 0.98, 0.95))

# ==============================================================================
# 3. PHYSICALLY-BASED CYCLES MATERIALS
# ==============================================================================
def make_glass_mat(name, ior=1.52, roughness=0.02, tint=(0.97, 0.99, 1.0, 1.0)):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = tint
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["IOR"].default_value = ior
    bsdf.inputs["Transmission Weight"].default_value = 1.0
    if "Coat Weight" in bsdf.inputs:
        bsdf.inputs["Coat Weight"].default_value = 0.5
    return mat

def make_quartz_mat():
    mat = bpy.data.materials.new("QuartzCounter")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.16
    if "Coat Weight" in bsdf.inputs:
        bsdf.inputs["Coat Weight"].default_value = 0.35
    # Speckled quartz procedural texture
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 65.0
    noise.inputs["Detail"].default_value = 8.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.35
    ramp.color_ramp.elements[0].color = (0.68, 0.65, 0.61, 1.0)
    ramp.color_ramp.elements[1].position = 0.68
    ramp.color_ramp.elements[1].color = (0.86, 0.84, 0.80, 1.0)
    nt.links.new(tex_coord.outputs["Object"], noise.inputs["Vector"])
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    return mat

def make_metal_mat(name, color=(0.82, 0.85, 0.88, 1.0), roughness=0.14):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Metallic"].default_value = 0.96
    bsdf.inputs["Roughness"].default_value = roughness
    return mat

def make_emissive_pbr(name, color, strength=3.0, roughness=0.15):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = roughness
    if "Emission Color" in bsdf.inputs:
        bsdf.inputs["Emission Color"].default_value = color
        bsdf.inputs["Emission Strength"].default_value = strength
    return mat

mat_glass = make_glass_mat("RealGlass", ior=1.52, roughness=0.015, tint=(0.98, 0.995, 1.0, 1.0))
mat_water = make_glass_mat("RealWater", ior=1.333, roughness=0.03, tint=(0.94, 0.98, 1.0, 1.0))
mat_quartz = make_quartz_mat()
mat_steel = make_metal_mat("BrushedSteel")
mat_oak = make_emissive_pbr("WarmOak", (0.45, 0.28, 0.16, 1.0), strength=0.0, roughness=0.45)
mat_cold_atom = make_emissive_pbr("ColdAtom", (0.04, 0.72, 1.0, 1.0), strength=4.5, roughness=0.10)
mat_hot_atom = make_emissive_pbr("HotAtom", (1.0, 0.20, 0.02, 1.0), strength=5.5, roughness=0.12)
mat_crack = make_emissive_pbr("ThermalCrack", (1.0, 0.82, 0.25, 1.0), strength=10.0, roughness=0.1)

# ==============================================================================
# 4. BUILD KITCHEN ENVIRONMENT (Physical scale: 1 Blender unit = 1 meter!)
# ==============================================================================
kitchen_col = bpy.data.collections.new("KitchenSet")
scene.collection.children.link(kitchen_col)

def link_obj(obj, col):
    col.objects.link(obj)
    return obj

# Quartz Countertop
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, -0.02))
counter = bpy.context.active_object
counter.scale = (1.6, 0.9, 0.04)
counter.data.materials.append(mat_quartz)
scene.collection.objects.unlink(counter)
link_obj(counter, kitchen_col)

# Background Warm Oak Cabinet + Stainless Appliance (blurred nicely by Cycles DoF!)
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-0.28, 0.52, 0.16))
cab = bpy.context.active_object
cab.scale = (0.48, 0.14, 0.42)
cab.data.materials.append(mat_oak)
scene.collection.objects.unlink(cab)
link_obj(cab, kitchen_col)

bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.24, 0.56, 0.24))
fridge = bpy.context.active_object
fridge.scale = (0.34, 0.14, 0.62)
fridge.data.materials.append(mat_steel)
scene.collection.objects.unlink(fridge)
link_obj(fridge, kitchen_col)

# ==============================================================================
# 5. BUILD REAL THICK-WALLED BOROSILICATE GLASS TUMBLER (Spin Mesh)
# ==============================================================================
def build_lathe(name, profile_rz, segs, mat, col):
    bm = bmesh.new()
    rings = []
    for r, z in profile_rz:
        ring = []
        for s in range(segs):
            a = (s / segs) * math.pi * 2.0
            v = bm.verts.new((math.cos(a) * r, math.sin(a) * r, z))
            ring.append(v)
        rings.append(ring)
    for i in range(len(rings) - 1):
        for s in range(segs):
            s2 = (s + 1) % segs
            bm.faces.new((rings[i][s], rings[i][s2], rings[i + 1][s2], rings[i + 1][s]))
    # Cap bottom & inner bottom
    bm.faces.new(rings[0][::-1])
    bm.faces.new(rings[-1])
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    for p in mesh.polygons:
        p.use_smooth = True
    obj = bpy.data.objects.new(name, mesh)
    obj.data.materials.append(mat)
    return link_obj(obj, col)

glass_profile = [
    (0.030, 0.0002),
    (0.034, 0.004),
    (0.039, 0.018),
    (0.042, 0.055),
    (0.039, 0.102),
    (0.0378, 0.105),
    (0.0355, 0.105),
    (0.0362, 0.098),
    (0.0372, 0.055),
    (0.0335, 0.020),
    (0.0285, 0.014),
]
glass_obj = build_lathe("HeroGlass", glass_profile, 64, mat_glass, kitchen_col)

water_profile = [
    (0.028, 0.0145),
    (0.033, 0.020),
    (0.0365, 0.055),
    (0.0358, 0.084),
]
water_obj = build_lathe("BoilingWater", water_profile, 48, mat_water, kitchen_col)

# 60 Refracting Boiling Bubbles inside water
bubbles = []
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.0018)
bub_proto = bpy.context.active_object
bub_mesh = bub_proto.data
bub_mesh.materials.append(mat_glass)
bpy.data.objects.remove(bub_proto, do_unlink=True)
for i in range(60):
    bo = bpy.data.objects.new(f"Bubble_{i}", bub_mesh)
    link_obj(bo, kitchen_col)
    bubbles.append((bo, (i * 2.39996) % 6.283, 0.004 + ((i * 0.013) % 0.026), 0.25 + (i % 7) * 0.08, (i * 0.37) % 1.0))

# Stainless Steel Pouring Kettle + Refracting Cold Water Stream
kettle_profile = [(0.042, -0.05), (0.048, 0.0), (0.036, 0.065), (0.028, 0.075)]
kettle_obj = build_lathe("SteelKettle", kettle_profile, 40, mat_steel, kitchen_col)
kettle_obj.location = (0.13, 0.0, 0.165)

# Curved Pour Stream (Tube)
bpy.ops.curve.primitive_bezier_curve_add()
pour_curve = bpy.context.active_object
pour_curve.data.bevel_depth = 0.0045
pour_curve.data.bevel_resolution = 8
pts = pour_curve.data.splines[0].bezier_points
pts[0].co = Vector((0.082, 0.0, 0.185))
pts[0].handle_right = Vector((0.045, 0.0, 0.165))
pts[1].co = Vector((0.016, 0.0, 0.075))
pts[1].handle_left = Vector((0.022, 0.0, 0.125))
pour_curve.data.materials.append(mat_water)
scene.collection.objects.unlink(pour_curve)
link_obj(pour_curve, kitchen_col)

# ==============================================================================
# 6. 54 REAL REFRACTING CRYSTAL SHATTER SHARDS (Bullet-Time Explosion!)
# ==============================================================================
shards_col = bpy.data.collections.new("ShatterShards")
scene.collection.children.link(shards_col)
shards = []
for idx in range(54):
    ang = (idx * 2.39996) % (math.pi * 2.0)
    z0 = 0.015 + ((idx * 0.017) % 0.085)
    bm = bmesh.new()
    w = 0.006 + ((idx * 0.0031) % 0.009)
    h = 0.010 + ((idx * 0.0053) % 0.014)
    v0 = bm.verts.new((0, 0, h * 0.6))
    v1 = bm.verts.new((w * 0.55, 0, -h * 0.15))
    v2 = bm.verts.new((w * 0.2, 0, -h * 0.55))
    v3 = bm.verts.new((-w * 0.48, 0, -h * 0.35))
    f = bm.faces.new((v0, v1, v2, v3))
    ret = bmesh.ops.extrude_face_region(bm, geom=[f])
    bmesh.ops.translate(bm, verts=[g for g in ret["geom"] if isinstance(g, bmesh.types.BMVert)], vec=(0, 0.0025, 0))
    m = bpy.data.meshes.new(f"ShardMesh_{idx}")
    bm.to_mesh(m)
    bm.free()
    so = bpy.data.objects.new(f"Shard_{idx}", m)
    so.data.materials.append(mat_glass)
    link_obj(so, shards_col)
    spd = 0.09 + ((idx * 0.023) % 0.12)
    shards.append({
        "obj": so,
        "origin": Vector((math.cos(ang) * 0.038, math.sin(ang) * 0.038, z0)),
        "vel": Vector((math.cos(ang) * spd, math.sin(ang) * spd, 0.035 + ((idx * 0.013) % 0.075))),
        "rot": Vector((((idx % 3) - 1) * 6.5 + 2.0, ((idx % 5) - 2) * 5.2, ((idx % 4) - 1.5) * 6.8)),
        "ang": ang,
    })

# ==============================================================================
# 7. SET B: ATOMIC MOLECULAR SiO2 CUTAWAY (Cold Cyan vs Molten Red + Shear Seam)
# ==============================================================================
mol_col = bpy.data.collections.new("MolecularSet")
scene.collection.children.link(mol_col)
bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=14, radius=0.0065)
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
    link_obj(ca, mol_col)
    cold_atoms.append((ca, -0.024 - gx, gy, gz, i * 0.71))

    ha = bpy.data.objects.new(f"HotAtom_{i}", atom_mesh.copy())
    ha.data.materials.append(mat_hot_atom)
    link_obj(ha, mol_col)
    hot_atoms.append((ha, 0.024 + gx, gy, gz, i * 0.93))

# Glowing Golden Shear-Fracture Plane in center of molecular set
bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.0018, depth=0.18, location=(0, 0, 0))
shear_bolt = bpy.context.active_object
shear_bolt.data.materials.append(mat_crack)
scene.collection.objects.unlink(shear_bolt)
link_obj(shear_bolt, mol_col)

# ==============================================================================
# 8. CAMERA WITH REAL CYCLES DEPTH-OF-FIELD (f-stop = 2.8)
# ==============================================================================
cam_data = bpy.data.cameras.new("CinemaCam")
cam_data.lens = 52.0
cam_data.dof.use_dof = True
cam_data.dof.aperture_fstop = 2.8
cam_obj = bpy.data.objects.new("CinemaCam", cam_data)
scene.collection.objects.link(cam_obj)
scene.camera = cam_obj

def aim_camera(pos, target, lens=52.0):
    cam_obj.location = Vector(pos)
    direction = Vector(target) - cam_obj.location
    cam_obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    cam_data.lens = lens
    cam_data.dof.focus_distance = direction.length

# ==============================================================================
# 9. RENDER ASSIGNED FRAME CHUNK [args.start .. args.end)
# ==============================================================================
for f in range(args.start, min(args.end, TOTAL_FRAMES)):
    t = f / FPS
    is_mol = (f >= BEATS[1]["f0"] + 86) and (f < BEATS[3]["f0"])
    shattered = (f >= SHATTER_F) and (f < BEATS[4]["f0"] + 48)
    pour_active = (f >= BEATS[1]["f0"]) and (f < BEATS[1]["f0"] + 86)

    # Toggle Sets
    kitchen_col.hide_render = is_mol
    mol_col.hide_render = not is_mol
    shards_col.hide_render = (not shattered) or is_mol

    if is_mol:
        bg_node.inputs[0].default_value = (0.015, 0.022, 0.045, 1.0)
        bg_node.inputs[1].default_value = 0.25
        m_u = max(0.0, min(1.0, (f - (BEATS[1]["f0"] + 86)) / max(1, BEATS[3]["f0"] - (BEATS[1]["f0"] + 86))))
        for obj, x, y, z, ph in cold_atoms:
            obj.location = (x - m_u * 0.014 + math.sin(t * 28 + ph) * 0.001, y, z * (1 - m_u * 0.08))
        for obj, x, y, z, ph in hot_atoms:
            obj.location = (x + m_u * 0.016 + math.sin(t * 48 + ph) * 0.003, y, z * (1 + m_u * 0.12))
        shear_bolt.hide_render = f < VAC["f0"]
    else:
        bg_node.inputs[0].default_value = (0.78, 0.74, 0.68, 1.0)
        bg_node.inputs[1].default_value = 0.65
        glass_obj.hide_render = shattered
        water_obj.hide_render = shattered
        pour_curve.hide_render = not pour_active
        kettle_obj.hide_render = not (pour_active or f < BEATS[1]["f0"])
        pe = math.sin(min(1.0, max(0.0, (f - BEATS[1]["f0"]) / 16.0)) * math.pi * 0.5) if pour_active else 0.0
        kettle_obj.location = (0.135 - pe * 0.02, 0.0, 0.165 + pe * 0.018)
        kettle_obj.rotation_euler = (0.0, -pe * 0.65, 0.0)

        for bo, ang, rad, spd, ph in bubbles:
            bo.hide_render = shattered
            yf = (ph + t * spd) % 1.0
            bo.location = (math.cos(ang) * rad, math.sin(ang) * rad, 0.016 + yf * 0.065)

        if shattered:
            raw_dt = (f - SHATTER_F) / FPS
            sim_t = raw_dt * 0.24 if raw_dt < 1.25 else 1.25 * 0.24 + (raw_dt - 1.25) * 0.85
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

    # Camera Choreography (8 dynamic cuts!)
    if f < 48:
        u = f / 48.0
        aim_camera((-0.02 + u * 0.02, -0.28 + u * 0.04, 0.095 - u * 0.012), (0, 0, 0.056), 54.0)
    elif f < BEATS[1]["f0"]:
        u = (f - 48) / max(1, BEATS[1]["f0"] - 48)
        a = -0.3 + u * 0.6
        aim_camera((math.sin(a) * 0.24, -math.cos(a) * 0.24, 0.075 + u * 0.016), (0, 0, 0.056), 52.0)
    elif f < BEATS[1]["f0"] + 86:
        u = (f - BEATS[1]["f0"]) / 86.0
        aim_camera((0.08 - u * 0.04, -0.25 + u * 0.02, 0.135 - u * 0.018), (0.015, 0, 0.074), 48.0)
    elif f < VAC["f0"]:
        u = (f - (BEATS[1]["f0"] + 86)) / max(1, VAC["f0"] - (BEATS[1]["f0"] + 86))
        aim_camera((-0.03 + u * 0.03, -0.21 + u * 0.02, 0.012), (0, 0, 0), 50.0)
    elif f < BEATS[2]["f0"]:
        u = (f - VAC["f0"]) / max(1, BEATS[2]["f0"] - VAC["f0"])
        aim_camera((0, -0.19 + u * 0.04, 0.006), (0, 0, 0), 44.0 + u * 14.0)
    elif f < BEATS[3]["f0"]:
        u = (f - BEATS[2]["f0"]) / max(1, BEATS[3]["f0"] - BEATS[2]["f0"])
        a = -0.3 + u * 0.75
        aim_camera((math.sin(a) * 0.20, -math.cos(a) * 0.20, 0.016), (0.006, 0, 0), 50.0)
    elif f < SHATTER_F:
        u = (f - BEATS[3]["f0"]) / max(1, SHATTER_F - BEATS[3]["f0"])
        aim_camera((-0.025 + u * 0.025, -0.23 + u * 0.025, 0.068), (0, 0, 0.056), 54.0)
    elif f < BEATS[4]["f0"]:
        u = (f - SHATTER_F) / max(1, BEATS[4]["f0"] - SHATTER_F)
        a = u * 1.4
        aim_camera((math.sin(a) * 0.29, -math.cos(a) * 0.29, 0.095), (0, 0, 0.054), 46.0)
    else:
        u = (f - BEATS[4]["f0"]) / max(1, TOTAL_FRAMES - BEATS[4]["f0"])
        e = u * u * (3 - 2 * u)
        aim_camera((0.04 * (1 - e) - 0.02 * e, -0.29 * (1 - e) - 0.28 * e, 0.10 * (1 - e) + 0.095 * e), (0, 0, 0.056), 54.0)

    scene.render.filepath = os.path.join(args.out, f"frame_{f:04d}.png")
    bpy.ops.render.render(write_still=True)

print(f"[Cycles] Finished chunk [{args.start}..{args.end}) -> {args.out}")
