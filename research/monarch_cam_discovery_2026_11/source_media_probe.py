"""Bounded acquisition of one publisher-linked CC-BY scientific supplement.
No YouTube/bot bypass; no third-party repository code is executed.
Cloud check outputs carry small attributed visual evidence, never credentials.
"""
import base64,hashlib,json,os,subprocess,urllib.request
from pathlib import Path
import imageio_ffmpeg
from PIL import Image,ImageDraw
URL='https://static-content.springer.com/esm/art%3A10.1038%2Fs41559-024-02525-2/MediaObjects/41559_2024_2525_MOESM7_ESM.mp4'
OUT=Path('studio/runtime/primary-media');OUT.mkdir(parents=True,exist_ok=True)
def check(name,payload):
    body={'name':name,'head_sha':os.environ['GITHUB_SHA'],'status':'completed','conclusion':'neutral','output':{'title':name,'summary':json.dumps(payload)}}
    req=urllib.request.Request('https://api.github.com/repos/'+os.environ['GITHUB_REPOSITORY']+'/check-runs',data=json.dumps(body).encode(),headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Accept':'application/vnd.github+json','Content-Type':'application/json'},method='POST')
    with urllib.request.urlopen(req,timeout=30) as r:print('CHECK',json.load(r)['id'],flush=True)
def main():
    report={'source':URL,'paper':'10.1038/s41559-024-02525-2','source_type':'primary_scientific_supplement_NOT_youtube_editorial_reference','license':'CC BY 4.0 per publisher rights section, subject to any clip-specific credit exceptions','attribution':'Sampaio et al. (2024), Nature Ecology & Evolution, doi:10.1038/s41559-024-02525-2. Supplementary Video 4. Sampled/scaled frames for research. https://creativecommons.org/licenses/by/4.0/','moving_picture_review':False,'audio_listening_review':False}
    try:
        path=OUT/'segment.mp4'
        ff=imageio_ffmpeg.get_ffmpeg_exe()
        # Prior run established a >80MB source; acquire only a bounded excerpt.
        # FFmpeg performs HTTP range/stream reads; output cap is not a guarantee
        # of network transfer size. Global subprocess deadline limits exposure.
        acquire=subprocess.run([ff,'-nostdin','-y','-v','error','-rw_timeout','15000000','-ss','0','-i',URL,'-t','6','-vf','scale=640:-2','-c:v','libx264','-crf','26','-c:a','aac','-b:a','64k','-fs','12000000','-movflags','+faststart',str(path)],capture_output=True,text=True,timeout=120)
        if acquire.returncode:raise ValueError('bounded FFmpeg acquisition failed: '+acquire.stderr[-500:])
        size=path.stat().st_size
        report.update(bytes=size,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),acquired_segment_seconds=6,source_full_download=False,source_full_decode=False)
        r=subprocess.run([ff,'-nostdin','-v','info','-xerror','-i',str(path),'-f','null','-'],capture_output=True,text=True,timeout=180)
        report['full_decode_passed']=r.returncode==0
        report['stream_report_tail']=r.stderr[-7000:]
        if r.returncode:raise ValueError('source decode failed')
        subprocess.run([ff,'-nostdin','-y','-v','error','-i',str(path),'-t','12','-vf','fps=5,scale=240:-2','-frames:v','60',str(OUT/'frame-%03d.jpg')],check=True,timeout=90)
        frames=sorted(OUT.glob('frame-*.jpg'));report['frames_extracted']=len(frames)
        for start in range(0,len(frames),6):
            selected=frames[start:start+6];images=[Image.open(p).convert('RGB') for p in selected];h=max(i.height for i in images)
            sheet=Image.new('RGB',(720,(h+18)*2+35),(12,18,22));draw=ImageDraw.Draw(sheet)
            draw.text((4,3),'Sampaio et al. 2024 | CC BY 4.0 | Supplement 4 | sampled source frames',fill='white')
            for j,im in enumerate(images):
                x=(j%3)*240;y=35+(j//3)*(h+18);sheet.paste(im,(x,y));draw.text((x+3,y+h+2),f'~{(start+j)/5:.1f}s; 5fps sample',fill='white')
            target=OUT/f'sheet-{start//6:02}.jpg';sheet.save(target,quality=36)
            raw=target.read_bytes()
            if len(raw)>42000:sheet.save(target,quality=22);raw=target.read_bytes()
            if len(raw)>42000:raise ValueError('sheet too large for bounded evidence')
            check('primary-media-sheet-'+str(start//6),{'filename':target.name,'sha256':hashlib.sha256(raw).hexdigest(),'jpeg_base64':base64.b64encode(raw).decode(),'attribution':report['attribution']})
        report['status']='acquired_decoded_sampled_NOT_reviewed'
    except Exception as exc:
        report['status']='access_or_processing_failed';report['error_type']=type(exc).__name__;report['error']=str(exc)[:500]
        check('primary-media-report',report)
        raise
    check('primary-media-report',report)
    (OUT/'receipt.json').write_text(json.dumps(report,indent=2))
if __name__=='__main__':main()
