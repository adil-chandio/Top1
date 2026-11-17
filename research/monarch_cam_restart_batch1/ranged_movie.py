"""Read ONE member of a public scientific ZIP using bounded HTTP ranges.

Refuses servers ignoring Range, archives with unsafe ratios and oversized members.
No login, cookies or alternate identities; no extraction to supplied archive paths.
"""
import io
import re
import urllib.request
import zipfile

URL='https://pmc.ncbi.nlm.nih.gov/articles/instance/11939058/bin/sciadv.adr3686_movies_s1_to_s6.zip'
CAP=40_000_000

class RangeReader(io.RawIOBase):
    def __init__(self,url):
        self.url=url; self.pos=0; self.transferred=0; self.size=None
        self._get(0,0)
    def readable(self): return True
    def seekable(self): return True
    def tell(self): return self.pos
    def seek(self,offset,whence=0):
        p=offset if whence==0 else (self.pos+offset if whence==1 else self.size+offset)
        if p<0 or p>self.size: raise ValueError('Seek outside archive')
        self.pos=p; return p
    def _get(self,start,end):
        length=end-start+1
        if self.transferred+length>CAP: raise ValueError('Network transfer cap')
        req=urllib.request.Request(self.url,headers={'Range':f'bytes={start}-{end}','Accept-Encoding':'identity','User-Agent':'MonarchCamResearch/1.0'})
        with urllib.request.urlopen(req,timeout=30) as response:
            if response.status!=206: raise ValueError('Server did not honor byte ranges; refusing full archive')
            match=re.fullmatch(r'bytes (\d+)-(\d+)/(\d+)',response.headers.get('Content-Range',''))
            if not match or int(match[1])!=start or int(match[2])!=end: raise ValueError('Invalid Content-Range')
            size=int(match[3])
            if self.size is not None and size!=self.size: raise ValueError('Remote size changed')
            self.size=size
            data=response.read(length+1); self.transferred+=len(data)
            if len(data)!=length: raise ValueError('Unexpected range length')
            return data
    def read(self,n=-1):
        if n is None or n<0: n=self.size-self.pos
        n=min(n,self.size-self.pos)
        if n<=0:return b''
        data=self._get(self.pos,self.pos+n-1);self.pos+=len(data);return data

def acquire_one(destination):
    remote=RangeReader(URL)
    with zipfile.ZipFile(remote) as archive:
        members=[i for i in archive.infolist() if not i.is_dir() and i.filename.lower().endswith('.mp4') and not i.filename.startswith('__MACOSX/')]
        # Enumerate only; do not silently pick unrelated smallest video.
        matches=[i for i in members if re.search(r'(?:movie[_ -]?|^|/)s?0?1(?:\D|$)',i.filename,re.I)]
        if len(matches)!=1: raise ValueError('Could not uniquely identify Movie S1: '+repr([i.filename for i in members]))
        member=matches[0]
        if member.file_size>CAP or member.compress_size>CAP or member.file_size>max(1,member.compress_size)*100:
            raise ValueError('Member too large or unsafe expansion')
        count=0
        with archive.open(member) as source, open(destination,'wb') as target:
            while True:
                block=source.read(65536)
                if not block: break
                count+=len(block)
                if count>CAP: raise ValueError('Expanded output cap')
                target.write(block)
    return {'archive_url':URL,'archive_size_bytes':remote.size,'actual_http_payload_bytes':remote.transferred,
            'member':member.filename,'member_bytes':count,'all_archive_members_downloaded':False}
