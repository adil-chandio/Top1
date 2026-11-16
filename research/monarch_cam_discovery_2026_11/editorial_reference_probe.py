"""Private research acquisition of a publicly released editorial test.
Not a licensed production asset or accepted quality/viral benchmark.
Only ciphertext and technical measurements leave the runner via public checks.
"""
import base64,hashlib,json,os,secrets,shutil,subprocess,urllib.request
from pathlib import Path
from cryptography.hazmat.primitives import serialization,hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
BASE=Path(__file__).parent
OUT=Path('studio/runtime/editorial-reference');OUT.mkdir(parents=True,exist_ok=True)
URL='https://github.com/jonaslacandola0617/curio-bureau/releases/download/visual-test-pistol-shrimp-v2-20261020/Curio-Test-03-Pistol-Shrimp-12s-v2.mp4'
def publish(name,data):
    payload={'name':name,'head_sha':os.environ['GITHUB_SHA'],'status':'completed','conclusion':'neutral','output':{'title':name,'summary':json.dumps(data)}}
    req=urllib.request.Request('https://api.github.com/repos/'+os.environ['GITHUB_REPOSITORY']+'/check-runs',data=json.dumps(payload).encode(),headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Accept':'application/vnd.github+json','Content-Type':'application/json'},method='POST')
    with urllib.request.urlopen(req,timeout=30) as r:print(name,json.load(r)['id'],flush=True)
def run(argv,seconds=120):
    p=subprocess.run(argv,capture_output=True,text=True,timeout=seconds)
    if p.returncode:raise RuntimeError(str(p.returncode)+':'+p.stderr[-1500:])
    return p.stderr

def main():
    report={'source_url':URL,'reference_kind':'owner-requested_public_visual_test_NOT_accepted_competitor_benchmark','production_reuse_permitted':False,'source_repository_code_executed':False,'actual_listening':False,'actual_realtime_viewing':False}
    try:
        ff=shutil.which('ffmpeg')
        if not ff:raise RuntimeError('native FFmpeg required')
        clip=OUT/'editorial-reference.mp4'
        run([ff,'-nostdin','-y','-v','error','-rw_timeout','15000000','-threads','1','-i',URL,'-t','12','-vf','scale=360:-2','-filter_threads','1','-c:v','libx264','-threads','1','-crf','30','-c:a','aac','-b:a','64k','-fs','3000000','-movflags','+faststart',str(clip)])
        raw=clip.read_bytes()
        if not raw or len(raw)>3000000:raise ValueError('bounded excerpt size invalid')
        report.update(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        report['full_excerpt_decode_log']=run([ff,'-nostdin','-v','info','-xerror','-i',str(clip),'-f','null','-'])[-5500:]
        report['loudness_measurement_log']=run([ff,'-nostdin','-v','info','-i',str(clip),'-vn','-af','ebur128=peak=true','-f','null','-'])[-3500:]
        wav=OUT/'speech.wav'
        run([ff,'-nostdin','-y','-v','error','-i',str(clip),'-vn','-ar','16000','-ac','1',str(wav)])
        try:
            from faster_whisper import WhisperModel
            model=WhisperModel('tiny.en',device='cpu',compute_type='int8',cpu_threads=2)
            segments,info=model.transcribe(str(wav),beam_size=3,word_timestamps=True,vad_filter=False)
            report['automatic_asr']={'language':info.language,'segments':[{'start':s.start,'end':s.end,'text':s.text,'words':[{'start':w.start,'end':w.end,'word':w.word,'probability':w.probability} for w in (s.words or [])]} for s in segments],'limitation':'Automatic transcription, NOT listening or verified narration accuracy.'}
        except Exception as exc:
            report['automatic_asr']={'status':'failed','type':type(exc).__name__}
        key=AESGCM.generate_key(bit_length=256);nonce=secrets.token_bytes(12)
        cipher=AESGCM(key).encrypt(nonce,raw,URL.encode())
        public=serialization.load_pem_public_key((BASE/'transfer-public.pem').read_bytes())
        wrapped=public.encrypt(key,padding.OAEP(mgf=padding.MGF1(hashes.SHA256()),algorithm=hashes.SHA256(),label=None))
        chunks=[cipher[i:i+40000] for i in range(0,len(cipher),40000)]
        if len(chunks)>76:raise ValueError('transfer chunk budget exceeded')
        for i,chunk in enumerate(chunks):publish('editorial-cipher-'+str(i),{'index':i,'base64':base64.b64encode(chunk).decode()})
        report['transfer']={'chunks':len(chunks),'nonce':base64.b64encode(nonce).decode(),'wrapped_key':base64.b64encode(wrapped).decode(),'cipher_sha256':hashlib.sha256(cipher).hexdigest(),'associated_data':URL}
        report['status']='acquired_and_measured_NOT_listened'
    except Exception as exc:
        report.update(status='access_or_processing_failed',error_type=type(exc).__name__,error=str(exc)[:1600])
        publish('editorial-reference-report',report)
        raise
    publish('editorial-reference-report',report)
if __name__=='__main__':main()
