import { readFile, mkdir, writeFile } from 'node:fs/promises';
import { join,resolve } from 'node:path';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import assert from 'node:assert/strict';
import { geckoCues, geckoScore, mixFilters } from './score.mjs';
import { loadGeckoEdit, VO_SHA256 } from './session.mjs';

const file=resolve(process.env.GECKO_VOICE??'.cache/monarch-gecko/input/narration.wav');
const dir=resolve(process.env.GECKO_MIX_DIR??'.cache/monarch-gecko/mix');
const session=await loadGeckoEdit();
const wav=await readFile(file);
const sha=createHash('sha256').update(wav).digest('hex');
assert.equal(sha,VO_SHA256,'Mix must use the original 60.80 s v2 recording');
await mkdir(dir,{recursive:true});
const fx=join(dir,'gecko-repo-fx.wav'), out=join(dir,'audio.m4a');
await writeFile(fx,geckoScore(session));
await writeFile(join(dir,'cues.json'),JSON.stringify(geckoCues(session),null,2)+'\n');
execFileSync(process.env.FFMPEG??'ffmpeg',['-nostdin','-hide_banner','-loglevel','error','-y','-i',file,'-i',fx,
  '-filter_complex',mixFilters(session.duration,+(process.env.GECKO_VOICE_GAIN??1.18)),'-map','[mix]','-threads','2','-c:a','aac','-b:a','192k','-ar','48000','-movflags','+faststart',out],{stdio:'inherit'});
console.log(`Mixed ${session.voiceDuration}s exact v2 VO, ${session.duration}s stereo edit: ${out}`);
