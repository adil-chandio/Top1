"""Fetch only inspected pinned scene assets through GitHub API, verify hashes."""
import base64,hashlib,json,urllib.request
from pathlib import Path
BASE=Path(__file__).parent
whales=json.loads((BASE/'tidewater_download_receipt.json').read_text())
orcas=json.loads((BASE/'orca_download_receipt.json').read_text())
def get(repo,commit,path,dest,expected):
 url=f'https://api.github.com/repos/{repo}/contents/{path}?ref={commit}'
 req=urllib.request.Request(url,headers={'User-Agent':'Monarch-Cam-asset-fetch','Accept':'application/vnd.github.raw+json'})
 with urllib.request.urlopen(req,timeout=60) as response:data=response.read()
 if hashlib.sha256(data).hexdigest()!=expected:raise RuntimeError('Pinned asset hash mismatch: '+path)
 dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
for name in ['humpback.bin','humpback.json','humpback_albedo.png','humpback_height.png']:
 get('dgreenheck/tidewater','4811ba48d795197de5621985f404e765c0b7c0ef','public/models/whale/'+name,BASE/'out/tidewater'/name,whales[name]['sha256'])
for name in ['orca.glb','LICENSE.md']:
 get('GilRaitses/orcastrike',orcas[name]['source_commit'],'public/orca/'+name,BASE/'out/orca'/name,orcas[name]['sha256'])
print('Pinned scene assets verified.')
