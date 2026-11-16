"""Internal proxy animatic timing test. NOT scored/sound-designed feasibility proof.
Uses original recovered narration without speed/pitch processing or added effects.
Waveform silence is a timing hint, never a listening or transcript verification.
"""
import argparse,hashlib,json,math,re,subprocess,wave
from pathlib import Path
import imageio_ffmpeg

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--layout',required=True);p.add_argument('--voice',required=True);p.add_argument('--out',required=True);a=p.parse_args()
 layout=Path(a.layout);voice=Path(a.voice);out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
 manifest=json.loads((layout.parent/'manifest.json').read_text());duration=manifest['duration_seconds'];fps=manifest['fps']
 if manifest['type']!='silent_original_proxy_layout_NOT_integrated_AV_proof':raise ValueError('proxy layout required')
 expected=next(x['sha256'] for x in manifest['files'] if x['path']==layout.name)
 if sha(layout)!=expected:raise ValueError('layout changed since render receipt')
 with wave.open(str(voice)) as w:voice_duration=w.getnframes()/w.getframerate();rate=w.getframerate()
 if voice_duration<duration:raise ValueError('not enough original voice; do not loop/speed it')
 ff=imageio_ffmpeg.get_ffmpeg_exe()
 detect=subprocess.run([ff,'-nostdin','-hide_banner','-i',str(voice),'-af','silencedetect=noise=-35dB:d=0.12','-f','null','-'],capture_output=True,text=True,check=True)
 starts=[float(x) for x in re.findall(r'silence_start: ([0-9.]+)',detect.stderr)];ends=[float(x) for x in re.findall(r'silence_end: ([0-9.]+)',detect.stderr)]
 intervals=list(zip(starts,ends));inside=any(s<=duration<=e for s,e in intervals)
 if not inside:raise ValueError('candidate endpoint not in detected quiet interval; choose new frame-aligned duration')
 dest=out/'VOICE_LAYOUT_INTERNAL.mp4'
 subprocess.run([ff,'-nostdin','-y','-v','error','-xerror','-i',str(layout),'-i',str(voice),'-map','0:v:0','-map','1:a:0','-t',str(duration),'-c:v','copy','-c:a','aac','-b:a','160k','-movflags','+faststart',str(dest)],check=True,timeout=90)
 subprocess.run([ff,'-nostdin','-v','error','-xerror','-i',str(dest),'-f','null','-'],check=True,timeout=90)
 decode=subprocess.run([ff,'-nostdin','-v','error','-i',str(dest),'-map','0:v:0','-f','framemd5','-'],capture_output=True,text=True,check=True,timeout=90)
 frame_hashes=[x for x in decode.stdout.splitlines() if x.strip() and not x.startswith('#')]
 if len(frame_hashes)!=manifest['frames']:raise ValueError('frame count changed')
 receipt={'type':'voice_only_proxy_animatic_NOT_creative_release','duration_seconds':duration,'frames':len(frame_hashes),'fps':fps,'resolution':manifest['resolution'],'original_voice_duration':voice_duration,'original_voice_sample_rate':rate,'voice_source_git_blob':'c3c8a13f12c532e32ffc4c27ba82e571cfd187bf','voice_sha256':sha(voice),'layout_sha256':sha(layout),'output_sha256':sha(dest),'bytes':dest.stat().st_size,'detected_quiet_intervals':intervals,'end_in_detected_quiet_interval':inside,'speed_change':False,'pitch_change':False,'music':False,'sfx':False,'actual_listening_review':False,'independent_review':False,'stage_advanced':False,'technical_checks':{'full_decode':True,'frame_count':True},'limitations':['Quiet interval is signal measurement, not verified sentence boundary or word alignment','Rough original vector proxies, not finished animal animation','No sound-design/mix/reference-AV/independent-quality gate cleared']}
 (out/'voice_animatic_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
