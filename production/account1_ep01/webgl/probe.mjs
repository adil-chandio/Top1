/* Minimal probe: launch Chromium, load the stage, init, draw one frame,
   screenshot. Writes a single JSON line so CI can commit the result and we
   can read it from the branch without needing the job log. */
import http from 'node:http'; import fs from 'node:fs'; import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '../../..');
const OUT = path.join(ROOT, 'production/account1_ep01/webgl/qc');
fs.mkdirSync(OUT, { recursive: true });
const steps = [];
const t0 = Date.now();
const log = (k, v) => { steps.push([k, v, +((Date.now()-t0)/1000).toFixed(1)]); console.log(k, v); };

const MIME={'.html':'text/html','.js':'application/javascript','.mjs':'application/javascript','.json':'application/json','.glb':'model/gltf-binary','.wasm':'application/wasm'};
const srv=http.createServer((req,res)=>{
  const u=(req.url||'/').split('?')[0]; let fp;
  if(u==='/'||u==='/scene.html') fp=path.join(HERE,'scene.html');
  else if(u.startsWith('/vendor/three/')) fp=path.join(ROOT,'node_modules/three',u.replace('/vendor/three/',''));
  else if(u.startsWith('/assets/')) fp=path.join(ROOT,'production/account1_ep01/assets/glb',path.basename(u));
  else {res.writeHead(404);res.end();return;}
  if(!fs.existsSync(fp)){res.writeHead(404);res.end('missing '+fp);return;}
  res.writeHead(200,{'Content-Type':MIME[path.extname(fp)]||'application/octet-stream'});
  fs.createReadStream(fp).pipe(res);
});
await new Promise(r=>srv.listen(0,'127.0.0.1',r));
const base=`http://127.0.0.1:${srv.address().port}`;
const tl=JSON.parse(fs.readFileSync(path.join(ROOT,'production/account1_ep01/build/timeline_full.json'),'utf8'));

let browser, page, verdict='unknown';
try {
  browser = await chromium.launch({ headless:true, args:[
    '--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader',
    '--enable-webgl','--ignore-gpu-blocklist','--no-sandbox','--disable-dev-shm-usage']});
  log('launch','ok');
  page = await browser.newPage({viewport:{width:1080,height:1920}});
  page.on('pageerror', e => log('pageerror', e.message.slice(0,300)));
  page.on('console', m => { if (m.type()==='error') log('console', m.text().slice(0,300)); });
  await page.goto(base+'/scene.html',{waitUntil:'networkidle',timeout:90000});
  log('goto','ok');
  const gl = await page.evaluate(()=>{const c=document.createElement('canvas');
    const g=c.getContext('webgl2')||c.getContext('webgl');
    if(!g) return 'none';
    const d=g.getExtension('WEBGL_debug_renderer_info');
    return d?g.getParameter(d.UNMASKED_RENDERER_WEBGL):g.getParameter(g.VERSION);});
  log('webgl', String(gl).slice(0,120));
  /* load each GLB on its own first, so a single bad asset names itself */
  const each = await page.evaluate(async()=>{
    const THREE = await import('/vendor/three/build/three.module.js');
    const { GLTFLoader } = await import('/vendor/three/examples/jsm/loaders/GLTFLoader.js');
    const { DRACOLoader } = await import('/vendor/three/examples/jsm/loaders/DRACOLoader.js');
    const l = new GLTFLoader(); const d = new DRACOLoader();
    d.setDecoderPath('/vendor/three/examples/jsm/libs/draco/'); l.setDRACOLoader(d);
    const names = ['LeePerrySmith','venice_mask','Soldier','DiffuseTransmissionPlant','Lantern','GlassHurricaneCandleHolder'];
    const out = {};
    for (const n of names) {
      try {
        const g = await new Promise((res, rej) => l.load(`/assets/${n}.glb`, res, undefined, rej));
        let v = 0; g.scene.traverse(o => { if (o.isMesh) v += o.geometry.attributes.position.count; });
        out[n] = `ok ${v}v`;
      } catch (e) { out[n] = 'ERR ' + e.message.slice(0, 90); }
    }
    return out;
  });
  for (const [k, v] of Object.entries(each)) log('asset:' + k, v);
  const init = await page.evaluate(async(tl)=>{try{window.__SET_TIMELINE__(tl);await window.__PEHRA_INIT__(tl);return 'ok';}catch(e){return 'ERR '+e.message;}},tl);
  log('init', init);
  /* one representative frame per beat, so the look of every beat can be
     inspected from the branch without waiting on a full render */
  const picks = tl.shots.filter(s => s.f_start >= +process.env.P_F0 && s.f_start <= +process.env.P_F1);
  const ab = await page.evaluate(()=>window.__ASSET_BOUNDS__ || null);
  log('asset_bounds', JSON.stringify(ab));
  const meshes = await page.evaluate(()=>window.__MASK_MESHES__ || null);
  log('mask_meshes', JSON.stringify(meshes));
  /* B01 keeps showing a smeared plate in the upper left. Render it with the
     candidates hidden one at a time so the culprit names itself instead of
     being guessed at. */
  /* A single decisive pair: the aerial frame with the ground, and without it.
     If the smear survives the second image it is not the ground. */
  for (const hide of ['ground','moonDisc','moonHalo','gate','monarch','guardA','guardB']) {
    await page.evaluate((h) => {
      window.__HIDE__(h, true);
      window.__PEHRA_FRAME__(104);
    }, hide);
    await page.screenshot({path:path.join(OUT, `hide_${hide}.jpg`), type:'jpeg', quality:88});
    await page.evaluate((h) => window.__HIDE__(h, false), hide);
    log('hidden', hide);
  }
  const placed = await page.evaluate(()=>window.__MASK_PLACED__ || null);
  log('mask_placed', JSON.stringify(placed));
  for (const s of picks) {
    const f = await page.evaluate((idx)=>{try{window.__PEHRA_FRAME__(idx);return 'ok';}catch(e){return 'ERR '+e.message;}}, s.lookdev_frame);
    await page.screenshot({path:path.join(OUT, `${s.id}.jpg`), type:'jpeg', quality:92});
    log('beat:'+s.id, f);
  }
  verdict = (init==='ok' && f==='ok') ? 'PASS' : 'FAIL';
} catch (e) {
  log('exception', (e?.message||String(e)).slice(0,400));
  verdict = 'FAIL';
} finally {
  try { await browser?.close(); } catch {}
  srv.close();
  fs.writeFileSync(path.join(OUT,'probe.json'),
    JSON.stringify({verdict, steps, run: process.env.GITHUB_RUN_ID||'local'}, null, 2));
  console.log('VERDICT', verdict);
  if (verdict !== 'PASS') process.exitCode = 1;
}
