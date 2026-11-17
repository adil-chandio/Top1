from pathlib import Path
import json,hashlib,subprocess
import imageio_ffmpeg
from PIL import Image
p=Path('studio/runtime/gecko/webgl-production');audio=Path('studio/runtime/gecko/narration/english-narration-v1.wav')
assert hashlib.sha256(audio.read_bytes()).hexdigest()=='1d7a3284670a93ded1ad21f24aee980f3f39eba2766daa6a16e85580c3e41cc8'
for i in range(1592):
 f=p/'frames'/f'f_{i:05}.jpg';assert f.exists(),f
 with Image.open(f) as im:assert im.size==(720,1280)
ff=imageio_ffmpeg.get_ffmpeg_exe();movie=p/'monarch-gecko-complete-webgl-v3.mp4'
subprocess.run([ff,'-y','-v','error','-framerate','25','-i',str(p/'frames/f_%05d.jpg'),'-i',str(audio),'-map','0:v:0','-map','1:a:0','-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-ar','48000','-t','63.68','-movflags','+faststart',str(movie)],check=True)
qc=subprocess.run([ff,'-v','error','-i',str(movie),'-f','null','-'],capture_output=True,text=True);assert qc.returncode==0 and not qc.stderr
meta=subprocess.run([ff,'-hide_banner','-i',str(movie)],capture_output=True,text=True);(p/'ffmpeg-metadata.txt').write_text(meta.stderr)
receipt={'file':str(movie),'bytes':movie.stat().st_size,'sha256':hashlib.sha256(movie.read_bytes()).hexdigest(),'md5':hashlib.md5(movie.read_bytes()).hexdigest(),'duration_seconds':63.68,'frames':1592,'fps':25,'native_webgl_resolution':[720,1280],'source':'Original illustrative geometry; 3D microscopic schematic, authored continuous single-digit curl; whole animal static pose with perspective camera moves. No reference image pixels or audio used.','audio_approved_source_sha256':hashlib.sha256(audio.read_bytes()).hexdigest(),'audio_changed':False,'technical_decode_pass':True,'quality_user_approved':False,'anatomy_validated':False,'native_av_listened_by_assistant':False,'limitations':['Original subject still illustrative, not anatomically validated','Local toe motion is qualitative, not a measured living gait','Microscopic world schematic, not microscopy','No claim of exceeding prior episode benchmark','No added music or SFX; approved narration only'],'public_sharing_authorized':False}
(p/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print('FULL_MOVIE_ENCODED',str(movie),flush=True)
