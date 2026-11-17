# User-suggested repos: actual source review

## Tyrrrz/YoutubeDownloader

https://github.com/Tyrrrz/YoutubeDownloader
Inspected commit:a419ef2be70392e57d31bd5103f1d6d0d20b3919

Readme,Directory.Packages.props,Downloading/VideoDownloader.cs,Utils/Http.cs actually read. App cross-platform GUI hai; coreC#usesYoutubeExplode6.6.3andConverter6.6.3, not yt-dlp. GetDownloadOptionsAsync calls Videos.Streams.GetManifestAsync; DownloadVideoAsync uses Videos.DownloadAsync. Optional initialCookies constructor accepts cookies but empty default allowed. CustomHttpClient has ordinary appUserAgent. READMEstatusmaintenance.

Decision: genuinely different downloader implementation; one anonymous bounded headless test of core library is technically worth considering. GUI install not required for library use. Source review alone proves neither successful media acquisition nor bot-check solution. Library dependency internals not audited in this pass; no execution/install performed. No cookies/proxy/account/challenge workaround authorized or attempted.

## mvanhorn/last30days-skill

https://github.com/mvanhorn/last30days-skill
Inspected commit:9cee9178210ee8492fac558df89855ef334adbcc

README,CONFIGURATIONselectedYouTubesections,andactualskills/last30days/scripts/lib/youtube_yt.py read/search-inspected. Source header explicitlyyt-dlp search/transcript extraction. Code tracks botcheck/rate-limit/blockedfetch outcomes. OptionalScrapeCreators fallback for search/transcripts/comments requires key and can spend credits. Documentation hasSSH/proxy/player-client routing; not activated/tested here. Installing allplatforms unreviewed would introduce unnecessary auth/spend/datahandling scope.

Discovery mode exists and can support broad trend nomination; creator register formats output, not new visual capability. No frame-by-frame video review engine established from inspected module. Discovery cannot replace within-channel comparable cohort or age-adjusted performance analysis. AIjudging/engagement scores are not causal proofs of virality.

Decision: useful discovery/research orchestrator, not demonstrated solution for fullmedia access. ItskeylessYouTubelane reuses previouslyblockedyt-dlp; wrapper install alone won't prove progress. Paidfallback not enabled; no globalinstallation; no third-partycodeexecution.

## Distinction

YoutubeDownloader: different media acquisition stack, not yet tested.
last30days: broader discovery+transcript workflow, no actual visuals inspected.
Neither repo counted as watched reference, neither changes topic-lock=false. Audio remains excluded per revised user scope. Actual successful new video acquisition count unchanged.
