#!/usr/bin/env python3
"""Blender 4.2 LTS Cycles renderer for the 15s PEHRA dark-cinema preview.

Every frame is a real, animated, path-traced 3D render. There are no still
plates, no flat backgrounds, and no 2D image cutouts: all scenery, props,
characters, fog, light shafts, dust, and practical flames exist as geometry,
volumes, or lights inside the scene. Editorial captions are added later as
motion-graphic text overlays by assemble_preview.py.

Usage (from Blender):
  blender -b --factory-startup --python render_scene.py -- \
    --shot S1_MIDNIGHT_FURROW --mode final --samples 12 --res-pct 100 \
    --out production/account1_ep01/frames
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import sys
import time
import traceback
from pathlib import Path

import bpy
from mathutils import Vector

BASE = Path(__file__).resolve().parent
ASSETS = BASE / "assets"
MANIFEST: dict = {}
VOLUME_NODE = None
SCENE = None

FPS = 30
WIDTH = 1080
HEIGHT = 1920
DURATION = 15.0
TOTAL_FRAMES = 450

C_MIDNIGHT = (0.006, 0.012, 0.026, 1.0)
C_TEAL = (0.10, 0.42, 0.52)
C_BLUE = (0.14, 0.28, 0.62)
C_AMBER = (1.0, 0.46, 0.12)
C_GOLD = (1.0, 0.72, 0.26)
C_CRIMSON = (0.75, 0.0, 0.025)


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
def warn(msg: str) -> None:
    print(f"[PEHRA][WARN] {msg}", flush=True)


def info(msg: str) -> None:
    print(f"[PEHRA] {msg}", flush=True)


def safe_set(obj, prop: str, value) -> None:
    try:
        setattr(obj, prop, value)
    except Exception:
        pass


def safe_input(node, name: str, value) -> None:
    try:
        if name in node.inputs:
            node.inputs[name].default_value = value
    except Exception:
        pass


def lerp(a, b, t: float):
    if isinstance(a, (tuple, list, Vector)):
        return type(a)(*(a[i] + (b[i] - a[i]) * t for i in range(len(a))))
    return a + (b - a) * t


def smoothstep(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def point_at(obj, target, axis: str = "-Z") -> None:
    direction = Vector(target) - obj.location
    if direction.length < 1e-8:
        return
    obj.rotation_euler = direction.to_track_quat(axis, "Y").to_euler()


def new_empty(name: str, location=(0, 0, 0), parent=None):
    obj = bpy.data.objects.new(name, None)
    SCENE.collection.objects.link(obj)
    obj.empty_display_type = "PLAIN_AXES"
    obj.empty_display_size = 0.18
    obj.location = location
    if parent is not None:
        obj.parent = parent
    return obj


def set_loc(obj, frame: int, loc) -> None:
    obj.location = loc
    obj.keyframe_insert(data_path="location", frame=frame)


def set_rot(obj, frame: int, rot) -> None:
    obj.rotation_euler = rot
    obj.keyframe_insert(data_path="rotation_euler", frame=frame)


def set_scale(obj, frame: int, scl) -> None:
    obj.scale = scl
    obj.keyframe_insert(data_path="scale", frame=frame)


def set_light_energy(light, frame: int, energy: float) -> None:
    light.data.energy = energy
    try:
        light.data.keyframe_insert(data_path="energy", frame=frame)
    except Exception:
        pass


def emission_node(mat):
    for node in mat.node_tree.nodes:
        if node.type == "EMISSION":
            return node
    return None


def set_emission(mat, frame: int, strength: float) -> None:
    node = emission_node(mat)
    if node is None:
        return
    node.inputs["Strength"].default_value = strength
    try:
        node.inputs["Strength"].keyframe_insert(data_path="default_value", frame=frame)
    except Exception:
        pass


def set_volume_density(frame: int, density: float) -> None:
    global VOLUME_NODE
    if VOLUME_NODE is None:
        return
    VOLUME_NODE.inputs["Density"].default_value = density
    try:
        VOLUME_NODE.inputs["Density"].keyframe_insert(data_path="default_value", frame=frame)
    except Exception:
        pass


def rebalance_scene(light_scale=0.55, volume_scale=0.18) -> None:
    """Tame CI exposure: scale all practical lights and volumetric fog after scene build."""
    for light in bpy.data.lights:
        try:
            light.energy *= light_scale
        except Exception:
            pass
        action = None
        try:
            action = light.animation_data.action
        except Exception:
            action = None
        if action:
            for fc in action.fcurves:
                for kp in fc.keyframe_points:
                    try:
                        kp.co[1] *= light_scale
                        kp.handle_left[1] *= light_scale
                        kp.handle_right[1] *= light_scale
                    except Exception:
                        pass
    global VOLUME_NODE
    if VOLUME_NODE is not None:
        try:
            VOLUME_NODE.inputs["Density"].default_value *= volume_scale
        except Exception:
            pass
        try:
            action = VOLUME_NODE.id_data.animation_data.action
        except Exception:
            action = None
        if action:
            for fc in action.fcurves:
                if "Density" not in fc.data_path:
                    continue
                for kp in fc.keyframe_points:
                    try:
                        kp.co[1] *= volume_scale
                        kp.handle_left[1] *= volume_scale
                        kp.handle_right[1] *= volume_scale
                    except Exception:
                        pass


def smooth_all_fcurves() -> None:
    for action in bpy.data.actions:
        try:
            fcurves = action.fcurves
        except Exception:
            continue
        for fc in fcurves:
            for kp in fc.keyframe_points:
                try:
                    kp.interpolation = "BEZIER"
                    kp.handle_left_type = "AUTO_CLAMPED"
                    kp.handle_right_type = "AUTO_CLAMPED"
                except Exception:
                    pass


# ---------------------------------------------------------------------------
# Asset lookup / import
# ---------------------------------------------------------------------------
def load_manifest() -> None:
    global MANIFEST
    path = ASSETS / "manifest.json"
    if path.exists():
        try:
            MANIFEST = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            warn(f"Could not read asset manifest: {exc}")
    else:
        warn("Asset manifest missing; using filesystem fallbacks")


def find_blend(asset_id: str) -> Path | None:
    try:
        rel = MANIFEST["models"][asset_id]["blend"]
        p = ASSETS / rel
        if p.exists():
            return p
    except Exception:
        pass
    candidates = sorted((ASSETS / "ph_models" / asset_id).glob("*.blend"))
    return candidates[0] if candidates else None


def find_glb(name: str) -> Path | None:
    p = ASSETS / "glb" / name
    if p.exists():
        return p
    found = sorted(ASSETS.rglob(name))
    return found[0] if found else None


def find_tex(asset_id: str, slot: str) -> Path | None:
    try:
        rel = MANIFEST["textures"][asset_id]["maps"][slot]
        p = ASSETS / rel
        if p.exists():
            return p
    except Exception:
        pass
    candidates = sorted((ASSETS / "ph_textures" / asset_id).glob(f"*_{slot}.*"))
    return candidates[0] if candidates else None


def repath_images(blend_dir: Path) -> None:
    """Poly Haven .blend files use //textures relative paths; make them absolute."""
    for img in bpy.data.images:
        if img.source != "FILE" or img.packed_file:
            continue
        raw = (img.filepath or "").replace("\\", "/")
        if not raw:
            continue
        rel = raw[2:] if raw.startswith("//") else raw
        candidates = [
            blend_dir / rel,
            blend_dir / "textures" / Path(rel).name,
            ASSETS / rel,
        ]
        for cand in candidates:
            try:
                if cand.exists():
                    img.filepath = str(cand.resolve())
                    break
            except Exception:
                pass


def append_blend(asset_id: str, name: str | None = None):
    path = find_blend(asset_id)
    if path is None:
        raise FileNotFoundError(f"Missing Poly Haven .blend for {asset_id}")
    before = set(bpy.data.objects)
    try:
        group = new_empty(name or f"ASSET_{asset_id}")
        with bpy.data.libraries.load(str(path), link=False) as (data_from, data_to):
            data_to.objects = list(data_from.objects)
        skip_tokens = ("backdrop", "shadow", "floor", "ground", "stage", "preview_plane")
        appended = []
        for obj in data_to.objects:
            if obj is None or obj.type in {"LIGHT", "CAMERA"}:
                continue
            lower = obj.name.lower()
            if any(token in lower for token in skip_tokens) or lower.startswith("plane"):
                continue
            if obj.type == "MESH" and max(obj.dimensions) > 12.0:
                continue
            appended.append(obj)
        appended_set = set(appended)
        for obj in appended:
            try:
                if SCENE.collection not in obj.users_collection:
                    SCENE.collection.objects.link(obj)
            except Exception:
                try:
                    SCENE.collection.objects.link(obj)
                except Exception:
                    pass
            obj.hide_render = False
            obj.hide_viewport = False
            if obj.parent is None or obj.parent not in appended_set:
                obj.parent = group
        repath_images(path.parent)
        bpy.context.view_layer.update()
        return group
    except Exception:
        for obj in list(bpy.data.objects):
            if obj not in before:
                try:
                    bpy.data.objects.remove(obj, do_unlink=True)
                except Exception:
                    pass
        raise


def append_glb(filename: str, name: str | None = None):
    path = find_glb(filename)
    if path is None:
        raise FileNotFoundError(f"Missing GLB asset {filename}")
    before = set(bpy.data.objects)
    try:
        try:
            bpy.ops.import_scene.gltf(filepath=str(path))
        except AttributeError:
            bpy.ops.preferences.addon_enable(module="io_scene_gltf2")
            bpy.ops.import_scene.gltf(filepath=str(path))
        group = new_empty(name or f"ASSET_{Path(filename).stem}")
        imported = [
            obj for obj in bpy.data.objects
            if obj not in before and obj is not group
            and obj.type not in {"LIGHT", "CAMERA"}
            and "icosphere" not in obj.name.lower()
        ]
        imported_set = set(imported)
        for obj in imported:
            try:
                if SCENE.collection not in obj.users_collection:
                    SCENE.collection.objects.link(obj)
            except Exception:
                pass
            obj.hide_render = False
            obj.hide_viewport = False
            if obj.parent is None or obj.parent not in imported_set:
                obj.parent = group
        bpy.context.view_layer.update()
        return group
    except Exception:
        for obj in list(bpy.data.objects):
            if obj not in before:
                try:
                    bpy.data.objects.remove(obj, do_unlink=True)
                except Exception:
                    pass
        raise


def try_append_blend(asset_id: str, name: str):
    try:
        return append_blend(asset_id, name)
    except Exception as exc:
        warn(f"{asset_id} .blend unavailable ({exc}); procedural fallback engaged")
        return None


def try_append_glb(filename: str, name: str):
    try:
        return append_glb(filename, name)
    except Exception as exc:
        warn(f"{filename} GLB unavailable ({exc}); procedural fallback engaged")
        return None


def bbox_group(group):
    bpy.context.view_layer.update()
    lo = Vector((math.inf, math.inf, math.inf))
    hi = Vector((-math.inf, -math.inf, -math.inf))
    found = False
    for obj in group.children_recursive:
        if obj.type != "MESH" or not obj.data.vertices:
            continue
        found = True
        for vert in obj.data.vertices:
            p = obj.matrix_world @ vert.co
            for i in range(3):
                lo[i] = min(lo[i], p[i])
                hi[i] = max(hi[i], p[i])
    if not found:
        return Vector((-0.5, -0.5, 0.0)), Vector((0.5, 0.5, 1.0))
    return lo, hi


