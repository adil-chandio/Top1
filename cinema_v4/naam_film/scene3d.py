"""NAAM LO — TRUE 3D look-dev stage (Blender/Cycles via bpy).
Run:  python3 scene3d.py <shot> <out.png> [res_scale] [samples]
Shots: hero · macro · xray · surfaceoff · wordmatter · mask
"""
import bpy, math, sys, os
from mathutils import Vector

D = os.path.dirname(os.path.abspath(__file__))
KEYED = os.path.join(D, "plates/char_keyed.png")

def clean():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def mat(name, base=(0.2, 0.2, 0.2), rough=0.5, metal=0.0, emit=None, emit_str=0.0, alpha=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*base, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = emit_str
    if alpha < 1:
        b.inputs["Alpha"].default_value = alpha
        m.blend_method = 'BLEND'
    return m

def box(name, size, loc, rot=(0,0,0), material=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object; o.name = name
    o.scale = (size[0]/2, size[1]/2, size[2]/2)
    if material: o.data.materials.append(material)
    return o

def plane(name, size, loc, rot=(0,0,0), material=None):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object; o.name = name
    o.scale = (size[0]/2, size[1]/2, 1)
    if material: o.data.materials.append(material)
    return o

def light(name, kind, loc, rot=(0,0,0), energy=500, size=2.0, color=(1,1,1), spot=45):
    d = bpy.data.lights.new(name, kind)
    d.energy = energy; d.color = color
    if kind == 'AREA': d.size = size
    if kind == 'SPOT':
        d.spot_size = math.radians(spot); d.spot_blend = 0.6
        d.shadow_soft_size = size
    o = bpy.data.objects.new(name, d); bpy.context.collection.objects.link(o)
    o.location = loc; o.rotation_euler = rot
    return o

# ------------------------------------------------------------------ world
def build_world(wire=False, fog=0.008):
    wood = mat("wood", (0.022, 0.015, 0.011), 0.5)
    plaster = mat("plaster", (0.055, 0.05, 0.048), 0.8)
    pn = plaster.node_tree
    pb = pn.nodes["Principled BSDF"]
    nz = pn.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 22.0
    nz.inputs["Detail"].default_value = 8.0
    bp = pn.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.35
    pn.links.new(nz.outputs["Fac"], bp.inputs["Height"])
    pn.links.new(bp.outputs["Normal"], pb.inputs["Normal"])
    card_m = mat("card", (0.34, 0.29, 0.20), 0.62)
    gold = mat("gold", (0.72, 0.52, 0.22), 0.28, metal=1.0)
    dark = mat("dark", (0.02, 0.02, 0.023), 0.6)

    o = []
    o.append(box("floor", (7, 7, 0.1), (0, 0, -0.05), material=wood))
    # back wall with a window gap
    o.append(box("wallL", (3.0, 0.12, 3.4), (-2.5, 2.1, 1.7), material=plaster))
    o.append(box("wallR", (3.0, 0.12, 3.4), (2.5, 2.1, 1.7), material=plaster))
    o.append(box("wallT", (2.0, 0.12, 2.1), (0.0, 2.1, 2.45), material=plaster))
    o.append(box("wallB", (2.0, 0.12, 1.6), (0.0, 2.1, 0.80), material=plaster))
    o.append(box("winGlow", (0.30, 0.02, 1.35), (-0.42, 2.34, 1.60),
                 material=mat("winglow", (0.5, 0.66, 0.9), 0.9, emit=(0.62, 0.78, 1.0), emit_str=3.0)))
    for bz in (0.95, 1.45, 1.95, 2.45):
        o.append(box("bar", (0.34, 0.05, 0.035), (-0.42, 2.20, bz),
                     material=mat("iron", (0.02,0.02,0.025), 0.4, metal=0.9)))
    # gold top card on the bundle (photographic texture)
    _gc = bpy.data.images.load(os.path.join(D, "plates/p01_cards.png"))
    gm = bpy.data.materials.new("goldcard"); gm.use_nodes = True
    gb = gm.node_tree.nodes["Principled BSDF"]
    gt = gm.node_tree.nodes.new("ShaderNodeTexImage"); gt.image = _gc
    gm.node_tree.links.new(gt.outputs["Color"], gb.inputs["Base Color"])
    gb.inputs["Roughness"].default_value = 0.32
    gb.inputs["Metallic"].default_value = 0.25
    # side wall for occlusion
    o.append(box("wallSide", (0.12, 4.2, 3.4), (-3.3, 0.4, 1.7), material=plaster))

    # table
    o.append(box("table", (1.7, 0.95, 0.06), (0, 0.35, 0.74), material=wood))
    for sx, sy in ((-1,-1),(1,-1),(-1,1),(1,1)):
        o.append(box("leg", (0.06, 0.06, 0.74), (sx*0.78, 0.35+sy*0.40, 0.37), material=wood))

    # the card bundle: 44 cards + red string
    for i in range(44):
        jitter = 0.004 * math.sin(i * 2.1)
        box(f"card{i}", (0.215, 0.145, 0.0035),
            (jitter, 0.34 + jitter*0.6, 0.775 + i * 0.0036),
            rot=(0.02*math.sin(i*0.7), 0.02*math.cos(i*0.9), 0.015*math.sin(i*1.3)),
            material=card_m)
    strm = mat("string", (0.30, 0.035, 0.025), 0.8)
    for k, z in enumerate((0.845, 0.905)):
        o.append(box("band" + str(k), (0.235, 0.165, 0.006), (0, 0.345, z), material=strm))
    o.append(box("stringR", (0.006, 0.166, 0.28), (0.0, 0.345, 0.90), material=strm))

    if wire:   # D2 surface-off
        for ob in o:
            m = ob.modifiers.new("wf", 'WIREFRAME'); m.thickness = 0.004
            em = mat("wire", (0.05, 0.7, 0.85), 0.4, emit=(0.06, 0.75, 0.95), emit_str=3.0)
            ob.data.materials.clear(); ob.data.materials.append(em)

    # volumetrics
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0.4, 2.0))
    vol = bpy.context.object; vol.name = "fog"; vol.scale = (14, 14, 9)
    vm = bpy.data.materials.new("fogmat"); vm.use_nodes = True
    nt = vm.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    vs = nt.nodes.new("ShaderNodeVolumeScatter")
    vs.inputs["Density"].default_value = fog
    vs.inputs["Color"].default_value = (0.75, 0.7, 0.62, 1)
    nt.links.new(vs.outputs[0], out.inputs["Volume"])
    vol.data.materials.append(vm)
    vol.visible_shadow = False

    # lights
    light("key", 'AREA', (-1.9, -1.3, 2.4), (math.radians(58), 0, math.radians(-40)),
          energy=520, size=2.0, color=(1.0, 0.70, 0.42))
    light("window", 'SPOT', (0.0, 3.2, 1.75), (math.radians(-78), 0, 0),
          energy=5200, size=0.05, color=(0.52, 0.70, 1.0), spot=26)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.035, location=(0.62, 0.18, 1.26))
    bpy.context.object.data.materials.append(mat("bulb", (1,0.8,0.5), 0.2, emit=(1.0,0.72,0.38), emit_str=40.0))
    light("practical", 'POINT', (0.55, 0.15, 1.32), energy=18, color=(1.0, 0.62, 0.30))
    light("rim", 'AREA', (0.75, 1.85, 1.75), (math.radians(-100), 0, math.radians(35)),
          energy=340, size=0.5, color=(0.48, 0.66, 1.0))
    light("edge", 'AREA', (-1.15, 0.55, 1.55), (math.radians(90), 0, math.radians(-72)),
          energy=90, size=0.35, color=(1.0, 0.78, 0.5))
    return o

