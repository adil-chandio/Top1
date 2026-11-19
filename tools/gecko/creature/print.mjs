import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { execFileSync, spawnSync } from 'node:child_process';
import { readFile, writeFile, mkdir, rename, stat } from 'node:fs/promises';
import { dirname, join, resolve } from 'node:path';
import { fps, frames, inFrame, outFrame, action } from './motion.js';
import { readGeckoSrt, VO_SHA256 } from '../session.mjs';

const root=resolve(process.env.GECKO_CREATURE_WORK??'.cache/monarch-gecko/creature');
const picture=resolve(process.argv[2]??join(root,'render'));
const output=resolve(process.argv[3]??'deliverables/How-Does-a-Gecko-Let-Go-Creature-Proof.mp4');
const media=output.replace(/\.mp4$/i,'.part.mp4');
assert.notEqual(output,media);
assert.ok(!/How-Does-a-Gecko-Let-Go(?:-Premiere-Edition)?\.mp4$/i.test(output),'Do not overwrite an existing edition');
const start=inFrame/fps,end=outFrame/fps,duration=frames/fps;
const voice=resolve(process.env.GECKO_VOICE??'.cache/monarch-gecko/input/narration.wav');
const captions=resolve(process.env.GECKO_CAPTIONS??'deliverables/How-Does-a-Gecko-Let-Go.en.srt');
const ffmpeg=process.env.FFMPEG??'ffmpeg',ffprobe=process.env.FFPROBE??'ffprobe';
const sha=(bytes)=>createHash('sha256').update(bytes).digest('hex');
assert.equal(sha(await readFile(voice)),VO_SHA256,'Use the unchanged original v2 recording');
const dest=join(root,'finish');await mkdir(dest,{recursive:true});
const ex=(cmd,args,options={})=>execFileSync(cmd,args,{maxBuffer:8_000_000,...options});
const rate=48000,total=duration*rate;
assert.ok(Number.isInteger(total));
const s=Math.sin,T=2*Math.PI,clamp=(x)=>Math.max(0,Math.min(1,x)),ramp=(t,a,b)=>{const u=clamp((t-a)/(b-a));return u*u*(3-2*u);};
const pan=(angle)=>[Math.cos(angle),Math.sin(angle)];
function rng(seed){let state=seed;return ()=>{state=(Math.imul(state,1664525)+1013904223)>>>0;return state/2**31-1;};}
const hz=(m)=>440*2**((m-69)/12);
const score=Buffer.alloc(44+total*4),foley=Buffer.alloc(score.length);
for(const buf of [score,foley]){
  buf.write('RIFF',0);buf.writeUInt32LE(buf.length-8,4);buf.write('WAVEfmt ',8);buf.writeUInt32LE(16,16);buf.writeUInt16LE(1,20);buf.writeUInt16LE(2,22);
  buf.writeUInt32LE(rate,24);buf.writeUInt32LE(rate*4,28);buf.writeUInt16LE(4,32);buf.writeUInt16LE(16,34);buf.write('data',36);buf.writeUInt32LE(total*4,40);
}
// No sampled or reference audio. Original short D-minor study: bowed drone,
// restrained wood plucks and a resolution that arrives after contact breaks.
const notes=[
  [.109,50,.102,-.36], [action.plant+.024,57,.079,.262], [1.546,62,.061,-.165],
  [2.09,60,.058,.291], [2.712,53,.079,-.301], [3.585,57,.047,.239], [4.426,64,.038,.335],
  [5.217,62,.053,-.293], [6.74,50,.098,-.25], [7.17,57,.076,.255], [7.59,65,.051,-.222], [8.05,62,.047,.2],
].map(([t,n,g,p])=>({t,f:hz(n),g,pan:pan(Math.PI/4+p)}));
const cues=[
  [.081,.583,.052,-.185,'reach / forearm cloth-like pass'],
  [action.plant-.006,.087,.094,.259,'dry pad set on glass'],
  [1.32,.427,.040,.361,'limb loading against fixed footprint'],
  [2.29,.435,.046,-.123,'shift onto the three other supports'],
  [action.free+.124,.314,.060,.284,'lift after the pads clear'],
  [7.38,.355,.030,.314,'wrist follows through'],
];
const r0=rng(20713),r1=rng(870143);let l=0,h=0,m=0, z=0;
for(let i=0;i<total;i++){
  const t=i/rate, tail=1-ramp(t,duration-.48,duration), opening=ramp(t,0,.079);
  const noise=r0(),nw=r1();
  l+=.011*(noise-l); h+=.135*(noise-h);m+=.042*(nw-m);z+=.231*(nw-z);
  const wind=(l*.093+m*.029)*( .42 + .38*s(t*.93+.7)**2 );
  const pulse=1+.18*s(t*3.19);
  const bowed = (.039*s(T*hz(38)*t+.112*s(3.81*t))+.019*s(T*hz(50)*t+.55+.31*s(t*12.3)) + .012*s(T*hz(57)*t+1.7)) * pulse;
  let ml=bowed*.92+wind,mr=bowed*.94+(l*.053-m*.044);
  for(const {t:at,f,g,pan:[a,b]} of notes){
    const d=t-at;if(d<0||d>2.09)continue;
    const e=(1-Math.exp(-d*76))*Math.exp(-d*2.38)*g;
    const voice=e*(s(T*f*d)+.297*s(T*f*2.007*d+.19)*Math.exp(-d*2.1)+.132*s(T*f*3.19*d)*Math.exp(-d*5.3));
    ml+=a*voice;mr+=b*voice;
  }
  let fl=0,fr=0;
  for(const [at,len,g,p] of cues){
    const d=t-at;if(d<0||d>len)continue;
    const u=d/len, a=Math.PI/4+p;
    const dry=(z-m)*.46+(h-l)*.98 + .104*s(T*(199*d+145*u*u))*Math.exp(-d*39);
    const env=(1-Math.exp(-d*(len<.1?192:35)))*(1-ramp(u,.19,1));
    const texture=dry*env*g;
    fl+=Math.cos(a)*texture;fr+=Math.sin(a)*texture;
  }
  for(const [buf,L,R] of [[score,ml*tail*opening,mr*tail*opening],[foley,fl,fr]]){
    buf.writeInt16LE(Math.round(L*32767),44+i*4);buf.writeInt16LE(Math.round(R*32767),46+i*4);
  }
}
await Promise.all([writeFile(join(dest,'score.wav'),score),writeFile(join(dest,'foley.wav'),foley),
  writeFile(join(dest,'cues.json'),JSON.stringify(cues.map(([second,length,, ,role])=>({second,length,role})),null,2)+'\n')]);
