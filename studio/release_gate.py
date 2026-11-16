"""Full-render preflight. Does not certify taste or replace actual media review."""
import argparse,hashlib,json
from pathlib import Path
from studio.pipeline import ROOT
REQUIRED=('reference_audiovisual_breakdown','art_direction','editing_blueprint','combined_short_test_review','sound_listening_review')
def check(manifest,root=ROOT):
 if manifest.get('channel')!='monarch_cam':raise ValueError('wrong active channel')
 if manifest.get('ready_for_full_render') is not True:raise ValueError('full render not cleared; research/redesign required')
 if not all(manifest.get('gates',{}).get(k) is True for k in REQUIRED):raise ValueError('creative gate incomplete')
 evidence=manifest.get('evidence',[])
 if {x.get('gate') for x in evidence}!=set(REQUIRED):raise ValueError('each gate needs evidence')
 for item in evidence:
  p=(root/item['path']).resolve()
  if not p.is_relative_to(root.resolve()) or not p.is_file():raise ValueError('missing/unsafe gate evidence')
  if hashlib.sha256(p.read_bytes()).hexdigest()!=item.get('sha256'):raise ValueError('gate evidence changed')
 return True
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--manifest',default='studio/active_release.json');args=p.parse_args()
 check(json.loads((ROOT/args.manifest).read_text()));print('Full render evidence preflight passed; artistic approval is not automated.')
