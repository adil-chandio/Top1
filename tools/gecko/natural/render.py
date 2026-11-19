"""Creature Edition picture-only workers. Only synthetic assets leave the workspace."""
import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import sys
import time

import bpy
from mathutils import Quaternion
ROOT=Path(__file__).resolve().parent
SOURCE=ROOT.parent / 'creature'
sys.path.insert(0,str(SOURCE))
from geometry import Animal, Eyes, W, eye_texture
from surface import iris_surface, simple, skin_surface
from filmlight import habitat, lighting, LamellarDigits

p=argparse.ArgumentParser()
p.add_argument('--poses',type=Path,default='.cache/monarch-gecko/natural/work/take.json')
p.add_argument('--out',type=Path,default='.cache/monarch-gecko/natural/picture/frames')
p.add_argument('--width',type=int,default=576)
p.add_argument('--samples',type=int,default=7)
p.add_argument('--threads',type=int,default=2)
sel=p.add_mutually_exclusive_group()
sel.add_argument('--stills');sel.add_argument('--range')
p.add_argument('--verbose',action='store_true')
a=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:])
if a.width<200 or a.width%2 or a.samples<1 or a.threads<1: p.error('Frame width must be even and at least 200; use positive samples and workers')
data=json.loads(a.poses.read_text()); take={s['frame']:s for s in data['take']}
frames=[int(n) for n in a.stills.split(',')] if a.stills else list(range(*map(int,a.range.split(':')))) if a.range else sorted(take)
if not frames or any(i not in take for i in frames):p.error('Only request frames designated for tracing')
a.out.mkdir(parents=True,exist_ok=True)
plate=SOURCE/'assets'/'conservatory.jpg'
h=hashlib.sha256()
for src in (a.poses,plate,*[SOURCE/f'{n}.py' for n in ['geometry','surface','habitat']],ROOT/'filmlight.py',Path(__file__)):
    h.update(src.read_bytes())
h.update(f'{a.width}:{a.samples}:{bpy.app.version_string}'.encode())
fingerprint=h.hexdigest();info=a.out/'picture.json';height=2*round(8*a.width/9)
if info.exists() and json.loads(info.read_text())['fingerprint']!=fingerprint: raise SystemExit('Use a fresh output directory for a different render fingerprint')
info.write_text(json.dumps({'fingerprint':fingerprint,'width':a.width,'height':height,'fps':data['fps'],'requested':len(frames)},indent=2)+'\n')

@contextmanager
def native_log():
    if a.verbose:
        yield
        return
    sys.stdout.flush();fd=os.dup(1)
    try:
        with (a.out/'cycles.log').open('w') as dst:
            os.dup2(dst.fileno(),1)
            yield
    finally:
        os.dup2(fd,1);os.close(fd)

bpy.ops.wm.read_factory_settings(use_empty=True)
s=bpy.context.scene;r=s.render;s.render.engine='CYCLES'
r.resolution_x=a.width;r.resolution_y=height;r.resolution_percentage=100;r.fps=data['fps'];r.threads_mode='FIXED';r.threads=a.threads
r.use_persistent_data=True;r.film_transparent=False;r.image_settings.file_format='PNG';r.image_settings.color_mode='RGB';r.image_settings.compression=9
cy=s.cycles;cy.samples=a.samples;cy.use_adaptive_sampling=True;cy.adaptive_threshold=.105;cy.adaptive_min_samples=min(4,a.samples)
cy.use_denoising=True;cy.denoising_input_passes='RGB_ALBEDO_NORMAL';cy.denoising_quality='BALANCED';cy.use_animated_seed=False
cy.diffuse_bounces=1;cy.glossy_bounces=1;cy.transmission_bounces=1;cy.transparent_max_bounces=4;cy.max_bounces=4
cy.sample_clamp_indirect=4.7;cy.light_sampling_threshold=.016
s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast';s.view_settings.exposure=.16
habitat(plate);lighting_at=lighting()
bpy.ops.object.camera_add();cam=bpy.context.object;s.camera=cam
cam.data.sensor_fit='VERTICAL';cam.data.sensor_height=28;cam.data.clip_start=.005;cam.data.clip_end=14
cam.data.dof.use_dof=True;cam.data.dof.aperture_blades=9
material=skin_surface()
# Stable single bind pose across every cut and across independently rendered shards.
bind=take[min(take)]
animal=Animal(bind,material);eye=Eyes(bind,material,iris_surface(eye_texture()),fade_ventral_bank=True)
feet=LamellarDigits(bind,skin_surface(with_pad_folds=True),simple('Fine restrained keratin tips','aa9c82',.58,Subsurface_Weight=.036))
wall=time.perf_counter()
for k,i in enumerate(frames):
    output=a.out/f'{i:04}.png'
    if output.is_file() and output.stat().st_size>=900:continue
    q=take[i];c=q['camera'];s.frame_set(i+1)
    animal.update(q);eye.update(q);clearance=feet.update(q);lighting_at(q)
    cam.location=W(c['place']);n=(W(c['aim'])-cam.location).normalized()
    cam.rotation_euler=(n.to_track_quat('-Z','Y') @ Quaternion((0,0,1),c.get('roll',0))).to_euler()
    cam.data.lens=c['focal'];cam.data.dof.focus_distance=max(.005,(W(c['focus'])-cam.location).dot(n));cam.data.dof.aperture_fstop=c['aperture']
    s.view_settings.exposure=.16+(.19 if c['side']=='beneath' else 0)
    r.filepath=str(output.with_suffix('.part.png').resolve());stamp=time.perf_counter()
    with native_log():bpy.ops.render.render(write_still=True)
    output.with_suffix('.part.png').rename(output)
    if a.stills or k%6==0 or k==len(frames)-1:
        print(f'{i:04} {q["shot"]:13} {i/24:6.3f}s · {time.perf_counter()-stamp:.2f}s/frame · elapsed {time.perf_counter()-wall:.1f}s · pane clearance {clearance:.4f}',flush=True)