def add_character(loc=(0, 1.35, 0), height=1.62, rotz=0.0, keyed=None):
    img = bpy.data.images.load(keyed or KEYED)
    m = bpy.data.materials.new("char"); m.use_nodes = True
    nt = m.node_tree; bsdf = nt.nodes["Principled BSDF"]
    tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = img
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Emission Color"])
    nt.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
    bsdf.inputs["Base Color"].default_value = (0.02, 0.02, 0.02, 1)
    bsdf.inputs["Emission Strength"].default_value = 0.62
    bsdf.inputs["Roughness"].default_value = 0.7
    bpy.ops.mesh.primitive_plane_add(size=1, location=(loc[0], loc[1], loc[2] + height/2),
                                     rotation=(math.radians(90), 0, rotz))
    o = bpy.context.object; o.name = "character"
    w = height * img.size[0] / img.size[1]
    o.scale = (w/2, height/2, 1)
    o.data.materials.append(m)
    return o

def add_ribcage(center=(0, 1.28, 1.16), scale=1.0, strength=14.0):
    bone = mat("bone", (0.55, 0.85, 0.95), 0.35, emit=(0.35, 0.85, 1.0), emit_str=strength)
    heart = mat("heart", (1.0, 0.15, 0.1), 0.3, emit=(1.0, 0.12, 0.06), emit_str=60.0)
    cx, cy, cz = center
    for i in range(7):                                   # rib arcs
        r = (0.13 + i*0.012) * scale
        z = cz + (0.10 - i*0.030) * scale
        bpy.ops.mesh.primitive_torus_add(location=(cx, cy, z),
                                         major_radius=r, minor_radius=0.0055*scale,
                                         major_segments=40, minor_segments=6,
                                         rotation=(math.radians(90), 0, 0))
        ob = bpy.context.object
        ob.scale = (1.0, 0.62, 1.0)
        ob.data.materials.append(bone)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.014*scale, depth=0.34*scale,
                                        location=(cx, cy - 0.02, cz + 0.02),
                                        rotation=(0, 0, 0))
    bpy.context.object.data.materials.append(bone)       # spine
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.045*scale, location=(cx + 0.02, cy - 0.05, cz - 0.05))
    h = bpy.context.object; h.data.materials.append(heart)
    light("heartlight", 'POINT', (cx + 0.02, cy - 0.12, cz - 0.05), energy=22, size=0.05,
          color=(1.0, 0.22, 0.12))

