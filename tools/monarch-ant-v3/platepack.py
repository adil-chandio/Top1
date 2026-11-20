"""Lossless, chapter-local storage for native RGBA and its separate actor matte.

A bounded sequential LZ4 desktop proxy (lossless RGB + alpha), not part of the
published media. There is one packet per native evaluation, no frame blending.
"""
import argparse
import ctypes as ct
import ctypes.util
import re
import struct
import sys
from pathlib import Path
import numpy as np

HEAD = struct.Struct('<8s4I')
U = struct.Struct('<I')
MAGIC = b'MONV3RGB'


def library():
    lib = ct.CDLL(ctypes.util.find_library('lz4') or 'liblz4.so.1')
    lib.LZ4_compressBound.argtypes = [ct.c_int]
    lib.LZ4_compressBound.restype = ct.c_int
    for n in ['LZ4_compress_default','LZ4_decompress_safe']:
        f=getattr(lib,n); f.argtypes = [ct.c_void_p,ct.c_void_p,ct.c_int,ct.c_int]; f.restype = ct.c_int
    return lib


def exact(s, n):
    x=s.read(n)
    if len(x)!=n:raise EOFError(f'Truncated native frame packet: got {len(x)} of {n}')
    return x


def pack(dest, w, h, lo, end):
    lib=library(); n=w*h*4; cap=lib.LZ4_compressBound(n)
    assert w>0 and h>0 and end>lo and cap>n
    b=ct.create_string_buffer(cap);prev=np.zeros(n,dtype=np.uint8); tmp=np.empty_like(prev)
    with dest.open('wb') as out:
        out.write(HEAD.pack(MAGIC,w,h,lo,end))
        for f in range(lo,end):
            x=np.frombuffer(exact(sys.stdin.buffer,n),dtype=np.uint8)
            np.bitwise_xor(prev,x,out=tmp)
            got=lib.LZ4_compress_default(tmp.ctypes.data,b,n,cap)
            if got<=0:raise RuntimeError((f,'failed LZ4 compression'))
            out.write(U.pack(got));out.write(b.raw[:got]);prev=x
        if sys.stdin.buffer.read(1):raise RuntimeError('Unexpected extra native picture bytes')


def frames(path):
    with path.open('rb') as f:
        magic,w,h,lo,hi=HEAD.unpack(exact(f,HEAD.size))
        assert magic==MAGIC and 256<=w<=1920 and 144<=h<=1080 and 0<=lo<hi<=8994
        lib=library();n=w*h*4
        prev=np.zeros(n,dtype=np.uint8); diff=np.empty_like(prev)
        cap=lib.LZ4_compressBound(n)
        for k in range(lo,hi):
            size,=U.unpack(exact(f,U.size));assert 0<size<=cap
            x=exact(f,size)
            if lib.LZ4_decompress_safe(x,diff.ctypes.data,size,n)!=n:raise ValueError((k,'damaged plate packet'))
            np.bitwise_xor(prev,diff,out=prev)
            yield k,w,h,prev
        assert not f.read(1)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('path',type=Path)
    for key in ('width','height','first','end'):p.add_argument(key,type=int)
    a=p.parse_args();pack(a.path,a.width,a.height,a.first,a.end)
