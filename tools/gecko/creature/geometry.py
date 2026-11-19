"""Original Tokay sculpt. Mesh lengths are local units; one unit is 6.2 cm.

The torso and four limbs share vertices at the shoulders. The planted geometry
uses the exported JS paths directly, including the integrated distal roll.
"""
import math

import bpy
from mathutils import Matrix, Vector
import numpy as np

UNIT = .062
TAU = 2 * math.pi


def W(p):
    x, y, z = p
    return Vector((x, -z, y)) * UNIT


def coords(p):
    a = np.asarray(p)
    return (a[..., [0, 2, 1]] * np.array([UNIT, -UNIT, UNIT])).astype('float32')


def smooth(t):
    a = np.clip(t, 0, 1)
    return a * a * (3 - 2 * a)


def ramp(t, a, b):
    return smooth((t - a) / (b - a))


def normalize(v):
    return v / np.maximum(np.linalg.norm(v, axis=-1, keepdims=True), 1e-10)


def spline(keys, samples):
    """Tangent-limited Hermite for both profiles and skin centerlines."""
    keys = np.asarray(keys, dtype=float)
    values = keys[:, 1:]
    h = np.diff(keys[:, 0])[:, None]
    slopes = np.diff(values, axis=0) / h
    tangents = np.empty_like(values)
    tangents[0], tangents[-1] = slopes[0], slopes[-1]
    signed = slopes[:-1] * slopes[1:] > 0
    tangents[1:-1] = np.where(signed, 2 * slopes[:-1] * slopes[1:] / np.where(signed, slopes[:-1] + slopes[1:], 1), 0)
    k = np.clip(np.searchsorted(keys[:, 0], samples, side='right') - 1, 0, len(h) - 1)
    u = np.clip((samples - keys[k, 0]) / h[k, 0], 0, 1)[:, None]
    e = u * u * (3 - 2 * u)
    return values[k] * (1-e) + values[k+1] * e + h[k] * (tangents[k] * u * (1-u)**2 - tangents[k+1] * u*u*(1-u))


def mesh(name, p, faces, mat, uv=None, *, shading=True):
    data = bpy.data.meshes.new(name)
    data.from_pydata(coords(p).tolist(), [], faces)
    data.update()
    if uv is not None:
        layer = data.uv_layers.new(name='UVMap')
        ix = np.empty(len(data.loops), dtype=np.int32)
        data.loops.foreach_get('vertex_index', ix)
        layer.data.foreach_set('uv', np.asarray(uv, dtype=np.float32)[ix].ravel())
    if shading:
        data.polygons.foreach_set('use_smooth', np.ones(len(data.polygons), dtype=np.bool_))
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    if mat:
        data.materials.append(mat)
    return obj


def put(obj, points):
    obj.data.vertices.foreach_set('co', coords(points).ravel())
    obj.data.update()


def pigment(rest):
    # Stable one-time pigment solve in the bind pose, so spots don't slide.
    # Distorted 3D cells give softly ragged rust markings; pigment and scale
    # relief are not the same field and do not tint the light reflected above.
    x,y,z=rest.T
    n=.46+.109*np.sin(7.12*x+4.66*y+8.3*z)*np.cos(3.9*y-7.1*z)+.082*np.sin(19.6*z-9.8*x+12.1*y)
    n+=.060*np.cos(x*25.9-y*26.65)*np.sin(z*16.1+y*12.7)
    q=rest*np.array([4.78,4.32,5.11])+np.column_stack([.19*np.sin(y*17.11+z*13),.23*np.sin(z*19.2+x*16.9),.11*np.cos(x*26.1-y*13.1)])
    cell=np.floor(q)
    dist=np.ones(len(rest))*2;v=np.zeros(len(rest))
    def fract(a): return a-np.floor(a)
    for ix in (-1,0,1):
        for iy in (-1,0,1):
            for iz in (-1,0,1):
                b=cell+[ix,iy,iz]
                a=b+np.column_stack([fract(np.sin(b@[61.77,38.29,95.35])*19737.79),
                                     fract(np.sin(b@[19.33,67.95,23.18])*49871.31),
                                     fract(np.sin(b@[27.61,93.31,55.87])*90323.63)])
                d=np.linalg.norm((q-a)*[1.07,.96,1.13],axis=1)
                v=np.where(d<dist,fract(np.sin(b@[29.19,57.31,17.67])*29981.73),v)
                dist=np.minimum(d,dist)
    rel=dist + .054*np.sin(x*244+z*195)*np.cos(y*239-z*172)
    red=(1-ramp(rel,.173+.143*v,.312+.124*v))*(.52+.46*v)
    return n,red