def add_dust(n=260, spread=(1.8, 1.4, 1.5), origin=(0, 0.4, 1.1)):
    m = mat("dust", (0.9, 0.85, 0.75), 0.4, emit=(1.0, 0.9, 0.75), emit_str=0.9)
    for i in range(n):
        import random
        x = origin[0] + random.uniform(-spread[0], spread[0])
        y = origin[1] + random.uniform(-spread[1], spread[1])
        z = origin[2] + random.uniform(-spread[2], spread[2])
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=random.uniform(0.0006, 0.0015),
                                              location=(x, y, z))
        bpy.context.object.data.materials.append(m)

# ------------------------------------------------------------------ camera / render
def camera(loc, look, lens=50, fstop=2.0, focus=None, shift=(0, 0)):
    cam = bpy.data.cameras.new("cam"); cam.lens = lens; cam.sensor_fit = 'VERTICAL'
    cam.sensor_height = 24.0; cam.shift_x, cam.shift_y = shift
    o = bpy.data.objects.new("cam", cam); bpy.context.collection.objects.link(o)
    o.location = loc
    d = Vector(look) - Vector(loc)
    o.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    if fstop:
        cam.dof.use_dof = True; cam.dof.aperture_fstop = fstop
        cam.dof.focus_distance = d.length if focus is None else focus
    bpy.context.scene.camera = o
    return o

def setup(res_scale=1.0, samples=48, exposure=-0.75):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 6
    sc.cycles.caustics_reflective = False
    sc.cycles.caustics_refractive = False
    sc.render.resolution_x = int(1080 * res_scale)
    sc.render.resolution_y = int(1920 * res_scale)
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = False
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.look = 'AgX - Medium High Contrast'
    sc.view_settings.exposure = exposure
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_depth = '16'
    # bloom is added in comp later (Blender 5 dropped scene.node_tree)
    return sc

