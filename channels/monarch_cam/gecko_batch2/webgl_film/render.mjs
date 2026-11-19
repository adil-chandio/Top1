import { chromium } from 'playwright-core';
import { build } from 'vite';
import { mkdtemp, mkdir, writeFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join, resolve, extname, relative, isAbsolute } from 'node:path';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { fileURLToPath } from 'node:url';
const root=fileURLToPath(new URL('.',import.meta.url));const temp=await mkdtemp(join(tmpdir(),'gecko-webgl-'));const output=join(root,'output');await mkdir(output,{recursive:true});const ffmpeg=process.env.FFMPEG||'ffmpeg';const stills=process.env.GECKO_STILLS==='1';const fps=24;let browser;
function score(){const sr=48000,n=12*sr,b=Buffer.alloc(44+n*4);b.write('RIFF',0);b.writeUInt32LE(b.length-8,4);b.write('WAVEfmt ',8);b.writeUInt32LE(16,16);b.writeUInt16LE(1,20);b.writeUInt16LE(2,22);b.writeUInt32LE(sr,24);b.writeUInt32LE(sr*4,28);b.writeUInt16LE(4,32);b.writeUInt16LE(16,34);b.write('data',36);b.writeUInt32LE(n*4,40);
 for(let i=0;i<n;i++){const t=i/sr,fade=Math.min(1,t/1.0,(12-t)/1.0),s=(Math.sin(2*Math.PI*110*t)*.06+Math.sin(2*Math.PI*164.81*t)*.035+Math.sin(2*Math.PI*220*t)*.02)*fade;const v=Math.round(32767*s);b.writeInt16LE(v,44+i*4);b.writeInt16LE(v,46+i*4)}return b}
function exit(child){return new Promise((ok,no)=>{child.on('error',no);child.on('close',code=>code===0?ok():no(Error('FFmpeg exit '+code)))})}
try{
 const dist=join(temp,'dist');await build({configFile:false,root,base:'./',publicDir:false,logLevel:'error',build:{outDir:dist,emptyOutDir:true,target:'esnext'}});
 browser=await chromium.launch({executablePath:process.env.CHROMIUM,args:['--no-sandbox','--enable-unsafe-swiftshader','--use-angle=swiftshader','--no-zygote'],headless:true});const page=await browser.newPage({viewport:{width:540,height:960}});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text())});
 await page.route('**/*',async route=>{const u=new URL(route.request().url());if(u.origin!=='http://render.local')return route.abort();const f=resolve(dist,'.'+decodeURIComponent(u.pathname));const r=relative(dist,f);if(r.startsWith('..')||isAbsolute(r))return route.abort();const types={'.html':'text/html','.js':'text/javascript','.css':'text/css'};try{await route.fulfill({path:f,contentType:types[extname(f)]||'application/octet-stream'})}catch{await route.fulfill({status:404,body:'not found'})}});
 await page.goto('http://render.local/index.html');await page.waitForFunction(()=>typeof window.renderFrame==='function',{timeout:30000});
 if(stills){for(const t of [0,2,4,6,8,9.5,11]){const jpg=await page.evaluate(t=>window.renderFrame(t),t);await writeFile(join(output,`still-${t}.jpg`),Buffer.from(jpg,'base64'));console.log('still',t)}}
 else{
  const wav=join(temp,'score.wav');await writeFile(wav,score());const file=join(output,'gecko-webgl-concept.mp4');
  const c=spawn(ffmpeg,['-hide_banner','-loglevel','error','-y','-f','image2pipe','-framerate',String(fps),'-c:v','mjpeg','-i','pipe:0','-i',wav,'-vf','format=yuv420p','-c:v','libx264','-crf','20','-preset','fast','-threads','2','-c:a','aac','-b:a','96k','-movflags','+faststart','-shortest',file],{stdio:['pipe','inherit','inherit']});let failure;const done=exit(c);done.catch(e=>failure=e);c.stdin.on('error',e=>failure=e);
  try{for(let i=0;i<fps*12;i++){if(failure)throw failure;const jpeg=await page.evaluate(t=>window.renderFrame(t),i/fps);if(!c.stdin.write(Buffer.from(jpeg,'base64')))await Promise.race([once(c.stdin,'drain'),done]);if(i%48===0)console.log('render',i/fps,'/ 12 s')}c.stdin.end();await done}catch(e){c.stdin.destroy();c.kill();await done.catch(()=>{});throw e}console.log('Saved',file)
 }
 if(errors.length)throw Error('Browser errors: '+errors.join('; '));
}finally{await browser?.close();await rm(temp,{recursive:true,force:true})}