def skin_attrs(obj, rest, tone):
    data = obj.data
    a = data.attributes.new('Rest', 'FLOAT_VECTOR', 'POINT')
    a.data.foreach_set('vector', (np.asarray(rest)[:,[0,2,1]]*np.array([1.,-1.,1.])).astype(np.float32).ravel())
    n, red = pigment(np.asarray(rest))
    tone = np.column_stack((tone, n, red))
    for j, name in enumerate(('Ventral', 'Crease', 'Pigment', 'Rust')):
        f = data.attributes.new(name, 'FLOAT', 'POINT')
        f.data.foreach_set('value', np.asarray(tone[:, j], dtype=np.float32))


def polygon_strip(ids, faces):
    for a, b in zip(ids[:-1], ids[1:]):
        n = len(a)
        faces.extend((a[j], a[(j+1) % n], b[(j+1) % n], b[j]) for j in range(n))


# x-z sections (center z, half width, dorsal height, ventral height).
PROFILE = [
    (-3.86,.125,.002,.001,.001),(-3.78,.134,.034,.023,.017),(-3.49,.163,.067,.041,.033),
    (-3.14,.188,.096,.056,.049),(-2.81,.233,.124,.079,.069),(-2.40,.280,.153,.109,.088),
    (-2.01,.332,.184,.135,.112),(-1.62,.377,.243,.163,.140),(-1.29,.423,.319,.204,.178),
    (-1.02,.485,.405,.242,.214),(-.71,.531,.463,.270,.234),(-.33,.546,.507,.286,.251),
    (.04,.550,.511,.286,.244),(.342,.526,.444,.259,.234),(.64,.484,.350,.217,.199),
    (.907,.477,.312,.180,.176),(1.079,.494,.390,.185,.190),(1.240,.543,.482,.213,.218),
    (1.413,.569,.522,.239,.218),(1.578,.563,.503,.222,.200),(1.702,.549,.455,.184,.171),
    (1.831,.526,.406,.153,.142),(1.966,.502,.367,.126,.123),(2.083,.494,.329,.116,.108),
    (2.171,.494,.257,.107,.095),(2.240,.500,.174,.083,.069),(2.285,.512,.091,.051,.042),
    (2.312,.516,.001,.002,.002),
]


def section(ys, phi):
    h, wide, high, low = spline(PROFILE, ys.ravel()).T
    h, wide, high, low = [v.reshape(ys.shape) for v in (h, wide, high, low)]
    c, s = np.cos(phi), np.sin(phi)
    snout = ramp(ys, 1.06, 1.50) * (1-ramp(ys, 2.27, 2.312))
    x = wide * np.sign(c) * np.abs(c)**(1-.14*snout)
    z = h + np.where(s > 0, high, low) * np.sign(s) * np.abs(s)**(1-.124*snout)
    # Staggered orbit volumes are part of the head surface, not stuck-on beads.
    dorsal = ramp(s, -.31, .63)
    skull = .030 * np.exp(-((ys-1.494)/.214)**2 - ((np.abs(c)-.80)/.186)**2) * dorsal
    x += np.sign(c) * skull * .74
    z += skull * .42
    # Thin mouth line, gently rising at the corner; deliberately not a smile.
    line = -.140 - .113*ramp(ys, 1.37, 2.27) + .082*np.exp(-((ys-1.225)/.15)**2)
    line_mask = ramp(ys,1.086,1.233)*(1-ramp(ys,2.284,2.311))
    mouth = np.exp(-((s-line)/.037)**2) * line_mask
    lip = np.exp(-((s-line-.065)/.038)**2) * line_mask
    x += np.sign(c) * (.008*lip - .012*mouth)
    # Muzzle prenasal depressions and ear openings in the skin surface.
    nostril = np.exp(-((ys-2.073)/.043)**2 - ((s-.463)/.085)**2) * (np.abs(c)>.51)
    ear = np.exp(-((ys-1.059)/.044)**2 - ((s+.065)/.106)**2) * (np.abs(c)>.57)
    x -= np.sign(c) * (.010*nostril+.010*ear)
    z -= .007*nostril
    shade = np.maximum(np.maximum(mouth*.92, nostril), ear*.72)
    tones = np.stack((1-ramp(s,-.29,.09),shade),axis=-1)
    return np.stack((x,ys,z),axis=-1),tones


