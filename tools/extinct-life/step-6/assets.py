#!/usr/bin/env python3
"""Rebuild the original Full Cut data; the opening approvals are never modified."""
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

HERE=Path(__file__).resolve().parent
S5=HERE.parent/'step-5'; C2=S5/'cinema-v2'
sys.path.insert(0,str(C2))
import geometry as pilot
from geometry import base, FONTS
from sound import FOL_LOCK

HOME=base.ATL/'film'; FIELDS=HOME/'fields'; AUDIO=HOME/'foley'; OUT=base.ROOT/'deliverables/extinct-life-step-6'
SOURCE=base.ROOT/'deliverables/extinct-life-step-3'; LOCK=json.loads((HERE.parent/'step-3/vo-v2-receipt.json').read_text())
VO=SOURCE/LOCK['files'][0]['file']; SRT=SOURCE/LOCK['files'][1]['file']
SCRIPT=HERE.parent/'step-2/Extinct-Life-Atlantic-Tracks-Script-v2.md'


def media_lock():
    for f in LOCK['files']:
        path=SOURCE/f['file']; assert path.stat().st_size==f['size'] and base.hashfile(path)==f['sha256'],path
    # The repository copy removes only private archive links from the approved script.
    assert base.hashfile(SCRIPT) in (LOCK['script_sha256'], LOCK.get('repository_script_sha256'))


def download(dst,repo,ref,path,h=None):
    if dst.is_file() and (not h or base.hashfile(dst)==h):return
    dst.parent.mkdir(parents=True,exist_ok=True)
    raw=subprocess.check_output(['gh','api','-H','Accept: application/vnd.github.raw+json',f'repos/{repo}/contents/{path}?ref={ref}'],timeout=40)
    if h:assert sha256(raw).hexdigest()==h,(dst,len(raw),sha256(raw).hexdigest())
    p=dst.with_suffix('.partial');p.write_bytes(raw);p.replace(dst)
    print('ASSET',dst.name,len(raw),flush=True)


def fetch():
    jobs=[(base.DATA/name,repo,ref,src,h) for name,repo,ref,src,h in base.GEODATA]
    path=HERE.parent/'step-2/map-sources.json'
    for m in json.loads(path.read_text())['inputs']:
        if m['name']!='ne_110m_land.geojson':jobs.append((base.ATL/'sources'/m['name'],m['repository'],m['ref'],m['path'],m['sha256']))
    fonts=json.loads((HERE.parent/'step-4/asset-lock.json').read_text())
    for f in fonts['fonts']:
        jobs.append((FONTS/f['file'],fonts['font_source'],fonts['font_ref'],f['path'].replace('[','%5B').replace(']','%5D'),f['sha256']))
        jobs.append((FONTS/(Path(f['file']).stem+'-OFL.txt'),fonts['font_source'],fonts['font_ref'],f['license_path'],None))
    bank='evanlin23/blocky-stories'; ref='328f356539d059f360175b66f3a88b2ba78e7c91'
    for i,h in FOL_LOCK.items():jobs.append((AUDIO/f'gravel_{i}.wav',bank,ref,f'assets/audio/steps/gravel/gravel_{i}.wav',h))
    jobs.append((AUDIO/'kenney-rpg-license.txt',bank,ref,'assets/licenses/kenney_rpg-audio_License.txt','5735dfd72cb64cbbceda4ebc00c380c41ca680edb82ff153aa7c9ab97614c539'))
    with ThreadPoolExecutor(max_workers=5) as p:list(p.map(lambda t:download(*t),jobs))


def material(key,n):
    # Purpose-made mineral albedo. Colour, flecks and strata are not photographs
    # of either locality; relief and depressions are separate world geometry.
    warm=key=='warm'; seed=9087 if warm else 8876
    a=base.gray_noise((n,n),(11,49,163,378,n),(.54,.24,.152,.098,.066),seed)
    d=base.gray_noise((n,n),(31,96,289,n),(.51,.34,.19,.13),seed+419)
    x,z=base.field_coords(n,9.6); weave=np.sin(z*17.6+x*5.9+a*3.5)
    t=base.smooth(.52+a*.76+d*.19+.071*weave)
    hue=base.mix(np.asarray((.103,.050,.021) if warm else (.083,.124,.110)),np.asarray((.387,.220,.087) if warm else (.311,.342,.252)),t)
    vein=base.smooth((d-.23)*3.1)*base.smooth(.88-np.abs(a)*1.41)
    haze=base.smooth((a+.29)*2.10)*(1-base.smooth((a+.13)*2.35))
    hue=base.mix(hue,np.asarray((.52,.350,.172) if warm else (.383,.40,.305)),vein*.42)
    hue=base.mix(hue,np.asarray((.101,.111,.074) if warm else (.06,.102,.091)),haze*.24)
    return hue.astype(np.float32)


