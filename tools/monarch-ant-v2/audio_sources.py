"""Verify or recover V2 audio inputs by their pinned Git blob identities.
The official individual licenses and modification credit are in the cut notes.
Requires gh only when a file is missing; never evaluates downloaded JS.
"""
import argparse
import base64
from hashlib import sha1, sha256
import json
from pathlib import Path
import subprocess

from cut import ROOT

K='evanlin23/blocky-stories'
W='NeoSoundFonts/WilhelmSFX'
F='gleitz/midi-js-soundfonts'
PINS={K:'328f356539d059f360175b66f3a88b2ba78e7c91',W:'ec4875a35d265b5431e3ba81fef6cc0ca0281bfc',F:'044fab8e1456bfafc5776e86dfd6bb8697149aef'}
# Git blob IDs are of the exact acquired material, not inferred from the clip title.
INPUTS=[
 (K,'assets/audio/steps/gravel/gravel_02.wav','downloaded/gravel_02.wav','874a41852b2523d040f8a820dcfa56668a6bf502'),
 (K,'assets/audio/steps/gravel/gravel_05.wav','downloaded/gravel_05.wav','a40b8365e9670e260ecc3c76fdb9513a92bef18d'),
 (K,'assets/audio/steps/gravel/gravel_07.wav','downloaded/gravel_07.wav','3c31c99f9ee8416da07fd38dcaa78a3f483cf3bb'),
 (K,'assets/audio/steps/gravel/gravel_08.wav','downloaded/gravel_08.wav','f02289859a8ffa3de5b56e0a3240d7caca665474'),
 (K,'assets/licenses/kenney_rpg-audio_License.txt','kenney-rpg-license.txt','c19921a2fb2402ead892083a2a5d09ce90e7e9e4'),
 (W,'Samples/146408__crashoverride6__sand-on-paper-dragged-long.wav','downloaded/sand-sweep.wav','b4ee9805c439630c0b1ae4b6af76d78dd0e22b26'),
 (W,'Samples/464699__branndybottle__sandwalking_step1.wav','downloaded/sand-step.wav','4dfdad819a1c63f123ff5acb1b9f075f9a4ab77a'),
 (W,'Samples/464695__branndybottle__sandwalking_step2.wav','downloaded/sand-step-alt.wav','803e4a8cdae7462b1407622aef9751c26618a219'),
 (W,'Samples/151214__owlstorm__click-finger-snap.wav','downloaded/soft-snap.wav','d9c03cd92493113a51e4df6e70b60f475a1990b8'),
 (W,'Samples/332604__vckhaze__single-finger-snap.wav','downloaded/snap-alt.wav','52f930d4436e276ef2d83c3f69d80635e9fd15a8'),
 (F,'FluidR3_GM/acoustic_grand_piano-mp3.js','instruments/acoustic_grand_piano.js','5eb408d4a7be57810a954540a9f9d0ac3690b0a2'),
 (F,'FluidR3_GM/cello-mp3.js','instruments/cello.js','02d23f84a90eb1e0413e56713ed03b28b0c553ac'),
 (F,'FluidR3_GM/pizzicato_strings-mp3.js','instruments/pizzicato_strings.js','361d8f1c14f92d849dc0ec0fb0921d96754689ba'),
 (F,'README.md','instr-readme.txt','a6e34ed5c9cae0f6bf6b598fe7273b71f740dfd1'),
]


def identify(b):
    return sha1(f'blob {len(b)}\0'.encode()+b).hexdigest()


def main(fetch=False):
    p=ROOT/'audio';l=[]
    for repo,src,dst,blob in INPUTS:
        f=p/dst
        if f.exists():b=f.read_bytes()
        elif fetch:
            d=json.loads(subprocess.check_output(['gh','api',f'repos/{repo}/git/blobs/{blob}']))
            b=base64.b64decode(''.join(d['content'].split()),validate=True)
        else:raise FileNotFoundError(f'{f}; use --fetch to retrieve the pinned copy')
        if identify(b)!=blob:raise ValueError(f'source mismatch: {f}')
        if not f.exists():
            f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(b)
        l.append(dict(name=dst,repository=repo,revision=PINS[repo],path=src,git_blob=blob,sha256=sha256(b).hexdigest(),bytes=len(b)))
    (p/'audio-sources.json').write_text(json.dumps(l,indent=2)+'\n')
    print(f'{len(l)} pinned assets and notices verified')


if __name__=='__main__':
    cli=argparse.ArgumentParser();cli.add_argument('--fetch',action='store_true');a=cli.parse_args();main(a.fetch)