const cap=readGeckoSrt(await readFile(captions,'utf8')).filter(([a,b])=>a>=start&&b<=end);
assert.equal(cap.length,4,'Proof window must contain the same four complete caption cues');
const time=(sec)=>{const k=Math.round(sec*100);return `0:${String(Math.floor(k/6000)).padStart(2,'0')}:${(k%6000/100).toFixed(2).padStart(5,'0')}`;};
const esc=(x)=>x.replaceAll('\\','\\h').replaceAll('{','(').replaceAll('}',')');
const events=cap.map(([a,b,...lines])=>`Dialogue: 0,${time(a-start)},${time(b-start)},Caption,,0,0,0,,${lines.map(esc).join('\\N')}`).join('\n');
await writeFile(join(dest,'sub.ass'),`[Script Info]\nTitle: Creature proof (private source captions)\nScriptType: v4.00+\nPlayResX: 576\nPlayResY: 1024\nScaledBorderAndShadow: yes\n\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle: Caption,DejaVu Sans,34,&H00F8FAFA,&H00F8FAFA,&H24091418,&H51050D10,-1,0,0,0,100,100,0,0,1,2.4,1.6,2,50,50,136,1\nStyle: Slug,DejaVu Sans,13,&H00CDF1DF,&H00CDF1DF,&H380A1919,&H55091213,-1,0,0,0,100,100,2.7,0,1,.88,.9,7,39,36,54,1\nStyle: Headline,DejaVu Sans,25,&H00FAF5E6,&H00FAF5E6,&H3B071317,&H59061116,-1,0,0,0,100,100,-.43,0,1,1.31,.9,7,39,36,79,1\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\nDialogue: 0,0:00:00.00,0:00:01.79,Slug,,0,0,0,,{\\fad(135,230)}MONARCH STUDIO  /  CREATURE STUDY\nDialogue: 0,0:00:00.03,0:00:01.79,Headline,,0,0,0,,{\\fad(135,230)}Tokay on glass\n${events}\n`);
const voiceTake=join(dest,'voice-excerpt.wav');
// Select samples at the source rate, then apply the same gain/low-cut as the
// original film. There is no TTS, speed change, word splice, or truncation.
ex(ffmpeg,['-nostdin','-v','error','-y','-i',voice,'-af',`atrim=start_sample=${start*24000}:end_sample=${Math.round(end*24000)},asetpts=PTS-STARTPTS`,voiceTake]);
const voiceFilter='aresample=48000,highpass=f=47,pan=stereo|FL=c0|FR=c0,volume=1.17';
const audio=join(dest,'mix.m4a');
const filter=[`[0:a]${voiceFilter},asplit=2[v][side]`,
  '[1:a]highpass=f=45,equalizer=f=2100:t=q:w=1:g=-3,volume=0.78[m]',
  '[m][side]sidechaincompress=threshold=0.041:ratio=3.70:attack=15:release=210[music]',
  '[2:a]highpass=f=68,volume=1.04[fx]',
  `[v][music][fx]amix=inputs=3:normalize=0:duration=first,alimiter=limit=.76:level=0:latency=1,atrim=end_sample=${total}[mix]`,
].join(';');
ex(ffmpeg,['-nostdin','-hide_banner','-v','error','-y','-i',voiceTake,'-i',join(dest,'score.wav'),'-i',join(dest,'foley.wav'),
  '-filter_complex',filter,'-map','[mix]','-c:a','aac','-b:a','192k','-ar','48000','-movflags','+faststart',audio],{stdio:'inherit'});
