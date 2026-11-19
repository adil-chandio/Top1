// Picture inputs are pulled and verified separately. The soundtrack, overlays,
// edit decisions and mux are local, never dispatched to GitHub.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { readFile, writeFile, mkdir, stat, rename } from 'node:fs/promises';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root=resolve(process.env.GECKO_NATURAL??'.cache/monarch-gecko/natural');
const work=join(root,'work'), segments=join(root,'picture','segments');
const prepare=process.env.GECKO_PREPARE==='1';
const ffmpeg=process.env.FFMPEG??'ffmpeg',probe=process.env.FFPROBE??'ffprobe';
const out=resolve(process.argv[3]??'deliverables/How-Does-a-Gecko-Let-Go-Creature-Edition.mp4');
assert.ok(!/How-Does-a-Gecko-Let-Go(?:-Premiere-Edition|-Creature-Proof)?\.mp4$/i.test(out));
const read=async (f)=>JSON.parse(await readFile(f,'utf8'));
const cut=await read(join(work,'edit.json')), plan=await read(join(work,'plan.json'));
assert.deepEqual([cut.frames,cut.fps,plan.frames,plan.fps],[1488,24,1488,24]);
assert.ok(!cut.captions,'Keep private dialogue separate');
const plate=resolve(process.env.GECKO_SCIENCE_PLATE??'.cache/monarch-gecko/upgrade/picture/edge-fix/picture.mp4');
const proof=resolve(process.env.GECKO_PROOF_PLATE??'.cache/monarch-gecko/creature/dispatch/44452508385/creature-plate.mp4');
const settle=resolve(process.env.GECKO_SETTLE_FRAMES??join(root,'picture','settle'));
const tiles=resolve(process.env.GECKO_TITLE_FRAMES??join(work,'titles'));
const mix=resolve(process.env.GECKO_CREATURE_MIX??join(work,'mix','audio.m4a'));
const local=process.argv[2]==='--native';
const packets=local?null:resolve(process.argv[2]??join(root,'dispatch','44457436403'));
const encode=['-an','-c:v','libx264','-profile:v','high','-level:v','4.0','-threads','2','-preset','fast','-crf','16','-g','48',
  '-maxrate','9500k','-bufsize','16000k','-pix_fmt','yuv420p','-r','24','-fps_mode','cfr','-video_track_timescale','24000',
  '-colorspace','bt709','-color_range','tv','-color_primaries','bt709','-color_trc','bt709',
  '-bsf:v','h264_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1:video_full_range_flag=0',
  '-movflags','+faststart+write_colr'];
const wrap=async (name,run)=>{
  const part=name.replace(/\.mp4$/i,'.part.mp4');assert.notEqual(name,part);
  await run(part);await rename(part,name);return name;
};
const inspect=(f)=>JSON.parse(execFileSync(probe,['-v','error','-count_frames','-show_streams','-of','json',f],{encoding:'utf8'})).streams;
const count=(f)=>+inspect(f)[0]?.nb_read_frames;
const run=(args)=>execFileSync(ffmpeg,['-nostdin','-hide_banner','-v','error','-xerror','-y',...args],{stdio:'inherit'});
const exists=async p=>(await stat(p).catch(()=>null))?.size>1000;
const quote=(s)=>s.replaceAll("'","'\\''");
const lists=async(file,parts)=>{
  await writeFile(file,'ffconcat version 1.0\n'+parts.map(({path,frames})=>`file '${quote(path)}'\nduration ${(frames/cut.fps).toFixed(9)}\n`).join(''));
  return ['-f','concat','-safe','0','-i',file];
};
await Promise.all([mkdir(segments,{recursive:true}),mkdir(join(root,'qa'),{recursive:true}),mkdir(dirname(out),{recursive:true})]);
const labels=await Promise.all(Array.from({length:cut.frames},(_,i)=>exists(join(tiles,`${String(i).padStart(4,'0')}.png`))));
assert.ok(labels.every(Boolean),'Render every frame-aligned title first');
assert.equal(count(plate),cut.frames,'Use the corrected underlying Premiere plate');
assert.equal(count(proof),plan.outFrame-plan.inFrame,'Use the clean reviewed creature proof plate, not the captioned video');
const receipt=prepare||local?null:await read(join(packets,'receipts.json'));
if(receipt){
  assert.equal(receipt.complete,true);
  assert.deepEqual(receipt.parts.map(({first,end})=>({first,end})),plan.parts);
  for(const p of receipt.parts){
    const b=await readFile(join(packets,p.file));
    assert.equal(createHash('sha256').update(b).digest('hex'),p.sha256);
  }
}

