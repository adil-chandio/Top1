"""NAAM // PRIME — true-3D macro stage (Cycles CPU).

Renders beauty + Z depth for the shots where real geometry matters:
  edge   : gold card slab edge with red string, raking key, extreme DOF
  shards : gold shards + string fragments exploding in a black void
  type   : extruded gold NAAM lettering in fog, red rim

Usage:
  LD_LIBRARY_PATH=/tmp/xstub /tmp/venv/bin/python scene3d.py <shot> <outdir> <scale> <spp>
Writes <outdir>/<shot>_beauty.png and <outdir>/<shot>_z.png
"""
import bpy, math, os, sys, random

random.seed(7)

GOLD = (0.62, 0.44, 0.13)
RED = (0.40, 0.022, 0.016)


def clean():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def mat(name, color, rough=0.3, metal=1.0, emit=None, estr=0.0, alpha=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = estr
    if alpha < 1:
        b.inputs["Alpha"].default_value = alpha
    return m


def box(name, size, loc, rot=(0, 0, 0), m=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if m:
        o.data.materials.append(m)
    return o


def cyl(name, r, depth, loc, rot=(0, 0, 0), m=None, verts=32):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, location=loc,
                                        rotation=rot, vertices=verts)
    o = bpy.context.object
    o.name = name
    if m:
        o.data.materials.append(m)
    return o


def torus(name, R, r, loc, rot=(0, 0, 0), m=None):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r,
                                     location=loc, rotation=rot,
                                     major_segments=64, minor_segments=12)
    o = bpy.context.object
    o.name = name
    if m:
        o.data.materials.append(m)
    return o


def light(name, kind, loc, rot, energy, size=1.0, color=(1, 1, 1), angle=None):
    d = bpy.data.lights.new(name, kind)
    d.energy = energy
    d.color = color
    if kind == 'AREA':
        d.size = size
    if angle is not None and kind == 'SPOT':
        d.spot_size = math.radians(angle)
        d.spot_blend = 0.35
    o = bpy.data.objects.new(name, d)
    bpy.context.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = rot
    return o


def flags():
    """Out-of-frame studio flags so metals have something to reflect."""
    m1 = mat("flagw", (0.0, 0.0, 0.0), rough=1.0, metal=0.0,
             emit=(1.0, 0.62, 0.30), estr=3.5)
    m2 = mat("flagc", (0.0, 0.0, 0.0), rough=1.0, metal=0.0,
             emit=(0.35, 0.55, 1.0), estr=1.6)
    m3 = mat("flagf", (0.0, 0.0, 0.0), rough=1.0, metal=0.0,
             emit=(1.0, 0.86, 0.70), estr=2.4)
    box("flagL", (0.02, 1.2, 1.2), (-0.85, -0.35, 0.30), m=m1)
    box("flagR", (0.02, 1.0, 1.0), (0.80, 0.40, 0.35), m=m2)
    box("flagF", (1.5, 0.02, 1.5), (0.0, -1.30, 0.20), m=m3)


def world_black():
    w = bpy.data.worlds.new("w")
    bpy.context.scene.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.0, 0.0, 0.0, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 1.0


def fog_cube(density=0.03, loc=(0, 0, 0), scale=(6, 6, 6)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object
    o.name = "fog"
    o.scale = scale
    m = bpy.data.materials.new("fogvol")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    v = nt.nodes.new("ShaderNodeVolumePrincipled")
    v.inputs["Density"].default_value = density
    v.inputs["Color"].default_value = (0.95, 0.93, 0.9, 1)
    v.inputs["Anisotropy"].default_value = 0.35
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(v.outputs[0], out.inputs["Volume"])
    o.data.materials.append(m)
    o.visible_shadow = False
    return o


def dust(n=140, spread=(0.35, 0.35, 0.3), origin=(0, 0, 0)):
    m = bpy.data.materials.new("dustm")
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (1, 0.95, 0.85, 1)
    b.inputs["Emission Color"].default_value = (1, 0.93, 0.8, 1)
    b.inputs["Emission Strength"].default_value = 0.8
    b.inputs["Roughness"].default_value = 0.6
    for i in range(n):
        p = (origin[0] + random.uniform(-spread[0], spread[0]),
             origin[1] + random.uniform(-spread[1], spread[1]),
             origin[2] + random.uniform(-spread[2], spread[2]))
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=random.uniform(0.00018, 0.0005),
                                              location=p)
        o = bpy.context.object
        o.name = f"dust{i}"
        o.data.materials.append(m)


