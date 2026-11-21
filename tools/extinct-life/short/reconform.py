#!/usr/bin/env python3
"""Replace a checked AAC mix without changing a single encoded video byte."""
from json import loads
from mix import MIX, ff
from spec import CACHE, NAME, QA, TITLE, digest, dump


def video_hash(p):
    line,_=ff(['-v','error','-i',p,'-map','0:v:0','-c:v','copy','-f','hash','-hash','sha256','-'])
    return line.decode('ascii').strip()


def remux():
    p=CACHE/'encode'/(NAME+'.pending.mp4');out=p.with_name(NAME+'.reconform.mp4');receipt=QA/'build.json'
    r=loads(receipt.read_text());m=loads((QA/'mix.json').read_text());wav=MIX/'program.wav'
    before=digest(p);locked=video_hash(p)
    assert before==r['encode_sha256'] and digest(wav)==m['sha256'] and r['program_audio']!=m['sha256']
    ff(['-v','error','-y','-i',p,'-i',wav,'-map','0:v:0','-map','1:a:0','-map_metadata','-1','-c:v','copy',
        '-c:a','aac','-profile:a','aac_low','-b:a','320k','-ar','48000','-metadata',f'title={TITLE}',
        '-metadata:s:a:0','language=eng','-movflags','+faststart',out])
    assert locked==video_hash(out)
    r.update(encode_sha256=digest(out),program_audio=m['sha256'],reconform={'previous_mp4':before,'video_packets':locked,'mix_only':True})
    out.replace(p);dump(receipt,r);print('SHORT_PICTURE_UNCHANGED_DURING_REMIX',locked,flush=True)

if __name__=='__main__':remux()