def fit_group(
    group,
    target_size: float,
    *,
    use: str = "max",
    center_xy=(0.0, 0.0),
    bottom_z: float = 0.0,
    rotation=(0.0, 0.0, 0.0),
):
    """Uniformly fit an imported hierarchy to a target size and place it."""
    if group is None:
        return None
    group.rotation_euler = rotation
    bpy.context.view_layer.update()
    lo, hi = bbox_group(group)
    dx, dy, dz = (hi - lo).x, (hi - lo).y, (hi - lo).z
    if use == "z":
        extent = dz
    elif use == "xy":
        extent = max(dx, dy)
    else:
        extent = max(dx, dy, dz)
    scale = target_size / max(extent, 1e-5)
    group.scale = (scale, scale, scale)
    bpy.context.view_layer.update()
    lo2, hi2 = bbox_group(group)
    cx, cy = (lo2.x + hi2.x) * 0.5, (lo2.y + hi2.y) * 0.5
    group.location = Vector(group.location) + Vector(
        (center_xy[0] - cx, center_xy[1] - cy, bottom_z - lo2.z)
    )
    bpy.context.view_layer.update()
    return group


def duplicate_hierarchy(src_root, name: str):
    """Cheap deep copy for repeated hero props (shared mesh/material datablocks)."""
    dst_root = new_empty(name)
    dst_root.location = src_root.location.copy()
    dst_root.rotation_euler = src_root.rotation_euler.copy()
    dst_root.scale = src_root.scale.copy()
    mapping = {src_root: dst_root}
    for obj in src_root.children_recursive:
        dup = obj.copy()
        if obj.data:
            dup.data = obj.data
        SCENE.collection.objects.link(dup)
        try:
            dup.animation_data_clear()
        except Exception:
            pass
        dup.parent = mapping.get(obj.parent, dst_root)
        dup.matrix_parent_inverse = obj.matrix_parent_inverse.copy()
        dup.location = obj.location.copy()
        dup.rotation_euler = obj.rotation_euler.copy()
        dup.scale = obj.scale.copy()
        dup.hide_render = obj.hide_render
        mapping[obj] = dup
    bpy.context.view_layer.update()
    return dst_root


def override_material_recursive(group, mat) -> None:
    if group is None or mat is None:
        return
    for obj in group.children_recursive:
        if obj.type != "MESH":
            continue
        try:
            obj.data.materials.clear()
            obj.data.materials.append(mat)
        except Exception:
            pass
        # glTF skinned meshes can use OBJECT-linked material slots; force DATA links.
        for slot in obj.material_slots:
            try:
                slot.link = "DATA"
                slot.material = mat
            except Exception:
                pass
        try:
            obj.active_material = mat
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Materials and primitive builders
# ---------------------------------------------------------------------------
def make_principled_mat(name, base, metallic=0.0, roughness=0.5, coat=0.0, transmission=0.0, noise=0.0, bump=0.22, bump_dist=0.08):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (420, 0)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (120, 0)
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    safe_input(bsdf, "Base Color", (*base[:3], 1.0) if len(base) == 3 else base)
    safe_input(bsdf, "Metallic", metallic)
    safe_input(bsdf, "Roughness", roughness)
    safe_input(bsdf, "Coat Weight", coat)
    safe_input(bsdf, "Coat Roughness", 0.16)
    safe_input(bsdf, "Transmission Weight", transmission)
    safe_input(bsdf, "IOR", 1.45)
    if noise > 0:
        tex = nt.nodes.new("ShaderNodeTexNoise")
        tex.location = (-420, -180)
        tex.inputs["Scale"].default_value = noise
        tex.inputs["Detail"].default_value = 4.0
        tex.inputs["Roughness"].default_value = 0.65
        bump_node = nt.nodes.new("ShaderNodeBump")
        bump_node.location = (-110, -160)
        bump_node.inputs["Strength"].default_value = bump
        bump_node.inputs["Distance"].default_value = bump_dist
        nt.links.new(tex.outputs["Fac"], bump_node.inputs["Height"])
        nt.links.new(bump_node.outputs["Normal"], bsdf.inputs["Normal"])
    mat.diffuse_color = (*base[:3], 1.0)
    return mat


