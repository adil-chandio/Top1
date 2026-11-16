#!/usr/bin/env python3
"""
MONARCH® PANAMA-PLUS 3D CINEMA RIG (Blender 4.2+)
Drop-in lighting, camera, AgX color, volumetric atmosphere, and 1080x1920 @ 30fps
render setup for Sketchfab/PolyHaven .glb/.gltf assets inside Monarch.Overall.Work.

Rule: NEVER sculpt hero animals/humans/ships from math primitives.
Load real .glb meshes via `load_glb_asset()` and let this rig light & shoot them
at cinema quality.
"""
from __future__ import annotations

import math
import os
from typing import Optional


def configure_cinema_render(
    bpy,
    width: int = 1080,
    height: int = 1920,
    fps: int = 30,
    samples: int = 64,
    prefer_gpu: bool = True,
) -> str:
    """Configure Blender Cycles (CUDA/OPTIX on Kaggle T4, or denoised CPU fallback) + AgX."""
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = 100
    scene.render.fps = fps

    # Cinema color management (AgX gives rich highlights without plastic clipping)
    view_settings = scene.view_settings
    try:
        view_settings.view_transform = "AgX"
        view_settings.look = "AgX - Medium High Contrast"
    except Exception:
        view_settings.view_transform = "Filmic"
        view_settings.look = "Medium High Contrast"
    view_settings.exposure = 0.15

    cycles = scene.cycles
    cycles.samples = samples
    cycles.use_adaptive_sampling = True
    cycles.adaptive_threshold = 0.02
    cycles.use_denoising = True
    cycles.max_bounces = 6
    cycles.diffuse_bounces = 3
    cycles.glossy_bounces = 3
    cycles.transmission_bounces = 4
    cycles.volume_bounces = 1
    cycles.sample_clamp_indirect = 8.0

    # Motion blur makes 30fps 3D animation feel fluid like real cinema
    scene.render.use_motion_blur = True
    scene.render.motion_blur_shutter = 0.45

    backend = "CPU"
    if prefer_gpu:
        try:
            prefs = bpy.context.preferences.addons["cycles"].preferences
            for device_type in ("OPTIX", "CUDA"):
                prefs.compute_device_type = device_type
                prefs.get_devices()
                gpu_devices = [d for d in prefs.devices if d.type == device_type]
                if gpu_devices:
                    for d in prefs.devices:
                        d.use = (d.type == device_type)
                    cycles.device = "GPU"
                    backend = f"GPU:{device_type}"
                    break
        except Exception:
            cycles.device = "CPU"

    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    return backend


def load_glb_asset(bpy, filepath: str, name: str, target_height: float = 2.5):
    """Import a real .glb/.gltf model, join into a parent Empty, and normalize scale."""
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"Missing 3D asset: {filepath}")

    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=filepath)
    imported = [obj for obj in bpy.data.objects if obj not in before]

    root = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(root)

    meshes = [o for o in imported if o.type == "MESH"]
    for obj in imported:
        if obj.parent is None:
            obj.parent = root

    if meshes:
        min_z = min(min((o.matrix_world @ v.co).z for v in o.data.vertices) for o in meshes if o.data.vertices)
        max_z = max(max((o.matrix_world @ v.co).z for v in o.data.vertices) for o in meshes if o.data.vertices)
        span = max(max_z - min_z, 1e-4)
        scale = target_height / span
        root.scale = (scale, scale, scale)
        bpy.context.view_layer.update()

    return root


def setup_three_point_rim_lighting(
    bpy,
    target_pos=(0.0, 0.0, 1.0),
    key_color=(1.0, 0.94, 0.86),
    rim_color=(0.25, 0.65, 1.0),
    fill_color=(0.35, 0.45, 0.65),
    key_energy: float = 850.0,
    rim_energy: float = 1200.0,
):
    """Create cinema Key + Cool Rim + Soft Fill lights aimed at target_pos."""
    from mathutils import Vector

    target = Vector(target_pos)

    def add_area(name: str, loc, energy: float, size: float, color):
        light_data = bpy.data.lights.new(name=name, type="AREA")
        light_data.energy = energy
        light_data.size = size
        light_data.color = color
        light_obj = bpy.data.objects.new(name=name, object_data=light_data)
        bpy.context.scene.collection.objects.link(light_obj)
        light_obj.location = Vector(loc)
        direction = target - light_obj.location
        light_obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
        return light_obj

    key = add_area("MONARCH_KeyLight", (4.5, -4.0, 5.0), key_energy, 3.0, key_color)
    rim = add_area("MONARCH_RimLight", (-3.5, 4.5, 3.2), rim_energy, 2.2, rim_color)
    fill = add_area("MONARCH_FillLight", (-4.5, -2.5, 2.0), key_energy * 0.28, 5.0, fill_color)
    return key, rim, fill


def add_volumetric_atmosphere(bpy, density: float = 0.014, color=(0.12, 0.18, 0.26)):
    """Add subtle volumetric scatter to the World shader for cinematic depth rays."""
    world = bpy.context.scene.world
    if world is None:
        world = bpy.data.worlds.new("MONARCH_World")
        bpy.context.scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()

    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs["Color"].default_value = (*color, 1.0)
    bg.inputs["Strength"].default_value = 0.45

    vol = nt.nodes.new("ShaderNodeVolumeScatter")
    vol.inputs["Color"].default_value = (0.75, 0.85, 1.0, 1.0)
    vol.inputs["Density"].default_value = density
    vol.inputs["Anisotropy"].default_value = 0.55

    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    nt.links.new(vol.outputs["Volume"], out.inputs["Volume"])


def create_cinema_camera(
    bpy,
    name: str = "MONARCH_Cam",
    lens_mm: float = 35.0,
    fstop: float = 2.8,
    focus_target: Optional[object] = None,
):
    """Create a tracked cinema camera with shallow Depth of Field."""
    cam_data = bpy.data.cameras.new(name=name)
    cam_data.lens = lens_mm
    cam_data.dof.use_dof = True
    cam_data.dof.aperture_fstop = fstop
    if focus_target is not None:
        cam_data.dof.focus_object = focus_target

    cam_obj = bpy.data.objects.new(name, cam_data)
    bpy.context.scene.collection.objects.link(cam_obj)
    bpy.context.scene.camera = cam_obj

    if focus_target is not None:
        track = cam_obj.constraints.new(type="TRACK_TO")
        track.target = focus_target
        track.track_axis = "TRACK_NEGATIVE_Z"
        track.up_axis = "UP_Y"

    return cam_obj


def add_handheld_micro_shake(cam_obj, frame_start: int, frame_end: int, amp: float = 0.025):
    """Keyframe subtle organic camera breathing so shots never look dead/static."""
    base_loc = cam_obj.location.copy()
    for f in range(frame_start, frame_end + 1, 6):
        t = f * 0.19
        cam_obj.location = (
            base_loc.x + math.sin(t) * amp,
            base_loc.y + math.cos(t * 0.73) * amp * 0.6,
            base_loc.z + math.sin(t * 1.31) * amp * 0.8,
        )
        cam_obj.keyframe_insert(data_path="location", frame=f)
