"""Pure geometry for an illustrative continuous pad. Units and timings arbitrary.
No measured tokay joint angles, shear forces or attachment order are claimed.
"""
import math
LENGTH=3.36
RADIUS_Z=.14
RINGS=81
SIDES=24
FRAMES=60

def smooth(t):
 t=max(0.,min(1.,t));return t*t*(3-2*t)

def phase(frame):
 if frame<=12:return 'APPROACH'
 if frame<=20:return 'CONTACT'
 if frame<=30:return 'DIRECTIONAL LOAD (symbolic)'
 if frame<=52:return 'TIP-FIRST RELEASE'
 return 'CLEAR'

def centerline(frame):
 """Inextensible centerline sweep; curvature propagates distal to proximal."""
 lift=.48*(1-smooth((frame-1)/11))+.45*smooth((frame-52)/8)
 points=[(0.,.155+lift,0.)]
 ds=LENGTH/(RINGS-1)
 for i in range(1,RINGS):
  u=(i-.5)/(RINGS-1)
  # Cumulative bend; onset is earliest at distal end. This is not a bone rig.
  theta=1.55*u*smooth((frame-(31+(1-u)*12))/9)
  x,z,_=points[-1];points.append((x+ds*math.cos(theta),z+ds*math.sin(theta),theta))
 return points

def width(u):
 # Broad ventral pad with smoothly rounded terminal cap, not digit-specific anatomy.
 return .17+.12*math.sin(math.pi*u)**.6

def surface(frame):
 centers=centerline(frame);verts=[]
 for i,(x,z,theta) in enumerate(centers):
  u=i/(RINGS-1)
  for j in range(SIDES):
   a=2*math.pi*j/SIDES;offset=RADIUS_Z*math.cos(a)
   verts.append((x-math.sin(theta)*offset,width(u)*math.sin(a),z+math.cos(theta)*offset))
 return verts

def contact_flags(frame,threshold=.024):
 v=surface(frame)
 return [min(v[i*SIDES+j][2] for j in range(SIDES))<threshold for i in range(RINGS)]
