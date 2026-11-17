"""Channel-first bounded API inventory; no topic search, media or credential logging."""
import os,json,datetime,urllib.request,urllib.parse,urllib.error,statistics
HANDLES=['fern-tv','zackdfilms','animagraffs','neoexplains','realscience','veritasium','BranchEducation']
KEY=next((os.environ.get(k) for k in ['YOUTUBE_API_KEY','YTAP1','YTAPI1','YT_KEY','YT_API_KEY'] if os.environ.get(k)),None)
report={'collected_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'topic_locked':False,'audio_excluded':True,'actual_visual_reviews':0,'api_calls':0,'channels':[],'errors':[],'limitations':['Latest uploads convenience sample, not popular catalogue or age-matched baseline.','Duration does not establish native Shorts classification.','API metadata does not provide video media.']}
def api(endpoint,**params):
    report['api_calls']+=1
    params['key']=KEY
    try:
        with urllib.request.urlopen('https://www.googleapis.com/youtube/v3/'+endpoint+'?'+urllib.parse.urlencode(params),timeout=20) as response:return json.load(response)
    except urllib.error.HTTPError as e:
        # Never include request URLs, response payloads or exception strings with keys.
        report['errors'].append({'endpoint':endpoint,'http_status':e.code})
        raise RuntimeError('api_http_failure') from None

def main():
    if not KEY:report['status']='no_configured_key'
    else:
        report['status']='running'
        try:
            for handle in HANDLES:
                items=api('channels',part='snippet,contentDetails,statistics',forHandle=handle).get('items',[])
                if not items:report['channels'].append({'handle':handle,'status':'not_found'});continue
                c=items[0];playlist=c['contentDetails']['relatedPlaylists']['uploads']
                entries=api('playlistItems',part='contentDetails',playlistId=playlist,maxResults=16).get('items',[])
                ids=[e['contentDetails']['videoId'] for e in entries]
                videos=api('videos',part='snippet,statistics,contentDetails',id=','.join(ids)).get('items',[]) if ids else []
                rows=[]
                for v in videos:
                    n=v['snippet'];s=v.get('statistics',{})
                    rows.append({'id':v['id'],'url':'https://www.youtube.com/watch?v='+v['id'],'title':n['title'],'published_at':n['publishedAt'],'duration_iso':v['contentDetails']['duration'],'views':int(s.get('viewCount',0)),'shorts_status':'unverified','visual_review':'not_inspected'})
                report['channels'].append({'handle':handle,'channel_id':c['id'],'title':c['snippet']['title'],'uploads':rows})
            report['status']='inventory_collected'
        except Exception as e:report['status']='partial_or_failed';report['error_type']=type(e).__name__
    body={'name':'channel-first-api-survey','head_sha':os.environ['GITHUB_SHA'],'status':'completed','conclusion':'neutral','output':{'title':'Channel-first metadata, not watched references','summary':json.dumps(report,ensure_ascii=True)}}
    req=urllib.request.Request('https://api.github.com/repos/'+os.environ['GITHUB_REPOSITORY']+'/check-runs',data=json.dumps(body).encode(),headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Accept':'application/vnd.github+json','Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=30) as response:print('receipt_check_id',json.load(response)['id'])
    print('status',report['status'],'api_calls',report['api_calls'])
if __name__=='__main__':main()
