// Local typography pass. Uses the exact caption painter and two font faces
// from Premiere; no dialogue is bundled or sent to the picture workers.
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { resolve, join } from 'node:path';
import { setImmediate as onTick } from 'node:timers/promises';
import assert from 'node:assert/strict';
import { chromium } from 'playwright-core';
import { naturalEdit, picturePlan } from './edit.mjs';

const cut=await naturalEdit({picture:true});
assert.equal(cut.captions.length,32);
const output=resolve(process.argv[2]??'.cache/monarch-gecko/natural/work/titles');
const select=process.argv[3]?.split(',').map(Number)??null;
const plan=picturePlan(cut);
await mkdir(output,{recursive:true});
const root=new URL('../',import.meta.url), repo=new URL('../../../',import.meta.url);
const routes=new Map();
for(const [route,path,mime] of [
  ['/premiere/titles.js', new URL('premiere/titles.js',root),'text/javascript'],
  ['/motion.js', new URL('motion.js',root),'text/javascript'],
  ['/copy.woff2',new URL('node_modules/@fontsource-variable/dm-sans/files/dm-sans-latin-wght-normal.woff2',repo),'font/woff2'],
  ['/display.woff2',new URL('node_modules/@fontsource-variable/space-grotesk/files/space-grotesk-latin-wght-normal.woff2',repo),'font/woff2'],
])routes.set(route,{body:await readFile(path),contentType:mime});
routes.set('/',{contentType:'text/html',body:`<!doctype html><meta charset="utf-8"><title>Creature Edition typography</title><canvas width="1080" height="1920" hidden></canvas>
<script type="module">
  import {premiereTitles} from '/premiere/titles.js';
  import {between,smooth} from '/motion.js';
  const ctx=document.querySelector('canvas').getContext('2d'),W=1080,H=1920;
  for(const [name,file] of [['Copy','copy'],['Display','display']]){
    document.fonts.add(await new FontFace(name,'url(/'+file+'.woff2)',{weight:'100 1000'}).load());
  }
  const top=ctx.createLinearGradient(0,0,0,318);
  top.addColorStop(0,'#071118b1');top.addColorStop(.57,'#07101847');top.addColorStop(1,'#07101800');
  window.setup=(cut)=>{
    const print=premiereTitles(ctx,cut,{replay:['SECOND ANGLE  /  TOE SCALE','Digital hyperextension']});
    window.paint=(shot,frames)=>frames.map((f)=>{
      const t=f/cut.fps,age=(f-shot.frame)/cut.fps,remaining=(shot.end-f)/cut.fps;
      ctx.clearRect(0,0,W,H);
      if(shot.source!=='science'){
        print(t,{...shot,age,remaining},{});
        const peel=between(t,cut.marks.curlStart-.23,cut.marks.curlStart+.14)*(1-between(t,36.97,37.35));
        if(shot.source==='proof'&&peel){
          ctx.save();ctx.globalAlpha=peel*.94;ctx.fillStyle=top;ctx.fillRect(0,0,W,318);
          ctx.fillStyle='#b8efd7';ctx.fillRect(70,126,72,2.5);ctx.font='680 22px Display';ctx.fillText('03  /  THE RELEASE',70,169);
          ctx.fillStyle='#f5f3e7';ctx.font='690 46px Display';ctx.fillText('Toe tips lift first',68,224);ctx.restore();
        }
        const fade=between(t,61.42,61.998);
        if(fade){ctx.fillStyle='rgba(4,7,9,'+fade+')';ctx.fillRect(0,0,W,H);}
      } else {
        // The original plate already carries captions and tracked graphics.
        // Mark these inserts as illustrations even between chapter titles.
        const label=shot.kind.startsWith('shear')||shot.kind==='recap-shear'?'MECHANICAL ILLUSTRATION':'MICROSCOPY ILLUSTRATION';
        ctx.save();ctx.textBaseline='middle';ctx.textAlign='right';ctx.font='650 19px Display';
        const w=ctx.measureText(label).width+44;
        ctx.beginPath();ctx.roundRect(W-66-w,89,w,42,7);ctx.fillStyle='#061417a6';ctx.fill();
        ctx.strokeStyle='#a7d0ba50';ctx.lineWidth=1.3;ctx.stroke();
        ctx.fillStyle='#b8d6cb';ctx.fillText(label,W-87,111);ctx.restore();
      }
      return ctx.canvas.toDataURL('image/png').split(',')[1];
    });
  };
</script>`});
const browser=await chromium.launch({executablePath:process.env.CHROMIUM||undefined,args:['--no-zygote']});
try{
  const page=await browser.newPage({viewport:{width:570,height:1000}});
  const errors=[];page.on('pageerror',(err)=>errors.push(err.message));
  const origin='https://creature-production.invalid';
  await page.route('**/*',async r=>{const url=new URL(r.request().url()),data=routes.get(url.pathname);if(url.origin===origin&&data)return r.fulfill(data);await r.abort();});
  await page.goto(`${origin}/`);
  await page.waitForFunction(()=>typeof window.setup==='function',{},{timeout:8000}).catch(error=>{throw new Error(errors.join('\n')||error.message);});
  await page.evaluate(c=>window.setup(c),cut);
  let n=0;
  for(const s of plan.entries){
    const frames=Array.from({length:s.end-s.frame},(_,i)=>i+s.frame).filter(i=>!select||select.includes(i));
    for(let j=0;j<frames.length;j+=12){
      if(errors.length)throw new Error(errors.join('\n'));
      const range=frames.slice(j,j+12),pngs=await page.evaluate(({s,range})=>window.paint(s,range),{s,range});
      await Promise.all(pngs.map((png,i)=>writeFile(join(output,`${String(range[i]).padStart(4,'0')}.png`),Buffer.from(png,'base64'))));
      n+=range.length;await onTick();
    }
    if(frames.length)console.log(`${s.frame}–${s.end}: ${s.kind}, title alpha (${n}/${select?.length??cut.frames})`);
  }
  assert.equal(n,select?.length??cut.frames);
}finally{await browser.close();}
