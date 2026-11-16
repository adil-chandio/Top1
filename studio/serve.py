"""Persistent local coordinator service; run only after doctor and real pilot pass.
No network listener. Durable job state lives under STUDIO_STATE_DIR.
"""
import os,signal,time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from studio.pipeline import ROOT,CONFIG,tick
import json
stop=False
def halt(*_):
 global stop
 stop=True
signal.signal(signal.SIGTERM,halt);signal.signal(signal.SIGINT,halt)
def main():
 base=Path(os.getenv('STUDIO_STATE_DIR',str(ROOT/'studio/runtime')))
 while not stop:
  active={}
  for p in sorted(base.glob('*/state.json')):
   s=json.loads(p.read_text())
   if s['status']=='queued':active.setdefault(s['channel'],p.parent)
  with ThreadPoolExecutor(max_workers=3) as pool:
   for result in pool.map(tick,active.values()):print(result,flush=True)
  for _ in range(30):
   if stop:return
   time.sleep(1)
if __name__=='__main__':main()
