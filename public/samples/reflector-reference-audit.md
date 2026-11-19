# Monarch Studio · Project 002 — visual reference audit

## What was actually reviewed

**One film:** [How The Ring And Chain Trick Works 😮](https://www.dailymotion.com/video/xac3wl6), as served by Dailymotion. The listing credits “Zack D. Films” (`ZackD.Films_x`, unverified). [A same-title listing credited to Zack D. Films on TikTok](https://www.tiktok.com/@zackdfilms92/video/7643814290712988942) supports the attribution, but was not used to establish that the two uploads are identical. The observations below refer only to what was decoded from Dailymotion.

- The local embed didn't play. A [one-off GitHub Actions inspection](https://github.com/adil-chandio/Top1/actions/runs/44428617308) decoded the public video stream. The picture-only review encode is **720 × 1280, 29.97 fps (`2997/100`), 1,200 video frames, 40.040040 s**. It was resized/re-encoded for inspection with source frame timing passed through. Audio was intentionally omitted from the review encode. This does **not** establish whether the original upload has sound; no speech, music, effects, or sound timing were analyzed. The analysis uses the video, not its preview thumbnail/filmstrip.
- Reviewed 16 ordered sheets of 75 consecutive native frames each, then the higher-resolution cadence overview and selected transition windows. `f0` is the first displayed frame. `f1199` begins at `40.006673 s`; the difference between that and the stream duration is the last frame's display time. Within each one-second row below the frame range is inclusive; seconds use presentation time, not frame-number rounding to 30 fps.
- [Frame measurements (CSV)](./reflector-reference-frames.csv) contains one numeric row per decoded frame. `luma`/`contrast` are the mean/std of 8-bit grayscale after area resize to 108×192; `saturation` is normalized HSV S; `edges` is the Canny edge fraction above the lower caption band. `delta` is the mean absolute grayscale difference and `hist_diff` the Bhattacharyya distance of binned Lab histograms, both on the top 135 rows. The two flow columns summarize Farnebäck optical flow in downsampled pixels per frame; blanks mark intervals skipped because the picture changed too much (`delta >= 30` or `hist_diff >= .48`). They are not world velocities. Stats include captions where stated and depend on crop, resize and encode. Whole-frame median luma was **117.33/255** and median content delta **6.28/255**. A delta spike is a place to look, **not** a cut detector or a measure of quality.
- Text and measurements only. No reference stills, video, character models, or soundtrack are included in the project.

## Second-by-second picture pass

| Seconds | Frames | What is visible and why it reads |
|---:|:---|:---|
| 00 | f0–29 | Table, performer and two hands establish the scale. Camera races toward the lower hand rather than waiting on a title. The thin chain leads the eye in from the top; at **f16** the ring has already become the focal object. |
| 01 | f30–59 | Reflective rim held almost horizontal; paired strands remain visible within and below it. The other hand enters from above. The cyan field helps separate silver from the dark sleeve. |
| 02 | f60–89 | Grip relaxes while the upper hand still supports the chain. The ring lip stays close to the same screen position, so the viewer can see the fingers separate rather than having to find the ring again. |
| 03 | f90–119 | Lower fingers flare open. For a brief beat the ring is isolated against cyan with the hanging loop below; its start down the chain is unobstructed. |
| 04 | f120–149 | Tilt/pan tracks down. The chain loop moves up out of the framing and tabletop enters from below; **f141–147** carry the falling ring over the tabletop and its separate shadow. |
| 05 | f150–179 | Rim angles up and down against the wood before settling. Silhouette and changing gap to the shadow communicate bounce/tip rather than teleporting to a resting pose. |
| 06 | f180–209 | Blurred tabletop crosses frame at **f184–189**. Readable destination is a second setup: hand, taut strands and coat buttons. The sentence changes direction with the picture. |
| 07 | f210–239 | Camera travels around the gripping hand; chain changes from near vertical to diagonal in screen space. Zoomed links substitute for the earlier full performer. |
| 08 | f240–269 | Palm fills the image, links legible against skin. Warm highlight isolates the thumb, then the macro move brings the other pinching finger into view. |
| 09 | f270–299 | Forefinger and thumb shown from the next side of the orbit. Chain is kept on the same hand; background and angle change more than the grip does. |
| 10 | f300–329 | Turn to front of palm. Warm overlays separate the three non-pinching fingers from the two controlling fingers. Cyan background comes back around the hand. |
| 11 | f330–359 | Held macro view with very little background motion. The held chain and fingertip spacing keep the grip readable while the finger-curl instruction builds. |
| 12 | f360–389 | Remaining fingers curl in; pinch stays up and chain hangs. Highlight recedes. The hand does the explanatory work instead of an unrelated cutaway. |
| 13 | f390–419 | Camera withdraws; single hanging strands resolve into a loop and the stage context comes back. No need to reintroduce a new prop. |
| 14 | f420–449 | Medium performer view: high hand holds the chain, free hand has the ring down by the table. The two jobs are separated vertically in 9:16. |
| 15 | f450–479 | Low hand brings ring up under the loop; **f464–465** show reframing of coat and lower hand, not a discontinuity of the ring's action. |
| 16 | f480–509 | Rim is threaded upward. Lower hand supports it and the doubled chain stretches above. Wood and jacket are texture/context, not the focus. |
| 17 | f510–539 | Overhead-ish view uses small directional arrows near the rim/strands. Circle against warm wood makes the sideways turn readable. Arrows describe one local action, then go away. |
| 18 | f540–569 | Rapid move from looking down through the circle to looking along its lip (**f547–559**). The rim changes from a circle to a thin ellipse; cyan takes over from the tabletop. |
| 19 | f570–599 | Nearly edge-on ring balanced between fingers, taut chain dropping through. Camera slows once the arrangement is clear. |
| 20 | f600–629 | Thumb withdraws; a small warm emphasis draws the eye to it. The upper hand is largely cropped so the lower gesture wins. |
| 21 | f630–659 | Thin ring starts to tip and a brief arrow marks spin. A difference of a few degrees reads because chain and backdrop barely move. |
| 22 | f660–689 | Hold on the released rim and hanging chain. The motion is visibly stretched; not enough evidence to infer physical time or the animation method. |
| 23 | f690–719 | Lip drops on one side and stays silhouetted. Camera doesn't chase the slipping hand; the next contact can be anticipated. |
| 24 | f720–749 | Oblique ring moves across the near strand. By **f737** a warm spot identifies the low rim/chain contact, not the whole ring. |
| 25 | f750–779 | Tight hold on contact. The glint separates the causal point from adjacent metal highlights; little caption movement competes with it. |
| 26 | f780–809 | Ring hangs at an edge-on angle, acting as if pivoting around that first contact. Framing shifts down, opening space for what will pass below. |
| 27 | f810–839 | Contact retained while the rim starts to rotate. Near **f834** the small ring angle, followed by an opening silhouette, signals that the next big movement is underway. |
| 28 | f840–869 | Rim opens into an oval as camera and object turn. **f846–856** take cyan through red into dark coat as a loose bight becomes visible below. The chain is traceable across the move. |
| 29 | f870–899 | Rim/loop viewed against coat and red floor. Strands cross the rim; the lower loose length is intentionally kept in frame. |
| 30 | f900–929 | Suspended ring has open space underneath for the loop. Motion holds slow here so the bight's shape can be read separately from the rim. |
| 31 | f930–959 | View travels across the coat; bight becomes smaller and starts wrapping in. Rim remains bright enough to see on dark material. |
| 32 | f960–989 | Loop slides/tightens and rim tips nearly horizontal. The sweep past the coat into cyan at **f976–979** changes much of the image but preserves the object and the action. |
| 33 | f990–1018 | Angled rim dips from the brighter view and the shorter loop approaches the top of the ring. Tight composition follows the ring, not the hand. |
| 34 | f1019–1048 | Ring ends vertically suspended, caught by a small loop. Compared to the first drop it stops above the table. Brief warmth around the catch stresses the result. |
| 35 | f1049–1078 | Relative motion drains away; the hung ring and stationary tabletop make the successful end state legible. |
| 36 | f1079–1108 | Residual swing, then selective desaturation and a rewind-like series: settled ring becomes tipped and its loop visibly opens. First large changes around **f1097–1104**. |
| 37 | f1109–1138 | Rewind-like passage returns to an earlier ring configuration. The next overlay/dissolve takes the viewer from the isolated ring to the performer's hands for a fast rerun. |
| 38 | f1139–1168 | Wider performer view shows the full action very quickly; rim hangs on the chain. Table re-enters. Realtime is how this passage is presented, not a validated speed measurement. |
| 39 | f1169–1198 | Further pullback reveals stage and foreground audience silhouettes. Reaction provides closure only after the successful catch can be seen. Caption clears before the last frame. |
| 40.00–40.04 | f1199 | Last wide frame. No extra end card in the decoded stream. |

## Frame-window checks: motion vs edit

| Window / time | Evidence-based classification |
|:---|:---|
| f8–22 / 0.267–0.734 | Strong push toward the grip. Delta peaks at **f16** (36.99); a matching ring and camera direction straddle it. A snap reframe or concealed edit is possible. No verified hard cut at that peak. |
| f141–147 / 4.705–4.905 | Continuous observable descent/track. Wood encroaches as shadow and ring move relative to each other. Not seven edits. |
| f184–189 / 6.139–6.306 | **Verified visual transition** between drop and grip setup. A blurred tabletop edge covers the hand reveal over several frames. Can't identify a hidden cut or pre-compositing method from the flattened copy. |
| f216–221 / 7.207–7.374 and f261–272 / 8.709–9.076 | Across these peaks finger/chain landmarks and the background sweep stay traceable. Class as rapid pose/camera changes, not hard cuts. |
| f464–465 / 15.482–15.516 | Reframe during same threading action; sleeve and chain continue on both sides of peak. |
| f547–559 / 18.252–18.652 | **Verified change of framing** from overhead geometry to lip-level release view. f549 shows hand/ring overhead, f551–555 show an aggressive tilt/zoom with intermediate angles, f557 onward reads as release setup. Highest local delta at f556 is 52.49; does not establish a hard cut at f556. |
| f720–810 / 24.024–27.027 | Contact and pivot beat: warm spot appears in the f730s, is established at f737, then loses prominence as the lower rim tips. Treat as visible emphasis, not proof of real forces. |
| f834–856 / 27.828–28.562 | Flip takes the ring from a sliver at f834 to an open oval at f848; the lower loop is clear by f854. Background tracks cyan → red → coat during the f846–856 spike. |
| f976–979 / 32.566–32.666 | Sweep past performer, not a confirmed cut. The loop is locked to the same rim as the colors and apparent aspect change. |
| f1097–1117 / 36.603–37.271 | **Verified tonal/time transition:** selective grayscale, reversal-like motion, then reframing across earlier loop states. f1109 is the largest delta (**61.23**); that alone does not identify a cut. Further ghosted performer/ring images in the later f1130s verify a dissolve into the wide rerun. |

The source doesn't expose an edit decision list. “Verified transition” above means frames show a change of presentation (occlusion, tonal/time change, or dissolve); it doesn't mean there was an isolated straight cut or disclose the 3D software used. Where an exact hard-cut boundary couldn't be verified it is left uncounted.

## Craft takeaways applied to the new film

| Direct visual observation | New implementation, not a shot copy |
|:---|:---|
| Show the object before the mechanism; show an ordinary result before the unexpected result. | Start with the red glint. Move from camera near the lamp to camera at the side with the lamp still on, then demonstrate a plain mirror before a corner cube. |
| Buildup makes a very small contact significant; the framing stops working so hard when the explanation needs reading time. | Hold the 3D bench while one ray makes three contacts. Each contact lights just the face it struck. After the turn, hold both outside segments in an orthographic view so perspective can't make them appear to converge. |
| Bright silver paired with cyan or a dark coat helps the eye track a thin continuous chain and the small ring. | Cool blue-black road/bench and a warm white incoming ray, coral outgoing ray, red lens. Keep the same geometry and direction through the closeups instead of decorating every frame. |
| Bottom phrases and short-lived guidance work without covering the active contact. | Phrase-length Roman Urdu captions, transient diagram labels and three bounce cues. Move the text higher in the one overhead road setup where it would cover the lamp. |
| Return to a wider view to demonstrate the outcome on the original prop. | Return to the bicycle; turn the headlight off in the wide view, then bring it back. It shows that the reflector returns supplied light, rather than creating light itself. |

These are observations about an animation, not empirical evidence of audience retention, an exact match in quality, or a claim about how the creator recorded the original sound. Project 002 uses separately authored 3D assets, a different topic, different shots, an original script and an independent score.

## Separate physics references for Project 002

[Ansys: Corner-cube retroreflectors](https://optics.ansys.com/hc/en-us/articles/43071088719763-How-to-model-corner-cube-retroreflectors) describes the three perpendicular faces, total internal reflection and return direction. [William Beaty's explanation of bicycle reflectors](https://www.madsci.org/posts/archives/dec2000/977675178.Es.r.html) describes the molded plastic array. These are sources for the reflector mechanism only, not evidence about what appears in the Dailymotion video. The film illustrates one ray at one accepted angle and uses a stylized cone for the roadside view; it is not a safety or brightness test.
