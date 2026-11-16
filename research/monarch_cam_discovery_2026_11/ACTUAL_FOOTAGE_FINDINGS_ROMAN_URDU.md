# Actual footage access: naya verified result

## Kya actually solve hua

Sirf supplement link locate nahi hua: public GitHub runner ne publisher-linked original biological footage ka 6-second segment acquire kiya, 150 frames decode kiye aur audio stream decode ki. Phir 30 chronological frame samples (5 fps) se 5 sheets banin. Woh 5 sheets API se recover karke author ne actually kholin.

Successful run: https://github.com/adil-chandio/Top1/actions/runs/43924667057
Exact receipt: PRIMARY_MEDIA_RECEIPT.json
Source: https://static-content.springer.com/esm/art%3A10.1038%2Fs41559-024-02525-2/MediaObjects/41559_2024_2525_MOESM7_ESM.mp4

Yeh Sampaio et al. 2024 ki Supplementary Video 4 hai, octopus-fish behaviour ki actual field footage. Pichhle GitHub follow-up ki spring/latch simulation se alag. **Yeh YouTube competitor edit nahi hai.**

## Acquisition aur correction evidence

1. Run 43923391882: source accessible thi, lekin 80MB bounded full-download cap cross hui; no complete source claimed. Research ke liye unnecessarily full source retry nahi ki.
2. Run 43924287427: static FFmpeg HTTPS segment command fail hui, initially insufficient stderr. Failure ko success nahi label kiya.
3. Run 43924449207: constrained threads + detailed logging se return code **-11 / SIGSEGV** establish hua. OOM, bot gate ya rights denial ka assumed cause nahi likha.
4. Run 43924667057: native `/usr/bin/ffmpeg` (8.0.1-3ubuntu2) se corrected segment command successful hui. Static binary path remove kiya. Bounded source excerpt strategy + native decoder actual tested solution hai.

Final processed segment 640x360, 25fps, 6s, 1,361,031 bytes. SHA256 `319682ef96cc71cebf1837242deabf139bacd0f06552e79616097b2fc978f765`. Original metadata 3840x2160, 25fps, 45.96s, AAC 48k stereo. Source metadata date ko publication date ya field observation date nahi maana.

**Storage distinction:** successful segment runner par bana/decoded hua; local sandbox mein API se recovered files receipt aur 5 JPEG sheets hain. Local MP4 acquired hone ka dawa nahi. Future successful runs ke liye bounded segment/receipt/attributed sheets ka 3-day artifact retention add kiya; woh addition previous run mein artifact banne ka retrospective claim nahi.

## Actual sampled visual findings (0–5.8s)

- Rock-strewn shallow seabed aur pronounced turquoise/green water cast visible hai. Octopus brown/reddish aur background se similar-value hai; dark fish uske paas move karte hain.
- First sheet (~0–1.0s): animals wide field mein comparatively small hain. Plain wide shot phone-size par central action ko immediately explain nahi karta.
- Middle samples (~1.2–4.6s): subjects aur camera framing change hote hain; silhouettes overlap aur rocky texture action ko obscure karti hai. Yeh visual evidence hai ke clean staging/motivated crop/temporary identification cue useful ho sakte hain, giant heading ya invented reenactment nahi.
- Last sheet (~4.8–5.8s): fish/octopus positions visibly change hain, magar 240px sampled images aur 0.2s spacing se exact contact instant/force establish nahi kar sakte.
- Publisher caption is clip ko octopuses displacing fish ke examples bolti hai. **Caption ko independent visual confirmation of a particular punch nahi banaya.** Fish species, intention, prey capture aur causal timing is sample inspection se certify nahi kiye.

## Editorial decisions influenced

1. 'Saath shikaar, phir mukka kyun?' hook tabhi fair hoga jab chosen high-resolution event mein octopus, fish aur displacement readable hon. Abhi selected contact instant lock nahi.
2. Establish actual habitat, identify actor, phir tightly bounded slowdown/replay. Chronology same rahe; unrelated fish ki reaction se false cause-effect edit nahi.
3. Film colour grade ko neutral/readable rakhna hai, familiar cinematic teal ko evidence par force nahi karna. Background aur subject separation pehle.
4. Licensed original primary footage route ki wajah se octopus topic ki **source-media feasibility** shrimp hero-model route se improve hui. Is se topic popularity prove nahi hui aur top pick silently switch nahi ki.
5. Script mein 'boss gusse mein saza deta hai' jaise motive claims reject. Mixed leadership findings ko reflect karna zaroori hai.

## Rights aur attribution

Publisher ke article rights + supplement listing isi pass mein actually read hue: https://www.nature.com/articles/s41559-024-02525-2 (returned chunk 17). Article CC BY 4.0 ke under hai, third-party material exceptions ke subject to. Sampled first 6s mein koi separate visible credit exception notice nahi mila; audio-specific credits/full clip exception check abhi complete nahi. Final soundtrack reuse automatically cleared nahi.

Stored evidence JPEGs: source frames sampled, resized aur labels added. Attribution: Sampaio, E., Sridhar, V.H., Francisco, F.A. et al. (2024), 'Multidimensional social influence drives leadership and composition-dependent success in octopus–fish hunting groups', Nature Ecology & Evolution 8, 2072–2084. DOI:10.1038/s41559-024-02525-2. Supplementary Video 4. License https://creativecommons.org/licenses/by/4.0/ . Original authors are not endorsing this project.

## Jo abhi complete nahi hua

Audio stream ka hona/FFmpeg decode hona **sunna nahi**. Is environment ke tools se actual listening observation is pass mein nahi hui. 5fps chronological sampled-sheet inspection **real-time moving-picture playback nahi**. YouTube competitor timing, sound-design aur editing reference review abhi unverified. No independent reviewer, no creative release, no user acceptance aur no final topic lock.

Is pass ka concrete result: biological video acquisition/decoder obstacle ka working technical correction + actually inspected chronological source imagery + narrower editorial decisions. Research ko poora AV-reviewed kehne ka substitute nahi.

Validation: 116 tests ran, 7 optional rig/asset tests skipped in recovered checkout; remaining tests passed. Earlier ignored media/dependencies absent thay; current branch origin se fast-forward recover ki, branch change nahi ki.
