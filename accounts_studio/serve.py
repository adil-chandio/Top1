"""Persistent local two-account coordinator service; run only after doctor and real pilot pass.
No network listener. Durable job state lives under ACCOUNTS_STATE_DIR.

Isolated from the three-channel studio system: separate package, separate
state dir, separate env vars.
"""
import os,signal,time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from accounts_studio.pipeline import ROOT,CONFIG,tick
import json
stop=False
def halt(*_):
 global stop
 stop=True
signal.signal(signal.SIGTERM,halt);signal.signal(signal.SIGINT,halt)
def main():
 base=Path(os.getenv('ACCOUNTS_STATE_DIR',str(ROOT/'accounts_studio/runtime')))
 while not stop:
  active={}
  for p in sorted(base.glob('*/state.json')):
   s=json.loads(p.read_text())
   if s['status']=='queued' and s['account']==CONFIG['active_account']:active.setdefault(s['account'],p.parent)
  with ThreadPoolExecutor(max_workers=2) as pool:
   for result in pool.map(tick,active.values()):print(result,flush=True)
  for _ in range(30):
   if stop:return
   time.sleep(1)
if __name__=='__main__':main()
