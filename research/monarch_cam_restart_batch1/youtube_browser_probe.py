"""Public browser playback diagnostic. No login, cookies import or challenge bypass."""
import asyncio
import json
import os
import urllib.request
from playwright.async_api import async_playwright

# Fixed supported runner OS avoids ubuntu-latest browser-library drift.
URL='https://www.youtube.com/watch?v=WqRpgJZeCPU'

async def main():
    result={'url':URL,'route':'standard Chromium public watch page',
            'login_used':False,'challenge_bypass':False,'human_listening':False,
            'success':False}
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True,args=['--no-sandbox'])
        page=await browser.new_page(viewport={'width':1280,'height':800})
        responses=[]
        page.on('response',lambda r: responses.append({'status':r.status,'host':r.url.split('/')[2]}) if 'googlevideo.com/' in r.url else None)
        try:
            response=await page.goto(URL,wait_until='domcontentloaded',timeout=45000)
            result['http_status']=response.status if response else None
            # Ordinary consent interaction only, not authentication or bot handling.
            for label in ['Reject all','Accept all']:
                button=page.get_by_role('button',name=label,exact=True)
                if await button.count():
                    await button.first.click(timeout=5000)
                    result['consent_button']=label
                    break
            await page.wait_for_selector('video',timeout=20000)
            await page.locator('video').first.evaluate('(v)=>{v.muted=true;v.play().catch(()=>{});} ')
            await page.wait_for_timeout(8000)
            result['first']=await page.locator('video').first.evaluate('(v)=>({time:v.currentTime,readyState:v.readyState,paused:v.paused,duration:Number.isFinite(v.duration)?v.duration:null,error:v.error?{code:v.error.code,message:v.error.message}:null,videoWidth:v.videoWidth,videoHeight:v.videoHeight})')
            await page.wait_for_timeout(4000)
            result['second']=await page.locator('video').first.evaluate('(v)=>({time:v.currentTime,readyState:v.readyState,paused:v.paused,videoWidth:v.videoWidth,videoHeight:v.videoHeight})')
            # Main content only; no comments/account or sensitive URL tokens captured.
            if result['second']['readyState']==0:
                await page.wait_for_timeout(15000)
                result['after_load_wait']=await page.locator('video').first.evaluate('(v)=>({time:v.currentTime,readyState:v.readyState,videoWidth:v.videoWidth})')
            result['public_page_message']=(await page.locator('body').inner_text(timeout=5000))[:2200]
            result['playability']=await page.evaluate('()=>window.ytInitialPlayerResponse?.playabilityStatus ?? null')
            result['player_message']=(await page.locator('#movie_player').inner_text(timeout=5000))[:1800]
            result['success']=result['second']['time']>result['first']['time']+1 and result['second']['videoWidth']>0
        except Exception as exc:
            result['exception']=str(exc)[:1200]
            text=await page.locator('body').inner_text(timeout=5000)
            result['public_page_message']=text[:1800]
        result['media_responses']=responses[:12]
        await browser.close()
    body={'name':'youtube-browser-playback-evidence','head_sha':os.environ['GITHUB_SHA'],
          'status':'completed','conclusion':'success' if result['success'] else 'neutral',
          'output':{'title':'Public player playback test, not listening approval',
                    'summary':'Playback advanced' if result['success'] else 'Playback not established',
                    'text':json.dumps(result,indent=2)}}
    request=urllib.request.Request('https://api.github.com/repos/'+os.environ['GITHUB_REPOSITORY']+'/check-runs',
        data=json.dumps(body).encode(),headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],
        'Accept':'application/vnd.github+json','Content-Type':'application/json'})
    with urllib.request.urlopen(request,timeout=30) as response: json.load(response)
    print(json.dumps(result,indent=2))

if __name__=='__main__': asyncio.run(main())
