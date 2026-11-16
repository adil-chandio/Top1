"""Original oblique-space editorial blocking. NOT animal animation/AV release proof.
Independent trajectories and projected vertical fluke movement; authored vector proxies,
not photographic stills or the rejected render. No reference footage/music reused.
Run: PYTHONPATH=.local-motion python research/monarch_cam_market/motion/layout_study.py
"""
import argparse,hashlib,json,math,subprocess
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
import imageio_ffmpeg

W,H,S,FPS,N=960,540,2,24,144
BASE=Path(__file__).parent

def smooth(points,steps=10):
    out=[];p=[points[-1],*points,points[0],points[1]]
    for i in range(1,len(p)-2):
        a,b,c,d=[np.array(q,dtype=float) for q in p[i-1:i+3]]
        for t in np.linspace(0,1,steps,endpoint=False):
            out.append(tuple(.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t)))
    return out

def state(t):
    # X/Y are stage-space metres, not measurements of a documented encounter.
    return [dict(name='orca_near',species='orca',x=-8+t*.9,y=1,z=0,length=6.4,yaw=.045,phase=.4),
            dict(name='orca_far',species='orca',x=-11+t*.82,y=7,z=-.8,length=5.6,yaw=-.035,phase=2.0),
            dict(name='humpback',species='humpback',x=20-t*1.35,y=9-t*.12,z=-.4,length=12,yaw=math.pi+.10,phase=1.2)]

def screen(x,y,z):return (W*.46+x*20,H*.48+y*11-z*16)

def animal(draw,a,t):
    ox,oy=screen(a['x'],a['y'],a['z']);unit=a['length']*20/10
    hump=a['species']=='humpback';yaw=a['yaw']
    cycle=t*(1.5 if hump else 2.1)+a['phase']
    def pt(q):
        x,y=q[:2];z=q[2] if len(q)>2 else 0
        # Tail deformation is world vertical, projected by the oblique view.
        k=max(0,min(1,(-x-1)/4))
        z+=math.sin(cycle-k*.7)*k*k*.40
        wx=x*math.cos(yaw)-y*math.sin(yaw);wy=x*math.sin(yaw)+y*math.cos(yaw)
        return ((ox+wx*unit)*S,(oy+wy*unit*.55-z*unit*.8)*S)
    def poly(coords,color,curved=False):
        q=[pt(p) for p in coords]
        draw.polygon(smooth(q,6) if curved else q,fill=color)
    depth=max(.55,1-a['y']*.025)
    body=tuple(int(v*depth) for v in ((57,94,110) if hump else (35,65,80)))
    edge=tuple(int(v*depth) for v in ((94,137,151) if hump else (145,177,180)))
    # Horizontal flukes and separately articulated pectorals.
    ztail=math.sin(cycle-.7)*.32
    poly([(-4.5,-.12,ztail),(-5.0,-1.5,ztail),(-5.8,-1.9,ztail),(-5.4,-.42,ztail),(-5.55,0,ztail),(-5.4,.42,ztail),(-5.8,1.9,ztail),(-5,1.5,ztail),(-4.5,.12,ztail)],body)
    reach=3.7 if hump else 1.8
    for side in (-1,1):
        dz=math.sin(cycle*.65+side*.4)*.16
        poly([(.8,side*.7,0),(.15,side*1.3,dz),(-1.6,side*reach,dz+.15),(-2,side*(reach+.2),dz+.2),(-1.9,side*(reach-.6),dz),(-.3,side*.85,0)],edge if hump else body,True)
    poly([(4.5,0),(4.1,-.58),(2.8,-1),(1,-1.13),(-1,-.95),(-3,-.48),(-4.7,-.12),(-4.8,.12),(-3,.48),(-1,.95),(1,1.13),(2.8,1),(4.1,.58)],body,True)
    # Restrained dorsal ridge, not huge identical male fins on every proxy.
    poly([(-1.4,-.08,.55),(-2,0,1.0 if hump else 1.45),(-2.5,.08,.4)],edge)
    if not hump:
        for side in (-1,1):
            poly([(2.8,side*.58,.12),(2.2,side*.92,.12),(1.55,side*.84,.12),(2,side*.58,.12)],(177,200,200),True)
        poly([(-1.8,-.62,.3),(-2.8,-.32,.35),(-3.0,.3,.35),(-1.8,.6,.3)],(65,92,105),True)
    else:
        q=[pt((x,-.22,.33)) for x in (-3,-2,0,2,3.8)]
        draw.line(q,fill=(92,131,144),width=S)
        for x in (2.8,3.25,3.7):
            p=pt((x,0,.2));draw.ellipse((p[0]-S,p[1]-S,p[0]+S,p[1]+S),fill=(110,145,155))

