"""Original unitless mechanical proxy, NOT a species-accurate anatomical asset.

Run directly to build a self-contained glTF with an articulated hinge and event
markers. Timing is deliberately slowed/illustrative, not measured biomechanics.
Only standard-library dependencies. No restricted source figure is traced.
"""
import base64
import json
import math
from pathlib import Path
import struct

EVENTS = {'closure_start': 0.6, 'closure_end': 1.0, 'jet_start': 1.0,
          'cavity_start': 1.12, 'collapse': 1.7, 'wave_end': 2.2}
DURATION = 3.0


def sample(t):
    u = min(1., max(0., (t-EVENTS['closure_start']) / .4))
    hinge = .85 * (1-u*u*(3-2*u))
    jet = .02
    if EVENTS['jet_start'] <= t < 1.3:
        jet = max(.02, min(1., (t-1.)/.08))
    cavity = .001
    if EVENTS['cavity_start'] <= t < EVENTS['collapse']:
        phase = (t-EVENTS['cavity_start'])/(EVENTS['collapse']-EVENTS['cavity_start'])
        cavity = max(.001, math.sin(math.pi*phase))
    wave = .001
    if EVENTS['collapse'] <= t <= EVENTS['wave_end']:
        wave = .08 + 4*(t-EVENTS['collapse'])
    return hinge, jet, cavity, wave


class Builder:
    def __init__(self):
        self.buffer = bytearray()
        self.doc = {'asset': {'version': '2.0', 'generator': 'Monarch Cam original mechanism proxy'},
                    'scene': 0, 'scenes': [{'nodes': []}], 'nodes': [], 'meshes': [],
                    'materials': [], 'bufferViews': [], 'accessors': [],
                    'extras': {'production_approved': False, 'anatomy_verified': False,
                               'real_time_biomechanics': False, 'unit': 'arbitrary',
                               'events_seconds_illustrative': EVENTS,
                               'warning': 'Mechanism proxy only; not realistic final animation.'}}

    def accessor(self, values, width, indices=False, target=None):
        while len(self.buffer) % 4:
            self.buffer.append(0)
        start = len(self.buffer)
        flat = [v for row in values for v in row] if width > 1 else values
        self.buffer.extend(struct.pack('<'+('H' if indices else 'f')*len(flat), *flat))
        view = len(self.doc['bufferViews'])
        self.doc['bufferViews'].append({'buffer': 0, 'byteOffset': start, 'byteLength': len(self.buffer)-start})
        if target is not None:
            self.doc['bufferViews'][-1]['target'] = target
        a = {'bufferView': view, 'componentType': 5123 if indices else 5126,
             'count': len(values), 'type': {1:'SCALAR', 3:'VEC3', 4:'VEC4'}[width]}
        if width == 1:
            a.update(min=[min(values)], max=[max(values)])
        elif width == 3:
            a.update(min=[min(v[k] for v in values) for k in range(3)],
                     max=[max(v[k] for v in values) for k in range(3)])
        self.doc['accessors'].append(a)
        return len(self.doc['accessors'])-1

    def material(self, name, rgb, alpha=1.):
        m = {'name': name, 'pbrMetallicRoughness': {'baseColorFactor': [*rgb, alpha],
             'metallicFactor': 0., 'roughnessFactor': .45}, 'doubleSided': True}
        if alpha < 1.:
            m.update(alphaMode='BLEND')
        self.doc['materials'].append(m)
        return len(self.doc['materials'])-1

    def ellipsoid_mesh(self, material, taper=0.):
        positions, normals, triangles = [], [], []
        rows, cols = 16, 24
        for i in range(rows+1):
            phi = math.pi*i/rows
            for j in range(cols+1):
                theta = 2*math.pi*j/cols
                x = math.cos(phi)
                y = math.sin(phi)*math.cos(theta)
                z = math.sin(phi)*math.sin(theta)
                # Smooth stylized proxy, not a reconstructed claw surface.
                positions.append([x, y*(1-taper*x), z*(1-taper*x)])
                normals.append([x,y,z])
        for i in range(rows):
            for j in range(cols):
                a=i*(cols+1)+j; b=a+cols+1
                # Outward winding for this parameterization.
                triangles.extend([a,b,a+1,a+1,b,b+1])
        self.doc['meshes'].append({'primitives': [{'attributes': {
            'POSITION': self.accessor(positions,3,target=34962), 'NORMAL': self.accessor(normals,3,target=34962)},
            'indices': self.accessor(triangles,1,True,target=34963), 'material': material}]})
        return len(self.doc['meshes'])-1

    def node(self, name, mesh=None, translation=None, scale=None, parent=None):
        n={'name':name}
        if mesh is not None: n['mesh']=mesh
        if translation is not None: n['translation']=translation
        if scale is not None: n['scale']=scale
        idx=len(self.doc['nodes']); self.doc['nodes'].append(n)
        if parent is None: self.doc['scenes'][0]['nodes'].append(idx)
        else: self.doc['nodes'][parent].setdefault('children',[]).append(idx)
        return idx

    def animate(self, channels):
        times=[i/120 for i in range(int(DURATION*120)+1)]
        ti=self.accessor(times,1)
        samplers=[]; output=[]
        for node,path,values,width in channels:
            samplers.append({'input':ti,'output':self.accessor(values,width),'interpolation':'LINEAR'})
            output.append({'sampler':len(samplers)-1,'target':{'node':node,'path':path}})
        self.doc['animations']=[{'name':'Illustrative closure jet cavity collapse',
                                'samplers':samplers,'channels':output}]

    def save(self,path):
        self.doc['buffers']=[{'byteLength':len(self.buffer),
            'uri':'data:application/octet-stream;base64,'+base64.b64encode(self.buffer).decode()}]
        Path(path).parent.mkdir(parents=True,exist_ok=True)
        Path(path).write_text(json.dumps(self.doc,separators=(',',':'))+'\n')


