"""Actual packaged GUI smoke/input tests. UI evidence is not download success."""
import os,json,subprocess,time,urllib.request,zipfile,tempfile,base64,io,shutil
from pathlib import Path
from PIL import Image
import pyautogui as gui
URL='https://www.youtube.com/watch?v=ZQvfHyfgBtA'
def publish(name,data):
 body={'name':name,'head_sha':os.environ['GITHUB_SHA'],'status':'completed','conclusion':'neutral','output':{'title':name,'summary':json.dumps(data)}}
 req=urllib.request.Request('https://api.github.com/repos/'+os.environ['GITHUB_REPOSITORY']+'/check-runs',data=json.dumps(body).encode(),headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Accept':'application/vnd.github+json','Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=30) as response:json.load(response)
kind=os.environ['APP_KIND']
releases={'tyrrrz':'https://github.com/Tyrrrz/YoutubeDownloader/releases/download/1.17.1/YoutubeDownloader.linux-x64.zip','ovd':'https://github.com/jely2002/youtube-dl-gui/releases/download/app-v3.2.1/Open.Video.Downloader_3.2.1_amd64.deb'}
r={'app':kind,'full_desktop':True,'process_started':False,'input_attempted':False,'download_verified':False,'visual_reference_review':False};proc=None
with tempfile.TemporaryDirectory(prefix='gui-matrix-') as work:
 try:
  root=Path(work);archive=root/'release';urllib.request.urlretrieve(releases[kind],archive)
  if kind=='tyrrrz':
   with zipfile.ZipFile(archive) as z:z.extractall(root/'app')
   exe=next(p for p in (root/'app').rglob('YoutubeDownloader') if p.is_file())
  else:
   subprocess.run(['dpkg-deb','-x',str(archive),str(root/'app')],check=True,timeout=30)
   candidates=[p for p in (root/'app/usr/bin').iterdir() if p.is_file()];exe=candidates[0]
  exe.chmod(0o755)
  env={k:v for k,v in os.environ.items() if k not in ('GH_TOKEN','GITHUB_TOKEN','ACTIONS_RUNTIME_TOKEN')};env.update(HOME=str(root/'home'),WEBKIT_DISABLE_COMPOSITING_MODE='1')
  (root/'home').mkdir();log=open(root/'app.log','w')
  proc=subprocess.Popen([str(exe)],env=env,stdout=log,stderr=log,start_new_session=True);r['process_started']=True;time.sleep(15)
  r['alive_before_input']=proc.poll() is None
  for stage in ['before','after']:
   if stage=='after':
    # Clipboard paste is ordinary GUI interaction, no injected application code.
    subprocess.run(['xclip','-selection','clipboard'],input=URL.encode(),timeout=5)
    gui.click(450,115);gui.hotkey('ctrl','v');time.sleep(2);gui.press('enter');r['input_attempted']=True;time.sleep(30)
   shot=gui.screenshot();shot.save(root/(stage+'.png'))
   ocr=subprocess.run(['tesseract',str(root/(stage+'.png')),'stdout'],capture_output=True,text=True,timeout=20)
   r[stage+'_ui_text']=ocr.stdout[:4200]
   shot.thumbnail((1000,700));b=io.BytesIO();shot.convert('RGB').save(b,'JPEG',quality=40)
   publish('desktop-'+kind+'-'+stage,{'jpeg_base64':base64.b64encode(b.getvalue()).decode()})
  r['alive_after_input']=proc.poll() is None
 except Exception as e:r['error_type']=type(e).__name__
 finally:
  if proc and proc.poll() is None:
   import signal
   os.killpg(proc.pid,signal.SIGTERM)
   try:proc.wait(timeout=10)
   except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL)
r['temporary_app_profile_deleted']=not Path(work).exists();publish('desktop-'+kind+'-receipt',r)
