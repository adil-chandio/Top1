import { createHash } from 'node:crypto';
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import { join,resolve } from 'node:path';
import { execFileSync } from 'node:child_process';
import assert from 'node:assert/strict';
import { loadGeckoEdit, VO_SHA256 } from '../session.mjs';
import { buildPremiereScore } from './score.mjs';

const cut=await loadGeckoEdit({from:new URL('./edit.json',import.meta.url)});
const voz=resolve(process.env.GECKO_VOICE??'.cache/monarch-gecko/input/narration.wav');
const dir=resolve(process.env.GECKO_MIX_DIR??'.cache/monarch-gecko/upgrade/mix');
assert.equal(createHash('sha256').update(await readFile(voz)).digest('hex'),VO_SHA256);
const {music,foley,cues}=buildPremiereScore(cut);
await mkdir(dir,{recursive:true});
const m=join(dir,'original-music.wav'), f=join(dir,'repo-effects.wav'), out=join(dir,'audio.m4a');
await Promise.all([writeFile(m,music),writeFile(f,foley),writeFile(join(dir,'cues.json'),JSON.stringify(cues,null,2)+'\n')]);
const filter=[
  '[0:a]aresample=48000,highpass=f=47,pan=stereo|FL=c0|FR=c0,volume=1.175,apad=whole_dur=62,asplit=2[vox][key]',
  '[1:a]highpass=f=44,equalizer=f=2300:t=q:w=1:g=-3,volume=0.77[music]',
  '[music][key]sidechaincompress=threshold=0.034:ratio=4.15:attack=13:release=248[score]',
  '[2:a]volume=1.06[sfx]',
  '[vox][score][sfx]amix=inputs=3:duration=first:normalize=0,alimiter=limit=0.77:level=0:latency=1,atrim=duration=62[print]',
].join(';');
execFileSync(process.env.FFMPEG??'ffmpeg',['-nostdin','-hide_banner','-loglevel','error','-y','-i',voz,'-i',m,'-i',f,'-filter_complex',filter,
  '-map','[print]','-c:a','aac','-ar','48000','-b:a','256k','-movflags','+faststart',out],{stdio:'inherit'});
console.log(`${cut.title}: ${cues.length} action cues, mixed exact original v2 VO with new stereo score at ${out}`);