def camera(loc, look, lens=100, fstop=2.8, focus=None, roll=0.0):
    cd = bpy.data.cameras.new("cam")
    cd.lens = lens
    cd.sensor_width = 36
    cd.dof.use_dof = True
    cd.dof.aperture_fstop = fstop
    cd.dof.focus_distance = focus if focus else (loc[0]**2 + loc[1]**2 + loc[2]**2) ** 0.5
    ob = bpy.data.objects.new("cam", cd)
    bpy.context.collection.objects.link(ob)
    bpy.context.scene.camera = ob
    ob.location = loc
    d = [look[i] - loc[i] for i in range(3)]
    import mathutils
    v = mathutils.Vector(d)
    ob.rotation_euler = v.to_track_quat('-Z', 'Y').to_euler()
    ob.rotation_euler.rotate_axis('Z', roll)
    return ob


def setup(scale=1.0, spp=32, exposure=0.0, res=(1080, 1920)):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = spp
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 6
    sc.cycles.transmission_bounces = 4
    sc.cycles.caustics_reflective = False
    sc.cycles.caustics_refractive = False
    sc.render.resolution_x = int(res[0] * scale)
    sc.render.resolution_y = int(res[1] * scale)
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = False
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_depth = '16'
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.look = 'AgX - Medium High Contrast'
    sc.view_settings.exposure = exposure
    sc.view_layers[0].use_pass_z = True
    return sc


# ---------------------------------------------------------------- shots

def shot_edge():
    """Macro: gold slab edge, red string binding, hard raking key."""
    gold = mat("gold", GOLD, rough=0.46)
    gold_r = mat("goldr", GOLD, rough=0.60)
    ff = bpy.data.materials.get("flagf")
    if ff:
        ff.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 0.06
    red = mat("redstr", RED, rough=0.55, metal=0.0)
    # card stack: 30 thin slabs with jitter
    for i in range(64):
        z = 0.0021 * 0.5 + i * 0.0021
        box(f"c{i}", (0.115, 0.082, 0.00205),
            (random.uniform(-0.0008, 0.0008), random.uniform(-0.0008, 0.0008), z),
            rot=(0, 0, random.uniform(-0.008, 0.008)),
            m=gold if i % 4 else gold_r)
    # red string: bands hugging the block on all four sides
    for i, zz in enumerate((0.034, 0.088)):
        w, d = 0.1156, 0.0826
        box(f"sf{i}", (w + 0.003, 0.0016, 0.0034), (0, -d/2, zz), m=red)
        box(f"sb{i}", (w + 0.003, 0.0016, 0.0034), (0, d/2, zz), m=red)
        box(f"sl{i}", (0.0016, d, 0.0034), (-w/2, 0, zz), m=red)
        box(f"sr{i}", (0.0016, d, 0.0034), (w/2, 0, zz), m=red)
    for i, (loc, sz) in enumerate((((0, 0, 0.1345), (0.010, 0.086, 0.0012)),
                                   ((0, 0, 0.1345), (0.118, 0.010, 0.0012)))):
        box(f"strap{i}", sz, loc, m=red)
    # a second stack behind, out of focus
    for i in range(40):
        box(f"b{i}", (0.11, 0.08, 0.0021), (0.24, 0.05, i * 0.0021), m=gold_r)
    fog_cube(0.020, loc=(0, 0, 0.05), scale=(9.0, 9.0, 7.0))
    dust(120, spread=(0.16, 0.16, 0.10), origin=(0.0, -0.02, 0.05))
    light("key", 'AREA', (-0.46, -0.22, 0.26), (math.radians(66), 0, math.radians(-52)),
          energy=26, size=0.20, color=(1.0, 0.70, 0.38))
    light("rim", 'AREA', (0.34, 0.20, 0.16), (math.radians(-84), 0, math.radians(48)),
          energy=10, size=0.14, color=(1.0, 0.24, 0.12))
    camera((-0.19, -0.42, 0.17), (0.0, 0.0, 0.065), lens=72, fstop=4.0, focus=0.47)


def shot_shards():
    """Gold shards + string fragments exploding in a black void."""
    gold = mat("gold", GOLD, rough=0.18)
    red = mat("redstr", RED, rough=0.6, metal=0.0)
    for i in range(120):
        r = random.uniform(0.0, 0.30) ** 0.8
        th = random.uniform(0, math.tau)
        ph = math.acos(random.uniform(-1, 1))
        p = (r * math.sin(ph) * math.cos(th),
             r * math.cos(ph) * 0.5 + 0.06,
             r * math.sin(ph) * math.sin(th) * 0.9 + 0.10)
        s = random.uniform(0.006, 0.034)
        box(f"s{i}", (s, s * random.uniform(0.3, 1.0), s * 0.10), p,
            rot=(random.uniform(0, 6), random.uniform(0, 6), random.uniform(0, 6)),
            m=gold)
    for i in range(26):
        r = random.uniform(0.02, 0.26)
        p = (random.uniform(-r, r), random.uniform(-r, r) * 0.5 + 0.06,
             random.uniform(-r, r) * 0.8 + 0.10)
        cyl(f"r{i}", 0.0009, random.uniform(0.01, 0.08), p,
            rot=(random.uniform(0, 6), random.uniform(0, 6), random.uniform(0, 6)), m=red)
    fog_cube(0.022, loc=(0, 0.05, 0.12), scale=(9.0, 9.0, 7.0))
    dust(90, spread=(0.3, 0.2, 0.25), origin=(0, 0.05, 0.12))
    light("key", 'AREA', (-0.30, -0.34, 0.34), (math.radians(58), 0, math.radians(-40)),
          energy=70, size=0.22, color=(1.0, 0.78, 0.5))
    light("rim", 'AREA', (0.30, 0.22, 0.14), (math.radians(-80), 0, math.radians(40)),
          energy=22, size=0.16, color=(1.0, 0.18, 0.10))
    camera((0.0, -0.52, 0.16), (0.0, 0.05, 0.11), lens=58, fstop=2.0, focus=0.52)


