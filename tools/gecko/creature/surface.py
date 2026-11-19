"""Path-traced materials: pigment, relief and lobe response are independent."""
import bpy
import numpy as np
from geometry import UNIT


def rgb(h):
    if not isinstance(h,str): return (*h[:3],1)
    s=[int(h[i:i+2],16)/255 for i in (0,2,4)]
    return tuple(x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4 for x in s)+(1.,)


class Graph:
    def __init__(self,name):
        self.mat=bpy.data.materials.new(name)
        self.mat.use_nodes=True
        self.N=self.mat.node_tree.nodes
        self.N.clear()
        self.L=self.mat.node_tree.links
        self.sink=self.n('ShaderNodeOutputMaterial')

    def n(self,t,label=None):
        n=self.N.new(t)
        if label: n.label=label
        return n

    def hit(self,n,key,value):
        s=n.inputs[key]
        if isinstance(value,bpy.types.NodeSocket): self.L.new(value,s)
        else: s.default_value=value

    def ramp(self,fac,colors,interp='EASE'):
        n=self.n('ShaderNodeValToRGB');n.color_ramp.interpolation=interp
        for i,(p,c) in enumerate(colors):
            e=n.color_ramp.elements[i] if i<2 else n.color_ramp.elements.new(p)
            e.position=p; e.color=rgb(c) if isinstance(c,str) else (c,c,c,1) if isinstance(c,(int,float)) else rgb(c)
        self.hit(n,'Fac',fac)
        return n.outputs['Color']

    def noise(self,p,scale,detail=2,rough=.63,dist=0):
        n=self.n('ShaderNodeTexNoise')
        self.hit(n,'Vector',p);self.hit(n,'Scale',scale);self.hit(n,'Detail',detail);self.hit(n,'Roughness',rough);self.hit(n,'Distortion',dist)
        return n.outputs

    def vor(self,p,scale,feature='DISTANCE_TO_EDGE'):
        n=self.n('ShaderNodeTexVoronoi');n.feature=feature
        self.hit(n,'Vector',p);self.hit(n,'Scale',scale)
        return n.outputs['Distance']

    def attr(self,attr,key):
        n=self.n('ShaderNodeAttribute');n.attribute_name=attr
        return n.outputs[key]

    def op(self,t,*vals):
        n=self.n('ShaderNodeMath');n.operation=t
        for i,x in enumerate(vals): self.hit(n,i,x)
        return n.outputs[0]

    def vec(self,t,a,b):
        n=self.n('ShaderNodeVectorMath');n.operation=t;self.hit(n,0,a);self.hit(n,3 if t=='SCALE' else 1,b)
        return n.outputs[0]

    def blend(self,fac,a,b,t='MIX'):
        n=self.n('ShaderNodeMixRGB');n.blend_type=t
        for i,x in enumerate((fac,a,b)): self.hit(n,i,x)
        return n.outputs[0]

    def mixshader(self,fac,a,b):
        n=self.n('ShaderNodeMixShader');self.hit(n,0,fac);self.hit(n,1,a);self.hit(n,2,b)
        return n.outputs[0]

    def bump(self,height,dist,strength=.65,normal=None):
        n=self.n('ShaderNodeBump');self.hit(n,'Height',height);self.hit(n,'Distance',UNIT*dist);self.hit(n,'Strength',strength)
        if normal: self.hit(n,'Normal',normal)
        return n.outputs['Normal']

    def pbr(self,col,rough,normal=None,**kwargs):
        n=self.n('ShaderNodeBsdfPrincipled');self.hit(n,'Base Color',col);self.hit(n,'Roughness',rough)
        if normal: self.hit(n,'Normal',normal)
        for k,v in kwargs.items(): self.hit(n,k.replace('_',' '),v)
        return n.outputs['BSDF']

    def set(self,bsdf):
        self.hit(self.sink,'Surface',bsdf)
        return self.mat


def scale_tile():
    n,cells=512,11
    x,y=np.meshgrid(np.arange(n)/n*cells,np.arange(n)/n*cells)
    fx,fy=np.floor(x).astype(int),np.floor(y).astype(int)
    r=np.random.default_rng(55847).uniform(.14,.86,(cells,cells,2))
    d0=np.full_like(x,4.);d1=d0.copy()
    for i in (-1,0,1):
        for j in (-1,0,1):
            a,b=fx+i,fy+j
            rxy=r[a%cells,b%cells]
            d=(x-a-rxy[:,:,0])**2+(y-b-rxy[:,:,1])**2
            d1=np.minimum(np.maximum(d0,d),d1)
            d0=np.minimum(d0,d)
    edge=np.maximum(0,np.sqrt(d1)-np.sqrt(d0))
    h=np.clip(edge*3.16,0,1)
    h=h*h*(3-2*h)*.81 + .083*np.sin(x*43.26+y*61.97)*np.sin(y*42.18-x*57.3)*np.clip(edge*4.8,0,1)
    h=np.clip(h,.026,1.)
    img=bpy.data.images.new('Periodic reptile scales / relief',width=n,height=n,alpha=False,float_buffer=True)
    img.colorspace_settings.name='Non-Color'
    px=np.stack([h,h,h,np.ones_like(h)],axis=-1).astype(np.float32)
    img.pixels.foreach_set(px.ravel());img.update()
    return img


