"""Frame-locked Blender 4.3 CPU proof. Images stay in an ignored output directory."""
import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import sys
import time

import bpy
from geometry import Animal, Digits, Eyes, W, eye_texture
from habitat import light, setup_habitat
from surface import iris_surface, simple, skin_surface

ROOT=Path(__file__).resolve().parent
p=argparse.ArgumentParser()
p.add_argument('--poses',default='.cache/monarch-gecko/creature/poses/take.json',type=Path)
p.add_argument('--out',default='.cache/monarch-gecko/creature/render',type=Path)
p.add_argument('--width',type=int,default=576)
p.add_argument('--samples',type=int,default=12)
p.add_argument('--stills',help='comma-separated frame indexes')
p.add_argument('--range',help='first:end-exclusive')
p.add_argument('--threads',type=int,default=2)
p.add_argument('--verbose',action='store_true')
a=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:])
data=json.loads(a.poses.read_text()); take=data['take']
if a.stills and a.range: p.error('Choose --stills or --range, not both')
requested=[int(v) for v in a.stills.split(',')] if a.stills else list(range(*map(int,a.range.split(':')))) if a.range else list(range(len(take)))
if not requested or min(requested)<0 or max(requested)>=len(take): p.error('Frame selection outside take')
if a.width<200 or a.width%2 or a.samples<1 or a.threads<1: p.error('Choose an even width >= 200, positive samples and threads')


@contextmanager
def render_log(path):
    if a.verbose:
        yield
        return
    # Keep Blender's native progress output available without flooding the job log.
    sys.stdout.flush(); saved=os.dup(1)
    try:
        with open(path,'w') as dst:
            os.dup2(dst.fileno(),1)
            yield
    finally:
        os.dup2(saved,1);os.close(saved)


a.out.mkdir(parents=True,exist_ok=True)
plate=ROOT/'assets'/'conservatory.jpg'
h=hashlib.sha256()
for src in (a.poses,plate,*(ROOT/s for s in ('render.py','surface.py','geometry.py','habitat.py'))):
    h.update(src.read_bytes())
h.update(f'{a.width},{a.samples},{bpy.app.version_string}'.encode())
source=h.hexdigest(); receipt=a.out/'picture.json'
if receipt.exists() and json.loads(receipt.read_text())['fingerprint']!=source:
    raise SystemExit('Output contains a different take/render fingerprint; use a new --out directory')
width,height=a.width,int(round(a.width*16/18)*2)
receipt.write_text(json.dumps({'fingerprint':source,'width':width,'height':height,'fps':data['fps'],'frames':len(take),'samples':a.samples},indent=2)+'\n')

bpy.ops.wm.read_factory_settings(use_empty=True)
s=bpy.context.scene
s.render.engine='CYCLES'
s.render.resolution_percentage=100;s.render.resolution_x=width;s.render.resolution_y=height
s.render.fps=data['fps'];s.render.threads_mode='FIXED';s.render.threads=a.threads
s.render.use_persistent_data=True;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB';s.render.image_settings.compression=12
s.render.film_transparent=False
s.cycles.samples=a.samples;s.cycles.use_adaptive_sampling=True;s.cycles.adaptive_threshold=.092;s.cycles.adaptive_min_samples=min(6,a.samples)
s.cycles.use_denoising=True;s.cycles.denoising_input_passes='RGB_ALBEDO_NORMAL';s.cycles.denoising_quality='BALANCED';s.cycles.use_animated_seed=False
s.cycles.diffuse_bounces=1;s.cycles.glossy_bounces=1;s.cycles.transmission_bounces=1;s.cycles.transparent_max_bounces=4;s.cycles.max_bounces=4
s.cycles.sample_clamp_indirect=4.5
s.cycles.light_sampling_threshold=.016
s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast';s.view_settings.exposure=.15

setup_habitat(plate);light()
bpy.ops.object.camera_add();cam=bpy.context.object;s.camera=cam
cam.name='Uncut macro dolly';cam.data.sensor_fit='VERTICAL';cam.data.sensor_height=28;cam.data.clip_start=.008;cam.data.clip_end=11.
cam.data.dof.use_dof=True;cam.data.dof.aperture_blades=9
skin=skin_surface()
animal=Animal(take[0],skin)
feet=Digits(take[0],skin,simple('Fine amber-grey claw keratin','9e9175',.53,Subsurface_Weight=.050))
eye=Eyes(take[0],skin,iris_surface(eye_texture()))

started=time.perf_counter()
for j in requested:
    path=a.out/f'{j:04d}.png'
    if path.is_file() and path.stat().st_size>900: continue
    q=take[j]
    s.frame_set(j+1)
    animal.update(q);eye.update(q);min_z=feet.update(q)
    c=q['camera'];cam.location=W(c['place']);orient=(W(c['aim'])-cam.location).normalized()
    cam.rotation_euler=orient.to_track_quat('-Z','Y').to_euler()
    cam.data.lens=c['focal'];cam.data.dof.aperture_fstop=c['aperture'];cam.data.dof.focus_distance=max(.003,(W(c['focus'])-cam.location).dot(orient))
    partial=path.with_suffix('.part.png');s.render.filepath=str(partial.resolve())
    stamp=time.perf_counter()
    with render_log(a.out/'cycles.log'):
        bpy.ops.render.render(write_still=True)
    partial.rename(path)
    if a.stills or j%12==0 or j==requested[-1]:
        print(f'Frame {j:03}/{len(take)-1} · {q["t"]:.3f}s · {time.perf_counter()-stamp:.2f}s/frame · elapsed {time.perf_counter()-started:.1f}s · pad clearance {min_z:.4f}',flush=True)
