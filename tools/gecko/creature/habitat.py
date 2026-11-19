"""Geometry between the camera and a far photographic matte gives real parallax."""
import math
import bpy
import numpy as np
from geometry import W, UNIT, mesh, spline, normalize
from surface import bark_surface, panel_surface, plant_surface, plate_surface, rgb, simple


def rect(name,x0,x1,y0,y1,z,mat):
    return mesh(name,[(x0,y0,z),(x1,y0,z),(x1,y1,z),(x0,y1,z)],[(0,1,2,3)],mat,[(0,0),(1,0),(1,1),(0,1)],shading=False)


def bough(name,points,width,bark,seed):
    points=np.asarray(points)
    n=36; k=22
    u=np.linspace(0,1,n)
    path=spline(np.column_stack((np.linspace(0,1,len(points)),points)),u)
    vec=normalize(np.gradient(path,axis=0))
    base=normalize(np.cross(vec,[.13,-.14,1.1]))
    binorm=np.cross(vec,base)
    ph=np.linspace(0,2*math.pi,k+1)
    ca,sa=np.cos(ph),np.sin(ph)
    ridges=1.+.127*np.sin(5.0*ph[None,:]+u[:,None]*8.37+seed)+.094*np.sin(9.*ph[None,:]-u[:,None]*7.5)
    d=width*(.51+.51*(1-u)**.44)*ridges.T
    pts=path[None,:,:]+(base[None,:,:]*ca[:,None,None]+binorm[None,:,:]*sa[:,None,None])*d[...,None]
    uv=np.stack(np.meshgrid(np.linspace(0,1,k+1),u,indexing='ij'),axis=-1)
    faces=[(j*n+i, (j+1)*n+i, (j+1)*n+i+1, j*n+i+1) for j in range(k) for i in range(n-1)]
    return mesh(name,pts.reshape(-1,3),faces,bark,uv.reshape(-1,2))


def leaf(name,from_,direction,length,wide,tint,phase):
    pos=np.asarray(from_); a=normalize(np.asarray(direction))
    b=normalize(np.cross(a,[0.,0.,1.]));n=np.cross(b,a)
    bend=.106*math.cos(phase)
    nn,nw=22,13
    u,s=np.meshgrid(np.linspace(0,1,nn),np.linspace(-1,1,nw),indexing='ij')
    bow=(np.maximum(0,np.sin(math.pi*u))**.78)*(.22+.78*(1-.55*u))
    width=bow*wide*(1+.087*np.cos(9*u+s*.6+phase))+.0006
    shape=(u**1.63-.43*u)*length*.48 + bend*u*u - width*(.122+.056*np.cos(u*16))*s*s
    pts=pos+u[...,None]*length*a+s[...,None]*width[...,None]*b+shape[...,None]*n
    ix=np.arange(nn*nw).reshape(nn,nw)
    faces=[(ix[i,j],ix[i,j+1],ix[i+1,j+1],ix[i+1,j]) for i in range(nn-1) for j in range(nw-1)]
    uv=np.stack((s*.5+.5,u),axis=-1)
    return mesh(name,pts.reshape(-1,3),faces,tint,uv.reshape(-1,2))


