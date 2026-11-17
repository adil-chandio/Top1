# Naye chaar repos: asal test aur hadd

Run: https://github.com/adil-chandio/Top1/actions/runs/44020651380
Source commit: 59aacda
Reference: https://www.youtube.com/watch?v=ZQvfHyfgBtA

- pytube 15.0.0 asal Python runtime mein chalaya. Anonymous video-info request par HTTP 400; media download ya frame decode tak nahin pohncha. Yeh is version/request/environment ka nateeja hai, har version ya har network ki nakami ka saboot nahin.
- youtube-transcript-api 1.2.5 ka asal fetch chalaya. IpBlocked exception; captions hasil nahin huay. Captions mil bhi jate to visual analysis nahin hota.
- h5player: abhi source inspection hi hui, runtime test nahin. mediaDownload.js existing media URL ya MediaSource buffers par kaam karta hai. Is se blocked YouTube URL resolve hone ka saboot nahin mila.
- h265player: abhi source inspection hi hui, runtime test nahin. Demo existing m3u8 sourceURL leta hai; YouTube watch URL resolve karna verify nahin hua.

Green Actions jobs ka matlab harness mukammal hua, video access ki kamyabi nahin. Is run mein media_acquired=false, frames_decoded=false, visual_review_complete=false. Koi reference footage download nahin hui; is liye is run se raw footage ki koi nayi copy nahin bani. Batch 1 ke qualifying visually reviewed references ab bhi 0 hain. Topic select nahin kiya.