def extended(name):
    n=960;span=9.6; x,z=base.field_coords(n,span); seed={'diffuse':811,'weather':817,'pressure':825,'ripples':841,'dried':850,'rim':859}[name]
    p,k,alb=base.base_rock(n,seed,'warm' if name in ('dried','rim') else 'cool')
    h=gaussian_filter(.057*p+.016*k,.90)+.029*np.sin(.71*x+.58*z)
    depths=np.zeros(h.shape,np.float32); edges=depths.copy()
    if name in ('diffuse','pressure','rim','weather'):
        cases={'diffuse':[(.05,.19,1.55,1.64,-13.,.91)],'pressure':[(.06,.20,1.26,1.51,0.,.95)],'rim':[(.06,.16,1.38,1.56,13.,.20)],
               'weather':[(-.28,-2.15,1.03,1.38,-11.,.24),(.25,-.95,1.03,1.37,5.,.42),(-.27,.32,1.03,1.36,-11.,.74),(.27,1.58,1.04,1.37,5.,1.4),(-.19,2.80,1.0,1.31,-11.,2.0)]}[name]
        for j,c in enumerate(cases):
            dx,d=base.imprint(x,z,span/n,*c[:-1],k,c[-1]); amount=(1-j*.173) if name=='weather' else 1.
            depths=np.maximum(depths,gaussian_filter(dx*amount,3.5 if name in ('diffuse','pressure','weather') else 1.6))
            edges=np.maximum(edges,gaussian_filter(d*amount,1.25))
        h+=-.146*depths+.022*edges
        if name=='rim': h+=.034*gaussian_filter(edges,1.1)
        if name in ('diffuse','weather'):h+=.012*depths*p
        alb*=((1-.20*depths)+(.23 if name=='rim' else .06)*edges)[...,None]
    elif name=='ripples':
        warp=.22*np.sin(3.7*x+.2*z)+.41*p+.2*k
        rhythm=12.7*z+3.13*x+.37*np.sin(2.98*x)+.66*np.sin(1.39*z)+warp
        rip=np.maximum(0,.40+.60*np.sin(rhythm))**2.08
        h=(.072*rip+.018*p+.009*k).astype(np.float32)
        alb*=np.clip(.71+.49*rip+.19*np.sin(rhythm-.7),.56,1.32)[...,None]
    else:
        from scipy.spatial import cKDTree
        r=np.random.default_rng(46); c=np.stack(np.meshgrid(np.arange(-5.2,5.4,.65),np.arange(-5.2,5.4,.62)),axis=2).reshape(-1,2)
        c+=r.uniform(-.27,.27,size=c.shape); sd=cKDTree(c).query(np.stack((x+.062*p+.04*k,z-.072*p),-1).reshape(-1,2),k=2)[0].reshape(n,n,2)
        valley=np.exp(-np.abs(sd[:,:,1]-sd[:,:,0])/.029).astype(np.float32)
        h-=.104*valley; h+=.041*np.exp(-np.square((valley-.52)/.33))
        alb*=np.clip(1-.61*valley+.10*p,.35,1.2)[...,None]
    base.write_local(name,span,h,alb,depths,edges)


def prepare():
    media_lock(); fetch(); FIELDS.mkdir(parents=True,exist_ok=True)
    base.PACK=FIELDS; base.material=material
    base.build_globes()
    for n in ('brazil','koum','steps','stamp'):pilot.macro_v2(n)
    for n in ('floodplain','river'):pilot.valley_v2(n)
    pilot.geology_v2()
    for n in ('diffuse','pressure','weather','rim','ripples','dried'):extended(n)
    rows={f.name:{'bytes':f.stat().st_size,'sha256':base.hashfile(f)} for f in sorted(FIELDS.glob('*.field'))}
    assert len(rows)==15,len(rows)
    (FIELDS/'manifest.json').write_text(json.dumps(rows,indent=2)+'\n')
    print('FIELDS_READY',FIELDS,flush=True)


if __name__=='__main__':prepare()