def build(path):
    b=Builder()
    shell=b.material('Proxy shell — geometry unverified',[.22,.32,.28])
    water=b.material('Jet marker — not actual visible water',[.15,.65,.9],.4)
    cavitymat=b.material('Cavity marker — not literal air balloon',[.75,.9,1.],.4)
    solid=b.ellipsoid_mesh(shell,.25)
    sphere=b.ellipsoid_mesh(cavitymat)
    jetmesh=b.ellipsoid_mesh(water)
    root=b.node('Original mechanical proxy — not anatomical reconstruction')
    b.node('Fixed palm proxy',solid,[-.7,-.25,0],[1.,.4,.32],root)
    b.node('Fixed finger proxy',solid,[.45,-.45,0],[.85,.12,.15],root)
    hinge=b.node('Dactyl hinge',translation=[-.15,.05,0],parent=root)
    b.node('Moving dactyl proxy',solid,[.65,0,0],[.85,.12,.15],hinge)
    jet=b.node('Explanatory jet marker',jetmesh,[1.8,-.17,0],[.001]*3,root)
    cavity=b.node('Explanatory cavity marker',sphere,[2.5,-.17,0],[.001]*3,root)
    wave=b.node('Pressure event marker — not a literal solid sphere',sphere,[2.5,-.17,0],[.001]*3,root)
    samples=[sample(i/120) for i in range(int(DURATION*120)+1)]
    b.animate([(hinge,'rotation',[[0,0,math.sin(a/2),math.cos(a/2)] for a,_,_,_ in samples],4),
               (jet,'scale',[[j*.6,j*.04,j*.04] for _,j,_,_ in samples],3),
               (cavity,'scale',[[c*.25]*3 for _,_,c,_ in samples],3),
               (wave,'scale',[[w*.25]*3 for _,_,_,w in samples],3)])
    b.save(path)
    return b.doc


if __name__=='__main__':
    target=Path(__file__).parent/'assets'/'claw-mechanism-proxy.gltf'
    build(target)
    print(target)
