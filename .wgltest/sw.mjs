import { chromium as pw } from 'playwright';
const b = await pw.launch({executablePath:'/tmp/chromium', headless:true,
  args:['--no-sandbox','--no-zygote','--disable-gpu-sandbox','--disable-dev-shm-usage',
        '--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const p = await b.newPage({viewport:{width:540,height:960}});
await p.setContent('<canvas id=c width=540 height=960></canvas>');
const r = await p.evaluate(()=>{const c=document.getElementById('c');
  const gl=c.getContext('webgl2')||c.getContext('webgl'); return gl?gl.getParameter(gl.VERSION):'NO WEBGL';});
console.log('RESULT:', r);
await b.close();
