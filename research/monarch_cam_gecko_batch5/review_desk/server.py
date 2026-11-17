"""Local-only review service: explicit file allowlist, byte ranges, no upload/approval API.
Run: python research/monarch_cam_gecko_batch5/review_desk/server.py --port 8765
The preview proxy supplies TLS. No credentials or arbitrary repository files served.
"""
import argparse,hashlib,json,re
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
VIDEO=ROOT/'studio/runtime/gecko/caption-readability/gecko-english-review-cut-v6.mp4'
EXPECTED='cebe198ec2cb2b7ae95145aad00c65879cd30c95a13a7f264d6b952dba1e9994'
ROUTES={'/':(HERE/'index.html','text/html; charset=utf-8'),'/film.mp4':(VIDEO,'video/mp4'),'/credits.txt':(ROOT/'research/monarch_cam_gecko_batch4/CREDITS_AND_SOURCES_ENGLISH.md','text/plain; charset=utf-8')}

def byte_range(header,size):
 if not header:return 0,size-1,False
 m=re.fullmatch(r'bytes=(\d*)-(\d*)',header)
 if not m or not any(m.groups()):raise ValueError('unsupported range')
 a,b=m.groups()
 if not a:
  if int(b)<=0:raise ValueError('empty suffix')
  return max(0,size-int(b)),size-1,True
 start=int(a);end=min(int(b),size-1) if b else size-1
 if start>=size or end<start:raise ValueError('unsatisfiable range')
 return start,end,True

class Handler(BaseHTTPRequestHandler):
 def do_HEAD(self):self.serve(head=True)
 def do_GET(self):self.serve()
 def serve(self,head=False):
  route=ROUTES.get(urlsplit(self.path).path)
  if route is None:self.send_error(404);return
  path,mime=route
  if not path.is_file():self.send_error(503,'Review asset missing');return
  size=path.stat().st_size
  try:start,end,partial=byte_range(self.headers.get('Range'),size)
  except ValueError:
   self.send_response(416);self.send_header('Content-Range',f'bytes */{size}');self.send_header('Content-Length','0');self.end_headers();return
  self.send_response(206 if partial else 200);self.send_header('Content-Type',mime)
  self.send_header('Accept-Ranges','bytes');self.send_header('Content-Length',str(end-start+1))
  self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff')
  self.send_header('Referrer-Policy','no-referrer')
  if partial:self.send_header('Content-Range',f'bytes {start}-{end}/{size}')
  self.end_headers()
  if head:return
  try:
   with path.open('rb') as f:
    f.seek(start);remaining=end-start+1
    while remaining:
     chunk=f.read(min(65536,remaining))
     if not chunk:break
     self.wfile.write(chunk);remaining-=len(chunk)
  except (BrokenPipeError,ConnectionResetError):pass

def main():
 p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8765);args=p.parse_args()
 if not VIDEO.is_file() or hashlib.sha256(VIDEO.read_bytes()).hexdigest()!=EXPECTED:raise SystemExit('Missing or mismatched V6; refusing ambiguous candidate')
 print(json.dumps({'candidate':'v6','sha256':EXPECTED,'server':'0.0.0.0','port':args.port,'final_pass':False}),flush=True)
 ThreadingHTTPServer(('0.0.0.0',args.port),Handler).serve_forever()
if __name__=='__main__':main()
