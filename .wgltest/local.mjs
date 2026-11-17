import http from 'node:http'; import fs from 'node:fs'; import path from 'node:path';
import { chromium as pw } from 'playwright';
const ROOT='/home/user/Top1', KIT=ROOT+'/production/account1_ep01/webgl';
const MIME={'.html':'text/html','.js':'application/javascript','.mjs':'application/javascript','.glb':'model/gltf-binary','.json':'application/json'};
const srv=http.createServer((req,res)=>{
  const u=(req.url||'/').split('?')[0]; let fp;
  if(u==='/'||u==='/scene.html') fp=KIT+'/scene.html';
  else if(u.startsWith('/vendor/three/')) fp=path.join(ROOT,'.wgltest/node_modules/three',u.replace('/vendor/three/',''));
  else if(u.startsWith('/assets/')) fp=path.join(ROOT,'production/account1_ep01/assets/glb',path.basename(u));
  else {res.writeHead(404);res.end();return;}
  if(!fs.existsSync(fp)){res.writeHead(404);res.end('missing '+fp);return;}
  res.writeHead(200,{'Content-Type':MIME[path.extname(fp)]||'application/octet-stream'});
  fs.createReadStream(fp).pipe(res);
});
await new Promise(r=>srv.listen(0,'127.0.0.1',r));
const base=`http://127.0.0.1:${srv.address().port}`;
console.log('serving',base);
const b=await pw.launch({executablePath:'/tmp/chromium',headless:true,
  args:['--no-sandbox','--no-zygote','--disable-gpu-sandbox','--disable-dev-shm-usage',
        '--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const p=await b.newPage({viewport:{width:1080,height:1920}});
p.on('pageerror',e=>console.log('PAGEERR:',e.message.slice(0,200)));
p.on('console',m=>{if(m.type()==='error')console.log('CONSOLE:',m.text().slice(0,200));});
const tl=JSON.parse(fs.readFileSync(ROOT+'/production/account1_ep01/build/timeline_full.json'));
let t=Date.now();
await p.goto(base+'/scene.html',{waitUntil:'networkidle',timeout:120000}).catch(e=>console.log('GOTO FAIL',e.message.slice(0,120)));
console.log('loaded in',((Date.now()-t)/1000).toFixed(1),'s');
t=Date.now();
const ok=await p.evaluate(async(tl)=>{try{window.__SET_TIMELINE__(tl);await window.__PEHRA_INIT__(tl);return 'OK';}catch(e){return 'INIT ERR: '+e.message;}},tl).catch(e=>'EVAL ERR: '+e.message);
console.log('init:',ok,((Date.now()-t)/1000).toFixed(1),'s');
t=Date.now();
const fr=await p.evaluate(()=>{try{window.__PEHRA_FRAME__(60);return 'FRAME OK';}catch(e){return 'FRAME ERR: '+e.message;}}).catch(e=>'EVAL ERR: '+e.message);
console.log('frame1:',fr,((Date.now()-t)/1000).toFixed(2),'s');
t=Date.now();
await p.evaluate(()=>window.__PEHRA_FRAME__(61)).catch(()=>{});
console.log('frame2:',((Date.now()-t)/1000).toFixed(2),'s');
await p.screenshot({path:'/tmp/localframe.jpg',type:'jpeg',quality:94});
console.log('screenshot saved');
await b.close(); srv.close();