# ------------------------------------------------------------------ shots
def shot_hero():
    build_world(); add_dust(240); add_character(loc=(0.06, 1.30, 0), height=1.58)
    # the gold card lying on top of the bundle, texture-mapped
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0.0, 0.34, 0.938),
                                     rotation=(0, 0, math.radians(2)))
    gtop = bpy.context.object; gtop.name = "goldtop"; gtop.scale = (0.115, 0.078, 1)
    gtop.data.materials.append(bpy.data.materials["goldcard"])
    for i, (fx, fy, rz, sy) in enumerate([(-0.62, -0.30, 14, 0.9), (0.55, -0.16, -22, 0.8)]):
        bpy.ops.mesh.primitive_plane_add(size=1, location=(fx, fy, 0.79 if i else 0.81),
                                        rotation=(math.radians(90), 0, math.radians(rz)))
        fo = bpy.context.object; fo.scale = (0.11 * sy, 0.075 * sy, 1)
        fo.data.materials.append(bpy.data.materials['plaster' if i else 'card'])
    camera((0.10, -1.62, 1.34), (-0.04, 0.95, 1.10), lens=55, fstop=1.6, focus=2.7)

def shot_macro():
    build_world(fog=0.05)
    # pencil
    pz = 0.93
    bpy.ops.mesh.primitive_cylinder_add(radius=0.006, depth=0.19, location=(0.06, 0.30, pz),
                                       rotation=(0, math.radians(78), 0))
    bpy.context.object.data.materials.append(mat("pencil", (0.55, 0.35, 0.12), 0.45))
    bpy.ops.mesh.primitive_cone_add(radius1=0.006, depth=0.028, location=(0.152, 0.30, pz - 0.090),
                                    rotation=(0, math.radians(78), 0))
    bpy.context.object.data.materials.append(mat("lead", (0.05, 0.05, 0.06), 0.3, metal=0.6))
    add_dust(420, spread=(0.7, 0.5, 0.4), origin=(0, 0.3, 0.95))
    camera((0.02, -0.62, 1.16), (0.06, 0.34, 0.92), lens=85, fstop=1.6, focus=0.34)

def shot_xray():
    build_world(fog=0.03); add_character(loc=(0, 1.35, 0), height=1.60)
    add_ribcage(center=(-0.02, 1.30, 1.14), scale=1.0, strength=9.0)
    camera((0.0, -0.95, 1.30), (0.0, 1.30, 1.18), lens=68, fstop=1.8, focus=2.25)

def shot_surfaceoff():
    build_world(wire=True, fog=0.05); add_dust(500)
    camera((0.05, -2.35, 1.42), (0.02, 0.9, 1.05), lens=46, fstop=1.8, focus=3.3)

def shot_wordmatter():
    build_world(fog=0.035)
    cu = bpy.data.curves.new("t", type='FONT'); cu.body = "LOG NAHI"
    cu.align_x = 'CENTER'; cu.extrude = 0.035; cu.size = 0.34
    ob = bpy.data.objects.new("txt", cu); bpy.context.collection.objects.link(ob)
    ob.data.materials.append(mat("em", (0.75, 0.10, 0.07), 0.35, metal=0.35,
                                 emit=(1.0, 0.22, 0.12), emit_str=2.2))
    ob.location = (0, 0.30, 1.30); ob.rotation_euler = (math.radians(74), 0, 0)
    # three fragments torn away
    for i, (dx, dy, dz, rz) in enumerate([(-0.30, -0.10, 0.12, 18), (0.26, -0.05, 0.20, -26), (0.02, -0.02, 0.34, 8)]):
        cu2 = bpy.data.curves.new(f"f{i}", type='FONT'); cu2.body = ["NA","HI","LO"][i]
        cu2.align_x = 'CENTER'; cu2.extrude = 0.03; cu2.size = 0.20
        o2 = bpy.data.objects.new(f"f{i}", cu2); bpy.context.collection.objects.link(o2)
        o2.data.materials.append(mat(f"em{i}", (0.7, 0.1, 0.07), 0.4, emit=(1.0, 0.25, 0.12), emit_str=1.6))
        o2.location = (dx, 0.28 + dy, 1.30 + dz); o2.rotation_euler = (math.radians(70), 0, math.radians(rz))
    camera((0.0, -1.35, 1.26), (0, 0.30, 1.34), lens=58, fstop=2.2, focus=1.6)

