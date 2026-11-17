using YoutubeExplode;
using System.Text.Json;
using System.Net.Http.Headers;
var r = new Dictionary<string,object?> {{"route","YoutubeExplode6.6.3 library, not full GUI"},{"video_id","ZQvfHyfgBtA"},{"media_acquired",false},{"visual_review_complete",false},{"audio_in_scope",false}};
var folder=Path.Combine(Path.GetTempPath(),Guid.NewGuid().ToString());Directory.CreateDirectory(folder);
try{
 using var timer=new CancellationTokenSource(TimeSpan.FromSeconds(90));
 using var yt=new YoutubeClient();
 var manifest=await yt.Videos.Streams.GetManifestAsync("ZQvfHyfgBtA",timer.Token);
 var stream=manifest.GetVideoOnlyStreams().OrderBy(s=>s.Size.Bytes).FirstOrDefault();
 if(stream==null)throw new InvalidOperationException();
 if(stream.Size.Bytes>60000000)throw new InvalidOperationException();
 await yt.Videos.Streams.DownloadAsync(stream,Path.Combine(folder,"source.mp4"),cancellationToken:timer.Token);
 r["media_acquired"]=true;r["bytes"]=new FileInfo(Path.Combine(folder,"source.mp4")).Length;
 // Media is not retained in Git; success would require separate frame extraction and inspection.
}catch(Exception e){r["error_type"]=e.GetType().Name;r["error_class"]="manifest_or_download_failed";}
finally{Directory.Delete(folder,true);r["temporary_source_deleted"]=!Directory.Exists(folder);}
using var http=new HttpClient();http.DefaultRequestHeaders.UserAgent.ParseAdd("MonarchCamResearch/1.0");http.DefaultRequestHeaders.Authorization=new AuthenticationHeaderValue("Bearer",Environment.GetEnvironmentVariable("GH_TOKEN"));
var body=new {name="youtubeexplode-route-receipt",head_sha=Environment.GetEnvironmentVariable("GITHUB_SHA"),status="completed",conclusion="neutral",output=new {title="Actual library result, not visual approval",summary=JsonSerializer.Serialize(r)}};
var response=await http.PostAsync("https://api.github.com/repos/"+Environment.GetEnvironmentVariable("GITHUB_REPOSITORY")+"/check-runs",new StringContent(JsonSerializer.Serialize(body),System.Text.Encoding.UTF8,"application/json"));response.EnsureSuccessStatusCode();Console.WriteLine(JsonSerializer.Serialize(r));
