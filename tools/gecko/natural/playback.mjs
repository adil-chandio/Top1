import assert from 'node:assert/strict';
import { resolve, join } from 'node:path';
import { tmpdir } from 'node:os';
import { pathToFileURL } from 'node:url';
import { mkdtemp, writeFile,rm } from 'node:fs/promises';
import { chromium, devices } from 'playwright-core';

const file=resolve(process.argv[2]??'deliverables/How-Does-a-Gecko-Let-Go-Creature-Edition.mp4');
const tmp=await mkdtemp(join(tmpdir(),'creature-edition-play-'));
const pagePath=join(tmp,'index.html');
let browser;
try{
  await writeFile(pagePath,`<!doctype html><meta name="viewport" content="width=device-width,initial-scale=1"><title>Private Creature Edition QC</title><body style="margin:0;background:#12141b"><video playsinline preload="auto" style="display:block;width:min(100vw,56.25dvh);height:100dvh;margin:auto" src="${pathToFileURL(file)}"></video><button id="play" style="position:fixed;top:10px;left:10px" onclick="document.querySelector('video').play()">Play</button></body>`);
  browser=await chromium.launch({executablePath:process.env.CHROMIUM||undefined,args:['--no-zygote','--enable-unsafe-swiftshader','--use-angle=swiftshader']});
  const page=await browser.newPage({...devices['Pixel 7']});
  await page.goto(pathToFileURL(pagePath).href);
  const v=page.locator('video');
  await page.waitForFunction(()=>{const el=document.querySelector('video');return el.error||el.readyState>=2;},{},{timeout:12000});
  const meta=await v.evaluate(el=>({w:el.videoWidth,h:el.videoHeight,d:el.duration,muted:el.muted,error:el.error?.message??null}));
  assert.deepEqual(meta,{w:1080,h:1920,d:62,muted:false,error:null});
  await page.getByRole('button',{name:'Play'}).tap();
  await page.waitForFunction(()=>document.querySelector('video').currentTime>2.48,{},{timeout:8000});
  const marks=[3.18,6.63,11.75,18.8,29.25,32.958,35.33,37.29,39.95,40.95,42.85,49.38,57.02,60.64];
  const read=await v.evaluate(async(el,ts)=>{
    el.pause();const result=[];
    for(const t of ts){
      await new Promise((done,reject)=>{
        const timer=setTimeout(()=>reject(new Error(`Seek failed at ${t}`)),6200);
        el.addEventListener('seeked',()=>{clearTimeout(timer);done();},{once:true});el.currentTime=t;
      });
      result.push([el.currentTime,el.error?.message??null,el.readyState]);
    }
    return result;
  },marks);
  assert.ok(read.every(([t,error,ready],i)=>Math.abs(t-marks[i])<1/24&&!error&&ready>=2));
  await v.evaluate(el=>{el.currentTime=el.duration-1.12;return el.play();});
  await page.waitForFunction(()=>document.querySelector('video').ended,{},{timeout:8000});
  console.log(JSON.stringify({viewport:'Pixel 7 emulation',metadata:meta,unmutedPlayback:true,seeks:marks,ended:true},null,2));
}finally{await browser?.close();await rm(tmp,{recursive:true,force:true});}
