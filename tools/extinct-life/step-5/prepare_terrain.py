#!/usr/bin/env python3
"""Prepare pinned geographic displacement and original heightfield sets.

No prior picture cut is decoded. The planet receives two data snapshots, not
an interpolation claiming to reconstruct intermediate time. Local terrain,
track outlines, stratigraphy and deposits are designed illustration geometry.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import struct
import subprocess
import sys
import zlib

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import distance_transform_edt, gaussian_filter, map_coordinates
import shapefile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ATL = ROOT / '.cache/monarch-extinct/atlantic-tracks'
CACHE = ATL / 'pilot-3d'
DATA = CACHE / 'geodata'
PACK = CACHE / 'packed'
OUT = ROOT / 'deliverables/extinct-life-step-5'
MATERIALS = OUT / 'source-materials'
LOCK = HERE / 'pilot-assets.json'
SIZE = (2048,1024)
GEODATA = (
    ('earth_relief.bin','voxiverse/voxiverse','6257fe65f72af1bb128aba7f3d01009a096535ee','assets/planet/earth_relief.bin','c06a9629982d888f6f7854603122111ad3b50145e091d93f8ec8c7811bec8774'),
    ('paleo-125.png','serroba/histeclipse','ab97795a724628ed8786756c804a6102f4552b5d','public/data/paleodem/125.png','8042af7e3d7b85afe7a1d57576f4166356f0062b4162dac81c19f54a8b30bf67'),
    ('ne_50m_land.geojson','nvkelso/natural-earth-vector','f1890d9f152c896d250a77557a5751a93d494776','geojson/ne_50m_land.geojson','e874b27a51d146452be360cafb3cc50c86001074a67d534113e6534682f9826b'),
)

sys.path.insert(0, str(HERE.parent/'step-2'))
import build_opening_board as mapdata


def hashfile(p):
    with Path(p).open('rb') as f:
        from hashlib import file_digest
        return file_digest(f,'sha256').hexdigest()


def check_inputs(fetch):
    DATA.mkdir(parents=True,exist_ok=True)
    for name,repo,ref,src,h in GEODATA:
        p=DATA/name
        if not p.exists() and fetch:
            blob=subprocess.check_output(['gh','api','-H','Accept: application/vnd.github.raw+json',f'repos/{repo}/contents/{src}?ref={ref}'])
            assert sha256(blob).hexdigest()==h
            p.write_bytes(blob)
        assert hashfile(p)==h,p
    required=json.loads((HERE.parent/'step-2/map-sources.json').read_text())
    for inp in required['inputs']:
        if inp['name']=='ne_110m_land.geojson':
            continue
        p=ATL/'sources'/inp['name']
        if not p.exists() and fetch:
            args=['gh','api','-H','Accept: application/vnd.github.raw+json',f'repos/{inp["repository"]}/contents/{inp["path"]}?ref={inp["ref"]}']
            data=subprocess.check_output(args)
            assert sha256(data).hexdigest()==inp['sha256']
            p.parent.mkdir(parents=True,exist_ok=True)
            p.write_bytes(data)
        assert hashfile(p)==inp['sha256'],p
    for f in json.loads(LOCK.read_text())['materials']:
        assert hashfile(MATERIALS/f['name'])==f['sha256']


def smooth(a):
    a=np.clip(a,0,1); return a*a*(3-2*a)


def gray_noise(shape, factors, amps, seed):
    rng=np.random.default_rng(seed)
    w,h=shape
    acc=np.zeros((h,w),dtype=np.float32)
    for d,a in zip(factors,amps):
        sw=max(3,round(d*w/h))
        values=rng.normal(0.,a,(d,sw)).astype(np.float32)
        acc+=np.asarray(Image.fromarray(values).resize((w,h),Image.Resampling.BICUBIC))
    return acc


def write(name, channels):
    height,width=channels[0].shape
    assert len(channels)==8 and all(c.shape==(height,width) for c in channels)
    data=np.stack(channels,axis=2).astype('<f4',copy=False)
    assert np.isfinite(data).all()
    f=PACK/f'{name}.field'
    with f.open('wb') as w:
        w.write(struct.pack('<4sIII',b'GEO8',width,height,8))
        w.write(data.tobytes())
    print(f'{name}: {width}x{height} × 8 channels, {f.stat().st_size:,} B',flush=True)


def rgb(v):
    return np.asarray(v,dtype=np.float32)


def mix(a,b,q):
    return np.asarray(a)*(1.-q[...,None])+np.asarray(b)*q[...,None]


def latlon(w,h):
    return np.meshgrid(360*(np.arange(w,dtype=np.float32)+.5)/w-180,90-180*(np.arange(h,dtype=np.float32)+.5)/h)


def coast(data, w,h):
    im=Image.new('L',(w,h)); d=ImageDraw.Draw(im)
    for outer,*holes in data:
        area=abs(sum(x1*y2-y1*x2 for (x1,y1),(x2,y2) in zip(outer,outer[1:])))
        if area<.009: continue
        for i,ring in enumerate((outer,*holes)):
            pts=[((x+180)/360*w,(90-y)/180*h) for x,y in ring]
            d.polygon(pts,fill=255 if not i else 0)
    return np.asarray(im,dtype=np.float32)/255


def build_globes():
    w,h=SIZE
    today=json.loads((DATA/'ne_50m_land.geojson').read_text())
    modern=[r for f in today['features'] for r in mapdata.polygons(f['geometry'])]
    with (ATL/'sources/125Ma_CS_v7.shp').open('rb') as f:
        past=[r for s in shapefile.Reader(shp=f).iterShapes() for r in mapdata.polygons(s.__geo_interface__)]
    rot=mapdata.get_rotations(ATL/'sources/m06c9h_3id_forPgeog_19o_r1c.rot')
    earlier=tuple(mapdata.rotated(p,mapdata.reconstruction(i,125.,rot)) for p,i in zip(mapdata.SITES,mapdata.PLATES,strict=True))
    p,b=[mapdata.land_ids(s,modern) for s in mapdata.SITES]; a,z=[mapdata.land_ids(s,past) for s in earlier]
    assert p and b and p.isdisjoint(b) and a & z
    meta={'modern':mapdata.SITES,'past':earlier,'distance_km':{'today':mapdata.separation(mapdata.SITES),'past_model':mapdata.separation(earlier)},
          'visual_labels_are_published_approximations':{'today':6000,'past':1000},'geometry':{'r_km':6371,'vertical_exaggeration':31.0},
          'then_ma':125,'then_age_is_not_a_footprint_date':True}
    (PACK/'world.json').write_text(json.dumps(meta,indent=2)+'\n')
    blob=(DATA/'earth_relief.bin').read_bytes(); assert blob[:16]==struct.pack('<4sIII',b'VXPL',1,w,h)
    e=np.frombuffer(zlib.decompress(blob[16:]),dtype='<i2').reshape(h,w).astype(np.float32)
    # The mirrored downsampled stream starts at -180, verified on both Andes and Himalayan cells.
    assert e[352,1517]>4000 and e[int(109/180*h),int(112/360*w)]>2500
    g=np.asarray(Image.open(DATA/'paleo-125.png'),dtype=np.float32)
    assert g.shape==(181,361)
    elev=np.where(g>=128,(g-128)*(6500/127),(g-127)*(11000/127)).astype(np.float32)
    lon,lat=latlon(w,h)
    de=map_coordinates(elev,np.stack((90-lat,lon+180)),order=1,mode='nearest')
    shade=gray_noise((w,h),(12,41,119,292,708),(.65,.34,.24,.14,.08),561)
    for land,rel,name,old in ((modern,e,'modern',False),(past,de,'ancient',True)):
        valid=coast(land,w,h)>.5
        mask=gaussian_filter(valid.astype(np.float32),.44,mode='wrap')
        hval=(np.float32(0.006)+np.maximum(0,rel)*.000031)*mask
        # Sub-grid appearance is tonal; modern and ancient data elevations are never swapped.
        dy,dx=np.gradient(gaussian_filter(hval,.46,mode='wrap'))
        dx/=np.maximum(.24,np.cos(np.deg2rad(lat)))*(2*np.pi*6.371/w)
        dy/=(np.pi*6.371/h)
        dry=(np.exp(-((np.abs(lat)-25.)/9.6)**2)*(.61+.37*np.cos(np.deg2rad(lon-28))))
        dry=np.clip(dry+(shade*.15),0,1)
        if old: dry=np.clip((dry+.13)*.77,0,1)
        greens=rgb((.108,.255,.173) if not old else (.138,.268,.159))
        deserts=rgb((.63,.445,.204) if not old else (.49,.38,.186))
        lands=mix(greens,deserts,dry)
        high=smooth((rel-540)/3400)
        lands=mix(lands,rgb((.56,.485,.35)),high)
        snow=smooth((rel-3400)/2800+smooth((np.abs(lat)-55)/45)*.86)*.89
        lands=mix(lands,rgb((.88,.891,.85)),snow)
        lands*=np.clip(.95+.18*shade,.7,1.22)[...,None]
        depth=np.maximum(0,-rel)
        blue=mix(rgb((.007,.026,.056)),rgb((.019,.111,.158)),np.exp(-depth/1970).astype(np.float32))
        shelf=np.power(np.exp(-distance_transform_edt(~valid).astype(np.float32)/6.2),1.6)
        blue=mix(blue,rgb((.023,.195,.181)),shelf*.52)
        sy,sx=np.gradient(gaussian_filter(rel,.70))
        undersea=np.clip((sx*.0016-sy*.0012),-.29,.33)*.52
        blue*=np.clip(.98+.10*shade+undersea,.60,1.36)[...,None]
        base=mix(blue,lands,mask)
        write(name,(hval,base[:,:,0],base[:,:,1],base[:,:,2],dx,dy,mask,shade))


FOOT=((-0.04,-0.50),(-.17,-.45),(-.22,-.34),(-.22,-.20),(-.33,-.08),(-.49,.08),(-.50,.19),(-.44,.233),(-.37,.19),(-.22,.066),(-.133,.016),(-.113,.064),(-.129,.228),(-.095,.435),(-.038,.52),(.019,.526),(.064,.462),(.082,.291),(.071,.108),(.104,.075),(.18,.11),(.29,.259),(.448,.333),(.494,.265),(.444,.16),(.326,.057),(.241,-.07),(.187,-.23),(.159,-.376),(.093,-.474))


def ring(poly):
    p=np.asarray(poly); out=[]
    for i in range(len(p)):
        a,b,c,d=(p[k%len(p)] for k in range(i-1,i+3))
        for t in np.linspace(0,1,4,endpoint=False):
            out.append(tuple((2*b+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t)*.5))
    return out


FP=ring(FOOT)


def field_coords(n,span):
    # Pixel centres from -span/2 to +span/2, row 0 equals negative world Z.
    return np.meshgrid((np.arange(n,dtype=np.float32)+.5)/n*span-span*.5,(np.arange(n,dtype=np.float32)+.5)/n*span-span*.5)


def imprint(x,z,df,px,pz,w,h,ang,texture,soft=0.):
    n=x.shape[0]; a=np.deg2rad(ang); co=np.cos(a); si=np.sin(a)
    mx=lambda a:(a-x.min())/df; mz=lambda a:(a-z.min())/df
    m=Image.new('L',(n,n));d=ImageDraw.Draw(m)
    d.polygon([(mx(px+p*w*co-q*h*si),mz(pz+p*w*si+q*h*co)) for p,q in FP],fill=1)
    a=np.asarray(m,dtype=bool)
    sd=(distance_transform_edt(a)-distance_transform_edt(~a)).astype(np.float32)*df
    sd+=texture*(.015 if not soft else .025)
    depth=smooth(.53+sd/(.123+soft*.106))
    edge=np.exp(-((sd+.035)/(.035+soft*.029))**2)
    grain=1+np.clip(texture,-.47,.6)*.35
    return depth*grain,edge


def material(key,n):
    im=Image.open(MATERIALS/('iron-silt.jpg' if key=='warm' else 'slate-silt.jpg')).convert('RGB')
    im=im.resize((n,n),Image.Resampling.BICUBIC)
    out=np.asarray(im,dtype=np.float32)/255.
    return np.power(out,2.05)


def base_rock(n,seed,key):
    noise=gray_noise((n,n),(6,18,51,127,330,n),(.42,.265,.16,.104,.085,.069),seed)
    detail=gray_noise((n,n),(17,86,258,n),(.44,.22,.15,.11),seed+17)
    tex=material(key,n)
    albedo=tex*np.float32(.85)+rgb((.095,.058,.032) if key=='warm' else (.09,.11,.079))*.42
    albedo*=np.clip(1+.22*noise,.58,1.36)[...,None]
    return noise,detail,albedo


def write_local(name,span,h,col,mark,rim):
    assert h.shape==mark.shape==rim.shape
    dz,dx=np.gradient(h,span/h.shape[0])
    # Linear colours, signed slopes, relative stamp-depth and raised rim.
    write(name,(h,col[:,:,0],col[:,:,1],col[:,:,2],dx,dz,mark,rim))


def macro(name):
    n,span=1280,9.6
    x,z=field_coords(n,span); df=span/n
    key='warm' if name=='brazil' else 'cool'
    seed={'brazil':41,'koum':52,'steps':77,'stamp':77}[name]
    n1,n2,albedo=base_rock(n,seed,key)
    stria=np.sin((z-.36*x)*27+n1*2.4)
    cracks=np.exp(-((np.sin(z*4.2+.55*x+gaussian_filter(n2,4)*.84)-.51)/(.095+.018*abs(n1)))**2)*smooth((n1+.12)*1.24)
    base=gaussian_filter(.048*n1+.011*n2+.0045*stria-.009*cracks,1.25)+.044*np.sin(.78*x+.65*z)
    albedo*=np.clip(1.-.36*cracks+.075*stria,.58,1.3)[...,None]
    # Isolated small, genuinely raised grains; avoid uniform noisy vertical spikes.
    rng=np.random.default_rng(seed+45)
    for _ in range(303):
        i,j=rng.integers(12,n-12,size=2)
        r=round(rng.uniform(1.8,6.2)); l=max(2,2*r)
        yy,xx=np.ogrid[-l:l+1,-l:l+1]
        t0=np.exp(-((xx/(r*.93))**2+(yy/(r*1.31))**2)*1.65)
        base[i-l:i+l+1,j-l:j+l+1]+=t0*rng.uniform(.006,.026)
        sub=albedo[i-l:i+l+1,j-l:j+l+1]
        sub[:]=mix(sub,rgb((.165,.138,.089) if key=='cool' else (.25,.157,.095)),t0*.50)
    coords={'brazil':[(0.10,.16,1.24,1.52,13.,0.)], 'koum':[(.16,.02,1.28,1.5,-22.,.17),(-1.27,1.43,.93,1.29,-9.,.57)],
            'steps':[(-.32,-2.58,1.0,1.31,-12.,0.),(.29,-1.30,1.02,1.33,7.,.04),(-.25,-.05,1.00,1.30,-10.,0.),(.29,1.19,1.0,1.28,6.,.14),(-.23,2.44,1.08,1.42,-8.,.25),(.26,3.67,1.01,1.31,9.,.28)],
            'stamp':[(.06,.20,1.26,1.51,0.,.10)]}[name]
    dep=np.zeros_like(base); rim=dep.copy()
    for px,pz,w,h,angle,soft in coords:
        p,r=imprint(x,z,df,px,pz,w,h,angle,n2,soft)
        dep=np.maximum(dep,p); rim=np.maximum(rim,r)
    write_local(name,span,base-.146*dep+.022*rim,albedo,dep,rim)


def river(name):
    n,span=960,96.
    x,z=field_coords(n,span); delta=name=='floodplain'
    no,d,alb=base_rock(n,533+int(delta)*27,'warm' if not delta else 'cool')
    middle=(8.9 if delta else 7.2)*np.sin(z*.087+(.49 if delta else 1.07))+2.1*np.sin(z*.157-1.4)
    width=(3.95 if delta else 3.04)+.74*np.sin(z*.137+.1)
    rolling=gaussian_filter(no,3.0)
    gap=np.abs(x-middle)-width + .34*rolling + .23*np.sin(.61*z+.22*x)
    bank=smooth((gap+.87)/1.72)
    H=-.52 + .80*bank+(.57 if delta else .91)*smooth((gap-2.4+.72*rolling)/1.03)
    H+=(.77 if delta else 1.28)*smooth((gap-6.0+1.32*rolling)/1.38)
    H+=(.92 if delta else 1.22)*smooth((gap-12.2+1.73*rolling)/1.68)
    H+=3.24*smooth((gap-19.4+3*rolling)/6.4)+3.5*smooth((z-25)/17)+smooth((gap-8)/18)*rolling*1.82
    H+=.039*no + .011*np.sin(16*H+no*1.2)*bank
    # Silt bars and softer, uneven shallow margins, not a channel traced from photographs.
    xx=x-middle
    H+=.66*np.exp(-((xx-.15)/1.10)**2)*np.exp(-((z-(-7 if delta else 5.5))/4.9)**2)
    H+=.49*np.exp(-((xx+2.13)/.91)**2)*np.exp(-((z+13.7)/3.7)**2)
    bank_tone=alb*.50 + rgb((.145,.091,.054) if not delta else (.093,.123,.077))
    stripe=.85+.13*np.sin(H*17+.35*np.sin(z*.31)+.41*no)+.10*np.cos(H*6.4+.20*x)
    bank_tone*=stripe[...,None]
    rust=smooth((no+.27)*.94)*smooth((gap-1.4)*.42)
    bank_tone=mix(bank_tone,rgb((.251,.133,.071) if not delta else (.085,.148,.065)),rust*.63)
    water_mask=smooth((.01-H)/.26)
    bank_tone=mix(bank_tone,rgb((.051,.092,.069)),water_mask*.74)
    # Low scrub clumps with actual silhouettes and shadow, not a texture of trees.
    brush=smooth((no-.19+.13*d)*3.2)*smooth((gap-4.6)/7.)
    H+=brush*(.83 if delta else .55)
    bank_tone=mix(bank_tone,rgb((.037,.075,.033) if delta else (.064,.091,.041)),brush*.93)
    # Uneven scatter of three-dimensional talus and low vegetated hummocks.
    rng=np.random.default_rng(772 if delta else 792)
    for j in range(865):
        y0,x0=rng.integers(48,n-48,size=2)
        side=gap[y0,x0]
        is_rock=j%3==0
        if side<(.35 if is_rock else 1.15) or side>35 or z[y0,x0]<-31:continue
        size=rng.uniform(2.2,14.0) if is_rock else rng.uniform(2.8,14.5)
        r=int(2.5*size); vv,uu=np.ogrid[-r:r+1,-r:r+1]
        zz=vv/size;xx=uu/(size*rng.uniform(.49,1.32))
        ang=rng.uniform(-1.1,1.1)
        sx=xx*np.cos(ang)-zz*np.sin(ang);sz=xx*np.sin(ang)+zz*np.cos(ang)
        jitter=1+.16*np.sin(uu*.76+vv*.31)+.12*np.sin(vv*1.4-uu*.40)
        w=smooth(1.10-(np.abs(sx)**1.52+np.abs(sz)**1.51)*jitter)
        s=np.s_[y0-r:y0+r+1,x0-r:x0+r+1]
        H[s]+=w*rng.uniform(.13,.64)*(1.0 if is_rock else (1.14 if delta else .76))
        c=rgb((.239,.156,.092) if not delta else (.168,.168,.114)) if is_rock else rgb((.050,.089,.039) if not delta else (.034,.077,.028))
        bank_tone[s]=mix(bank_tone[s],c,w*(.69 if is_rock else .94))
    write_local(name,span,H,bank_tone,np.zeros_like(H),np.zeros_like(H))


def shelf():
    n,span=1056,14.
    x,z=field_coords(n,span)
    no,detail,alb=base_rock(n,41,'cool'); wobble=.31*np.sin(x*.7)+.26*no
    strata=smooth((z+3.0+wobble)/.21)+smooth((z+1.2+wobble)/.23)+smooth((z-.75+wobble)/.21)+smooth((z-2.84+wobble)/.28)
    H=.36+strata*.60 + .083*no+.017*detail
    lamina=.78+.19*np.sin((H+no*.042)*41.0)+.075*np.cos(H*107+1.8*no)
    alb=alb*.65+rgb((.20,.134,.077))*.63
    alb*=lamina[...,None]
    stamps=[]
    for i,cz in enumerate((-1.91,-.17,1.89,4.05)):
        for cx in ((-1.17,.73) if i%2==0 else (-.8,1.27)):
            p,r=imprint(x,z,span/n,cx,cz,.78,1.19,-5.+i*6,no*.67,.12)
            stamps.append(p)
    mark=np.maximum.reduce(stamps)
    write_local('shelves',span,H-mark*.095,alb,mark,np.zeros_like(H))


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--fetch',action='store_true'); a=ap.parse_args()
    check_inputs(a.fetch)
    PACK.mkdir(parents=True,exist_ok=True)
    build_globes()
    for name in ('brazil','koum','stamp','steps'):macro(name)
    for name in ('river','floodplain'):river(name)
    shelf()


if __name__=='__main__': main()