if(process.env.GECKO_AUDIO_ONLY==='1'){console.log(`Original proof mix and four shifted captions: ${dest}`);process.exit(0);}
const pngs=!picture.endsWith('.mp4');
const videoIn=pngs?['-framerate',String(fps),'-start_number','0','-i',join(picture,'%04d.png')]:['-i',picture];
if(pngs){
  const receipt=JSON.parse(await readFile(join(picture,'picture.json'),'utf8'));
  assert.deepEqual([receipt.fps,receipt.frames],[fps,frames]);
  for(let i=0;i<frames;i++)assert.ok((await stat(join(picture,`${String(i).padStart(4,'0')}.png`))).size>900);
}
await mkdir(dirname(output),{recursive:true});
const fontDir=process.env.GECKO_FONT_DIR??'/usr/share/fonts/truetype/dejavu';
const csc=pngs?'scale=in_range=full:out_range=tv:out_color_matrix=bt709,':'';
ex(ffmpeg,['-nostdin','-hide_banner','-v','error','-y','-filter_threads','1',...videoIn,'-i',audio,
  '-map','0:v:0','-map','1:a:0','-vf',`${csc}format=yuv420p,ass=sub.ass:fontsdir=${fontDir}`,'-frames:v',`${frames}`,
  '-c:v','libx264','-profile:v','high','-preset','slow','-crf','16','-g','48','-threads','2','-color_range','tv',
  '-colorspace','bt709','-color_primaries','bt709','-color_trc','bt709',
  '-bsf:v','h264_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1:video_full_range_flag=0','-c:a','copy','-movflags','+faststart+write_colr',media],{cwd:dest,stdio:'inherit'});
