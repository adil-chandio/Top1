import assert from 'node:assert/strict';
import { resolve, join } from 'node:path';
import { tmpdir } from 'node:os';
import { pathToFileURL } from 'node:url';
import { mkdtemp, writeFile,rm } from 'node:fs/promises';
import { chromium, devices } from 'playwright-core';
import { action, fps, frames } from './motion.js';
const file=resolve(process.argv[2]??'deliverables/How-Does-a-Gecko-Let-Go-Creature-Proof.mp4');
const scratch=await mkdtemp(join(tmpdir(),'monarch-creature-play-'));
const pagePath=join(scratch,'preview.html');
let browser;
try{
  await writeFile(pagePath,`<!doctype html><meta name="viewport" content="width=device-width,initial-scale=1"><title>Private proof QA</title><body style="margin:0;background:#12141b"><video playsinline preload="auto" style="display:block;width:min(100vw,56.25dvh);height:100dvh;margin:auto" src="${pathToFileURL(file)}"></video><button id="play" style="position:fixed;top:10px;left:10px" onclick="document.querySelector('video').play()">Play</button></body>`);
  browser=await chromium.launch({executablePath:process.env.CHROMIUM||undefined,args:['--no-zygote','--enable-unsafe-swiftshader','--use-angle=swiftshader']});
  const page=await browser.newPage({...devices['Pixel 7']});
  await page.goto(pathToFileURL(pagePath).href);
  const v=page.locator('video');
  await page.waitForFunction(()=>{const el=document.querySelector('video');return el.error||el.readyState>=2;},{},{timeout:12000});
  const meta=await v.evaluate(el=>({w:el.videoWidth,h:el.videoHeight,d:el.duration,muted:el.muted,error:el.error?.message??null}));
  assert.ok(meta.w>400 && Math.abs(meta.w/meta.h-.5625)<.002 && Math.abs(meta.d-frames/fps)<.01);
  assert.equal(meta.muted,false);assert.equal(meta.error,null);
  await page.getByRole('button',{name:'Play'}).tap();
  await page.waitForFunction(()=>document.querySelector('video').currentTime>.48,{},{timeout:7000});
  const marks=[action.plant,1.84,action.peel+.45,(action.peel+action.free)/2,action.free-.15,action.wristClear];
  for(const t of marks){
    const state=await v.evaluate((el,t)=>new Promise((done,reject)=>{
      el.pause();const timer=setTimeout(()=>reject(new Error('seek timeout')),5000);
      el.addEventListener('seeked',()=>{clearTimeout(timer);done({t:el.currentTime,error:el.error?.message??null});},{once:true});
      el.currentTime=t;
    }),t);
    assert.ok(Math.abs(state.t-t)<1/fps);assert.equal(state.error,null);
  }
  await v.evaluate(el=>{el.currentTime=el.duration-.69;return el.play();});
  await page.waitForFunction(()=>document.querySelector('video').ended,{},{timeout:7000});
  console.log(JSON.stringify({viewport:'Pixel 7 emulation',metadata:meta,unmutedPlayback:true,seeks:marks,ended:true},null,2));
}finally{await browser?.close();await rm(scratch,{recursive:true,force:true});}