def deform(raw, p):
    def rotation(a, b, theta):
        return a*np.cos(theta)+b*np.sin(theta), b*np.cos(theta)-a*np.sin(theta)
    x,y,z = raw[..., 0].copy(),raw[...,1].copy(),raw[...,2].copy()
    y -= .171*ramp(y,1.399,2.31)
    tail = 1-ramp(y, -3.79, -.79)
    x += .331 * tail**1.23 + (.051 + .039*np.sin(p['t']*1.66-y*2.48))*tail*np.cos(y*1.35+.44)
    x += p.get('tailFollow',0.) * tail**1.78
    x += p['twist'] * np.clip(y,-.95,1.05)
    z += .014 * tail * np.sin(p['t']*1.69-y*1.56)
    breath = .010*np.sin(3.01*p['t']+y*2.0)*ramp(y,-1.19,-.67)*(1-ramp(y,.48,1.06))
    z += breath * ramp(z,.42,.79)
    x,z = rotation(x,z-.48,-p['roll']*.77)
    z += .48
    h = ramp(y,.84,1.34)
    x,y1 = rotation(x,y-.98,p['headAngle']*h)
    y = y1 + .98
    y1,z = rotation(y-.92,z-.48,-.117*np.sin(p['headLift']*5.7)*h)
    z += .48 + p['headLift']*h
    return np.stack((x+p['x'],y1+.92+p['y'],z+p['z']),axis=-1)