const p=JSON.parse(ex(ffprobe,['-v','error','-count_frames','-show_format','-show_streams','-of','json',media],{encoding:'utf8'}));
const [v,a]=p.streams;assert.equal(p.streams.length,2);
assert.deepEqual([v.codec_name,v.pix_fmt,v.color_range,v.color_space,v.color_primaries,v.color_transfer,v.avg_frame_rate,+v.nb_read_frames],['h264','yuv420p','tv','bt709','bt709','bt709','24/1',frames]);
assert.deepEqual([a.codec_name,a.profile,a.channels,+a.sample_rate],['aac','LC',2,rate]);
assert.ok(Math.abs(+v.duration-duration)<.001&&Math.abs(+a.duration-duration)<.003);
assert.equal(+v.start_time,0);assert.equal(+a.start_time,0);
const mp4=await readFile(media);let i=0;const tags=[];
while(i<mp4.length){const n=mp4.readUInt32BE(i);assert.ok(n>=8&&i+n<=mp4.length);tags.push(mp4.toString('ascii',i+4,i+8));i+=n;}
assert.ok(tags.indexOf('moov')>0&&tags.indexOf('moov')<tags.indexOf('mdat'));
const decode=spawnSync(ffmpeg,['-nostdin','-hide_banner','-xerror','-err_detect','explode','-i',media,'-af','ebur128=peak=true:framelog=verbose','-f','null','-'],{encoding:'utf8',maxBuffer:2_000_000});
assert.equal(decode.status,0,decode.stderr);
const meter=decode.stderr.split('Summary:').at(-1);
const lufs=Number(meter.match(/\bI:\s*(-?[\d.]+) LUFS/)?.[1]);const tp=Number(meter.match(/\bPeak:\s*(-?[\d.]+) dBFS/)?.[1]);
assert.ok(lufs>=-17&&lufs<=-13&&tp<=-1.15,`Unexpected output levels ${lufs} LUFS / ${tp} dBTP`);
const pcm=(path,original)=>{
  const fx=original?'aresample=48000,highpass=f=47,':'pan=mono|c0=.5*c0+.5*c1,';
  const b=ex(ffmpeg,['-nostdin','-v','error','-i',path,'-vn','-af',`${fx}aresample=24000,highpass=f=428,lowpass=f=7200`,'-f','f32le','-']);
  return new Float32Array(b.buffer,b.byteOffset,b.length/4);
};
const src=pcm(voiceTake,true),mixed=pcm(media,false);let windows=0,least=1,delay=0;
for(let u=14;u+6000<=src.length-12;u+=6000){
  let n=0;for(let k=u;k<u+6000;k++)n+=src[k]**2;
  if(n/6000<.000044)continue;
  let best=-1,lag=0;
  for(let d=-9;d<=9;d++){
    let ab=0,nn=0;for(let k=u;k<u+6000;k++){ab+=src[k]*mixed[k+d];nn+=mixed[k+d]**2;}
    const s=ab/Math.sqrt(n*nn);if(s>best){best=s;lag=d;}
  }
  assert.ok(best>.92&&Math.abs(lag)<=4,`Proof narration mismatch at ${u/24000}s, ${best}, lag ${lag}`);
  least=Math.min(least,best);delay=Math.max(delay,Math.abs(lag));windows++;
}
assert.ok(windows>=23,'too few speech windows');
await rename(media,output);
const stats={file:output,bytes:mp4.length,sha256:sha(mp4),width:v.width,height:v.height,fps,frames,duration,
  fullDecode:true,fastStart:true,stereo48k:true,lufs,tp,captionCues:cap.length,
  voice:{source:VO_SHA256,cut:[start,end],speechWindows:windows,minCorrelation:least,maxLagMS:delay/24}};
await writeFile(join(dest,'verification.json'),JSON.stringify(stats,null,2)+'\n');
console.log(JSON.stringify(stats,null,2));
