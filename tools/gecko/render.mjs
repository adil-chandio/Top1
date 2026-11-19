import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { createHash } from 'node:crypto';
import { mkdir, mkdtemp, readFile, readdir, rm, writeFile, rename, stat } from 'node:fs/promises';
import { resolve, join, dirname, extname, relative, isAbsolute } from 'node:path';
import { tmpdir } from 'node:os';
import { fileURLToPath } from 'node:url';
import assert from 'node:assert/strict';
import { chromium } from 'playwright-core';
import { build } from 'vite';
import { loadGeckoEdit } from './session.mjs';

const premiere=process.env.GECKO_EDITION==='premiere';
const repo=fileURLToPath(new URL('../../',import.meta.url));
const route=premiere?'premiere/stage.html':'stage.html';
const entry=fileURLToPath(new URL(`./${route}`,import.meta.url));
const cut=await loadGeckoEdit({picture:true,from:process.env.GECKO_TIMELINE??(premiere?new URL('./premiere/edit.json',import.meta.url):undefined)});
const target=resolve(process.env.GECKO_OUTPUT??(premiere?'.cache/monarch-gecko/upgrade/picture/picture.mp4':'.cache/monarch-gecko/master/picture.mp4'));
const raster=process.env.GECKO_RASTER??(premiere?'.72':'.65');
const stills=process.env.GECKO_STILLS?.split(',').map(Number);
const [first,last]=(process.env.GECKO_FRAMES?.split(':').map(Number)??[0,cut.frames]);
assert.ok(Number.isInteger(first)&&Number.isInteger(last)&&first>=0&&last<=cut.frames&&last>first);
assert.ok(!stills||stills.every(t=>Number.isFinite(t)&&t>=0&&t<cut.duration));
const ORIGIN='http://monarch-gecko-render.local';
const temp=await mkdtemp(join(tmpdir(),'gecko-dispatch-'));
const viewport=join(temp,'viewport');
const media=target.replace(/\.mp4$/i,'.part.mp4');
const wait=(child)=>new Promise((yes,no)=>{child.once('error',no);child.once('close',(code,signal)=>code===0?yes():no(new Error(`FFmpeg failure ${code??signal}`)));});
let browser;
try{
  assert.ok(stills||target!==media,`Movie render output must end in .mp4: ${target}`);
  await mkdir(stills?target:dirname(target),{recursive:true});
  const cutPath=join(temp,'cut.json');
  await writeFile(cutPath,JSON.stringify(cut));
  await build({configFile:false,root:repo,base:'./',publicDir:false,logLevel:'error',resolve:{alias:{'#gecko-cut':cutPath}},build:{outDir:viewport,emptyOutDir:true,target:'esnext',rollupOptions:{input:entry}}});
  browser=await chromium.launch({executablePath:process.env.CHROMIUM||undefined,args:['--enable-unsafe-swiftshader','--use-angle=swiftshader','--no-zygote']});
  const page=await browser.newPage({viewport:{width:600,height:1066}});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));page.on('console',msg=>{if(msg.type()==='error')errors.push(msg.text());});
  const types={'.html':'text/html','.js':'text/javascript','.woff2':'font/woff2','.json':'application/json','.jpg':'image/jpeg','.webp':'image/webp','.png':'image/png'};
  await page.route('**/*', async (r)=>{
    const url=new URL(r.request().url()),path=resolve(viewport,`.${decodeURIComponent(url.pathname)}`),rel=relative(viewport,path);
    if(url.origin!==ORIGIN||rel.startsWith('..')||isAbsolute(rel)||!types[extname(path)])return r.abort();
    try{await r.fulfill({path,contentType:types[extname(path)]});}catch{await r.fulfill({status:404});}
  });
  await page.goto(`${ORIGIN}/tools/gecko/${route}?raster=${raster}&optics=${encodeURIComponent(process.env.GECKO_OPTICS??'film')}`);
  try{await page.waitForFunction(()=>typeof window.monarchGeckoFrame==='function',{},{timeout:20_000});}
  catch(e){throw new Error(`Gecko compositor did not initialize: ${errors.join('; ')||e.message}`);}
  if(stills){
    for(const at of stills){
      const jpeg=await page.evaluate((t)=>window.monarchGeckoFrame(t),at);
      const path=join(target,`gecko-${at.toFixed(2)}.jpg`);await writeFile(path,Buffer.from(jpeg,'base64'));console.log(path);
    }
  }else{
    const ffmpeg=process.env.FFMPEG??'ffmpeg';
    const saveParts=premiere && !process.env.GECKO_FRAMES;
    const parts= saveParts ? [0,253,537,819,1074,1264,1488] : [first,last];
    const start=Date.now();
    const run=async(args)=>wait(spawn(ffmpeg,args,{stdio:['ignore','ignore','inherit']}));
    const paths=[];
    let subdir;
    if(saveParts){
      const hash=createHash('sha256').update(`${cut.frames},${raster},${process.env.GECKO_OPTICS??'film'},enc-2`);
      for(const path of (await readdir(viewport,{recursive:true,withFileTypes:true})).filter(x=>x.isFile()).map(x=>join(x.parentPath,x.name)).sort()){
        hash.update(relative(viewport,path));hash.update(await readFile(path));
      }
      subdir=join(dirname(target),'segments',hash.digest('hex').slice(0,20));
      await mkdir(subdir,{recursive:true});
    }
    for(let seg=0;seg<parts.length-1;seg++){
      const begin=parts[seg],end=parts[seg+1];
      const path=saveParts?join(subdir,`frames-${begin}-${end}.mp4`):target;
      const part=path.replace(/\.mp4$/i,'.part.mp4');
      paths.push(path);
      if(saveParts&&(await stat(path).catch(()=>null))?.size>1000){console.log(`Using sealed chapter ${begin}–${end-1}`);continue;}
      let failure;
      const child=spawn(ffmpeg,['-nostdin','-hide_banner','-loglevel','error','-y','-filter_threads','1',
        '-f','image2pipe','-framerate',`${cut.fps}`,'-c:v','mjpeg','-i','pipe:0','-an',
        '-vf','scale=in_range=full:in_color_matrix=bt601:out_range=tv:out_color_matrix=bt709,format=yuv420p',
        '-c:v','libx264','-profile:v','high','-level:v','4.0','-preset','veryfast','-crf',premiere?'17':'18','-g','48','-threads','2','-maxrate',premiere?'8800k':'7200k','-bufsize',premiere?'17600k':'14400k','-colorspace','bt709','-color_primaries','bt709','-color_trc','bt709','-color_range','tv','-bsf:v','h264_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1:video_full_range_flag=0','-movflags','+faststart+write_colr',part],{stdio:['pipe','ignore','inherit']});
      const encoded=wait(child);encoded.catch((e)=>{failure=e;});child.stdin.on('error',e=>{failure ||= e;});
      try{
        for(let i=begin;i<end;i+=4){
          if(failure)throw failure;if(errors.length)throw new Error(errors.join('; '));
          const frames=await page.evaluate(({first,last,fps})=>Array.from({length:last-first},(_,j)=>window.monarchGeckoFrame((first+j)/fps)),{first:i,last:Math.min(end,i+4),fps:cut.fps});
          for(const f of frames)if(!child.stdin.write(Buffer.from(f,'base64')))await Promise.race([once(child.stdin,'drain'),encoded]);
          if((i-begin)%(cut.fps*3)===0)console.log(`${i}/${last} frames · ${(i/cut.fps).toFixed(2)}s · elapsed ${((Date.now()-start)/1000).toFixed(1)}s`);
        }
        child.stdin.end();await encoded;
        await rename(part,path);console.log(`${path}: ${(await stat(path)).size} bytes`);
      }catch(e){child.stdin.destroy();if(child.exitCode===null)child.kill();await encoded.catch(()=>{});throw e;}
    }
    if(saveParts){
      const list=join(temp,'join.ffconcat');
      const esc=(s)=>s.replaceAll("'","'\\''");
      await writeFile(list,'ffconcat version 1.0\n'+paths.map((path,i)=>`file '${esc(path)}'\nduration ${((parts[i+1]-parts[i])/cut.fps).toFixed(9)}\n`).join(''));
      await run(['-nostdin','-hide_banner','-loglevel','error','-y','-safe','0','-f','concat','-i',list,'-map','0:v:0','-c','copy','-movflags','+faststart+write_colr',media]);
      await rename(media,target);console.log(`${target}: ${(await stat(target)).size} bytes`);
    }
  }
  if(errors.length)throw new Error(errors.join('; '));
}finally{await browser?.close();await rm(temp,{recursive:true,force:true});}