class Animal:
    def __init__(self, bind, skin):
        self.rows, self.sides = 210, 112
        self.lin = np.linspace(-3.86,2.312,self.rows)
        self.phi = np.linspace(-math.pi/2,1.5*math.pi,self.sides,endpoint=False)
        ys, ang = np.meshgrid(self.lin,self.phi,indexing='ij')
        self.raw,self.tone = section(ys,ang)
        # Scattered low ridges and bumps break the profile independently of bump mapping.
        rng=np.random.default_rng(405651)
        grain=np.zeros(ys.shape)
        for yc,pc,a,w in zip(rng.uniform(-2.5,1.84,294),rng.uniform(-.34,3.48,294),rng.uniform(.003,.018,294),rng.uniform(.025,.066,294)):
            dp=(ang-pc+math.pi) % TAU - math.pi
            grain+=a*np.exp(-((ys-yc)/w)**2-(dp/(.082+1.13*w))**2)
        self.raw[:,:,0]+=grain*np.cos(ang)*.69
        self.raw[:,:,2]+=grain*np.sin(ang)
        self.holes=[]
        grid=np.arange(self.rows*self.sides).reshape(self.rows,self.sides)
        mask=np.ones((self.rows-1,self.sides),dtype=bool)
        all_rings=[]
        base_faces=[]
        next_index=int(grid.size)
        for i,q in enumerate(bind['limbs']):
            center=.70 if q['front'] else -.818
            idx=int(np.argmin(np.abs(self.lin-center)))
            k0,k1=idx-(7 if q['front'] else 9),idx+(7 if q['front'] else 9)
            at=-.225 if q['side']>0 else math.pi+.225
            j0=int(np.argmin(np.abs(self.phi-at)))-9
            j1=j0+18
            mask[k0:k1,j0:j1]=False
            seq=list(grid[k0:k1,j0])+list(grid[k1,j0:j1])+list(grid[k1:k0:-1,j1])+list(grid[k0,j1:j0:-1])
            # Even angular spacing is derived from the actual opening, not the vertex count.
            hole=self.raw.reshape(-1,3)[seq]
            hole_center=hole.mean(axis=0)
            axis=(hole-hole_center)
            phi0=np.unwrap(np.arctan2(q['side']*axis[:,2],axis[:,1]))
            self.holes.append((seq,phi0,hole_center,q['front'],q['side']))
            section_count=44
            patch=np.arange(next_index,next_index+section_count*len(seq)).reshape(section_count,len(seq))
            next_index+=patch.size
            polygon_strip([seq,*patch],all_rings)
            all_rings.append(tuple(patch[-1]))
        for k,j in zip(*np.where(mask)):
            j1=(j+1)%self.sides
            base_faces.append((grid[k,j],grid[k+1,j],grid[k+1,j1],grid[k,j1]))
        base_faces.extend((tuple(grid[0]),tuple(grid[-1][::-1])))
        points,tone=self.points(bind)
        self.obj=mesh('Tokay • one continuous shoulder and hip skin',points,base_faces+all_rings,skin)
        skin_attrs(self.obj,points,tone)

    def points(self,p):
        body=deform(self.raw,p).reshape(-1,3)
        parts=[body]; palette=[self.tone.reshape(-1,2)]
        for (seq,angles,_,front,side),q in zip(self.holes,p['limbs']):
            boundary=body[seq]
            hinge=np.asarray(q['shoulder']);elbow=np.asarray(q['knee']);wrist=np.asarray(q['wrist'])
            x,y,z=q['at']; a=q['yaw']; f=np.array([math.sin(a),math.cos(a),0.])
            end=np.array([x,y,z])+.121*f+np.array([0.,0.,.047])
            a0=boundary.mean(axis=0)
            a1=hinge*.33+elbow*.67
            pad=np.array([x,y,z])+.048*f+np.array([0.,0.,.061])
            key=np.array([a0,a1,elbow,.62*elbow+.38*wrist,wrist,pad,end])
            kn=np.array([0,.211,.419,.566,.785,.894,1.])
            u=np.linspace(0,1,45)
            centers=spline(np.column_stack([kn,key]), u)
            for _ in range(5):
                centers[1:-1]=.205*centers[:-2]+.590*centers[1:-1]+.205*centers[2:]
            tangent=normalize(np.gradient(centers,axis=0))
            uaxis=np.empty_like(tangent)
            ref=np.array([0.,1.,0.])
            for j,td in enumerate(tangent):
                ref=normalize(ref-np.dot(td,ref)*td)
                uaxis[j]=ref
            vaxis=np.cross(tangent,uaxis)
            sideway=np.array([f[1],-f[0],0.])
            # Parallel transport across the elbow, then flatten the palm against the pane.
            phi=np.arctan2(vaxis@sideway,uaxis@sideway)[-1]
            sweep=ramp(u,.673,.968)*phi
            up=uaxis*np.cos(sweep[:,None])+vaxis*np.sin(sweep[:,None])
            back=np.cross(tangent,up)
            size=spline([[0,.185,.166],[.19,.156 if front else .209,.147 if front else .164],
                         [.375,.103 if front else .151,.098 if front else .135],[.55,.112 if front else .124,.100],
                         [.73,.068,.057],[.804,.069,.047],[.911,.110 if front else .119,.056],[.98,.080,.039],[1,.003,.003]],u)
            offset=(up[:,None,:]*np.cos(angles)[None,:,None]*size[:,0,None,None]
                    +back[:,None,:]*np.sin(angles)[None,:,None]*size[:,1,None,None])
            join = (1-ramp(u,.0,.213))[:,None,None]
            attached=centers[:,None,:] + offset + join*(boundary[None,:,:]-a0[None,None,:]-offset[0:1])
            normal=normalize(attached-centers[:,None,:])
            attached[...,2]=np.maximum(attached[...,2],.003+z*ramp(u,.52,.89)[:,None])
            tone=np.stack((1-ramp(normal[:,:,2],-.25,.36),np.zeros(normal.shape[:2])),axis=-1)
            parts.append(attached[1:].reshape(-1,3));palette.append(tone[1:].reshape(-1,2))
        return np.concatenate(parts),np.concatenate(palette)

    def update(self,p):
        put(self.obj,self.points(p)[0])


