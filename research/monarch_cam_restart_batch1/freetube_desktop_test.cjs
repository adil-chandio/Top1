const { _electron: electron } = require('playwright');
const fs=require('node:fs/promises');
(async()=>{
 const r={application:'official FreeTube 0.26.0-beta Linux desktop',full_desktop:true,video_id:'ZQvfHyfgBtA',launched:false,playback_established:false,audio_in_scope:false};let app;
 try{
  app=await electron.launch({executablePath:process.env.FREETUBE_EXE,args:['--no-sandbox','--disable-gpu','--user-data-dir=/tmp/freetube-test-profile'],timeout:45000});
  const page=await app.firstWindow({timeout:45000});await page.waitForLoadState('domcontentloaded');r.launched=true;
  // Navigate the app's existing Vue route, not a replacement browser player.
  await page.evaluate(()=>{location.hash='/watch/ZQvfHyfgBtA';});
  await page.waitForTimeout(20000);
  const sample=()=>page.evaluate(()=>Array.from(document.querySelectorAll('video')).map(v=>({time:v.currentTime,readyState:v.readyState,width:v.videoWidth,height:v.videoHeight,paused:v.paused,error:v.error?.code??null})));
  r.first=await sample();
  if(await page.locator('video').count())await page.locator('video').first().evaluate(v=>{v.muted=true;v.play().catch(()=>{});});
  await page.waitForTimeout(7000);r.second=await sample();
  r.playback_established=r.second.some((v,i)=>v.width>0&&v.time>(r.first[i]?.time??0)+1);
  r.ui_text=(await page.locator('body').innerText()).slice(0,4500);
  await fs.mkdir('evidence',{recursive:true});await page.screenshot({path:'evidence/freetube-desktop.png'});
 }catch(e){r.error_type=e.name;r.failure_stage=r.launched?'desktop_navigation_or_player':'desktop_launch';}
 finally{if(app)await app.close();await fs.rm('/tmp/freetube-test-profile',{recursive:true,force:true});r.temporary_profile_deleted=true;}
 await fs.mkdir('evidence',{recursive:true});await fs.writeFile('evidence/receipt.json',JSON.stringify(r,null,2));
 const body={name:'freetube-full-desktop-receipt',head_sha:process.env.GITHUB_SHA,status:'completed',conclusion:'neutral',output:{title:'Actual full desktop execution',summary:JSON.stringify(r)}};
 const response=await fetch('https://api.github.com/repos/'+process.env.GITHUB_REPOSITORY+'/check-runs',{method:'POST',headers:{Authorization:'Bearer '+process.env.GH_TOKEN,Accept:'application/vnd.github+json','Content-Type':'application/json'},body:JSON.stringify(body)});if(!response.ok)throw Error('receipt publication failed');
})();
