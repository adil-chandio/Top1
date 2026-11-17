"""Numerical mesh deformation checks. Not expert anatomy or playback verification."""
from pathlib import Path
import numpy as np,json
BASE=Path(__file__).parent
exec(compile((BASE/'animate_tidewater.py').read_text().split("if '--poses' in sys.argv:")[0],str(BASE/'animate_tidewater.py'),'exec'))
edges=np.array([tuple(e.vertices) for e in ob.data.edges],dtype=np.int32)
base=pose(0).copy();a=edges[:,0];b=edges[:,1]
restlen=np.linalg.norm(base[a]-base[b],axis=1);mask=restlen>1e-5
receipts=[]
for frame in range(0,240,12):
 now=pose(frame/FPS);length=np.linalg.norm(now[a]-now[b],axis=1)
 ratio=length[mask]/restlen[mask]
 receipts.append({'frame':frame,'finite':bool(np.isfinite(now).all()),'edge_length_ratio_p01':float(np.quantile(ratio,.01)),'edge_length_ratio_p99':float(np.quantile(ratio,.99)),'edge_length_ratio_min':float(ratio.min()),'edge_length_ratio_max':float(ratio.max()),'max_displacement_from_frame0_m':float(np.linalg.norm(now-base,axis=1).max())})
r={'scope':'20 one-second mesh samples; relative to frame0 pose, not rest mesh; camera fixed in renderer; does not prove biological accuracy','samples':receipts}
(BASE/'out/numerical_motion_qa.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps({'all_finite':all(x['finite'] for x in receipts),'worst_edge_min':min(x['edge_length_ratio_min'] for x in receipts),'worst_edge_max':max(x['edge_length_ratio_max'] for x in receipts),'max_displacement':max(x['max_displacement_from_frame0_m'] for x in receipts)},indent=2))
