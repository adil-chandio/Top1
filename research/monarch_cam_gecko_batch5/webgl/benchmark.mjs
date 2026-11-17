import { chromium as playwright } from 'playwright-core';
import chromium from '@sparticuz/chromium';
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import {performance} from 'node:perf_hooks';
const root=path.dirname(new URL(import.meta.url).pathname);
const out=path.resolve(root,'../../../studio/runtime/gecko/webgl-benchmark');fs.mkdirSync(out,{recursive:true});
const server=http.createServer((req,res)=>{const relative=decodeURIComponent((req.url||'/').split('?')[0]);const p=path.resolve(root,'.'+(relative==='/'?'/scene.html':relative));if(!p.startsWith(root+path.sep)){res.writeHead(403);res.end();return;}try{res.setHeader('Content-Type',p.endsWith('.html')?'text/html':'application/javascript');res.end(fs.readFileSync(p));}catch{res.writeHead(404);res.end();}});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
let browser;
try {
 browser=await playwright.launch({executablePath:await chromium.executablePath(),args:chromium.args,headless:true});const page=await browser.newPage({viewport:{width:720,height:1280}});page.on('pageerror',e=>console.error(e));await page.goto(`http://127.0.0.1:${server.address().port}/`);await page.waitForFunction(()=>window.ready===true);
 const timings=[];for(let f=0;f<12;f++){const start=performance.now();await page.evaluate(f=>window.renderFrame(f),f);await page.screenshot({path:path.join(out,`frame-${String(f).padStart(4,'0')}.jpg`),type:'jpeg',quality:94});timings.push((performance.now()-start)/1000);console.log('BENCHMARK_FRAME',f,timings.at(-1));}
 fs.writeFileSync(path.join(out,'receipt.json'),JSON.stringify({purpose:'WebGL infrastructure speed test only, not gecko quality proof',resolution:[720,1280],frames:12,seconds_per_frame:timings,quality_pass:false},null,2));
} finally {if(browser)await browser.close();await new Promise(r=>server.close(r));}
