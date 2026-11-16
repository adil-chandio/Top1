"""One bounded official supplement, temporary media only; never a YouTube bypass."""
import base64, hashlib, json, os, shutil, subprocess, tempfile, urllib.request
from pathlib import Path
from PIL import Image, ImageDraw
# Publisher supplement denied HTTP403; do not bypass or retry it.
# This separately accessible creator test is NOT a viral benchmark or cuttlefish footage.
URL='https://github.com/jonaslacandola0617/curio-bureau/releases/download/visual-test-pistol-shrimp-v2-20261020/Curio-Test-03-Pistol-Shrimp-12s-v2.mp4'
CAP=40_000_000

def publish(name, report, text=''):
    body={'name':name,'head_sha':os.environ['GITHUB_SHA'],'status':'completed','conclusion':'neutral',
          'output':{'title':name,'summary':json.dumps(report),'text':text}}
    req=urllib.request.Request('https://api.github.com/repos/'+os.environ['GITHUB_REPOSITORY']+'/check-runs',data=json.dumps(body).encode(),headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Accept':'application/vnd.github+json','Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=30) as response: json.load(response)

def main():
    report={'url':URL,'source_type':'creator GitHub editorial test, NOT viral/approved reference',
            'credit':'Curio Bureau creator test, GitHub release visual-test-pistol-shrimp-v2-20261020',
            'rights':'No reuse licence established. Internal research only; not cleared for production footage.',
            'full_realtime_review':False,'actual_listening':False,'sampled_frames_opened':False,'success':False}
    with tempfile.TemporaryDirectory(prefix='monarch-one-reference-') as tmp:
        root=Path(tmp); source=root/'source.mp4'
        try:
            request=urllib.request.Request(URL,headers={'User-Agent':'MonarchCamResearch/1.0'})
            count=0; digest=hashlib.sha256()
            with urllib.request.urlopen(request,timeout=30) as response, source.open('wb') as dest:
                if int(response.headers.get('Content-Length','0'))>CAP: raise ValueError('Declared media exceeds cap')
                while True:
                    block=response.read(min(65536,CAP-count+1))
                    if not block: break
                    count+=len(block)
                    if count>CAP: raise ValueError('Streaming byte cap exceeded')
                    digest.update(block); dest.write(block)
            report.update(bytes=count,sha256=digest.hexdigest())
            ff=shutil.which('ffmpeg'); probe=shutil.which('ffprobe')
            meta=json.loads(subprocess.check_output([probe,'-v','error','-show_streams','-show_format','-of','json',str(source)],timeout=30))
            duration=float(meta['format']['duration'])
            report.update(duration_seconds=duration,streams=[{k:s.get(k) for k in ['codec_type','codec_name','width','height','sample_rate','channels','r_frame_rate']} for s in meta['streams']])
            if duration>300: raise ValueError('Duration exceeds research bound')
            decode=subprocess.run([ff,'-nostdin','-v','error','-xerror','-i',str(source),'-f','null','-'],capture_output=True,text=True,timeout=120)
            report['whole_file_decode_passed']=decode.returncode==0
            if decode.returncode: raise ValueError(decode.stderr[-1000:])
            interval=duration/48
            subprocess.run([ff,'-nostdin','-v','error','-i',str(source),'-vf',f'fps={48/duration},scale=240:-2','-frames:v','48',str(root/'frame-%03d.jpg')],check=True,timeout=90)
            frames=sorted(root.glob('frame-*.jpg')); report['sample_interval_seconds']=interval
            report['sampling_note']='FFmpeg fps samples near interval midpoints; labels approximate, not exact cut timings'
            report['frames_sampled']=len(frames)
            for start in range(0,len(frames),6):
                images=[Image.open(p).convert('RGB') for p in frames[start:start+6]]
                h=images[0].height; sheet=Image.new('RGB',(720,2*(h+20)+32),'#101820'); draw=ImageDraw.Draw(sheet)
                draw.text((5,4),'Curio Bureau creator test | internal research, NOT viral benchmark',fill='white')
                for i,im in enumerate(images):
                    x=(i%3)*240;y=32+(i//3)*(h+20);sheet.paste(im,(x,y));draw.text((x+3,y+h+2),f'~{(start+i+.5)*interval:.2f}s',fill='white')
                path=root/'sheet.jpg';sheet.save(path,quality=38);raw=path.read_bytes()
                if len(raw)>42000: sheet.save(path,quality=22);raw=path.read_bytes()
                if len(raw)>42000: raise ValueError('Evidence sheet cap exceeded')
                publish(f'media-lifecycle-sheet-{start//6:02d}',{'sha256':hashlib.sha256(raw).hexdigest(),'credit':report['credit'],'approximate_sample_interval_seconds':interval},base64.b64encode(raw).decode())
            report['success']=True
        except Exception as exc:
            report['error']=str(exc)[:1500]
        finally:
            # Raw audio/video and extracted working frames never enter the repository.
            for path in root.iterdir():
                if path.is_file(): path.unlink()
            report['temporary_media_deleted']=not any(root.iterdir())
            publish('media-lifecycle-receipt',report)
    print(json.dumps(report,indent=2))

if __name__=='__main__': main()
