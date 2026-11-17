// Test FreeTube's underlying extractor, not the full Electron application.
// One anonymous ordinary request; no cookies/proxy/client rotation or paid API.
import { Innertube } from 'youtubei.js';
import fs from 'node:fs/promises';
import { spawnSync } from 'node:child_process';
const receipt={route:'youtubei.js 18.3.0 underlying FreeTube dependency, NOT full FreeTube',video_id:'ZQvfHyfgBtA',media_acquired:false,frames_decoded:false,visual_review_complete:false,audio_in_scope:false};
let dir;
try {
 dir=await fs.mkdtemp('/tmp/visual-route-');
 const yt=await Innertube.create({retrieve_player:true});
 const info=await yt.getBasicInfo(receipt.video_id);
 receipt.playability_status=info.playability_status?.status??null;
 if(info.playability_status?.status && info.playability_status.status!=='OK') throw new Error('playback_refused');
 const format=info.chooseFormat({type:'video',quality:'worst',format:'mp4'});
 if(format.content_length && Number(format.content_length)>60000000)throw new Error('size_cap');
 const stream=await yt.download(receipt.video_id,{type:'video',quality:'worst',format:'mp4'});
 const file=await fs.open(dir+'/source.mp4','w');let bytes=0;
 try{for await(const chunk of stream){bytes+=chunk.length;if(bytes>60000000)throw new Error('size_cap');await file.write(chunk);}}finally{await file.close();}
 receipt.bytes=bytes;receipt.media_acquired=bytes>0;
 const decoded=spawnSync('ffmpeg',['-nostdin','-v','error','-xerror','-i',dir+'/source.mp4','-an','-vf','fps=1/5,scale=320:-2','-frames:v','96',dir+'/frame-%03d.jpg'],{timeout:90000});
 receipt.frames_decoded=decoded.status===0;
 receipt.frame_count=(await fs.readdir(dir)).filter(x=>x.endsWith('.jpg')).length;
 // Do not publish copyrighted frames in checks; preserve bounded evidence artifact only on success.
 if(receipt.frames_decoded){await fs.mkdir('evidence/frames',{recursive:true});for(const n of await fs.readdir(dir)){if(n.endsWith('.jpg'))await fs.copyFile(dir+'/'+n,'evidence/frames/'+n);}}
}catch(e){receipt.error_type=e.name;receipt.error_class=receipt.playability_status&&receipt.playability_status!=='OK'?'playback_refused':'extractor_or_network_failure';}
finally{if(dir)await fs.rm(dir,{recursive:true,force:true});receipt.temporary_source_deleted=true;}
await fs.mkdir('evidence',{recursive:true});await fs.writeFile('evidence/receipt.json',JSON.stringify(receipt,null,2));
const body={name:'freetube-dependency-route-receipt',head_sha:process.env.GITHUB_SHA,status:'completed',conclusion:'neutral',output:{title:'Actual underlying extractor test; not full FreeTube playback',summary:JSON.stringify(receipt)}};
const response=await fetch('https://api.github.com/repos/'+process.env.GITHUB_REPOSITORY+'/check-runs',{method:'POST',headers:{Authorization:'Bearer '+process.env.GH_TOKEN,Accept:'application/vnd.github+json','Content-Type':'application/json'},body:JSON.stringify(body)});
if(!response.ok)throw new Error('receipt_publication_failed');console.log(JSON.stringify(receipt));