def shot_type(word="NAAM"):
    """Extruded metal lettering standing in fog."""
    gold = mat("gold", GOLD, rough=0.16)
    bpy.ops.object.text_add(location=(0.0, 0.0, 0.058), rotation=(math.radians(90), 0, 0))
    t = bpy.context.object
    t.data.body = word
    t.data.align_x = 'CENTER'
    t.data.align_y = 'CENTER'
    t.data.size = 0.026
    t.data.space_character = 1.22
    t.data.extrude = 0.0045
    t.data.bevel_depth = 0.0012
    t.data.bevel_resolution = 3
    t.data.font = bpy.data.fonts.load(
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf")
    t.data.materials.append(gold)
    fog_cube(0.030, loc=(0, 0.10, 0.06), scale=(9.0, 9.0, 7.0))
    dust(46, spread=(0.34, 0.18, 0.18), origin=(0, 0.0, 0.08))
    light("key", 'AREA', (-0.26, -0.26, 0.20), (math.radians(64), 0, math.radians(-40)),
          energy=42, size=0.24, color=(1.0, 0.74, 0.46))
    light("rim", 'AREA', (0.24, 0.16, 0.10), (math.radians(-84), 0, math.radians(44)),
          energy=9, size=0.12, color=(1.0, 0.16, 0.10))
    camera((0.0, -0.50, 0.058), (0.0, 0.0, 0.058), lens=95, fstop=4.0, focus=0.50)


SHOTS = {"edge": shot_edge, "shards": shot_shards, "type": shot_type}


def render_depth(outdir, shot, near=0.15, far=1.4):
    """Second pass: View-Z rendered as emission, normalised to 0..1 => <shot>_z.png"""
    sc = bpy.context.scene
    m = bpy.data.materials.new("dmat")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    cd = nt.nodes.new("ShaderNodeCameraData")
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = near
    mr.inputs["From Max"].default_value = far
    mr.inputs["To Min"].default_value = 1.0
    mr.inputs["To Max"].default_value = 0.0
    em = nt.nodes.new("ShaderNodeEmission")
    out = nt.nodes.get("Material Output") or nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(cd.outputs["View Z Depth"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], em.inputs["Color"])
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.name not in ("fog",):
            o.data.materials.clear()
            o.data.materials.append(m)
    sc.world.node_tree.nodes["Background"].inputs[1].default_value = 0.0
    sc.cycles.samples = 4
    sc.cycles.use_denoising = False
    sc.view_settings.view_transform = 'Standard'
    sc.view_settings.look = 'None'
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_depth = '8'
    sc.render.filepath = os.path.join(outdir, f"{shot}_z.png")
    bpy.ops.render.render(write_still=True)
    print("WROTE", sc.render.filepath)


def main_all():
    """render every shot: beauty + depth"""
    outdir, scale, spp = sys.argv[2], float(sys.argv[3]), int(sys.argv[4])
    for name in SHOTS:
        clean(); world_black(); setup(scale, spp); flags(); SHOTS[name]()
        bpy.context.scene.render.filepath = os.path.join(outdir, f"{name}_beauty.png")
        bpy.ops.render.render(write_still=True)
        print("WROTE", bpy.context.scene.render.filepath)
        render_depth(outdir, name)


def main():
    shot = sys.argv[1] if len(sys.argv) > 1 else "edge"
    outdir = sys.argv[2] if len(sys.argv) > 2 else "build"
    scale = float(sys.argv[3]) if len(sys.argv) > 3 else 0.5
    spp = int(sys.argv[4]) if len(sys.argv) > 4 else 32
    os.makedirs(outdir, exist_ok=True)
    clean()
    world_black()
    setup(scale, spp)
    flags()
    SHOTS[shot]()
    sc = bpy.context.scene
    sc.render.filepath = os.path.join(outdir, f"{shot}_beauty.png")
    bpy.ops.render.render(write_still=True)
    print("WROTE", sc.render.filepath)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "all":
        main_all()
    else:
        main()