def shot_mask():
    build_world(fog=0.02)
    add_character(loc=(0, 0.55, 0), height=1.66)
    # red band behind the subject
    box("band", (2.6, 0.02, 0.16), (0, 0.95, 1.62),
        material=mat("band", (0.8, 0.05, 0.03), 0.6, emit=(1.0, 0.08, 0.04), emit_str=12.0))
    light("bandl", 'AREA', (0, 0.9, 1.55), (math.radians(90), 0, 0), energy=180, size=1.6,
          color=(1.0, 0.12, 0.06))
    camera((0.0, -0.55, 1.42), (0.0, 0.55, 1.40), lens=95, fstop=1.4, focus=1.10)


def photo_plane(path, y, w, h, z=None, emit=1.0):
    img = bpy.data.images.load(path)
    m = bpy.data.materials.new("ph_" + os.path.basename(path)); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = img
    nt.links.new(t.outputs["Color"], b.inputs["Emission Color"])
    b.inputs["Base Color"].default_value = (0.01, 0.01, 0.01, 1)
    b.inputs["Emission Strength"].default_value = emit
    nt.links.new(t.outputs["Alpha"], b.inputs["Alpha"])
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, y, h/2 if z is None else z),
                                     rotation=(math.radians(90), 0, 0))
    o = bpy.context.object; o.scale = (w/2, h/2, 1)
    o.data.materials.append(m)
    return o

def shot_d1():
    """D1 PHOTO-TO-FLESH on a photographic stage: plate behind, keyed subject,
    real 3D ribcage + emissive heart lighting the jaw, real DOF, real shaft."""
    build_world(fog=0.0025)
    for ob in list(bpy.data.objects):
        if ob.type in ('MESH',) and ob.name not in ('floor',):
            if ob.name.startswith(("wall", "win", "bar", "table", "leg", "card", "band", "string")):
                bpy.data.objects.remove(ob, do_unlink=True)
    photo_plane(os.path.join(D, "plates/p01_cards.png"), 2.6, 3.4, 4.6, z=2.3, emit=0.42)
    add_character(loc=(0.02, 1.15, 0), height=1.66,
                  keyed=os.path.join(D, "plates/char_xray.png"))
    add_ribcage(center=(0.0, 1.215, 1.06), scale=0.62, strength=6.0)
    add_dust(200, spread=(0.9, 0.7, 0.8), origin=(0, 0.8, 1.2))
    light("key2", 'AREA', (-1.3, 0.15, 2.0), (math.radians(68), 0, math.radians(-58)),
          energy=150, size=1.1, color=(1.0, 0.72, 0.44))
    light("rim2", 'AREA', (0.95, 1.55, 1.62), (math.radians(-96), 0, math.radians(52)),
          energy=300, size=0.45, color=(0.46, 0.66, 1.0))
    camera((0.0, -1.05, 1.32), (0.0, 1.15, 1.24), lens=72, fstop=1.6, focus=2.2)

SHOTS = dict(hero=shot_hero, macro=shot_macro, xray=shot_xray,
             surfaceoff=shot_surfaceoff, wordmatter=shot_wordmatter, mask=shot_mask)
SHOTS['d1'] = shot_d1

if __name__ == "__main__":
    shot = sys.argv[1]; out = sys.argv[2]
    rs = float(sys.argv[3]) if len(sys.argv) > 3 else 0.5
    spp = int(sys.argv[4]) if len(sys.argv) > 4 else 32
    clean(); SHOTS[shot]()
    sc = setup(rs, spp)
    sc.render.filepath = out
    bpy.ops.render.render(write_still=True)
    print("WROTE", out)