const results=[];
for(const s of plan.spans){
  const n=s.end-s.first;
  if(prepare&&s.source==='trace')continue;
  const name=join(segments,`f-${s.first}-${s.end}.mp4`);
  let clip,rgb=false,start=0;
  if(s.source==='trace'){
    if(local){
      rgb=true;
      clip=['-framerate','24','-start_number',String(s.first),'-i',join(root,'picture','frames','%04d.png')];
    }else{
      const sections=receipt.parts.filter(p=>p.first>=s.first&&p.end<=s.end);
      assert.equal(sections[0].first,s.first);assert.equal(sections.at(-1).end,s.end);
      assert.equal(sections.reduce((i,x)=>i+x.end-x.first,0),n);
      clip=await lists(join(segments,`trace-${s.first}.ffconcat`),sections.map(p=>({path:join(packets,p.file),frames:p.end-p.first})));
    }
  }else if(s.source==='science'){
    clip=['-i',plate];start=s.first;
  }else if(s.source==='proof'){
    clip=['-i',proof];
  }else if(s.source==='settle'){
    rgb=true;clip=['-framerate','24','-start_number',String(plan.outFrame-plan.inFrame),'-i',join(settle,'%04d.png')];
  }else throw new Error(`Unknown shot source: ${s.source}`);
  if(!await exists(name)||process.env.GECKO_REMASTER==='1'){
    const resize=rgb?'scale=1080:1920:flags=lanczos:in_range=full:out_range=tv:out_color_matrix=bt709':'scale=1080:1920:flags=lanczos:in_range=tv:out_range=tv';
    const timeline='settb=1/24000,setpts=N*1000';
    const sep=[`[0:v]trim=start_frame=${start}:end_frame=${start+n},${timeline},${resize},format=yuv420p,setsar=1[plate]`,
      `[1:v]trim=end_frame=${n},${timeline},scale=1080:1920:in_range=full:out_range=tv:out_color_matrix=bt709,format=yuva420p[title]`,
      '[plate][title]overlay=shortest=1:format=yuv420[graded]'].join(';');
    await wrap(name,part=>run(['-filter_complex_threads','2','-threads','2',...clip,'-threads','2','-framerate','24','-start_number',String(s.first),'-i',join(tiles,'%04d.png'),
      '-filter_complex',sep,'-map','[graded]','-frames:v',String(n),...encode,part]));
  }
  const v=inspect(name)[0];
  assert.deepEqual([+v.nb_read_frames,v.width,v.height,Math.round(+v.duration*cut.fps),v.avg_frame_rate,v.color_space],
    [n,1080,1920,n,'24/1','bt709']);
  results.push({path:name,frames:n,source:s.source,first:s.first,end:s.end});
  console.log(`Printed ${s.source.padEnd(7)} frames ${s.first}–${s.end} (exclusive)`);
}
if(prepare){console.log('Illustrations and release are ready; waiting for the native action ranges.');process.exit(0);}
assert.equal(results.reduce((i,s)=>i+s.frames,0),cut.frames);
const joinList=await lists(join(segments,'full.ffconcat'),results);
const video=join(root,'picture','creature-edition-picture.mp4');
await wrap(video,part=>run([...joinList,'-map','0:v:0','-c:v','copy','-an','-video_track_timescale','24000','-movflags','+faststart+write_colr',part]));
assert.equal(count(video),cut.frames);
const t=JSON.parse(execFileSync(probe,['-v','error','-select_streams','v:0','-show_frames','-show_entries','frame=best_effort_timestamp,pkt_duration','-of','json',video],{encoding:'utf8'})).frames;
assert.ok(t.length===cut.frames&&t.every((q,i)=>+q.best_effort_timestamp===i*1000),'Video frames must be uniformly timed, including all seams');
const verify=fileURLToPath(new URL('../finish.mjs',import.meta.url));
execFileSync(process.execPath,[verify, video,mix,out],{stdio:'inherit',env:{...process.env,
  GECKO_EDITION:'premiere',GECKO_TIMELINE:join(work,'edit.json'),GECKO_PROOF:join(root,'qa','master.json')}});
await writeFile(join(root,'qa','timeline.json'),JSON.stringify({frames:cut.frames,ptsUniform:true,nativeRun:receipt?.run??null,spans:results},null,2)+'\n');
