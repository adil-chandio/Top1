import assert from 'node:assert/strict';
import { execFileSync, spawnSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { loadGeckoEdit, VO_SHA256 } from './session.mjs';

const [file,voice='.cache/monarch-gecko/input/narration.wav',session]=process.argv.slice(2);
if(!file) throw new Error('Usage: node tools/gecko/verify.mjs master.mp4 [v2.wav] [timeline.json]');
const cut=await loadGeckoEdit({from:session});
const ffmpeg=process.env.FFMPEG||'ffmpeg', ffprobe=process.env.FFPROBE||'ffprobe';
const hash=(file)=>createHash('sha256').update(readFileSync(file)).digest('hex');
const sha=hash(voice);
assert.equal(sha,VO_SHA256);
const p=JSON.parse(execFileSync(ffprobe,['-v','error','-count_frames','-show_streams','-show_format','-of','json',file],{encoding:'utf8'}));
const [v,a]=p.streams;
assert.equal(p.streams.length,2);
assert.equal(+p.format.duration,cut.duration);assert.equal(+v.duration,cut.duration);assert.equal(+a.duration,cut.duration);
assert.equal(+v.start_time,0);assert.equal(+a.start_time,0);assert.equal(+v.nb_read_frames,cut.frames);
assert.deepEqual([v.codec_name,v.profile,v.width,v.height,v.pix_fmt,v.color_range,v.color_space,v.color_primaries,v.color_transfer,v.avg_frame_rate],
  ['h264','High',1080,1920,'yuv420p','tv','bt709','bt709','bt709',`${cut.fps}/1`]);
assert.deepEqual([a.codec_name,a.profile,a.channels,+a.sample_rate],['aac','LC',2,48000]);
const mp4=readFileSync(file), boxes=[];
for(let offset=0;offset<mp4.length;){
  const size=mp4.readUInt32BE(offset);assert.ok(size>=8&&offset+size<=mp4.length);
  boxes.push(mp4.toString('ascii',offset+4,offset+8));offset+=size;
}
assert.equal(boxes[0],'ftyp');assert.ok(boxes.indexOf('moov')>0&&boxes.indexOf('moov')<boxes.indexOf('mdat'));
const decode=spawnSync(ffmpeg,['-nostdin','-hide_banner','-xerror','-err_detect','explode','-threads','2','-i',file,'-map','0:v:0','-map','0:a:0','-af','ebur128=peak=true','-f','null','-'],{encoding:'utf8',maxBuffer:2_000_000});
if(decode.error) throw decode.error;
assert.equal(decode.status,0,decode.stderr);
const meter=decode.stderr.split('Summary:').at(-1);
const integrated=Number(meter.match(/\bI:\s*(-?[\d.]+) LUFS/u)?.[1]);
const peak=Number(meter.match(/\bPeak:\s*(-?[\d.]+) dBFS/u)?.[1]);
assert.ok(integrated>=-16&&integrated<=-13,`Unexpected mix loudness ${integrated}`);
assert.ok(peak<=-1,`Post-AAC true peak ${peak}`);

// Does the same spoken performance appear in every speech-bearing window at
// its original time? Removing the low score bed makes the comparison robust
// to the authorized gain, stereofolding, EQ, limiter and AAC encoding.
const pcm=(source,mono)=>{
  const fx=mono?'aresample=48000,highpass=f=47,':'pan=mono|c0=.5*c0+.5*c1,';
  const bytes=execFileSync(ffmpeg,['-nostdin','-hide_banner','-v','error','-i',source,'-vn','-af',`${fx}aresample=24000,highpass=f=410,lowpass=f=7100`,'-f','f32le','-'],{maxBuffer:8_000_000});
  return new Float32Array(bytes.buffer,bytes.byteOffset,bytes.byteLength/4);
};
const mono=pcm(voice,true),mixed=pcm(file,false);
const hz=24000;
assert.equal(mono.length,cut.voiceDuration*hz);
assert.ok(mixed.length>=cut.duration*hz&&mixed.length<=cut.duration*hz+1024);
let speechWindows=0, minCorrelation=1, maxAbsLag=0;
for(let from=0;from<mono.length;from+=hz/4) {
  const start=Math.max(12,from),end=Math.min(mono.length,from+hz/4);
  let sum=0;for(let i=start;i<end;i++)sum+=mono[i]**2;
  if(sum<.000040*(end-start))continue;
  let best=-1,delay=0;
  for(let lag=-12;lag<=12;lag++){
    let dot=0,amp=0;
    for(let i=start;i<end;i++) {const value=mixed[i+lag];dot+=mono[i]*value;amp+=value*value;}
    const c=dot/Math.sqrt(sum*amp);
    if(c>best){best=c;delay=lag;}
  }
  assert.ok(best>.92,`Narration mismatch near ${(start/hz).toFixed(2)}s: ${best}`);
  assert.ok(Math.abs(delay)<=4,`Narration drift near ${(start/hz).toFixed(2)}s: ${delay} samples`);
  minCorrelation=Math.min(minCorrelation,best);maxAbsLag=Math.max(maxAbsLag,Math.abs(delay));speechWindows++;
}
assert.ok(speechWindows>175);
console.log(JSON.stringify({
  file,bytes:mp4.length,sha256:createHash('sha256').update(mp4).digest('hex'),duration:+p.format.duration,
  frames:+v.nb_read_frames,width:v.width,height:v.height,fps:v.avg_frame_rate,
  color:'BT.709 limited',audio:'AAC-LC stereo 48 kHz',integratedLUFS:integrated,truePeakDBTP:peak,
  fullDecode:true,fastStart:true,narration:{sha256:sha,seconds:mono.length/hz,speechWindows,minCorrelation:+minCorrelation.toFixed(4),maxMeasuredLagMS:+(1000*maxAbsLag/hz).toFixed(3)},
},null,2));