def background():
    y,x=np.mgrid[0:H,0:W];light=np.exp(-(((x-W*.64)/(W*.8))**2+((y+50)/(H*.9))**2))
    a=np.zeros((H,W,3),dtype=np.uint8)
    for i,(base,gain) in enumerate(((4,13),(17,35),(27,44))):a[:,:,i]=(base+gain*light).astype(np.uint8)
    return Image.fromarray(a).resize((W*S,H*S),Image.Resampling.BICUBIC)

def main():
    global N
    p=argparse.ArgumentParser();p.add_argument('--out',default=str(BASE/'out/layout-v2'));p.add_argument('--frames',type=int,default=144);args=p.parse_args()
    if not 24<=args.frames<=216:raise ValueError('internal study limited to 1–9 seconds')
    N=args.frames
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    base=background();rng=np.random.default_rng(42);particles=rng.uniform([0,70],[W,H],(95,2))
    ff=imageio_ffmpeg.get_ffmpeg_exe();video=out/'SPATIAL_LAYOUT_INTERNAL.mp4'
    cmd=[ff,'-nostdin','-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-an','-c:v','libx264','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(video)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE);samples=[];trace=[]
    try:
        for frame in range(N):
            t=frame/FPS;image=base.copy();d=ImageDraw.Draw(image)
            for x,y in particles:
                x=(x+t*.7)%W;d.ellipse((x*S,y*S,x*S+S,y*S+S),fill=(33,67,81))
            # Small neutral prey proxy supplies a readable pursuit target; no escape outcome.
            px,py=screen(1.5+t*.65,3,0)
            prey=[((px+dx)*S,(py+dy)*S) for dx,dy in ((10,0),(4,-3),(-8,-2),(-13,-5),(-11,0),(-13,5),(-8,2),(4,3))]
            d.polygon(prey,fill=(142,153,135))
            actors=state(t)
            for a in sorted(actors,key=lambda a:a['y'],reverse=True):animal(d,a,t)
            # Clearly labelled internal diagnostic, never passed off as final production.
            d.text((28*S,22*S),'INTERNAL SPATIAL LAYOUT / NOT FINAL',fill=(125,158,168),font=ImageFont.load_default(size=12*S))
            d.text((28*S,43*S),'Original vector proxies | Silent | No factual encounter reconstruction',fill=(95,128,139),font=ImageFont.load_default(size=10*S))
            image=image.resize((W,H),Image.Resampling.LANCZOS)
            if frame in (0,N//2,N-1):
                image.save(out/f'layout-{frame:03}.jpg',quality=95);samples.append(image)
            proc.stdin.write(image.tobytes());trace.append({'frame':frame,'actors':actors})
        proc.stdin.close();code=proc.wait(timeout=60)
        if code:raise RuntimeError('encoder failed')
    except BaseException:
        proc.kill();proc.wait();raise
    subprocess.run([ff,'-nostdin','-v','error','-xerror','-i',str(video),'-f','null','-'],check=True,timeout=60)
    sheet=Image.new('RGB',(W,3*H))
    for i,img in enumerate(samples):sheet.paste(img,(0,i*H))
    sheet.save(out/'layout-contact-sheet.jpg',quality=94)
    (out/'trajectory.json').write_text(json.dumps(trace,indent=2))
    # Centre-distance check only, not full silhouette collision/anatomy certification.
    closest=min(math.hypot(r['actors'][0]['x']-r['actors'][2]['x'],r['actors'][0]['y']-r['actors'][2]['y']) for r in trace)
    manifest={'type':'silent_original_proxy_layout_NOT_integrated_AV_proof','duration_seconds':N/FPS,'fps':FPS,'frames':N,'resolution':[W,H],'full_decode_passed':True,'closest_near_orca_humpback_centre_stage_units':closest,'camera_static':True,'independent_trajectories':True,'vertical_tail_projection':True,'source_rights':'Original vector proxy geometry and background; no third-party media/audio','audio':False,'not_passed':['reference_audiovisual_gate','anatomy_review','sound_listening','independent_review','final_creative_approval'],'files':[{'path':f.name,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in out.iterdir() if f.is_file()]}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2));print(json.dumps({k:v for k,v in manifest.items() if k!='files'},indent=2))
if __name__=='__main__':main()