def digits_surface(path, base, yaw):
    pts=np.asarray(path)
    s=np.linspace(0,1,len(pts))
    dx,dy=math.sin(yaw),math.cos(yaw)
    side=np.array([dy,-dx,0.])
    along=np.array([dx,dy,0.])
    roll=pts[:,2]
    up=-np.sin(roll[:,None])*along[None,:]
    up[:,2]=np.cos(roll)
    c=np.asarray(base)[None,:]+pts[:,0,None]*along[None,:]
    c[:,2]+=pts[:,1]+pts[:,4]+.00195
    phi=np.linspace(0,TAU,24,endpoint=False)
    sp,cp=np.sin(phi),np.cos(phi)
    # Continuous pad, gently squared plantar surface. Inset transverse folds
    # are carved into that skin; there are no floating ridges or bead joints.
    amp=ramp(s,.27,.342)*(1-ramp(s,.841,.938))
    ridges=(.5+.5*np.cos(TAU*(s*14.53+.094)))**3.4
    dim = pts[:,4,None]*np.sign(sp)[None,:]*np.abs(sp[None,:])**.69
    dim += (amp*ridges)[:,None]*.0051*np.maximum(0.,-sp[None,:])**3
    p=c[:,None,:]+side[None,None,:]*pts[:,3,None,None]*np.sign(cp[None,:,None])*np.abs(cp[None,:,None])**.88+up[:,None,:]*dim[:,:,None]
    tone=np.stack((np.tile(1-ramp(sp,-.24,.11),(len(s),1)),np.zeros((len(s),len(phi)))),axis=-1)
    toe=pts[-2]
    tip=c[-2] + up[-2]*(toe[4]-.005)
    heading=along*math.cos(roll[-2])+np.array([0,0,math.sin(roll[-2])])
    return p.reshape(-1,3),tone.reshape(-1,2),tip,heading,side,up[-2]


class Digits:
    def __init__(self,bind,skin,claw_mat):
        self.items=[]
        for l in bind['limbs']:
            for j,d in enumerate(l['digits']):
                p,tone,tip,tan,side,up=digits_surface(d['points'],d['base'],d['yaw'])
                num=len(d['points']); ring=np.arange(num*24).reshape(num,24)
                f=[]; polygon_strip([row[::-1] for row in ring],f)
                # Last ring at the claw-free tip and the buried heel cap.
                f.extend((tuple(ring[0]),tuple(ring[-1][::-1])))
                ob=mesh(f'Continuous digital pad {len(self.items)+1:02}',p,f,skin)
                skin_attrs(ob,p,tone)
                nail=None
                if j>0:
                    rr=np.arange(9*11).reshape(9,11)
                    faces=[]; polygon_strip([row[::-1] for row in rr],faces)
                    nail=mesh('Recessed keratin tip',self.claw(tip,tan,side,up),faces,claw_mat)
                self.items.append((ob,nail))

    @staticmethod
    def claw(tip,tan,side,up):
        u=np.linspace(0,1,9)
        c=tip[None,:]+(u[:,None]-.18)*.042*tan[None,:]+(.003+.012*np.sin(u*2.93)-.008*u*u)[:,None]*up[None,:]
        phi=np.linspace(0,TAU,11,endpoint=False)
        rr=.0107*(1-u)**.71+.00051
        return (c[:,None,:]+side[None,None,:]*(rr[:,None]*np.cos(phi)[None,:])[:,:,None]+up[None,None,:]*(rr[:,None]*np.sin(phi)[None,:])[:,:,None]).reshape(-1,3)

    def update(self,p):
        min_z = math.inf
        for q,(ob,nail) in zip((q for leg in p['limbs'] for q in leg['digits']),self.items):
            a,_,tip,tan,side,up=digits_surface(q['points'],q['base'],q['yaw'])
            min_z = min(min_z,float(np.min(a[:,2])))
            put(ob,a)
            if nail: put(nail,self.claw(tip,tan,side,up))
        if min_z < -1e-5:
            raise ValueError(f'Pad crosses glass at {p["t"]:.4f}s by {-min_z:.5f} local units')
        return min_z


