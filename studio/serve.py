"""Persistent local coordinator service; run only after doctor and real pilot pass.
No network listener. Durable job state lives under STUDIO_STATE_DIR.
"""
import os,signal,time
from pathlib import Path
from studio.pipeline import ROOT,CONFIG,tick
import json
stop=False
def halt(*_):
 global stop
 stop=True
signal.signal(signal.SIGTERM,halt);signal.signal(signal.SIGINT,halt)
def main():
 from studio.readiness import inspect
 ready=inspect()
 if not ready['configuration_ready']:
  print(json.dumps(ready,indent=2),flush=True)
  raise SystemExit(2)
 base=Path(os.getenv('STUDIO_STATE_DIR',str(ROOT/'studio/runtime')))
 while not stop:
  from studio.lifecycle import select_job
  job=select_job(base,CONFIG['active_channel'])
  if job:print(job.name,tick(job),flush=True)
  for _ in range(30):
   if stop:return
   time.sleep(1)
if __name__=='__main__':main()
