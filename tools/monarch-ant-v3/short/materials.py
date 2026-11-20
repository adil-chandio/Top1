"""New deterministic portrait material tiles, not recovered V3 plates."""
import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


def soft(size, points, rng):
    i = Image.fromarray(rng.integers(4, 252, (points, points), dtype=np.uint8))
    return np.asarray(i.resize((size, size), Image.Resampling.BICUBIC), dtype=np.float32)/255


def quartz(rng):
    n = 1024
    # Jittered nearest grains; an illumination ramp and occluded grain boundaries
    # give the shader fine mineral texture without a photographed baked shadow.
    N = 179
    cx = rng.uniform(.02, .98, (N, N)).astype('f'); cy = rng.uniform(.02, .98, (N, N)).astype('f')
    tone = rng.normal(0., 1., (N, N)).astype('f'); shape = rng.random((N, N)).astype('f')
    x = np.arange(n, dtype='f')[None, :]*N/n; y = x.T
    ix = x.astype('i'); iy = y.astype('i')
    near = np.full((n,n), 10., 'f'); next_ = near.copy(); grain = np.zeros_like(near); gx=near.copy(); gy=near.copy(); spec=near.copy()
    for oy in (-1, 0, 1):
        for ox in (-1, 0, 1):
            j, i = (iy+oy)%N, (ix+ox)%N
            u=x-(ix+ox+cx[j,i]); v=y-(iy+oy+cy[j,i]); r=shape[j,i]
            d=np.abs(u+.32*(r-.5)*v)**(1.56+.97*r)+(np.abs(v)*(.79+.52*r))**(1.72+.92*r)
            ok=d<near
            next_=np.where(ok,near,np.minimum(next_,d));near=np.minimum(near,d)
            grain=np.where(ok,tone[j,i],grain);gx=np.where(ok,u,gx);gy=np.where(ok,v,gy);spec=np.where(ok,r,spec)
    edge=np.clip((next_-near)*6.2,0,1)
    noise=rng.normal(0,.022,(n,n)).astype('f')
    facet=.081*np.clip(-.73*gx-.58*gy,-.59,.62) + .075*np.maximum(0,1-2.5*(abs(gx-.034)+abs(gy+.215)))*(spec>.63)
    field=.679+.080*np.clip(grain,-2,1.65)+facet-.093*(1-edge)**2+noise+.041*(soft(n,43,rng)-.5)+.051*(soft(n,9,rng)-.5)
    darker=np.clip(-grain*.017,0,.07)
    return np.clip(np.stack((field+.028, field*.868+.012+darker*.26,field*.704+.039+darker*.70),axis=-1)*255,0,255).astype('B')


def cuticle(rng):
    n=768
    y,x=np.meshgrid(np.arange(n,dtype='f'),np.arange(n,dtype='f'),indexing='ij')
    p=.177+.035*(soft(n,78,rng)-.5)+.054*(soft(n,144,rng)-.5)+.045*(soft(n,24,rng)-.5)
    p+=.024*np.sin(x*.267+.062*y+soft(n,10,rng)*5.3) + rng.normal(0,.008,(n,n))
    return np.clip(np.stack((p*1.14,p,p*.81),axis=-1)*255,0,255).astype('B')


def canopy(rng):
    x,y=np.meshgrid(np.linspace(0,1,1024),np.linspace(0,1,576))
    b=.065+.096*np.exp(-((x-.30)**2*7+(y-.22)**2*8))+.051*np.exp(-((x-.86)**2*25+(y-.31)**2*18))
    a=Image.fromarray(np.clip(np.stack((b*.93,b*1.21,b*.71),axis=-1)*255,0,255).astype('B'))
    g=Image.new('RGBA',a.size); d=ImageDraw.Draw(g)
    for _ in range(64):
        u,v=rng.uniform(-50,1074),rng.uniform(-40,616);r=rng.uniform(5,43)
        d.ellipse((u-r,v-r,u+r,v+r), fill=(rng.integers(90,165),rng.integers(107,177),rng.integers(53,100),rng.integers(15,63)))
    return Image.alpha_composite(a.convert('RGBA'),g.filter(ImageFilter.GaussianBlur(16))).convert('RGB')


def make(out):
    out.mkdir(parents=True,exist_ok=True)
    rng=np.random.default_rng(724934)
    for name, texture in [('quartz', quartz(rng)), ('cuticle',cuticle(rng)), ('canopy',canopy(rng))]:
        plate=texture if isinstance(texture,Image.Image) else Image.fromarray(texture)
        (out/f'{name}.rgba').write_bytes(plate.convert('RGBA').transpose(Image.Transpose.FLIP_TOP_BOTTOM).tobytes())


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('out',type=Path);make(ap.parse_args().out)
