"""Two-sided window stage. The plane stays fixed across the entire climb."""
import math
import bpy
import numpy as np
from geometry import UNIT, W, mesh, Digits, ramp
from habitat import area, bough, leaf, rect
from surface import Graph, bark_surface, plant_surface, plate_surface, simple, rgb


class LamellarDigits(Digits):
    def __init__(self,bind,skin,claw):
        super().__init__(bind,skin,claw)
        for ob,_ in self.items:
            u=np.linspace(0,1,len(ob.data.vertices)//24)[:,None]
            phi=np.arange(24)[None,:]*math.tau/24.
            plantar=np.maximum(0,-np.sin(phi))**1.67*ramp(u,.247,.34)*(1-ramp(u,.841,.939))
            seam=plantar*(.5+.5*np.cos(math.tau*(14.53*u+.112-.135*np.cos(phi)**2)))**4.6
            for name,arr in [('LamellarFold',seam),('PlantarPad',plantar)]:
                att=ob.data.attributes.new(name,'FLOAT','POINT')
                att.data.foreach_set('value',arr.ravel().astype(np.float32))


def window_glass():
    g=Graph('Dry continuous glass / restrained soft reflection')
    clear=g.n('ShaderNodeBsdfTransparent');clear.inputs[0].default_value=rgb('fcfdfb')
    gloss=g.n('ShaderNodeBsdfGlossy');gloss.inputs['Color'].default_value=rgb('dae7e0');gloss.inputs['Roughness'].default_value=.129
    fr=g.n('ShaderNodeFresnel');fr.inputs['IOR'].default_value=1.44
    refl=g.op('MINIMUM',g.op('MULTIPLY',fr.outputs[0],.72),.15)
    scatter=g.mixshader(refl,clear.outputs[0],gloss.outputs[0])
    return g.set(g.mixshader(g.n('ShaderNodeLightPath').outputs['Is Shadow Ray'],scatter,clear.outputs[0]))


def habitat(plate_file):
    # Outside and inside matte layers remain where they are when the reverse
    # camera looks through the same glass. No composited copy of the foot.
    for z, name in [(-10.62,'Far canopy on the north side'),(10.88,'Far canopy on the south side')]:
        ob=rect(name,-61,36,-12.9,16.8,z,plate_surface(plate_file))
        ob.visible_diffuse=False;ob.visible_shadow=False;ob.visible_glossy=False
    rect('Continuous dry observation pane',-3.01,2.84,-7.15,7.85,0,window_glass())
    trim=simple('Worn dark bronze sash','38463f',.465,Metallic=.38,Coat_Weight=.16)
    lip=simple('Scraped narrow glass edge','58695f',.39,Metallic=.30,Coat_Weight=.235)
    for x in (-3.064,2.884):
        for ab,thick,z,mat in [(x,.166,-.040,trim),(x+(1 if x<0 else -1)*.087,.024,.008,lip)]:
            bpy.ops.mesh.primitive_cube_add(size=1,location=W((ab,.32,z)))
            obj=bpy.context.object;obj.name='Soft-edged observation rail'
            obj.scale=(UNIT*thick,UNIT*.124,UNIT*15.18);obj.data.materials.append(mat)
            bevel=obj.modifiers.new('Rounded top edge','BEVEL');bevel.width=.091;bevel.segments=3
    bark=bark_surface()
    outdoors=[
        ('Root near the left rim',[(-3.76,-7.48,-1.44),(-3.45,-4.49,-1.75),(-2.99,-1.34,-2.19),(-3.66,1.9,-2.61),(-4.34,6.75,-2.95)],.64,1.2),
        ('Far diagonal cork',[(-5.55,-6.74,-3.83),(-4.84,-4.03,-3.99),(-3.99,-.79,-4.12),(-2.17,2.67,-4.31),(-.61,6.73,-4.3)],.370,9.),
        ('High liana away from feet',[(4.2,7.48,-4.14),(2.92,5.44,-3.78),(2.52,4.35,-3.58),(2.97,2.62,-3.41)],.418,10.3),
        ('Twigs in lower side', [(-4.32,-6.29,-2.2),(-3.56,-4.11,-2.22),(-2.64,-3.51,-2.83),(-1.28,-2.77,-3.53)],.178,3.39),
        ('Cork silhouettes at the right edge',[(5.35,-7.07,3.89),(6.01,-4.78,4.8),(5.00,-2.11,4.97),(5.82,.715,5.38),(5.42,3.98,5.23)],.49,7.1),
        ('Vine on the reverse side',[(-3.44,-6.93,1.69),(-3.57,-4.35,2.4),(-3.08,-1.72,2.74),(-3.58,1.57,3.45),(-4.46,4.34,4.08)],.33,5.32),
        ('Deep fork behind underside',[(1.58,-6.24,6.61),(1.48,-3.87,7.11),(.18,-1.13,7.19),(-2.41,4.98,7.87)],.19,11.164),
    ]
    for name,pts,w,seed in outdoors: bough(name,pts,w,bark,seed)
    mats=[plant_surface(i) for i in range(3)]
    rng=np.random.default_rng(469098)
    for i in range(52):
        sign = 1 if i>33 else -1
        xx = rng.uniform(-8.15,-2.39) if i%3 else rng.uniform(2.18,6.4)
        yy = rng.uniform(-6.74,7.57)
        zz = sign*rng.uniform(2.28,6.05)
        d=rng.normal(size=3);d[0]*=1.19;d[1]=abs(d[1])+.18;d[2]*=.59
        leaf(f'Habitat depth leaf {i+1}',[xx,yy,zz],d,rng.uniform(.59,1.98),rng.uniform(.23,.52),mats[i%3],rng.uniform(0,7))
    # Very few mineral marks on the pane edge, never across a footprint.
    silt=simple('Dry mineral flecks beside the pane','76887a',.65,Specular_IOR_Level=.18)
    points=[];faces=[]
    for i in range(195):
        x=rng.choice([-1,1])*rng.uniform(1.89,2.79);y=rng.uniform(-6.9,7.4)
        r=rng.uniform(.0024,.012)*1.03
        f=len(points)
        points.extend((x+math.cos(a)*r,y+math.sin(a)*r*.71,.00139) for a in np.arange(5)*math.tau/5)
        faces.append(tuple(range(f,f+5)))
    mesh('Sparse dry surface etching',points,faces,silt,shading=False)
    gx,gz=np.meshgrid(np.linspace(-8,8,44),np.linspace(-8,8,33),indexing='ij')
    gy=-7.12+.11*np.cos(gx*1.78+gz)+.07*np.sin(gx*7.93-gz*5.31)+rng.normal(0,.043,gx.shape)
    ix=np.arange(gx.size).reshape(gx.shape)
    f=[(ix[i,j],ix[i,j+1],ix[i+1,j+1],ix[i+1,j]) for i in range(gx.shape[0]-1) for j in range(gx.shape[1]-1)]
    mesh('Layered cork substrate',np.stack((gx,gy,gz),axis=-1).reshape(-1,3),f,bark,np.stack((gx/7,gz/6),axis=-1).reshape(-1,2))


def lighting():
    world=bpy.data.worlds.new('Night garden overcast')
    world.use_nodes=True
    sky=world.node_tree.nodes.get('Background')
    sky.inputs[0].default_value=rgb('bbced0');sky.inputs[1].default_value=.179
    bpy.context.scene.world=world
    sources=[
        ('Filtered warm skylight',(.35,3.54,4.08),(.005,.60,.31),303,'fff0dd',2.75,3.70),
        ('Cool pane fill and throat bounce',(-2.72,2.83,-2.95),(.29,.83,.24),102,'c4e7f5',2.89,3.68),
        ('Dorsal side fill',(-4.04,1.28,2.37),(-.06,.56,.45),36,'e7e8d9',4.16,3.2),
        ('Rim from below through canopy', (3.09,-.63,-1.81),(.48,.14,.32),68,'e0e4c5',1.75,2.51),
        ('Eye catchlight', (2.27,2.46,1.77),(.54,1.42,.68),21,'fff0d8',.73,1.22),
    ]
    lamps=[area(*src) for src in sources]
    def at(p):
        body=p['y'];c=p['camera'];back=c.get('side')=='beneath'
        for i,(ob,src) in enumerate(zip(lamps,sources)):
            _,xyz,aim,power,*_=src
            if i==4 and p['shot'] in ('eye','hero-eye'):
                focus=c['focus'];x,y,z=(focus[0]+1.78,focus[1]+1.14,focus[2]+.844);a=focus
            else:
                x,y,z=xyz; y+=body*.76; a=(aim[0]+p['x']*.23,aim[1]+body,aim[2])
            ob.location=W((x,y,z));ob.rotation_euler=(W(a)-ob.location).to_track_quat('-Z','Y').to_euler()
            ob.data.energy=power*UNIT**2 * ((.95 if i==0 else 1.38 if i in (1,3) else .65) if back else 1)
            if p['shot'] in ('replay','recap-peel') and i==4: ob.data.energy*=.47
    return at
