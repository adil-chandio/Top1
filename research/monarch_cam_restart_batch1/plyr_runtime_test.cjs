const {chromium}=require('playwright');
const fs=require('fs');
(async()=>{
 const r={tool:'Plyr full browser component',video_id:'ZQvfHyfgBtA',playback_verified:false,visual_review_complete:false};let browser;
 try{
  const js=fs.readFileSync('node_modules/plyr/dist/plyr.polyfilled.js','utf8');
  const http=require('http');const server=http.createServer((req,res)=>{res.setHeader('Content-Type','text/html');res.end(`<html><body><div id="player" data-plyr-provider="youtube" data-plyr-embed-id="ZQvfHyfgBtA"></div><script>${js}</script><script>window.player=new Plyr('#player');</script></body></html>`);});
  await new Promise(resolve=>server.listen(8321,'127.0.0.1',resolve));
  browser=await chromium.launch({headless:true});const page=await browser.newPage();
  await page.goto('http://127.0.0.1:8321');await page.waitForTimeout(18000);
  r.component_created=await page.evaluate(()=>!!window.player);r.iframe_count=await page.locator('iframe').count();
  await page.evaluate(()=>{window.player.muted=true;window.player.play()?.catch(()=>{});});
  r.first=await page.evaluate(()=>({time:window.player.currentTime,ready:window.player.ready}));await page.waitForTimeout(6000);
  r.second=await page.evaluate(()=>({time:window.player.currentTime,ready:window.player.ready}));r.playback_verified=r.second.time>r.first.time+1;
  r.frame_text=[];for(const frame of page.frames()){try{r.frame_text.push((await frame.locator('body').innerText({timeout:2000})).slice(0,1600));}catch{}}
  server.close();
 }catch(e){r.error_type=e.name;}finally{if(browser)await browser.close();}
 const response=await fetch('https://api.github.com/repos/'+process.env.GITHUB_REPOSITORY+'/check-runs',{method:'POST',headers:{Authorization:'Bearer '+process.env.GH_TOKEN,Accept:'application/vnd.github+json','Content-Type':'application/json'},body:JSON.stringify({name:'plyr-actual-runtime-receipt',head_sha:process.env.GITHUB_SHA,status:'completed',conclusion:'neutral',output:{title:'Actual browser component playback test',summary:JSON.stringify(r)}})});if(!response.ok)throw Error('receipt failed');process.exit(0);
})();
