import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { join,resolve } from 'node:path';
import assert from 'node:assert/strict';
import { naturalEdit } from './edit.mjs';
import { buildPremiereScore } from '../premiere/score.mjs';
import { editionCues } from './sound.mjs';
import { VO_SHA256 } from '../session.mjs';

const ffmpeg=process.env.FFMPEG??'ffmpeg';
const cut=await naturalEdit();
const voice=resolve(process.env.GECKO_VOICE??'.cache/monarch-gecko/input/narration.wav');
const out=resolve(process.argv[2]??'.cache/monarch-gecko/natural/work/mix');
assert.equal(createHash('sha256').update(await readFile(voice)).digest('hex'),VO_SHA256,'Use the unchanged approved narration');
const {music,foley,cues}=buildPremiereScore(cut,{cues:editionCues(cut),creature:true});
await mkdir(out,{recursive:true});
const m=join(out,'score.wav'), f=join(out,'foley.wav'), dest=join(out,'audio.m4a');
await Promise.all([writeFile(m,music),writeFile(f,foley),writeFile(join(out,'cues.json'),JSON.stringify(cues,null,2)+'\n')]);
const mix=[
  '[0:a]aresample=48000,highpass=f=47,pan=stereo|FL=c0|FR=c0,volume=1.175,apad=whole_len=2976000,asplit=2[voice][key]',
  '[1:a]highpass=f=44,equalizer=f=2240:t=q:w=1:g=-3,volume=0.74[bed]',
  '[bed][key]sidechaincompress=threshold=.034:ratio=4.45:attack=13:release=228[score]',
  '[2:a]highpass=f=68,volume=0.98[sfx]',
  '[voice][score][sfx]amix=inputs=3:duration=first:normalize=0,alimiter=limit=.77:level=0:latency=1,atrim=end_sample=2976000[a]',
].join(';');
execFileSync(ffmpeg,['-nostdin','-hide_banner','-v','error','-y','-i',voice,'-i',m,'-i',f,'-filter_complex',mix,
  '-map','[a]','-c:a','aac','-ar','48000','-b:a','256k','-movflags','+faststart',dest],{stdio:'inherit'});
console.log(`Exact v2 VO + Creature score and ${cues.length} Foley cues → ${dest}`);
