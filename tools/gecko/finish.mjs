import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import { mkdir, rename, rm, writeFile } from 'node:fs/promises';
import { loadGeckoEdit } from './session.mjs';

const premiere=process.env.GECKO_EDITION==='premiere';
const scope=premiere?'.cache/monarch-gecko/upgrade':'.cache/monarch-gecko';
const [picture=`${scope}/${premiere?'picture':'master'}/picture.mp4`,mix=`${scope}/mix/audio.m4a`,out=`deliverables/How-Does-a-Gecko-Let-Go${premiere?'-Premiere-Edition':''}.mp4`]=process.argv.slice(2);
const edit=process.env.GECKO_TIMELINE??fileURLToPath(new URL(premiere?'./premiere/edit.json':'./edit.json',import.meta.url));
const cut=await loadGeckoEdit({from:edit});
const file=resolve(out), part=resolve(dirname(file),`.gecko-working-${process.pid}.mp4`);
const ffmpeg=process.env.FFMPEG||'ffmpeg';
const verify=fileURLToPath(new URL('./verify.mjs',import.meta.url));
await mkdir(dirname(file),{recursive:true});
try {
  execFileSync(ffmpeg,['-nostdin','-hide_banner','-loglevel','error','-y','-i',picture,'-i',mix,'-map','0:v:0','-map','1:a:0','-c','copy',
    '-map_metadata','-1','-metadata',`title=${cut.title}`,'-metadata:s:a:0','language=eng','-movflags','+faststart+write_colr',part],{stdio:'inherit'});
  const output=execFileSync(process.execPath,[verify,part,process.env.GECKO_VOICE??'.cache/monarch-gecko/input/narration.wav',edit],{encoding:'utf8'});
  const proof={...JSON.parse(output),file:out};
  await rename(part,file);
  if(process.env.GECKO_PROOF)await writeFile(process.env.GECKO_PROOF,JSON.stringify(proof,null,2)+'\n');
  console.log(JSON.stringify(proof,null,2));
} finally { await rm(part,{force:true}); }
