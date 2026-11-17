import { chromium as pw } from 'playwright';
const browser = await pw.launch({
  executablePath: '/tmp/chromium',
  headless: true,
  args: ['--no-sandbox','--no-zygote','--disable-dev-shm-usage',
         '--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader',
         '--enable-webgl','--ignore-gpu-blocklist','--disable-gpu-sandbox'],
  ignoreDefaultArgs: ['--headless'],
});
const page = await browser.newPage({ viewport:{width:1080,height:1920} });
await page.setContent('<canvas id=c width=1080 height=1920></canvas>');
const info = await page.evaluate(()=>{
  const c=document.getElementById('c');
  const gl=c.getContext('webgl2')||c.getContext('webgl');
  if(!gl) return {ok:false};
  const d=gl.getExtension('WEBGL_debug_renderer_info');
  return {ok:true, version:gl.getParameter(gl.VERSION), renderer: d?gl.getParameter(d.UNMASKED_RENDERER_WEBGL):'?'};
});
console.log('WEBGL:', JSON.stringify(info));
await browser.close();
