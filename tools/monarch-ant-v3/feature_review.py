"""Make a fit-to-Drive copy only when the verified workspace master is too big.

Same edit, raster, cadence, captions (sidecar) and untouched AAC. This is a
second-generation picture encode and is labeled as such in the handoff.
"""
import json

from feature_cut import ANCHORS, DELIVER, MASTER, NAME, QA, WORK
from feature_finish import COLORS, VUI, filehash
from feature_delivery import decode_info, fast_start
from mix import ff

# The connector limits workspace staging to 100 MB (decimal conservative cap).
LIMIT=100_000_000


def build():
    master=WORK/f'{NAME}.mp4';r=json.loads((QA/'feature-delivery.json').read_text())
    assert r['sha256']==filehash(master) and master.stat().st_size==r['bytes']
    if master.stat().st_size<LIMIT:print('MASTER_FITS_DRIVE',master,flush=True);return
    p=DELIVER/f'{NAME}-Drive-Review.mp4';p.parent.mkdir(parents=True,exist_ok=True)
    tmp=WORK/'drive-review.pending.mp4'
    ff('-loglevel','warning','-y','-threads',2,'-i',master,
       '-map','0:v:0','-map','0:a:0','-map_metadata','0','-map_chapters','-1',
       '-c:v','libx264','-threads',2,'-preset','veryfast','-crf','18.5','-maxrate','2240k','-bufsize','3400k',
       '-g','60','-keyint_min','15','-profile:v','high','-level:v','4.1','-pix_fmt','yuv420p',
       '-video_track_timescale','30000','-fps_mode','passthrough','-bsf:v',VUI,*COLORS,
       '-c:a','copy','-movie_timescale','48000','-movflags','+faststart+write_colr',tmp)
    assert tmp.stat().st_size<LIMIT,tmp.stat().st_size
    h,tb,d=decode_info(tmp)
    assert len(d)==ANCHORS[-1] and any(f'{MASTER[0]}x{MASTER[1]}' in l and '30 fps' in l for l in h),h
    assert any('Audio: aac (LC)' in l and '48000 Hz, stereo' in l for l in h),h
    # Prove that compression did not replace, shift, or normalize the delivered mix.
    compare=lambda q:ff('-loglevel','error','-i',q,'-map','0:a:0','-vn','-c:a','copy','-f','hash','-hash','sha256','-').stdout
    digest=compare(master);assert compare(tmp)==digest
    fast_start(tmp)
    out=dict(bytes=tmp.stat().st_size,sha256=filehash(tmp),frames=len(d),timebase=str(tb),audio_hash=digest.decode().strip(),master_sha256=r['sha256'])
    (QA/'drive-review.json').write_text(json.dumps(out,indent=2)+'\n')
    # Put the viewable file beside the master, not inside the plate cache.
    tmp.replace(p);print(f'DRIVE_REVIEW_READY {p} · {out["bytes"]:,} bytes · {out["sha256"]}',flush=True)


if __name__=='__main__':build()
