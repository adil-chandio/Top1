import hashlib,threading,unittest
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from http.server import ThreadingHTTPServer
from server import Handler,VIDEO,EXPECTED,byte_range
class ReviewDeskChecks(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.server=ThreadingHTTPServer(('127.0.0.1',0),Handler);cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start();cls.url=f'http://127.0.0.1:{cls.server.server_port}'
 @classmethod
 def tearDownClass(cls):cls.server.shutdown();cls.server.server_close();cls.thread.join()
 def test_candidate_identity(self):self.assertEqual(hashlib.sha256(VIDEO.read_bytes()).hexdigest(),EXPECTED)
 def test_ranges(self):
  self.assertEqual(byte_range('bytes=10-19',100),(10,19,True));self.assertEqual(byte_range('bytes=-10',100),(90,99,True));self.assertEqual(byte_range('bytes=95-',100),(95,99,True))
  for value in ['bytes=100-','bytes=10-1','bytes=0-1,3-4','bytes=-0','bytes=-','wat']:
   with self.assertRaises(ValueError):byte_range(value,100)
 def test_video_seek_and_head(self):
  with urlopen(Request(self.url+'/film.mp4',headers={'Range':'bytes=256-511'})) as r:
   self.assertEqual(r.status,206);self.assertEqual(r.read(),VIDEO.read_bytes()[256:512]);self.assertEqual(r.headers['Accept-Ranges'],'bytes')
  with urlopen(Request(self.url+'/film.mp4',method='HEAD')) as r:
   self.assertEqual(r.status,200);self.assertEqual(int(r.headers['Content-Length']),VIDEO.stat().st_size);self.assertEqual(r.read(),b'')
 def test_no_arbitrary_files_or_write_API(self):
  for path in ['/../.git/config','/studio/MONARCH_CAM_WORKFLOW_STATE.json','/notes.json','/%2e%2e/.git/config']:
   with self.assertRaises(HTTPError) as e:urlopen(self.url+path)
   self.assertEqual(e.exception.code,404)
  with self.assertRaises(HTTPError) as e:urlopen(Request(self.url+'/',data=b'{}',method='POST'))
  self.assertEqual(e.exception.code,501)
 def test_unsatisfiable_range(self):
  with self.assertRaises(HTTPError) as e:urlopen(Request(self.url+'/film.mp4',headers={'Range':'bytes=999999999-'}))
  self.assertEqual(e.exception.code,416)
 def test_page_and_preview_host(self):
  with urlopen(Request(self.url+'/',headers={'Host':'8765-example.e2b.app'})) as r:
   html=r.read().decode();self.assertEqual(r.status,200)
   self.assertIn('final_signoff:false',html);self.assertIn('project_holds_cleared:false',html)
   self.assertNotIn('http://localhost',html);self.assertNotIn('X-Frame-Options',r.headers)
if __name__=='__main__':unittest.main()