def setup_habitat(plate_file):
    bark=bark_surface()
    leaf_mats=[plant_surface(i) for i in range(3)]
    # Far layer is never used as the animal's skin, world lighting, or composited creature.
    ob=rect('Conservatory, photographed far layer',-49.4,12.0,-14.30,16.30,-7.24,plate_surface(plate_file))
    ob.visible_diffuse=False;ob.visible_shadow=False
    panel=rect('Dry grip interface at z = 0',-3.87,2.34,-4.25,4.77,0,panel_surface())
    frame=simple('Dark weathered anodized frame','354139',.43,Metallic=.42,Coat_Weight=.17)
    # Slim sash edge on the far side. The camera never crosses the glass plane.
    for xs in (-3.88,2.385):
        bpy.ops.mesh.primitive_cube_add(size=1,location=W((xs,.19,-.040)))
        rail=bpy.context.object;rail.name='Terrarium mullion';rail.scale=(UNIT*.13,UNIT*.165,UNIT*9.22)
        rail.data.materials.append(frame)
        bv=rail.modifiers.new('Old radius','BEVEL');bv.width=.085;bv.segments=3
    bough('Cork root to the left', [(-3.65,-3.95,-1.35),(-3.17,-1.89,-1.81),(-2.88,.06,-2.18),(-3.73,2.54,-2.33),(-4.39,4.2,-2.58)],.69,bark,1.2)
    bough('Receding diagonal branch',[(-4.08,-3.70,-3.89),(-2.97,-2.61,-3.94),(-1.96,-1.59,-4.15),(-.13,.31,-4.25),(1.4,3.25,-4.24)],.305,bark,9.0)
    bough('Wet broken branch at substrate',[(-1.91,-3.50,1.44),(-2.51,-2.86,.84),(-2.76,-2.27,.41),(-2.79,-1.08,.42)],.27,bark,7.41)
    bough('Fork behind the pane',[(-4.78,-1.96,-3.32),(-5.04,-.27,-3.93),(-5.43,1.56,-3.37),(-6.51,3.37,-3.38)],.284,bark,8.93)
    rng=np.random.default_rng(248608)
    for i in range(37):
        if i<11:
            x=rng.uniform(-4.9,-1.8);y=rng.uniform(-3.72,3.8);z=rng.uniform(-2.61,-.96)
        elif i<27:
            x=rng.uniform(-8.8,-.95);y=rng.uniform(-3.0,4.49);z=rng.uniform(-5.75,-3.72)
        else:
            x=rng.uniform(1.89,4.8);y=rng.uniform(-3.77,1.5);z=rng.uniform(-2.97,-1.04)
        d=rng.normal(size=3);d[0]*=1.34;d[1]=abs(d[1])+.15;d[2]*=.67
        leaf(f'Pothos leaf {i+1:02}',[x,y,z],d,rng.uniform(.51,1.6),rng.uniform(.26,.60),leaf_mats[i%3],rng.uniform(0,7))
    leaf('Near fern, lower left edge',(-2.43,-2.55,.81),(1.1,1.47,.58),1.14,.40,leaf_mats[1],2.0)
    leaf('Twisted foreground cuticle',(-3.30,3.46,.44),(-.47,-1.25,.16),1.61,.52,leaf_mats[0],5.9)
    # Only edge-side mineral trace: a real thin mark parallel to the frame, not a
    # diagram. Kept off the toe path and faint enough to retain the clear pane.
    streakmat=simple('Dried hazy trace at the pane edge','697a70',.51,Specular_IOR_Level=.30)
    for i in range(3):
        xs=2.139+i*.054
        yy=-1.31+i*.70
        amp=.008-i*.0016
        w0=np.linspace(0,1,38)
        trace=[]
        for w in w0:
            mid=xs+.007*math.sin(w*8.61+i)+.0038*math.cos(w*7.22)
            width=amp*math.sin(math.pi*w)**.53+.00041
            trace.extend(((mid-width,yy+w*(4.11-i*.63),.00125),(mid+width,yy+w*(4.11-i*.63),.00125)))
        mesh('Hair-thin dry pane trace',trace,[(j,j+1,j+3,j+2) for j in range(0,2*(len(w0)-1),2)],streakmat,shading=False)
    # Tiny dry dust marks are separate from the animal/habitat and off the main footprints.
    speck=simple('Scattered silt on pane','819175',.71,Specular_IOR_Level=.20)
    markp,markf=[],[]
    for i in range(59):
        x=rng.uniform(-3.75,2.29);y=rng.uniform(-3.65,4.50)
        if (-1.45<x<1.94 and .16<y<2.91):continue
        d=rng.uniform(.0015,.007)**1.02*1.59
        j=len(markp)
        markp.extend((x+d*math.cos(th),y+d*.73*math.sin(th),.00137) for th in np.linspace(0,2*math.pi,5,endpoint=False))
        markf.append(tuple(range(j,j+5)))
    if markf: mesh('Infrequent glass dust outside stance',markp,markf,speck,shading=False)
    # Uneven packed ground. Mostly out of frame; its occlusion and bounce anchor the shot.
    gx,gz=np.meshgrid(np.linspace(-6,6,45),np.linspace(-8,5,37),indexing='ij')
    gy=-3.96+.12*np.sin(2.1*gx+gz*.8)+.090*np.sin(6.1*gx+gz*2.66)+.046*rng.normal(size=gx.shape)
    gp=np.stack((gx,gy,gz),axis=-1);ix=np.arange(gx.size).reshape(gx.shape)
    face=[(ix[i,j],ix[i,j+1],ix[i+1,j+1],ix[i+1,j]) for i in range(gx.shape[0]-1) for j in range(gx.shape[1]-1)]
    mesh('Cork fragments and rainforest soil',gp.reshape(-1,3),face,bark,np.stack(((gx+6)/7,(gz+8)/6),axis=-1).reshape(-1,2))
    return panel


def area(name,place,aim,power,light_color,size,secondary=None):
    dat=bpy.data.lights.new(name,'AREA');ob=bpy.data.objects.new(name,dat);bpy.context.collection.objects.link(ob)
    ob.location=W(place);ob.rotation_euler=(W(aim)-ob.location).to_track_quat('-Z','Y').to_euler()
    dat.energy=power*UNIT**2;dat.color=rgb(light_color)[:3]
    dat.shape='RECTANGLE' if secondary else 'DISK';dat.size=size*UNIT
    if secondary:dat.size_y=secondary*UNIT
    return ob


def light():
    world=bpy.data.worlds.new('Muted post-storm sky')
    world.use_nodes=True
    world.node_tree.nodes.get('Background').inputs[0].default_value=rgb('b1c7cc')
    world.node_tree.nodes.get('Background').inputs[1].default_value=.182
    bpy.context.scene.world=world
    area('Warm broken skylight / lateral',(.55,4.84,2.48),(.33,1.02,.24),201,'fff0d8',2.37,3.18)
    area('Cool pane rim',(2.37,3.32,-1.60),(.28,.74,.31),110,'c2e9ff',1.50,2.92)
    area('Close soft fill',(4.75,1.21,3.91),(.23,1.12,.31),36,'e9e2d2',3.97,3.21)
    area('Small cornea catchlight',(3.22,3.93,3.0),(.56,1.5,.61),15,'f6e8d9',.71,1.04)
    area('Side bounce near toe edge',(3.81,-1.48,1.48),(1.05,1.51,.092),29,'c6d5e0',1.67,2.33)
