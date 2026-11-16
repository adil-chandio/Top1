"""Sequential, bounded public-reference acquisition. Audio deliberately excluded.
No authentication, cookie import, proxies or challenge bypass. No media in Git.
Acquisition is not visual approval; human/model inspection is recorded separately.
"""
import json, subprocess, tempfile, hashlib, shutil
from pathlib import Path
BASE=Path(__file__).parent
OUT=Path('studio/runtime/visual-reference-review')

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    results=[]
    for ref in json.loads((BASE/'CHANNEL_FIRST_REFERENCE_REGISTER.json').read_text())['references']:
        receipt={'video_id':ref['video_id'],'url':ref['url'],'audio_in_scope':False,
                 'visual_inspection_completed':False,'acquisition_success':False}
        try:
            with tempfile.TemporaryDirectory(prefix='reference-') as work:
                root=Path(work)
                args=['yt-dlp','--ignore-config','--no-playlist','--no-progress',
                      '--socket-timeout','15','--retries','0','--fragment-retries','0',
                      '--max-filesize','80M','-f','worstvideo[height<=360]/worst[height<=360]',
                      '--output',str(root/'source.%(ext)s'),ref['url']]
                proc=subprocess.run(args,capture_output=True,text=True,timeout=90)
                sources=[p for p in root.glob('source.*') if p.suffix not in ('.part','.ytdl')]
                if proc.returncode or len(sources)!=1:
                    # URLs/tokens omitted from receipt, retain only known error classes.
                    msg=proc.stderr.lower()
                    receipt['failure_class']='login_or_bot_check' if ('sign in' in msg or 'bot' in msg) else 'public_acquisition_failed'
                    continue
                source=sources[0]
                if source.stat().st_size>80_000_000:raise ValueError('size cap')
                info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-of','json',str(source)],timeout=20))
                duration=float(info['format']['duration'])
                if duration<=0 or duration>5400:raise ValueError('duration cap')
                target=OUT/ref['video_id'];target.mkdir(exist_ok=True)
                # Whole-duration survey; dense local windows must follow actual survey inspection.
                interval=max(1,duration/160)
                subprocess.run(['ffmpeg','-nostdin','-v','error','-i',str(source),'-an',
                    '-vf',f'fps=1/{interval},scale=320:-2,tile=4x4','-frames:v','10',
                    str(target/'sheet-%02d.jpg')],check=True,timeout=150)
                receipt.update(acquisition_success=True,duration_seconds=duration,
                    bytes=source.stat().st_size,sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                    sampling_interval_seconds=interval,survey_only=True,
                    dense_frame_review_complete=False)
        except Exception as exc:
            receipt['failure_class']=type(exc).__name__
        finally:
            receipt['temporary_source_deleted']=not Path(work).exists() if 'work' in locals() else None
            results.append(receipt)
            (OUT/'receipt.json').write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps(results,indent=2))

if __name__=='__main__':main()