def make_emission_mat(name, color, strength=5.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    emit = nt.nodes.new("ShaderNodeEmission")
    emit.name = "Emitter"
    emit.inputs["Color"].default_value = (*color[:3], 1.0)
    emit.inputs["Strength"].default_value = strength
    nt.links.new(emit.outputs["Emission"], out.inputs["Surface"])
    mat.diffuse_color = (*color[:3], 1.0)
    return mat


def make_transparent_emission_mat(name, color, strength=1.0, alpha=0.05):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    trans = nt.nodes.new("ShaderNodeBsdfTransparent")
    emit = nt.nodes.new("ShaderNodeEmission")
    emit.name = "Emitter"
    emit.inputs["Color"].default_value = (*color[:3], 1.0)
    emit.inputs["Strength"].default_value = strength
    mix = nt.nodes.new("ShaderNodeMixShader")
    mix.inputs[0].default_value = alpha
    nt.links.new(trans.outputs["BSDF"], mix.inputs[1])
    nt.links.new(emit.outputs["Emission"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    safe_set(mat, "surface_render_method", "DITHERED")
    mat.diffuse_color = (*color[:3], alpha)
    return mat


def make_pbr_material(name, asset_id: str, *, repeat=4.0, wet=1.0, darken=1.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (760, 0)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (480, 0)
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    safe_input(bsdf, "Metallic", 0.0)
    safe_input(bsdf, "Roughness", 0.72)
    safe_input(bsdf, "Coat Weight", 0.22 if wet < 0.8 else 0.05)
    safe_input(bsdf, "Coat Roughness", 0.18)

    coord = nt.nodes.new("ShaderNodeTexCoord")
    coord.location = (-1000, 0)
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.location = (-780, 0)
    mapping.inputs["Scale"].default_value = (repeat, repeat, repeat)
    nt.links.new(coord.outputs["UV"], mapping.inputs["Vector"])

    def image_node(rel_x, rel_y, path, non_color=True):
        node = nt.nodes.new("ShaderNodeTexImage")
        node.location = (rel_x, rel_y)
        node.image = bpy.data.images.load(str(path), check_existing=True)
        node.extension = "REPEAT"
        node.interpolation = "Linear"
        if non_color:
            try:
                node.image.colorspace_settings.name = "Non-Color"
            except Exception:
                pass
        nt.links.new(mapping.outputs["Vector"], node.inputs["Vector"])
        return node

    diff_path = find_tex(asset_id, "diff")
    if diff_path:
        diff = image_node(-540, 260, diff_path, non_color=False)
        if darken < 0.999:
            tint = nt.nodes.new("ShaderNodeMixRGB")
            tint.blend_type = "MULTIPLY"
            tint.inputs[0].default_value = 1.0
            tint.inputs[2].default_value = (darken, darken * 0.96, darken * 1.05, 1.0)
            nt.links.new(diff.outputs["Color"], tint.inputs[1])
            nt.links.new(tint.outputs["Color"], bsdf.inputs["Base Color"])
        else:
            nt.links.new(diff.outputs["Color"], bsdf.inputs["Base Color"])
    else:
        safe_input(bsdf, "Base Color", (0.055, 0.045, 0.038, 1.0))

    rough_path = find_tex(asset_id, "rough")
    if rough_path:
        rough = image_node(-540, -20, rough_path)
        mult = nt.nodes.new("ShaderNodeMath")
        mult.operation = "MULTIPLY"
        mult.location = (160, -60)
        mult.inputs[1].default_value = wet
        nt.links.new(rough.outputs["Color"], mult.inputs[0])
        nt.links.new(mult.outputs["Value"], bsdf.inputs["Roughness"])
    else:
        safe_input(bsdf, "Roughness", 0.68 * wet)

    nor_path = find_tex(asset_id, "nor_gl")
    disp_path = find_tex(asset_id, "disp")
    bump = nt.nodes.new("ShaderNodeBump")
    bump.location = (220, -240)
    bump.inputs["Strength"].default_value = 0.34
    bump.inputs["Distance"].default_value = 0.12
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    if nor_path:
        nor = image_node(-540, -300, nor_path)
        normal_map = nt.nodes.new("ShaderNodeNormalMap")
        normal_map.location = (-40, -250)
        normal_map.inputs["Strength"].default_value = 0.85
        nt.links.new(nor.outputs["Color"], normal_map.inputs["Color"])
        nt.links.new(normal_map.outputs["Normal"], bump.inputs["Normal"])
    if disp_path:
        disp = image_node(-540, -560, disp_path)
        nt.links.new(disp.outputs["Color"], bump.inputs["Height"])
    else:
        noise = nt.nodes.new("ShaderNodeTexNoise")
        noise.location = (-320, -560)
        noise.inputs["Scale"].default_value = 22.0
        nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    return mat


def make_box(name, dims, location, mat, *, parent=None, rotation=(0, 0, 0), bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=2.0, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = (dims[0] / 2.0, dims[1] / 2.0, dims[2] / 2.0)
    obj.rotation_euler = rotation
    if parent is not None:
        obj.parent = parent
    if mat:
        obj.data.materials.append(mat)
    if bevel > 0:
        mod = obj.modifiers.new("Cinematic Bevel", "BEVEL")
        mod.width = bevel
        mod.segments = 3
        safe_set(mod, "limit_method", "ANGLE")
    return obj


def make_cylinder(name, radius, depth, location, mat, *, parent=None, rotation=(0, 0, 0), vertices=24, bevel=0.0):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_euler = rotation
    if parent is not None:
        obj.parent = parent
    if mat:
        obj.data.materials.append(mat)
    if bevel > 0:
        mod = obj.modifiers.new("Cinematic Bevel", "BEVEL")
        mod.width = bevel
        mod.segments = 3
    return obj


def make_cone(name, radius1, radius2, depth, location, mat, *, parent=None, rotation=(0, 0, 0), vertices=24):
    bpy.ops.mesh.primitive_cone_add(
        vertices=vertices, radius1=radius1, radius2=radius2, depth=depth, location=location
    )
    obj = bpy.context.object
    obj.name = name
    obj.rotation_euler = rotation
    if parent is not None:
        obj.parent = parent
    if mat:
        obj.data.materials.append(mat)
    return obj


def make_sphere(name, radii, location, mat, *, parent=None, segments=20, rings=12, smooth=True):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, radius=1.0, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = radii
    if parent is not None:
        obj.parent = parent
    if mat:
        obj.data.materials.append(mat)
    if smooth:
        for poly in obj.data.polygons:
            poly.use_smooth = True
    return obj


def make_torus(name, major_radius, minor_radius, location, mat, *, parent=None, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_torus_add(
        major_segments=20,
        minor_segments=8,
        major_radius=major_radius,
        minor_radius=minor_radius,
        location=location,
    )
    obj = bpy.context.object
    obj.name = name
    obj.rotation_euler = rotation
    if parent is not None:
        obj.parent = parent
    if mat:
        obj.data.materials.append(mat)
    for poly in obj.data.polygons:
        poly.use_smooth = True
    return obj


def make_pbr_ground(name, asset_id, *, size=24.0, repeat=4.0, disp_strength=0.35, wet=1.0, darken=1.0):
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=110, y_subdivisions=110, size=size)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(
        make_pbr_material(f"MAT_{name}", asset_id, repeat=repeat, wet=wet, darken=darken)
    )
    disp = find_tex(asset_id, "disp")
    if disp:
        tex = bpy.data.textures.new(f"TEX_{name}_DISP", type="IMAGE")
        tex.image = bpy.data.images.load(str(disp), check_existing=True)
        try:
            tex.image.colorspace_settings.name = "Non-Color"
        except Exception:
            pass
        mod = obj.modifiers.new("Real Mud Displacement", "DISPLACE")
        mod.texture = tex
        mod.texture_coords = "UV"
        mod.strength = disp_strength
        mod.mid_level = 0.5
    return obj


def make_dark_backdrop(name, mats, *, y=7.0, z=3.0, width=20.0, height=9.0):
    """A real 3D midnight wall; prevents over-bright volume fog from washing out the frame."""
    bpy.ops.mesh.primitive_plane_add(size=2.0, location=(0, y, z))
    obj = bpy.context.object
    obj.name = name
    obj.rotation_euler = (math.pi / 2.0, 0, 0)
    obj.scale = (width / 2.0, height / 2.0, 1.0)
    obj.data.materials.append(mats["backdrop"])
    return obj


def make_camera(name="PEHRA_CAMERA"):
    cam_data = bpy.data.cameras.new(name)
    cam = bpy.data.objects.new(name, cam_data)
    SCENE.collection.objects.link(cam)
    SCENE.camera = cam
    cam.data.sensor_fit = "VERTICAL"
    cam.data.sensor_height = 24.0
    cam.data.lens = 45.0
    cam.data.clip_start = 0.01
    cam.data.clip_end = 180.0
    try:
        cam.data.dof.use_dof = True
        cam.data.dof.aperture_fstop = 1.9
        cam.data.dof.aperture_blades = 7
    except Exception:
        pass
    return cam


def key_camera(cam, frame, loc, target, lens=45.0, focus=3.0):
    cam.location = loc
    point_at(cam, target, "-Z")
    cam.data.lens = lens
    cam.keyframe_insert(data_path="location", frame=frame)
    cam.keyframe_insert(data_path="rotation_euler", frame=frame)
    cam.data.keyframe_insert(data_path="lens", frame=frame)
    try:
        cam.data.dof.focus_distance = focus
        cam.data.dof.keyframe_insert(data_path="focus_distance", frame=frame)
    except Exception:
        pass


def add_area(name, loc, target, energy, color, size=3.0, size_y=None):
    data = bpy.data.lights.new(name, "AREA")
    data.energy = energy
    data.color = color
    data.shape = "RECTANGLE"
    data.size = size
    data.size_y = size_y or size
    obj = bpy.data.objects.new(name, data)
    SCENE.collection.objects.link(obj)
    obj.location = loc
    point_at(obj, target, "-Z")
    return obj


def add_point(name, loc, energy, color, radius=0.12):
    data = bpy.data.lights.new(name, "POINT")
    data.energy = energy
    data.color = color
    data.shadow_soft_size = radius
    obj = bpy.data.objects.new(name, data)
    SCENE.collection.objects.link(obj)
    obj.location = loc
    return obj


def add_spot(name, loc, target, energy, color, cone=0.55):
    data = bpy.data.lights.new(name, "SPOT")
    data.energy = energy
    data.color = color
    data.spot_size = cone
    data.spot_blend = 0.35
    obj = bpy.data.objects.new(name, data)
    SCENE.collection.objects.link(obj)
    obj.location = loc
    point_at(obj, target, "-Z")
    return obj


def animate_flicker(light, start, end, base, amp, seed=1, step=4):
    rng = random.Random(seed)
    for f in range(start, end + 1, step):
        wave = math.sin((f - start) * 0.37 + seed) * 0.35 + math.sin((f - start) * 0.11) * 0.25
        energy = max(0.5, base + amp * (wave + (rng.random() - 0.5) * 0.55))
        set_light_energy(light, f, energy)
    set_light_energy(light, end, base)


def animate_emission(mat, start, end, base, amp, seed=1, step=4):
    rng = random.Random(seed)
    for f in range(start, end + 1, step):
        wave = math.sin((f - start) * 0.31 + seed) * 0.4
        set_emission(mat, f, max(0.0, base + amp * (wave + (rng.random() - 0.5) * 0.4)))
    set_emission(mat, end, base)


def animate_swing(obj, start, end, amp=0.06, period=38.0, axis=0, step=4):
    base = list(obj.rotation_euler)
    for f in range(start, end + 1, step):
        rot = list(base)
        rot[axis] += amp * math.sin(2 * math.pi * (f - start) / period)
        set_rot(obj, f, rot)
    set_rot(obj, end, tuple(base))


# ---------------------------------------------------------------------------
# Procedural 3D set pieces (also used as fail-safe art direction)
# ---------------------------------------------------------------------------
def build_material_library():
    return {
        "iron": make_principled_mat("MAT_WROUGHT_IRON", (0.018, 0.022, 0.028), 0.92, 0.28, noise=38),
        "brass": make_principled_mat("MAT_AGED_BRASS", (0.52, 0.29, 0.075), 0.95, 0.23, coat=0.2, noise=26),
        "gold": make_principled_mat("MAT_ROYAL_GOLD", (0.95, 0.57, 0.14), 0.86, 0.19, coat=0.35),
        "black": make_principled_mat("MAT_BLACK_COAT", (0.008, 0.010, 0.014), 0.08, 0.78),
        "obsidian": make_principled_mat("MAT_OBSIDIAN", (0.006, 0.008, 0.012), 0.35, 0.16, coat=0.8, noise=12),
        "monarch_skin": make_principled_mat("MAT_MONARCH_WARM_SKIN", (0.115, 0.074, 0.050), 0.0, 0.58, coat=0.10, noise=140, bump=0.05, bump_dist=0.0015),
        "monarch_marble": make_principled_mat("MAT_MONARCH_DARK_MARBLE", (0.028, 0.024, 0.023), 0.0, 0.30, coat=0.45, noise=22, bump=0.10, bump_dist=0.004),
        "guard_coat": make_principled_mat("MAT_ROYAL_GUARD_CHARCOAL", (0.030, 0.036, 0.048), 0.12, 0.52, coat=0.35, noise=10),
        "backdrop": make_principled_mat("MAT_NIGHT_BACKDROP", (0.004, 0.008, 0.018), 0.0, 0.94, noise=6),
        "earth": make_principled_mat("MAT_WET_EARTH", (0.055, 0.037, 0.026), 0.0, 0.86, noise=34),
        "potato": make_principled_mat("MAT_EARTHY_TUBER", (0.30, 0.16, 0.065), 0.0, 0.82, noise=28),
        "wicker": make_principled_mat("MAT_WICKER", (0.31, 0.16, 0.065), 0.0, 0.72, noise=30),
        "crimson": make_emission_mat("MAT_CRIMSON_EYE_BAND", C_CRIMSON, 2.0),
        "amber": make_emission_mat("MAT_PRACTICAL_FLAME", C_AMBER, 14.0),
        "gold_emit": make_emission_mat("MAT_GOLD_DUST", C_GOLD, 1.4),
        "godray": make_transparent_emission_mat("MAT_GODRAY_SHAFT", C_GOLD, 1.6, 0.045),
        "glass": make_principled_mat("MAT_SMOKE_GLASS", (0.15, 0.19, 0.23), 0.0, 0.06, coat=0.9, transmission=0.82),
    }


def make_procedural_potato(name, loc, mats, scale=0.20, rotation=(0, 0, 0)):
    root = new_empty(name, loc)
    make_sphere(name + "_body", (scale, scale * 0.62, scale * 0.55), (0, 0, 0), mats["potato"], parent=root)
    root.rotation_euler = rotation
    return root


def make_procedural_plant(name, loc, mats, height=0.55):
    root = new_empty(name, loc)
    stem = make_principled_mat("MAT_STEM_" + name, (0.035, 0.075, 0.035), 0.0, 0.8, noise=12)
    leaf = make_principled_mat("MAT_LEAF_" + name, (0.025, 0.10, 0.052), 0.0, 0.55, transmission=0.22)
    make_cylinder(name + "_stem", 0.012, height * 0.72, (0, 0, height * 0.36), stem, parent=root, vertices=10)
    for i in range(7):
        ang = i * 2.399
        z = height * (0.34 + 0.075 * i)
        r = 0.07 + 0.035 * (i % 3)
        leaf_obj = make_sphere(
            name + f"_leaf_{i}", (0.085, 0.028, 0.012),
            (math.cos(ang) * r, math.sin(ang) * r, z), leaf,
            parent=root, segments=12, rings=8,
        )
        leaf_obj.rotation_euler = (math.radians(12), math.radians(10), ang)
    return root


def make_procedural_lantern(name, loc, mats, height=0.65):
    root = new_empty(name, loc)
    make_cylinder(name + "_base", 0.14, 0.035, (0, 0, 0.03), mats["iron"], parent=root, vertices=12)
    make_cylinder(name + "_cap", 0.12, 0.035, (0, 0, height), mats["iron"], parent=root, vertices=12)
    for i in range(6):
        ang = i * math.pi / 3
        make_cylinder(
            name + f"_bar_{i}", 0.008, height * 0.9,
            (math.cos(ang) * 0.115, math.sin(ang) * 0.115, height * 0.5),
            mats["iron"], parent=root, vertices=8,
        )
    core = make_sphere(name + "_flame_core", (0.065, 0.065, 0.13), (0, 0, height * 0.5), mats["amber"], parent=root)
    return root, core


def make_procedural_streetlamp(name, loc, mats, height=3.4):
    root = new_empty(name, loc)
    make_cylinder(name + "_post", 0.055, height, (0, 0, height / 2), mats["iron"], parent=root, vertices=16)
    make_cylinder(name + "_base", 0.16, 0.12, (0, 0, 0.06), mats["iron"], parent=root, vertices=16)
    make_sphere(name + "_glass", (0.16, 0.16, 0.24), (0, 0, height + 0.1), mats["glass"], parent=root)
    flame = make_sphere(name + "_flame", (0.065, 0.065, 0.13), (0, 0, height + 0.1), mats["amber"], parent=root)
    return root, flame


def make_procedural_rifle(name, loc, mats, length=1.15):
    root = new_empty(name, loc)
    make_box(name + "_stock", (0.34, 0.075, 0.11), (-length * 0.30, 0, 0), mats["black"], parent=root, bevel=0.02)
    make_cylinder(name + "_barrel", 0.018, length * 0.86, (length * 0.19, 0, 0.015), mats["iron"], parent=root, rotation=(0, math.pi / 2, 0), vertices=12)
    make_cone(name + "_bayonet", 0.018, 0.001, 0.34, (length * 0.72, 0, 0.015), mats["iron"], parent=root, rotation=(0, math.pi / 2, 0), vertices=10)
    return root


def make_tricorn(name, loc, mats, parent=None):
    root = new_empty(name, loc, parent=parent)
    make_cylinder(name + "_brim", 0.34, 0.035, (0, 0, 0), mats["black"], parent=root, vertices=3, bevel=0.01)
    make_cone(name + "_crown", 0.24, 0.10, 0.18, (0, 0, 0.10), mats["black"], parent=root, vertices=3)
    return root


def make_procedural_guard(name, loc, mats, height=1.82):
    root = new_empty(name, loc)
    coat = mats["guard_coat"]
    make_cylinder(name + "_torso", 0.20, 0.72, (0, 0, height * 0.56), coat, parent=root, vertices=16)
    make_sphere(name + "_head", (0.13, 0.12, 0.16), (0, 0, height * 0.89), coat, parent=root)
    for sx in (-1, 1):
        make_cylinder(name + f"_leg_{sx}", 0.075, 0.78, (sx * 0.10, 0, height * 0.22), coat, parent=root, vertices=12)
        make_cylinder(name + f"_arm_{sx}", 0.055, 0.62, (sx * 0.25, 0, height * 0.56), coat, parent=root, vertices=10, rotation=(0, 0, sx * 0.12))
    make_tricorn(name + "_tricorn", (0, 0, height * 1.01), mats, parent=root)
    for i in range(4):
        make_sphere(name + f"_button_{i}", (0.018, 0.018, 0.018), (0, -0.19, height * (0.66 - i * 0.075)), mats["brass"], parent=root, segments=10, rings=6)
    rifle = make_procedural_rifle(name + "_rifle", (0.32, -0.10, height * 0.60), mats, length=1.12)
    rifle.parent = root
    rifle.rotation_euler = (math.radians(8), math.radians(72), math.radians(5))
    return root


def make_fence(name, mats, y=-1.1, width=5.4, height=2.0, count=15):
    root = new_empty(name, (0, y, 0))
    for i in range(count):
        x = -width / 2 + width * i / (count - 1)
        make_cylinder(f"{name}_bar_{i}", 0.022, height, (x, 0, height / 2), mats["iron"], parent=root, vertices=10)
        make_cone(f"{name}_spear_{i}", 0.032, 0.001, 0.18, (x, 0, height + 0.08), mats["iron"], parent=root, vertices=10)
    for z in (0.42, 1.35):
        make_box(f"{name}_rail_{int(z * 100)}", (width, 0.055, 0.075), (0, 0, z), mats["iron"], parent=root, bevel=0.012)
    return root


def make_chain(name, mats, length=1.75, links=24):
    root = new_empty(name, (0, -0.13, 1.10))
    for i in range(links):
        u = i / (links - 1) - 0.5
        x = u * length
        z = -0.16 * (u * 2.0) ** 2
        link = make_torus(
            f"{name}_link_{i}", 0.052, 0.013,
            (x, 0, z), mats["iron"], parent=root,
            rotation=(0 if i % 2 else math.pi / 2, 0, 0),
        )
        link.scale = (1.0, 1.0, 0.82)
    return root


def make_padlock(name, mats, loc=(0, -0.20, 0.92)):
    root = new_empty(name, loc)
    body = make_box(name + "_body", (0.28, 0.10, 0.32), (0, 0, 0), mats["brass"], parent=root, bevel=0.035)
    pivot = new_empty(name + "_shackle_pivot", (0.09, 0, 0.16), parent=root)
    shackle = make_torus(name + "_shackle", 0.11, 0.022, (0, 0, 0.04), mats["brass"], parent=pivot, rotation=(math.pi / 2, 0, 0))
    shackle.scale = (1.0, 0.85, 1.0)
    make_sphere(name + "_keyhole", (0.022, 0.012, 0.032), (0, -0.055, -0.02), mats["iron"], parent=root, segments=10, rings=6)
    return root, pivot, body


def make_gate(name, mats, *, y=0.0, width=2.8, height=2.2):
    root = new_empty(name, (0, y, 0))
    left = new_empty(name + "_LEFT_HINGE", (-width / 2, 0, 0), parent=root)
    right = new_empty(name + "_RIGHT_HINGE", (width / 2, 0, 0), parent=root)
    leaf_w = width / 2
    for direction, hinge, tag in ((1, left, "L"), (-1, right, "R")):
        for i in range(7):
            x = direction * (0.10 + i * (leaf_w - 0.18) / 6)
            make_cylinder(f"{name}_{tag}_bar_{i}", 0.024, height, (x, 0, height / 2), mats["iron"], parent=hinge, vertices=10)
            make_cone(f"{name}_{tag}_spear_{i}", 0.038, 0.001, 0.20, (x, 0, height + 0.09), mats["iron"], parent=hinge, vertices=10)
        for z in (0.38, 1.08, 1.78):
            make_box(f"{name}_{tag}_rail_{int(z * 100)}", (leaf_w, 0.06, 0.085), (direction * leaf_w / 2, 0, z), mats["iron"], parent=hinge, bevel=0.012)
    chain = make_chain(name + "_HEAVY_CHAIN", mats, length=1.75)
    chain.parent = root
    lock, lock_pivot, lock_body = make_padlock(name + "_BRASS_PADLOCK", mats)
    lock.parent = root
    return {
        "root": root,
        "left": left,
        "right": right,
        "chain": chain,
        "lock": lock,
        "lock_pivot": lock_pivot,
        "lock_body": lock_body,
    }


def make_procedural_board(name, mats, size=2.4):
    root = new_empty(name, (0, 0, 0.12))
    dark = make_principled_mat("MAT_MIRROR_BOARD_DARK", (0.008, 0.010, 0.014), 0.72, 0.09, coat=0.9)
    light = make_principled_mat("MAT_MIRROR_BOARD_LIGHT", (0.075, 0.062, 0.048), 0.62, 0.12, coat=0.7)
    sq = size / 8.0
    for row in range(8):
        for col in range(8):
            make_box(
                f"{name}_sq_{row}_{col}", (sq * 0.99, sq * 0.99, 0.035),
                (-size / 2 + sq * (col + 0.5), -size / 2 + sq * (row + 0.5), 0),
                dark if (row + col) % 2 == 0 else light,
                parent=root, bevel=0.006,
            )
    return root


def make_procedural_knight(name, loc, mats, height=0.35):
    root = new_empty(name, loc)
    make_cylinder(name + "_base", 0.105, 0.045, (0, 0, 0.022), mats["obsidian"], parent=root, vertices=24, bevel=0.012)
    make_cone(name + "_stem", 0.085, 0.055, height * 0.55, (0, 0, height * 0.34), mats["obsidian"], parent=root, vertices=20)
    head = make_box(name + "_horse_head", (0.16, 0.10, 0.20), (0.02, 0, height * 0.72), mats["obsidian"], parent=root, rotation=(math.radians(-18), 0, 0), bevel=0.025)
    make_cone(name + "_muzzle", 0.065, 0.025, 0.16, (0.02, -0.10, height * 0.72), mats["obsidian"], parent=root, rotation=(math.radians(80), 0, 0), vertices=12)
    for sx in (-1, 1):
        make_cone(name + f"_ear_{sx}", 0.022, 0.001, 0.075, (sx * 0.045, 0.02, height * 0.88), mats["obsidian"], parent=root, vertices=8)
    return root, head


def make_procedural_basket(name, loc, mats, radius=0.43):
    root = new_empty(name, loc)
    make_cylinder(name + "_body", radius, 0.34, (0, 0, 0.17), mats["wicker"], parent=root, vertices=24, bevel=0.02)
    make_torus(name + "_rim", radius, 0.035, (0, 0, 0.35), mats["wicker"], parent=root)
    for i in range(12):
        ang = i * math.pi / 6
        make_cylinder(name + f"_weave_{i}", 0.012, 0.34, (math.cos(ang) * radius, math.sin(ang) * radius, 0.17), mats["wicker"], parent=root, vertices=8)
    return root


def make_procedural_candle(name, loc, mats, height=0.34):
    root = new_empty(name, loc)
    wax = make_principled_mat("MAT_WAX_" + name, (0.82, 0.73, 0.55), 0.0, 0.55, transmission=0.12)
    make_cylinder(name + "_wax", 0.042, height * 0.72, (0, 0, height * 0.36), wax, parent=root, vertices=16)
    make_cylinder(name + "_holder", 0.10, 0.035, (0, 0, 0.018), mats["brass"], parent=root, vertices=16)
    flame = make_cone(name + "_flame", 0.035, 0.001, 0.12, (0, 0, height * 0.82), mats["amber"], parent=root, vertices=12)
    return root, flame


def make_procedural_head(name, loc, mats, height=0.44):
    """Human-proportioned head: skull + jaw + hair, built around the root empty."""
    root = new_empty(name, loc)
    skin = mats.get("monarch_skin", mats["obsidian"])
    hw = height * 0.235          # half width
    hd = height * 0.255          # half depth
    hh = height * 0.315          # half height
    make_sphere(name + "_skull", (hw, hd, hh), (0, 0, 0), skin, parent=root, segments=40, rings=24)
    make_sphere(
        name + "_jaw", (hw * 0.80, hd * 0.82, hh * 0.52),
        (0, -hd * 0.22, -hh * 0.62), skin, parent=root, segments=32, rings=18,
    )
    make_sphere(
        name + "_hair", (hw * 1.06, hd * 1.03, hh * 0.56),
        (0, hd * 0.10, hh * 0.52), mats["black"], parent=root, segments=32, rings=18,
    )
    for sx in (-1, 1):
        make_sphere(
            name + f"_ear_{sx}", (hw * 0.24, hd * 0.30, hh * 0.34),
            (sx * hw * 0.96, 0, -hh * 0.04), skin, parent=root, segments=20, rings=12,
        )
    make_box(name + "_hair_part", (0.006, hd * 0.95, 0.010), (0, hd * 0.05, hh * 0.92), mats["crimson"], parent=root)
    return root


def make_procedural_mask(name, loc, mats, width=0.42):
    """A Venetian half-mask that hugs the face: shell, gold rim, eye slots, filigree."""
    root = new_empty(name, loc)
    half_w = width / 2.0
    shell_d = width * 0.115
    shell_h = width * 0.165
    make_sphere(
        name + "_shell", (half_w, shell_d, shell_h), (0, 0, 0),
        mats["black"], parent=root, segments=40, rings=22,
    )
    make_torus(
        name + "_gold_rim", half_w * 0.965, 0.0035, (0, -shell_d * 0.55, 0),
        mats["brass"], parent=root, rotation=(math.pi / 2, 0, 0),
    )
    make_box(
        name + "_brow_filigree", (width * 0.90, 0.009, 0.009),
        (0, -shell_d * 0.78, shell_h * 0.72), mats["brass"], parent=root, bevel=0.003,
    )
    make_cylinder(
        name + "_nose", 0.013, shell_h * 0.62, (0, -shell_d * 0.92, -shell_h * 0.18),
        mats["obsidian"], parent=root, vertices=16, bevel=0.005, rotation=(math.pi / 2, 0, 0),
    )
    for sx in (-1, 1):
        eye = make_box(
            name + f"_eye_{sx}", (width * 0.235, 0.016, 0.022),
            (sx * half_w * 0.50, -shell_d * 0.86, shell_h * 0.10), mats["obsidian"],
            parent=root, bevel=0.009,
        )
        eye.rotation_euler = (0, math.radians(sx * 7), 0)
        for i in range(4):
            make_sphere(
                name + f"_stud_{sx}_{i}", (0.0065, 0.0065, 0.0065),
                (sx * (half_w * 0.20 + i * half_w * 0.28), -shell_d * 0.93, shell_h * 0.62 - i * 0.006),
                mats["brass"], parent=root, segments=10, rings=6,
            )
    return root


def make_godray_cones(name, mats, count=4, start_frame=1, end_frame=450):
    root = new_empty(name, (0, 2.6, 2.4))
    rng = random.Random(909)
    cones = []
    for i in range(count):
        cone = make_cone(
            f"{name}_{i}", 0.03, 0.52 + rng.random() * 0.35, 4.6,
            (rng.uniform(-0.7, 0.7), rng.uniform(-0.2, 0.2), 0),
            mats["godray"], parent=root, vertices=24,
        )
        local_target = Vector((0.0, -4.2, -2.0))
        direction = local_target - Vector(cone.location)
        cone.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()
        cones.append(cone)
    return root, cones


def make_particles(name, mat, *, count=44, center=(0, 0, 0.3), spread=1.0, seed=5):
    root = new_empty(name, center)
    rng = random.Random(seed)
    mesh = None
    objs = []
    for i in range(count):
        if mesh is None:
            tmp = make_sphere(name + "_proto", (0.012, 0.012, 0.012), (0, 0, 0), mat, segments=8, rings=5)
            mesh = tmp.data
            bpy.data.objects.remove(tmp, do_unlink=True)
        obj = bpy.data.objects.new(f"{name}_mote_{i}", mesh)
        SCENE.collection.objects.link(obj)
        obj.parent = root
        obj.location = (
            rng.uniform(-spread, spread),
            rng.uniform(-spread, spread),
            rng.uniform(-0.05, spread * 0.8),
        )
        base_radius = 0.009
        obj.scale = (rng.uniform(0.5, 1.8) * base_radius,) * 3
        objs.append(obj)
    return root, objs


def animate_particles(objs, start, end, *, lift=0.8, seed=11, appear_frame=None):
    rng = random.Random(seed)
    for i, obj in enumerate(objs):
        base = Vector(obj.location)
        original_scale = Vector(obj.scale)
        end_loc = base + Vector((rng.uniform(-0.35, 0.35), rng.uniform(-0.25, 0.45), lift * rng.uniform(0.5, 1.3)))
        set_loc(obj, start, base)
        if appear_frame is not None:
            set_scale(obj, start, (0.001, 0.001, 0.001))
            set_scale(obj, appear_frame - 1, (0.001, 0.001, 0.001))
            set_loc(obj, appear_frame - 1, base)
            set_scale(obj, appear_frame, original_scale)
            set_loc(obj, appear_frame, base)
        else:
            set_scale(obj, start, original_scale)
        set_loc(obj, end, end_loc)
        set_scale(obj, end, (0.001, 0.001, 0.001))


# ---------------------------------------------------------------------------
# Asset-backed helpers
# ---------------------------------------------------------------------------
def make_potato_prototype(mats):
    group = try_append_blend("sweet_potato", "PROTO_SWEET_POTATO")
    if group:
        fit_group(group, 0.23, use="max", center_xy=(0, 0), bottom_z=0.0)
    return group


def make_potato_instances(mats, count=18, seed=21, center=(0, 0), spread=(1.5, 1.5), z=0.04):
    rng = random.Random(seed)
    proto = make_potato_prototype(mats)
    instances = []
    for i in range(count):
        loc = (
            center[0] + rng.uniform(-spread[0], spread[0]),
            center[1] + rng.uniform(-spread[1], spread[1]),
            z + rng.uniform(0.0, 0.035),
        )
        rot = (rng.uniform(-0.35, 0.35), rng.uniform(-0.25, 0.25), rng.uniform(0, math.pi * 2))
        if proto:
            obj = duplicate_hierarchy(proto, f"POTATO_{i:02d}")
            obj.location = Vector(proto.location) + Vector(loc)
            obj.rotation_euler = rot
            obj.scale = Vector(proto.scale) * rng.uniform(0.72, 1.18)
        else:
            obj = make_procedural_potato(f"POTATO_{i:02d}", loc, mats, scale=rng.uniform(0.15, 0.23), rotation=rot)
        instances.append(obj)
    if proto:
        proto.hide_render = True
        for child in proto.children_recursive:
            child.hide_render = True
    return instances


def make_plant_instances(mats, count=6, seed=31):
    rng = random.Random(seed)
    proto = try_append_glb("DiffuseTransmissionPlant.glb", "PROTO_TRANSMISSION_PLANT")
    if proto:
        fit_group(proto, 0.62, use="z", center_xy=(0, 0), bottom_z=0.0)
    instances = []
    for i in range(count):
        loc = (rng.uniform(-1.7, 1.7), rng.uniform(-0.2, 2.2), 0.02)
        if proto:
            obj = duplicate_hierarchy(proto, f"PLANT_{i:02d}")
            obj.location = Vector(proto.location) + Vector(loc)
            obj.rotation_euler.z = rng.uniform(0, math.pi * 2)
            obj.scale = Vector(proto.scale) * rng.uniform(0.75, 1.22)
        else:
            obj = make_procedural_plant(f"PLANT_{i:02d}", loc, mats, height=rng.uniform(0.36, 0.64))
        instances.append(obj)
    if proto:
        proto.hide_render = True
        for child in proto.children_recursive:
            child.hide_render = True
    return instances


def make_lantern(mats, loc, height=0.68, use_glb=False):
    if use_glb:
        group = try_append_glb("Lantern.glb", "KHronos_Lantern")
        if group:
            fit_group(group, height, use="max", center_xy=(loc[0], loc[1]), bottom_z=loc[2])
            return group, None
    group = try_append_blend("Lantern_01", "PH_Lantern_01")
    if group:
        fit_group(group, height, use="z", center_xy=(loc[0], loc[1]), bottom_z=loc[2])
        return group, None
    return make_procedural_lantern("PROC_Lantern", loc, mats, height)


def make_candle(mats, loc, height=0.35):
    group = try_append_blend("wooden_candlestick", "PH_Wooden_Candlestick")
    if group:
        fit_group(group, height, use="z", center_xy=(loc[0], loc[1]), bottom_z=loc[2])
        flame = make_cone(
            "Candle_Practical_Flame", 0.032, 0.001, 0.115,
            (loc[0], loc[1], loc[2] + height * 0.98), mats["amber"], vertices=12,
        )
        return group, flame
    return make_procedural_candle("PROC_Candle", loc, mats, height)


def make_guard_rig(mats, name, loc, *, with_rifle=True, use_soldier=True):
    rig = new_empty(name, loc)
    soldier = try_append_glb("Soldier.glb", name + "_SOLDIER") if use_soldier else None
    if soldier:
        fit_group(soldier, 1.82, use="z", center_xy=(0, 0), bottom_z=0.0)
        override_material_recursive(soldier, mats["guard_coat"])
        soldier.parent = rig
    else:
        proc = make_procedural_guard(name + "_PROC_GUARD", (0, 0, 0), mats)
        proc.parent = rig
    make_tricorn(name + "_TRICORN", (0, 0, 1.78), mats, parent=rig)
    for i in range(4):
        make_sphere(
            name + f"_BRASS_BUTTON_{i}", (0.018, 0.018, 0.018),
            (0, -0.19, 1.16 - i * 0.13), mats["brass"], parent=rig, segments=10, rings=6,
        )
    if with_rifle:
        proc_rifle = make_procedural_rifle(name + "_PROC_RIFLE", (0.34, -0.12, 0.95), mats)
        proc_rifle.parent = rig
        proc_rifle.rotation_euler = (math.radians(8), math.radians(74), math.radians(4))
    return rig


def make_chess_setup(mats, procedural_only=False):
    if procedural_only:
        board = make_procedural_board("PROC_CHESS_BOARD_CINEMA", mats, size=2.65)
        knight_rig, knight_head = make_procedural_knight(
            "BLACK_MARBLE_KNIGHT", (0, 0, 0), mats, height=0.38
        )
        return board, knight_rig, knight_head, 0.20
    board = try_append_blend("chess_set", "PH_CHESS_SET")
    if board:
        fit_group(board, 2.65, use="xy", center_xy=(0, 0), bottom_z=0.16, rotation=(0, 0, 0))
        # Turn the imported board into a black mirror surface; keep imported pieces.
        for obj in board.children_recursive:
            if obj.type == "MESH" and "board" in obj.name.lower():
                obj.data.materials.clear()
                obj.data.materials.append(mats["obsidian"])
    else:
        board = make_procedural_board("PROC_CHESS_BOARD", mats, size=2.65)

    knight_rig = None
    knight_head = None
    # Prefer an imported knight if the Poly Haven hierarchy exposes one.
    if board:
        for obj in board.children_recursive:
            if obj.type == "MESH" and any(k in obj.name.lower() for k in ("knight", "horse")):
                bpy.context.view_layer.update()
                dup = obj.copy()
                dup.data = obj.data.copy()
                SCENE.collection.objects.link(dup)
                dup.parent = None
                dup.matrix_world = obj.matrix_world.copy()
                obj.hide_render = True
                knight_rig = new_empty("BLACK_MARBLE_KNIGHT_RIG")
                dup.parent = knight_rig
                dup.matrix_parent_inverse = knight_rig.matrix_world.inverted()
                override_material_recursive(knight_rig, mats["obsidian"])
                break
    knight_base_z = 0.0
    if knight_rig is None:
        knight_rig, knight_head = make_procedural_knight("BLACK_MARBLE_KNIGHT", (0, 0, 0), mats, height=0.38)
        knight_base_z = 0.20
    return board, knight_rig, knight_head, knight_base_z


def make_basket_setup(mats, loc=(1.35, 1.15, 0.02), procedural_only=False):
    if procedural_only:
        basket = make_procedural_basket("PROC_WICKER_BASKET_CINEMA", loc, mats)
        rng = random.Random(707)
        for i in range(12):
            pos = (
                loc[0] + rng.uniform(-0.30, 0.30),
                loc[1] + rng.uniform(-0.25, 0.25),
                loc[2] + 0.28 + rng.uniform(0.0, 0.18),
            )
            make_procedural_potato(
                f"BASKET_POTATO_{i:02d}", pos, mats,
                scale=rng.uniform(0.10, 0.16),
                rotation=(rng.uniform(-0.5, 0.5), rng.uniform(-0.4, 0.4), rng.uniform(0, math.pi * 2)),
            )
        return basket
    basket = try_append_blend("wicker_basket_01", "PH_WICKER_BASKET")
    if basket:
        fit_group(basket, 0.88, use="xy", center_xy=(loc[0], loc[1]), bottom_z=loc[2])
    else:
        basket = make_procedural_basket("PROC_WICKER_BASKET", loc, mats)
    # Potatoes overflowing the basket, all real 3D geometry.
    rng = random.Random(707)
    proto = make_potato_prototype(mats)
    for i in range(12):
        pos = (
            loc[0] + rng.uniform(-0.30, 0.30),
            loc[1] + rng.uniform(-0.25, 0.25),
            loc[2] + 0.28 + rng.uniform(0.0, 0.18),
        )
        if proto:
            obj = duplicate_hierarchy(proto, f"BASKET_POTATO_{i:02d}")
            obj.location = Vector(proto.location) + Vector(pos)
            obj.rotation_euler = (rng.uniform(-0.5, 0.5), rng.uniform(-0.4, 0.4), rng.uniform(0, math.pi * 2))
            obj.scale = Vector(proto.scale) * rng.uniform(0.65, 0.95)
        else:
            make_procedural_potato(f"BASKET_POTATO_{i:02d}", pos, mats, scale=rng.uniform(0.10, 0.16))
    if proto:
        proto.hide_render = True
        for child in proto.children_recursive:
            child.hide_render = True
    return basket


def make_monarch_setup(mats, procedural_only=True):
    """The MONARCH: real marble bust wearing the scanned Venetian mask.

    Measured facts (see debug_s5_measure.py), for a 0.92 m bust:
      bust  x ±0.243 · y -0.268..+0.268 · z 0.500..1.420
      mask  asset bbox is 0.485 × 0.263 × 0.955 — the crest makes it read
            taller than the face, so size it by WIDTH only, then seat the chin.
    """
    skin = mats.get("monarch_skin", mats["obsidian"])
    bust_h = 0.92

    # --- torso/head: real photogrammetry marble bust (Poly Haven, CC0) ------
    bust = try_append_blend("marble_bust_01", "PH_MARBLE_BUST")
    if bust:
        fit_group(bust, bust_h, use="z", center_xy=(0, 0), bottom_z=0.50)
        override_material_recursive(bust, mats.get("monarch_marble", mats["black"]))
        bpy.context.view_layer.update()
        blo, bhi = bbox_group(bust)
        bust_top, bust_front = bhi.z, blo.y
    else:
        bust = make_box("MONARCH_WARM_BUST", (0.62, 0.30, 0.42), (0, 0.42, 0.86), skin, bevel=0.10)
        bust_top, bust_front = 1.42, -0.268

    # A marble bust of this height wears roughly a 0.26 m wide face.
    face_w = bust_h * 0.285
    # Seat the mask so its eye slots land on the bust's eye line (~1.29 m in
    # world space); the crest is then allowed to rise above the crown.
    mask_bottom_z = bust_top - bust_h * 0.44

    # --- the mask: real scanned Venetian half-mask, worn on the face --------
    mask = try_append_glb("venice_mask.glb", "MONARCH_VENICE_MASK")
    if mask:
        bpy.context.view_layer.update()
        mlo, mhi = bbox_group(mask)
        scale = face_w / max(mhi.x - mlo.x, 1e-4)
        mask.scale = (scale, scale, scale)
        bpy.context.view_layer.update()
        mlo, mhi = bbox_group(mask)
        mask.location = Vector(mask.location) + Vector((
            -(mlo.x + mhi.x) * 0.5,          # centre on the face
            (bust_front + 0.015) - mhi.y,    # back of the shell rests on the face
            mask_bottom_z - mlo.z,           # eye slots land on the bust eye line
        ))
        bpy.context.view_layer.update()
    else:
        mask = make_procedural_mask(
            "MONARCH_3D_VENICE_MASK",
            (0, bust_front + face_w * 0.5, mask_bottom_z + face_w * 1.2),
            mats, width=face_w,
        )

    head = new_empty("MONARCH_HEAD_REF", (0, bust_front, bust_top))
    # Crimson signature: a light burning just behind the mask so it leaks
    # through the eye slots instead of a bar floating in mid-air.
    glow_z = mask_bottom_z + (bbox_group(mask)[1].z - mask_bottom_z) * 0.60 if mask else mask_bottom_z + 0.14
    eye_light = add_point(
        "MONARCH_EYE_GLOW", (0, bust_front + face_w * 0.30, glow_z), 22, C_CRIMSON, 0.030,
    )
    return head, bust, None, None, mask, eye_light


# ---------------------------------------------------------------------------
# Scene setup
# ---------------------------------------------------------------------------
def setup_world_and_render(args, shot_start, shot_end, render_start, render_end):
    global SCENE, VOLUME_NODE
    bpy.ops.wm.read_factory_settings(use_empty=True)
    safe_set(bpy.context.preferences.edit, "use_global_undo", False)
    SCENE = bpy.context.scene
    SCENE.name = "PEHRA_DARK_3D_CINEMA"
    SCENE.frame_start = shot_start
    SCENE.frame_end = shot_end
    SCENE.render.engine = "CYCLES"
    SCENE.cycles.device = "CPU"
    SCENE.cycles.samples = int(args.samples)
    safe_set(SCENE.cycles, "use_adaptive_sampling", True)
    safe_set(SCENE.cycles, "adaptive_threshold", 0.045)
    safe_set(SCENE.cycles, "adaptive_min_samples", 4)
    safe_set(SCENE.cycles, "max_bounces", 5)
    safe_set(SCENE.cycles, "diffuse_bounces", 2)
    safe_set(SCENE.cycles, "glossy_bounces", 3)
    safe_set(SCENE.cycles, "transmission_bounces", 2)
    safe_set(SCENE.cycles, "volume_bounces", 1)
    safe_set(SCENE.cycles, "transparent_max_bounces", 4)
    safe_set(SCENE.cycles, "use_light_tree", True)
    safe_set(SCENE.cycles, "use_denoising", True)
    safe_set(SCENE.cycles, "denoiser", "OPENIMAGEDENOISE")
    safe_set(SCENE.cycles, "denoising_input_passes", "RGB_ALBEDO_NORMAL")
    safe_set(SCENE.cycles, "sample_clamp_indirect", 3.0)
    safe_set(SCENE.cycles, "seed", sum(ord(c) for c in args.shot) % 99991)
    safe_set(SCENE.cycles, "use_animated_seed", False)
    safe_set(SCENE.render, "use_motion_blur", True)
    safe_set(SCENE.render, "motion_blur_shutter", 0.34)
    safe_set(SCENE.render, "motion_blur_position", "CENTER")
    safe_set(SCENE.render, "use_persistent_data", True)
    safe_set(SCENE.render, "threads_mode", "AUTO")
    SCENE.render.resolution_x = WIDTH
    SCENE.render.resolution_y = HEIGHT
    SCENE.render.resolution_percentage = int(args.res_pct)
    SCENE.render.fps = FPS
    SCENE.render.pixel_aspect_x = 1.0
    SCENE.render.pixel_aspect_y = 1.0
    SCENE.render.film_transparent = False
    SCENE.render.image_settings.file_format = "PNG"
    SCENE.render.image_settings.color_mode = "RGB"
    SCENE.render.image_settings.color_depth = "8"
    SCENE.render.image_settings.compression = 15
    SCENE.render.use_file_extension = True
    SCENE.render.use_overwrite = True
    SCENE.render.use_placeholder = False
    SCENE.render.use_stamp = False
    safe_set(SCENE.render, "dither_intensity", 1.0)
    safe_set(SCENE.view_settings, "view_transform", "AgX")
    try:
        looks = list(SCENE.view_settings.bl_rna.properties["look"].enum_items.keys())
        for candidate in ("AgX - Medium High Contrast", "Medium High Contrast", "AgX - High Contrast"):
            if candidate in looks:
                SCENE.view_settings.look = candidate
                break
    except Exception:
        pass
    safe_set(SCENE.view_settings, "exposure", 0.25)
    safe_set(SCENE.view_settings, "gamma", 1.0)
    safe_set(SCENE.display_settings, "display_device", "sRGB")

    world = bpy.data.worlds.new("MIDNIGHT_BLUE_VOLUMETRIC_FOG")
    SCENE.world = world
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs["Color"].default_value = C_MIDNIGHT
    bg.inputs["Strength"].default_value = 0.18
    vol = nt.nodes.new("ShaderNodeVolumeScatter")
    vol.name = "Animated_Volume_Fog"
    vol.inputs["Color"].default_value = (0.09, 0.18, 0.27, 1.0)
    vol.inputs["Density"].default_value = 0.006
    vol.inputs["Anisotropy"].default_value = 0.55
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    nt.links.new(vol.outputs["Volume"], out.inputs["Volume"])
    VOLUME_NODE = vol

    SCENE.use_nodes = True
    comp = SCENE.node_tree
    comp.nodes.clear()
    rl = comp.nodes.new("CompositorNodeRLayers")
    glare = comp.nodes.new("CompositorNodeGlare")
    safe_set(glare, "glare_type", "FOG_GLOW")
    safe_set(glare, "quality", "HIGH")
    safe_set(glare, "threshold", 0.92)
    safe_set(glare, "size", 7)
    safe_set(glare, "mix", -0.88)
    composite = comp.nodes.new("CompositorNodeComposite")
    glare_input = None
    try:
        glare_input = glare.inputs.get("Image")
    except Exception:
        pass
    if glare_input is None:
        glare_input = glare.inputs[0]
    comp.links.new(rl.outputs["Image"], glare_input)
    glare_output = None
    try:
        glare_output = glare.outputs.get("Image")
    except Exception:
        pass
    if glare_output is None:
        glare_output = glare.outputs[0]
    composite_input = None
    try:
        composite_input = composite.inputs.get("Image")
    except Exception:
        pass
    if composite_input is None:
        composite_input = composite.inputs[0]
    comp.links.new(glare_output, composite_input)

    SCENE.frame_start = render_start
    SCENE.frame_end = render_end
    SCENE.frame_set(render_start)
    bpy.context.view_layer.update()


# ---------------------------------------------------------------------------
# Six animated shots
# ---------------------------------------------------------------------------
def shot_s1(mats, s, e):
    make_pbr_ground("WET_MUD_FURROWS", "dry_mud_field_001", size=24, repeat=5.5, disp_strength=0.34, wet=0.72, darken=0.82)
    make_dark_backdrop("S1_MIDNIGHT_BACKDROP", mats, y=7.0, z=3.0)
    # Raised furrow ridges — real geometry, not a texture-only trick.
    rng = random.Random(101)
    for i in range(9):
        x = -1.8 + i * 0.45
        ridge = make_cylinder(
            f"FURROW_RIDGE_{i}", 0.17, 5.6, (x, 0.35, 0.035), mats["earth"],
            rotation=(math.pi / 2, 0, rng.uniform(-0.02, 0.02)), vertices=14,
        )
        ridge.scale = (1.0, 1.0, 0.42)
    potatoes = make_potato_instances(mats, count=20, seed=21, center=(0, 0.4), spread=(1.45, 1.35), z=0.055)
    plants = make_plant_instances(mats, count=7, seed=31)
    for i, plant in enumerate(plants):
        animate_swing(plant, s, e, amp=0.045 + 0.012 * (i % 3), period=44 + i * 3, axis=1, step=5)

    lantern, proc_flame = make_lantern(mats, (1.15, -0.55, 0.92), height=0.72, use_glb=False)
    animate_swing(lantern, s, e, amp=0.095, period=48, axis=0, step=4)
    animate_swing(lantern, s, e, amp=0.055, period=57, axis=1, step=4)
    lantern_light = add_point("SWINGING_LANTERN_PRACTICAL", (1.15, -0.55, 1.38), 48, C_AMBER, 0.16)
    animate_flicker(lantern_light, s, e, 48, 10, seed=3, step=3)
    set_light_energy(lantern_light, s, 18)
    set_light_energy(lantern_light, s + 8, 58)
    set_light_energy(lantern_light, e, 42)

    bg_lantern, _ = make_lantern(mats, (-1.75, 2.2, 0.75), height=0.58, use_glb=True)
    add_point("DISTANT_LANTERN_GLOW", (-1.75, 2.2, 1.15), 18, C_AMBER, 0.22)
    add_area("MOONLIT_BLUE_TOP", (-3.0, 1.0, 4.2), (0, 0, 0.1), 120, (0.22, 0.42, 0.85), 5.0, 3.0)
    add_area("S1_WARM_MACRO_FILL", (0.0, -2.2, 1.6), (0.0, 0.45, 0.18), 88, C_AMBER, 2.6, 1.4)
    add_area("S1_COOL_POTATO_RIM", (2.2, 1.4, 1.8), (0.0, 0.4, 0.2), 55, (0.30, 0.52, 0.95), 2.0, 1.2)
    add_area("S1_COOL_MACRO_FILL", (0.0, -2.5, 1.2), (0, 0.5, 0.2), 70, (0.35, 0.50, 0.80), 2.5, 1.5)
    add_area("WARM_EDGE_KICK", (2.8, 1.6, 1.6), (0, 0, 0.25), 42, C_AMBER, 2.4, 1.2)
    set_volume_density(s, 0.016)
    set_volume_density((s + e) // 2, 0.024)
    set_volume_density(e, 0.019)

    dust, motes = make_particles("S1_FOG_MOTES", mats["gold_emit"], count=32, center=(0, 0.2, 0.7), spread=1.5, seed=12)
    animate_particles(motes, s, e, lift=0.28, seed=13)

    cam = make_camera("S1_MACRO_DOLLY")
    key_camera(cam, s, (0.00, -3.85, 0.72), (0.00, 0.55, 0.20), lens=38, focus=3.55)
    key_camera(cam, s + 24, (0.10, -3.35, 0.68), (0.06, 0.62, 0.22), lens=40, focus=3.20)
    key_camera(cam, s + 48, (0.16, -2.92, 0.64), (0.12, 0.72, 0.23), lens=42, focus=2.85)
    key_camera(cam, e, (0.22, -2.62, 0.62), (0.16, 0.80, 0.24), lens=44, focus=2.60)
    return cam


def shot_s2(mats, s, e):
    make_pbr_ground("WET_COBBLESTONE_YARD", "cobblestone_floor_06", size=26, repeat=6.0, disp_strength=0.16, wet=0.38, darken=0.38)
    make_dark_backdrop("S2_NIGHT_BACKDROP", mats, y=7.0, z=3.2)
    fence = make_fence("FOREGROUND_IRON_SPEARS", mats, y=-1.05, width=5.8, height=2.15, count=17)
    fence.location.x = 0.0

    lamp1, flame1 = None, None
    lamp = try_append_blend("street_lamp_01", "PH_STREET_LAMP_LEFT")
    if lamp:
        fit_group(lamp, 3.6, use="z", center_xy=(-2.4, 1.35), bottom_z=0.0)
        lamp1 = lamp
    else:
        lamp1, flame1 = make_procedural_streetlamp("PROC_STREET_LAMP_LEFT", (-2.4, 1.35, 0), mats)
    add_point("LEFT_LAMP_PRACTICAL", (-2.4, 1.35, 3.65), 72, C_AMBER, 0.22)
    lamp2, flame2 = make_procedural_streetlamp("PROC_STREET_LAMP_RIGHT", (2.5, 2.35, 0), mats, height=3.35)
    add_point("RIGHT_LAMP_PRACTICAL", (2.5, 2.35, 3.45), 38, C_AMBER, 0.26)

    guard_a = make_guard_rig(mats, "GUARD_A", (-0.82, 1.35, 0.0))
    guard_b = make_guard_rig(mats, "GUARD_B", (0.86, 1.55, 0.0))
    guard_c = make_guard_rig(mats, "GUARD_C_WALKING_AWAY", (0.08, 3.15, 0.0))
    for idx, guard in enumerate((guard_a, guard_b, guard_c)):
        set_scale(guard, s, (1.0, 1.0, 1.0))
        set_scale(guard, s + 20, (1.0, 1.0, 1.012))
        set_scale(guard, s + 42, (1.0, 1.0, 1.0))
        set_scale(guard, e, (1.0, 1.0, 1.008))
        set_rot(guard, s, (0, 0, 0.015 * (idx - 1)))
        set_rot(guard, e, (0, 0, -0.012 * (idx - 1)))
    set_loc(guard_c, s, (0.08, 3.15, 0.0))
    set_loc(guard_c, s + 36, (0.22, 3.65, 0.0))
    set_loc(guard_c, e, (0.42, 4.35, 0.0))
    set_rot(guard_c, s, (0, 0, math.pi))
    set_rot(guard_c, e, (0, 0, math.pi + 0.05))

    add_area("TEAL_RIM_LEFT", (-4.0, 0.8, 2.4), (0, 1.4, 1.1), 220, C_TEAL, 3.0, 4.0)
    add_area("S2_GUARD_FRONT_FILL", (0.0, -2.5, 2.0), (0, 1.2, 1.0), 220, (0.28, 0.42, 0.68), 3.0, 2.0)
    add_area("TEAL_RIM_RIGHT", (4.0, 1.0, 2.2), (0, 1.4, 1.1), 115, C_BLUE, 2.4, 3.8)
    add_spot("GUARD_FACE_KICK", (0.0, -2.3, 2.8), (0, 1.4, 1.2), 85, (0.55, 0.68, 1.0), 0.75)
    set_volume_density(s, 0.020)
    set_volume_density(s + 40, 0.028)
    set_volume_density(e, 0.021)

    dust, motes = make_particles("S2_FOG_MOTES", mats["gold_emit"], count=26, center=(0, 1.1, 1.0), spread=2.0, seed=22)
    animate_particles(motes, s, e, lift=0.42, seed=23)

    cam = make_camera("S2_LOW_CRANE_PUSH")
    key_camera(cam, s, (0.00, -4.35, 0.58), (0.00, 1.40, 1.18), lens=38, focus=4.55)
    key_camera(cam, s + 28, (0.08, -3.75, 0.68), (0.02, 1.48, 1.16), lens=40, focus=4.05)
    key_camera(cam, s + 56, (0.14, -3.18, 0.78), (0.04, 1.56, 1.14), lens=43, focus=3.55)
    key_camera(cam, e, (0.18, -2.85, 0.84), (0.06, 1.62, 1.12), lens=45, focus=3.30)
    return cam


def shot_s3(mats, s, e):
    make_pbr_ground("S3_WET_COBBLE", "cobblestone_floor_06", size=14, repeat=3.0, disp_strength=0.10, wet=0.42, darken=0.42)
    make_dark_backdrop("S3_IRON_BACKDROP", mats, y=5.5, z=2.5)
    gate = make_gate("S3_LOCKED_IRON_GATE", mats, y=0.0, width=2.8, height=2.2)
    set_rot(gate["left"], s, (0, 0, 0))
    set_rot(gate["right"], s, (0, 0, 0))
    set_rot(gate["left"], e, (0, 0, 0))
    set_rot(gate["right"], e, (0, 0, 0))
    # Barely perceptible chain breathing before the dead-silence snap.
    animate_swing(gate["chain"], s, 196, amp=0.012, period=34, axis=2, step=4)
    set_loc(gate["chain"], 205, (0, -0.13, 1.10))
    set_loc(gate["chain"], 207, (-0.03, -0.13, 1.02))
    set_rot(gate["lock_pivot"], s, (0, 0, 0))
    set_rot(gate["lock_pivot"], 205, (0, 0, 0))
    set_rot(gate["lock_pivot"], 207, (0, math.radians(-64), 0))
    set_loc(gate["lock"], 205, (0, -0.20, 0.92))
    set_loc(gate["lock"], 207, (0.02, -0.20, 0.88))

    add_area("S3_COLD_KEY", (-2.3, -2.2, 2.6), (0, 0, 1.1), 155, (0.30, 0.52, 0.92), 2.6, 2.0)
    add_area("S3_BRASS_KICK", (2.0, -1.2, 1.5), (0, 0, 1.0), 46, C_AMBER, 1.4, 1.0)
    add_point("S3_PADLOCK_WARM_PRACTICAL", (0.0, -0.9, 1.22), 38, C_AMBER, 0.12)
    flash = add_point("S3_PADLOCK_SNAP_FLASH", (0, -0.7, 1.18), 1, C_GOLD, 0.14)
    set_light_energy(flash, s, 1)
    set_light_energy(flash, 205, 2)
    set_light_energy(flash, 206, 120)
    set_light_energy(flash, 207, 34)
    set_light_energy(flash, e, 8)
    set_volume_density(s, 0.022)
    set_volume_density(200, 0.013)
    set_volume_density(206, 0.010)
    set_volume_density(e, 0.016)

    cam = make_camera("S3_SHALLOW_PUSH")
    key_camera(cam, s, (0.00, -2.75, 1.18), (0.00, 0.00, 1.08), lens=52, focus=2.55)
    key_camera(cam, s + 22, (0.02, -2.38, 1.16), (0.00, 0.00, 1.08), lens=57, focus=2.25)
    key_camera(cam, 202, (0.03, -2.02, 1.14), (0.00, 0.00, 1.08), lens=63, focus=1.92)
    key_camera(cam, e, (0.04, -1.88, 1.13), (0.00, 0.00, 1.07), lens=67, focus=1.80)
    return cam


def shot_s4(mats, s, e):
    make_pbr_ground("S4_GOLDEN_WET_COBBLE", "cobblestone_floor_06", size=20, repeat=4.5, disp_strength=0.15, wet=0.28, darken=0.34)
    make_dark_backdrop("S4_GOLDEN_FOG_BACKDROP", mats, y=8.0, z=3.2)
    gate = make_gate("S4_UNGUARDED_GATE", mats, y=0.0, width=2.9, height=2.25)
    # Chain and open padlock have already fallen; gates now swing toward the golden fog.
    set_loc(gate["chain"], s, (-0.15, -0.18, 0.08))
    set_rot(gate["chain"], s, (0, 0, math.radians(18)))
    set_loc(gate["lock"], s, (0.18, -0.22, 0.06))
    set_rot(gate["lock"], s, (0, 0, math.radians(-22)))
    set_rot(gate["lock_pivot"], s, (0, math.radians(-64), 0))
    set_rot(gate["left"], s, (0, 0, 0))
    set_rot(gate["right"], s, (0, 0, 0))
    set_rot(gate["left"], s + 14, (0, 0, math.radians(22)))
    set_rot(gate["right"], s + 14, (0, 0, math.radians(-22)))
    set_rot(gate["left"], s + 34, (0, 0, math.radians(58)))
    set_rot(gate["right"], s + 34, (0, 0, math.radians(-58)))
    set_rot(gate["left"], e, (0, 0, math.radians(72)))
    set_rot(gate["right"], e, (0, 0, math.radians(-72)))

    guard = make_guard_rig(mats, "S4_GUARD_LEAVING", (0.0, 3.35, 0.0), with_rifle=False)
    set_rot(guard, s, (0, 0, math.pi))
    set_loc(guard, s, (0.0, 3.35, 0.0))
    set_loc(guard, s + 28, (0.18, 4.15, 0.0))
    set_loc(guard, e, (0.42, 5.25, 0.0))
    set_scale(guard, s, (0.78, 0.78, 0.78))
    set_scale(guard, e, (0.74, 0.74, 0.74))

    add_area("S4_GOLDEN_GATE_BACKLIGHT", (0.0, 4.2, 2.7), (0, 0, 0.9), 260, C_GOLD, 4.5, 3.0)
    add_spot("S4_GOLDEN_GODRAY_SPOT", (0.0, 3.6, 3.2), (0, -1.0, 0.4), 150, C_GOLD, 0.72)
    add_area("S4_COOL_FRONT_FILL", (-3.0, -2.5, 2.0), (0, 0, 1.0), 100, C_TEAL, 3.0, 2.0)
    add_area("S4_GUARD_FRONT_RIM", (-2.0, -1.8, 1.8), (0, 2.0, 1.0), 120, (0.35, 0.50, 0.80), 2.2, 1.6)
    add_area("S4_GATE_FRONT_FILL", (0.0, -2.5, 1.8), (0, 0.0, 1.0), 90, (0.30, 0.45, 0.70), 2.5, 2.0)
    set_volume_density(s, 0.026)
    set_volume_density(s + 28, 0.020)
    set_volume_density(e, 0.014)

    dust, motes = make_particles("S4_GOLDEN_DUST", mats["gold_emit"], count=52, center=(0, 1.0, 0.7), spread=1.5, seed=41)
    animate_particles(motes, s, e, lift=0.75, seed=42)

    cam = make_camera("S4_DOLLY_THROUGH_OPEN_GATE")
    key_camera(cam, s, (0.00, -3.85, 1.28), (0.00, 1.35, 1.08), lens=36, focus=3.70)
    key_camera(cam, s + 22, (0.04, -3.15, 1.22), (0.02, 1.70, 1.05), lens=38, focus=3.25)
    key_camera(cam, s + 44, (0.06, -2.48, 1.16), (0.05, 2.15, 1.02), lens=40, focus=2.85)
    key_camera(cam, e, (0.08, -1.95, 1.12), (0.08, 2.60, 0.98), lens=42, focus=2.55)
    return cam


def shot_s5(mats, s, e):
    head, bust, shoulders, neck, mask, bar = make_monarch_setup(mats, procedural_only=True)
    make_dark_backdrop("S5_MONARCH_SMOKE_WALL", mats, y=4.8, z=2.6)
    make_cylinder("MONARCH_OBSIDIAN_PEDESTAL", 0.62, 0.48, (0, 0.65, 0.24), mats["obsidian"], vertices=48, bevel=0.035)

    # Foreground practical candles create real depth-of-field bokeh.
    candle_a, flame_a = make_procedural_candle("S5_CANDLE_A", (1.28, -1.05, 0.34), mats, height=0.38)
    candle_b, flame_b = make_procedural_candle("S5_CANDLE_B", (-1.32, -0.92, 0.30), mats, height=0.32)
    make_cylinder(
        "S5_GLASS_HURRICANE_HOLDER", 0.16, 0.44,
        (-1.32, -0.92, 0.52), mats["glass"], vertices=24,
    )
    light_a = add_point("MONARCH_CANDLE_A", (1.28, -1.05, 0.78), 36, C_AMBER, 0.10)
    light_b = add_point("MONARCH_CANDLE_B", (-1.32, -0.92, 0.68), 24, C_AMBER, 0.12)
    animate_flicker(light_a, s, e, 36, 10, seed=51, step=3)
    animate_flicker(light_b, s, e, 24, 8, seed=52, step=3)
    animate_emission(mats["amber"], s, e, 14, 5, seed=53, step=3)
    animate_emission(mats["crimson"], s, e, 2.0, 0.6, seed=54, step=3)

    add_area("MONARCH_FRONT_FILL", (0.0, -2.4, 1.9), (0, 0.35, 1.16), 70, (0.55, 0.55, 0.60), 2.2, 1.5)
    add_area("MONARCH_CRIMSON_RIM", (0.0, -1.6, 1.45), (0, 0.3, 1.15), 30, C_CRIMSON, 1.8, 1.0)
    add_area("MONARCH_COLD_EDGE", (-2.4, 1.2, 2.3), (0, 0.4, 1.1), 75, C_TEAL, 2.5, 2.0)
    add_area("MONARCH_GOLD_HAIRLIGHT", (2.1, 1.5, 2.2), (0, 0.4, 1.2), 48, C_GOLD, 1.8, 1.0)
    set_volume_density(s, 0.030)
    set_volume_density((s + e) // 2, 0.038)
    set_volume_density(e, 0.028)

    smoke, motes = make_particles("S5_DARK_SMOKE_MOTES", mats["gold_emit"], count=18, center=(0, 0.7, 1.35), spread=0.9, seed=61)
    animate_particles(motes, s, e, lift=0.30, seed=62)

    # The bust sits on a 0.48 m pedestal and is 0.92 m tall, so the masked
    # face lives around z = 1.28. Hold the camera at eye level and push in.
    # Bust sits on a 0.48 m pedestal and is 0.92 m tall; crown ≈ 1.42,
    # mask crest ≈ 1.66. Frame the masked face, then push in on it.
    cam = make_camera("S5_MASKED_MONARCH_PUSH")
    key_camera(cam, s, (0.00, -4.20, 1.38), (0.00, -0.10, 1.20), lens=46, focus=4.05)
    key_camera(cam, s + 14, (0.04, -3.85, 1.37), (0.00, -0.10, 1.21), lens=49, focus=3.70)
    key_camera(cam, s + 28, (0.07, -3.55, 1.36), (0.00, -0.10, 1.22), lens=52, focus=3.42)
    key_camera(cam, e, (0.09, -3.30, 1.35), (0.00, -0.10, 1.23), lens=55, focus=3.18)
    return cam


def shot_s6(mats, s, e):
    board, knight, knight_head, knight_base_z = make_chess_setup(mats, procedural_only=False)
    basket = make_basket_setup(mats, loc=(1.34, 1.12, 0.02), procedural_only=False)
    candle_a, flame_a = make_procedural_candle("S6_CANDLE_A", (1.78, 0.78, 0.18), mats, height=0.30)
    candle_b, flame_b = make_procedural_candle("S6_CANDLE_B", (0.92, 1.55, 0.18), mats, height=0.27)
    make_dark_backdrop("S6_CHESS_BACKDROP", mats, y=6.0, z=2.8)
    light_a = add_point("S6_BASKET_CANDLE_A", (1.78, 0.78, 0.55), 32, C_AMBER, 0.10)
    light_b = add_point("S6_BASKET_CANDLE_B", (0.92, 1.55, 0.50), 24, C_AMBER, 0.12)
    animate_flicker(light_a, s, e, 32, 8, seed=81, step=4)
    animate_flicker(light_b, s, e, 24, 7, seed=82, step=4)

    add_area("S6_BOARD_TOP_LIGHT", (-2.2, -1.1, 3.0), (0, 0, 0.2), 165, (0.35, 0.52, 0.82), 3.0, 2.4)
    add_area("S6_GOLD_BASKET_KICK", (2.6, 2.2, 2.0), (1.2, 1.1, 0.4), 150, C_GOLD, 2.2, 1.8)
    add_spot("S6_KNIGHT_RIM", (0.0, -2.6, 2.2), (0, 0, 0.25), 95, (0.55, 0.72, 1.0), 0.65)

    # Decisive black-marble knight move: lift, glide, rotate, SLAM on frame 361.
    if knight_head is not None:
        knight_head.rotation_euler = (math.radians(-18), 0, 0)
    set_loc(knight, s, (-0.72, -0.22, knight_base_z))
    set_rot(knight, s, (0, 0, math.radians(-8)))
    set_loc(knight, 340, (-0.34, -0.08, knight_base_z + 0.075))
    set_rot(knight, 340, (0, 0, math.radians(4)))
    set_loc(knight, 358, (0.26, 0.18, knight_base_z + 0.095))
    set_rot(knight, 358, (0, 0, math.radians(10)))
    set_loc(knight, 361, (0.34, 0.24, knight_base_z))
    set_rot(knight, 361, (0, 0, math.radians(12)))
    set_loc(knight, 365, (0.34, 0.24, knight_base_z + 0.012))
    set_loc(knight, 372, (0.34, 0.24, knight_base_z))
    set_loc(knight, e, (0.34, 0.24, knight_base_z))
    set_rot(knight, e, (0, 0, math.radians(12)))

    shock_mat = make_emission_mat("MAT_S6_SHOCKWAVE", C_GOLD, 0.0)
    shock = make_torus("S6_GOLDEN_SHOCKWAVE_RING", 1.0, 0.012, (0.34, 0.24, 0.205), shock_mat)
    shock.scale = (0.001, 0.001, 0.001)
    set_scale(shock, s, (0.001, 0.001, 0.001))
    set_scale(shock, 360, (0.001, 0.001, 0.001))
    set_scale(shock, 361, (0.08, 0.08, 0.08))
    set_scale(shock, 378, (0.72, 0.72, 0.72))
    set_scale(shock, e, (1.12, 1.12, 1.12))
    set_emission(shock_mat, s, 0.0)
    set_emission(shock_mat, 360, 0.0)
    set_emission(shock_mat, 361, 2.0)
    set_emission(shock_mat, 386, 0.7)
    set_emission(shock_mat, e, 0.0)

    dust, motes = make_particles("S6_GOLDEN_IMPACT_DUST", mats["gold_emit"], count=64, center=(0.34, 0.24, 0.22), spread=0.42, seed=91)
    animate_particles(motes, s, e, lift=0.95, seed=92, appear_frame=361)
    basket_dust, basket_motes = make_particles("S6_BASKET_GLIMMER", mats["gold_emit"], count=24, center=(1.34, 1.12, 0.42), spread=0.55, seed=93)
    animate_particles(basket_motes, s, e, lift=0.35, seed=94)

    set_volume_density(s, 0.016)
    set_volume_density(361, 0.024)
    set_volume_density(390, 0.018)
    set_volume_density(e, 0.013)

    cam = make_camera("S6_ANAMORPHIC_TRACK_RACK_FOCUS")
    key_camera(cam, s, (-0.55, -2.80, 1.10), (-0.10, 0.05, 0.24), lens=42, focus=2.80)
    key_camera(cam, 340, (-0.30, -2.62, 1.08), (0.02, 0.10, 0.25), lens=44, focus=2.62)
    key_camera(cam, 361, (0.02, -2.42, 1.05), (0.32, 0.22, 0.25), lens=46, focus=2.42)
    key_camera(cam, 390, (0.42, -2.22, 1.08), (0.82, 0.78, 0.36), lens=48, focus=2.48)
    key_camera(cam, 420, (0.72, -2.02, 1.12), (1.28, 1.10, 0.42), lens=50, focus=2.62)
    key_camera(cam, e, (0.86, -1.90, 1.15), (1.38, 1.18, 0.44), lens=52, focus=2.68)
    return cam


SHOT_BUILDERS = {
    "S1_MIDNIGHT_FURROW": shot_s1,
    "S2_ROYAL_GUARDS": shot_s2,
    "S3_LOCKED_IRON": shot_s3,
    "S4_UNGUARDED_GATE": shot_s4,
    "S5_MASKED_MONARCH": shot_s5,
    "S6_MASTER_MOVE": shot_s6,
}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else sys.argv[1:]
    parser = argparse.ArgumentParser()
    parser.add_argument("--shot", required=True, choices=sorted(SHOT_BUILDERS.keys()))
    parser.add_argument("--mode", choices=("lookdev", "final"), default="final")
    parser.add_argument("--samples", type=int, default=12)
    parser.add_argument("--res-pct", type=int, default=100)
    parser.add_argument("--timeline", default=str(BASE / "build" / "timeline_15s.json"))
    parser.add_argument("--assets", default=str(BASE / "assets"))
    parser.add_argument("--out", default=str(BASE / "frames"))
    parser.add_argument(
        "--frames", default=None,
        help="Optional frame subset, e.g. 311-350. Defaults to the whole shot.",
    )
    return parser.parse_args(argv)


def main():
    global ASSETS
    args = parse_args()
    ASSETS = Path(args.assets).resolve()
    load_manifest()

    timeline_path = Path(args.timeline).resolve()
    timeline = json.loads(timeline_path.read_text(encoding="utf-8"))
    shot = next((x for x in timeline["shots"] if x["id"] == args.shot), None)
    if shot is None:
        raise RuntimeError(f"Shot {args.shot} not found in {timeline_path}")

    shot_start = int(shot["f_start"])
    shot_end = int(shot["f_end"])
    if args.mode == "lookdev":
        render_start = render_end = int(shot["lookdev_frame"])
        samples = max(int(args.samples), 18)
    else:
        render_start, render_end = shot_start, shot_end
        samples = int(args.samples)

    if args.frames:
        lo_s, _, hi_s = args.frames.partition("-")
        render_start = max(shot_start, int(lo_s))
        render_end = min(shot_end, int(hi_s or lo_s))
        if render_end < render_start:
            raise SystemExit(
                f"--frames {args.frames} lies outside {args.shot} ({shot_start}-{shot_end})"
            )

    info(
        f"Building {args.shot}: full shot {shot_start}-{shot_end}, "
        f"render {render_start}-{render_end}, {samples} samples @ {args.res_pct}%"
    )
    setup_world_and_render(args, shot_start, shot_end, render_start, render_end)
    SCENE.cycles.samples = samples

    mats = build_material_library()
    builder = SHOT_BUILDERS[args.shot]
    try:
        builder(mats, shot_start, shot_end)
    except Exception:
        warn(f"Shot builder raised an exception; scene still contains fallback geometry:\n{traceback.format_exc()}")
        raise
    rebalance_scene()
    smooth_all_fcurves()

    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    SCENE.frame_start = render_start
    SCENE.frame_end = render_end
    SCENE.frame_set(render_start)
    bpy.context.view_layer.update()

    (out_dir / f"render_info_{args.shot}.json").write_text(
        json.dumps(
            {
                "shot": args.shot,
                "mode": args.mode,
                "shot_frame_range": [shot_start, shot_end],
                "render_frame_range": [render_start, render_end],
                "samples": samples,
                "resolution_percentage": int(args.res_pct),
                "output_resolution": [WIDTH, HEIGHT],
                "fps": FPS,
                "bpy_version": bpy.app.version_string,
                "blender_binary": bpy.app.binary_path,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    t0 = time.time()
    if render_start == render_end:
        SCENE.render.filepath = str(out_dir / f"f_{render_start:06d}.png")
        info(f"Rendering single lookdev frame -> {SCENE.render.filepath}")
        bpy.ops.render.render(write_still=True)
    else:
        SCENE.render.filepath = str(out_dir / "f_######")
        info(f"Rendering animation sequence -> {SCENE.render.filepath}")
        bpy.ops.render.render(animation=True)
    info(f"Render complete in {time.time() - t0:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