def eye_texture():
    n=512
    y,x=np.meshgrid(np.linspace(-1,1,n),np.linspace(-1,1,n),indexing='ij')
    a=np.arctan2(y,x);r=np.hypot(x,y)
    veins=(.5+.5*np.sin(66*a + 1.9*np.sin(r*19+a*7) + 1.13*np.sin(9*a)))**8.9
    rough=.5*np.sin(a*43+r*19+np.sin(a*8+r*21)*2.64)+.27*np.sin(r*26+5*a)+.23*np.sin(a*129-r*9)
    freckles=np.maximum(0,np.sin(x*263+.36*np.sin(y*579))*np.sin(y*396+x*176))**7
    gain=(.64+.28*rough+.17*np.exp(-((r-.43)/.38)**2)-.29*veins-.33*freckles) * (1-ramp(r,.72,1.03)*.77)
    base=np.clip(gain[:,:,None]*np.array([.446,.217,.047])[None,None,:]+np.array([.014,.011,.010])[None,None,:],0,1)
    # Gaze is rolled slightly as the head leans into its wall-climbing pose.
    py = -.58*x+.8146*y
    pupil_x = .8146*x+.58*y+.024 + .017*np.sin(py*5.0)
    width=.064*(np.clip(1-(py/.863)**2,0,1)**.61) + .017*np.exp(-((py-.24)/.07)**2)+.011*np.exp(-((py+.35)/.075)**2)
    pupil=(1-ramp(np.abs(pupil_x),width-.009,width+.007))*(1-ramp(np.abs(py),.825,.868))
    base=base*(1-pupil[:,:,None])+np.array([.0043,.0052,.0055])[None,None,:]*pupil[:,:,None]
    img=bpy.data.images.new('Painted radial amber iris (linear)',width=n,height=n,alpha=True,float_buffer=True)
    img.colorspace_settings.name='Linear Rec.709'
    img.pixels.foreach_set(np.concatenate([base,np.ones((n,n,1))],axis=2).astype(np.float32).ravel())
    img.update()
    return img


class Eyes:
    def __init__(self,bind,skin,iris,*,fade_ventral_bank=False):
        self.eye=[]
        for side in (-1,1):
            phi=.405 if side==1 else math.pi-.405
            v=section(np.array([1.540]),np.array([phi]))[0][0]
            n=normalize(np.array([side*.893,.192,.438]))
            h=normalize(np.array([0.,-.062,1.])-n*np.dot(n,[0.,-.062,1.]))
            w=np.cross(h,n)
            # Recess the eye into the orbit. The dorsal rim rises above the lens at the edge.
            center=v-n*.083
            n_side=84
            r=np.linspace(.0001,1,23)
            a=np.arange(n_side)*TAU/n_side
            s,c=np.sin(a),np.cos(a)
            rx=.143*(1+.12*c*side-.05*s)*c
            ry=.136*s*(1-.13*np.abs(c))
            iris_profile=.056+.109*np.sqrt(np.maximum(0,1-(r*.876)**2))
            sphere=(center[None,None,:]+r[:,None,None]*(w[None,None,:]*rx[None,:,None]+h[None,None,:]*ry[None,:,None])+iris_profile[:,None,None]*n[None,None,:])
            uv=np.stack([.5+r[:,None]*c[None,:]*.502,.5+r[:,None]*s[None,:]*.502],axis=-1).reshape(-1,2)
            faces=[];polygon_strip([row[::-1] for row in np.arange(sphere.shape[0]*n_side).reshape(-1,n_side)],faces)
            raw=sphere.reshape(-1,3)
            lens=mesh('Seated amber spectacle',deform(raw,bind),faces,iris,uv)
            r=np.linspace(.88,1.45,13)
            lip=np.maximum(s,0)
            depth=np.interp(r,[.88,.986,1.083,1.22,1.45],[.119,.121,.114,.055,-.154])
            lipshape=(.004+.022*lip)[None,:]*np.exp(-((r[:,None]-1.07)/.18)**2)
            if fade_ventral_bank:
                # Behind the spectacle, bury the lower rim into the pale jaw
                # rather than letting a small pigmented sliver break through.
                lipshape-=.117*ramp(r[:,None],1.035,1.29)*np.maximum(-s,.18)[None,:]
            bank=(center[None,None,:]+r[:,None,None]*(w[None,None,:]*rx[None,:,None]+h[None,None,:]*ry[None,:,None])
                  +(depth[:,None]+lipshape)[...,None]*n[None,None,:])
            ring=[];polygon_strip([row[::-1] for row in np.arange(bank.shape[0]*n_side).reshape(-1,n_side)],ring)
            orb=mesh('Raised integrated brow / spectacle rim',deform(bank.reshape(-1,3),bind),ring,skin)
            shadow=np.repeat(.51*(1-ramp(r,.89,1.081)),n_side)
            skin_attrs(orb,deform(bank.reshape(-1,3),bind),np.stack((np.zeros(shadow.shape),shadow),axis=1))
            self.eye.extend(((lens,raw),(orb,bank.reshape(-1,3))))

    def update(self,p):
        for ob,raw in self.eye: put(ob,deform(raw,p))
