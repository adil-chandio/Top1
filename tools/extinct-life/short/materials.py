#!/usr/bin/env python3
"""Cook non-directional high-pass detail textures; all relief and light is 3D."""
from hashlib import sha256
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter

ROOT=Path(__file__).resolve().parents[3]
DIR=ROOT/'.cache/atlantic-short/materials'
INPUTS={
 'silt':('river-bed-grain.jpg','9d07ac0263f658c58e332b6fbd415c54a5260b42a04117d935473d1cf637d7e0'),
 'scales':('scale-grain.jpg','8e56b406c19e735da076a7a35d82691788a6ed546d9f50c665c1a9567755bae1'),
}

def make(folder=DIR):
 for name,(source,digest) in INPUTS.items():
    p=folder/source
    assert sha256(p.read_bytes()).hexdigest()==digest, p
    legacy=Image.open(p).convert('L').resize((512,512),Image.Resampling.LANCZOS)
    a=np.array(legacy,dtype=np.float32)/255.
    blur=np.array(legacy.filter(ImageFilter.GaussianBlur(22)),dtype=np.float32)/255.
    mid=a-.78*blur-.22*np.mean(a)
    # Fade in a half-period offset only near the outer margins, so mip filters
    # do not introduce a seam across a moving lit surface.
    bd=63;y=np.clip(np.minimum(np.arange(512),np.arange(511,-1,-1))/bd,0,1).astype(np.float32)
    y=y*y*(3-2*y)
    mid=mid*y[None,:]+np.roll(mid,256,1)*(1-y[None,:]);mid=mid*y[:,None]+np.roll(mid,256,0)*(1-y[:,None])
    p=folder/f'{name}.u8'; p.write_bytes(np.clip(np.round(255*(.54+(2.8 if name=='scales' else 1.95)*mid)),4,247).astype('uint8').tobytes())
    print('DETAIL_TILE', name, sha256(p.read_bytes()).hexdigest())

if __name__=='__main__':make()