def skin_surface(with_pad_folds=False):
    g=Graph('Tokay integument / baked bind colour, relief and satin scatter')
    p=g.attr('Rest','Vector');ventral=g.attr('Ventral','Fac');crease=g.attr('Crease','Fac')
    macro=g.attr('Pigment','Fac'); rust=g.attr('Rust','Fac')
    dorsal=g.ramp(macro,[(.244,'2b4046'),(.47,'576b74'),(.73,'829599')])
    spots=g.ramp(macro,[(.23,'744332'),(.47,'b87148'),(.74,'d69564')])
    color=g.blend(rust,dorsal,spots)
    belly=g.ramp(macro,[(.244,'716f64'),(.47,'a9a38d'),(.77,'c6b9a2')])
    color=g.blend(ventral,color,belly)
    color=g.blend(g.op('MULTIPLY',crease,.86),color,rgb('2a2222'))
    scales=g.n('ShaderNodeTexImage');scales.image=scale_tile();scales.projection='BOX';scales.projection_blend=.385;scales.extension='REPEAT'
    theta=g.vec('SCALE',p,4.83);g.hit(scales,'Vector',theta)
    height=scales.outputs['Color']
    color=g.blend(.19,color,height,'MULTIPLY')
    normal=g.bump(height,.0049,.69)
    if with_pad_folds:
        # Local to each curved toe, not in world space. Keratin lamellar folds
        # trace only the ventral pad; these are not individual setae.
        seam=g.attr('LamellarFold','Fac')
        plantar=g.attr('PlantarPad','Fac')
        color=g.blend(g.op('MULTIPLY',plantar,.27),color,rgb('d0bf9f'))
        color=g.blend(g.op('MULTIPLY',seam,.58),color,rgb('614e39'))
        normal=g.bump(g.op('MULTIPLY',seam,-1.),.01,.73,normal)
    rough=g.ramp(macro,[(.27,.368),(.72,.602)])
    return g.set(g.pbr(color,rough,normal,IOR=1.43,Specular_IOR_Level=.37,Coat_Weight=.128,Coat_Roughness=.205,
                       Subsurface_Weight=.050,Subsurface_Radius=(1,.49,.31),Subsurface_Scale=UNIT*.028))


def iris_surface(image):
    g=Graph('Spectacle / amber stromal fibres beneath cornea')
    tex=g.n('ShaderNodeTexImage'); tex.image=image
    tex.interpolation='Linear'; tex.extension='EXTEND'
    return g.set(g.pbr(tex.outputs['Color'],.223,IOR=1.385,Specular_IOR_Level=.43,Coat_Weight=.38,Coat_Roughness=.070))


def panel_surface():
    g=Graph('Observation pane / thin dielectric, independent front-surface reflection')
    passray=g.n('ShaderNodeBsdfTransparent'); passray.inputs[0].default_value=rgb('fafcf8')
    smooth_reflect=g.n('ShaderNodeBsdfGlossy')
    smooth_reflect.inputs['Color'].default_value=rgb('dfeae4')
    g.hit(smooth_reflect,'Roughness',.047)
    fresnel=g.n('ShaderNodeFresnel');fresnel.inputs['IOR'].default_value=1.43
    spec=g.op('MINIMUM',g.op('MULTIPLY',fresnel.outputs[0],1.37),.398)
    combo=g.mixshader(spec,passray.outputs[0],smooth_reflect.outputs[0])
    return g.set(g.mixshader(g.n('ShaderNodeLightPath').outputs['Is Shadow Ray'],combo,passray.outputs[0]))


def plate_surface(file):
    g=Graph('Original photographic conservatory matte (far field only)')
    n=g.n('ShaderNodeTexImage');n.image=bpy.data.images.load(str(file),check_existing=True);n.extension='EXTEND'
    em=g.n('ShaderNodeEmission');g.hit(em,0,n.outputs['Color']);g.hit(em,1,.77)
    return g.set(em.outputs[0])


def plant_surface(k):
    g=Graph(f'Leaf cuticle / variation {k}')
    p=g.n('ShaderNodeTexCoord').outputs['UV']
    n=g.noise(p,10.7,2,.72,.12)['Fac']
    palettes=[('183429','41633c','5d753d'),('142e2d','385747','5b7b4e'),('1e3d34','466851','778957')]
    col=g.ramp(n,list(zip((.14,.51,.85),palettes[k%len(palettes)])))
    col=g.blend(.13,col,g.noise(p,81.4,2)['Fac'],'MULTIPLY')
    pbr=g.pbr(col,.49,g.bump(n,.011,.44),Specular_IOR_Level=.32,Coat_Weight=.12)
    sub=g.n('ShaderNodeBsdfTranslucent');g.hit(sub,0,col)
    return g.set(g.mixshader(.20,pbr,sub.outputs[0]))


def bark_surface():
    g=Graph('Twisted cork and moss substrate')
    tc=g.n('ShaderNodeTexCoord').outputs['UV']
    p=g.vec('MULTIPLY',tc,(3.12,1.,1.))
    n=g.noise(p,7.3,3,.72,.37)['Fac']; f=g.noise(p,42,2,.72,.21)['Fac']
    col=g.ramp(n,[(.16,'23221b'),(.42,'423120'),(.59,'6f5035'),(.72,'8d6c44')])
    moss=g.ramp(f,[(.51,0),(.61,.78)])
    col=g.blend(moss,col,g.ramp(n,[(.2,'253a29'),(.6,'6d753b')]))
    return g.set(g.pbr(col,.81,g.bump(f,.065,.71),Specular_IOR_Level=.23))


def simple(name,color,rough=.5,**kwargs):
    g=Graph(name)
    return g.set(g.pbr(rgb(color),rough,**kwargs))
