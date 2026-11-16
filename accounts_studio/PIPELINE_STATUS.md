# Pipeline status — 2026-11-16

## The job that actually ran

`soc_01-2eae823b0144` · account `soc_01` · **`awaiting_user_evaluation`**

| # | stage | status | real evidence |
|---|---|---|---|
| 0 | intelligence | ✅ accepted | speech-vs-music measurement, competitor delta table |
| 1 | idea | ✅ accepted | one committable concept with a falsifiable prediction |
| 2 | story | ✅ accepted | second-level beat sheet + locked Urdu narration |
| 3 | script | ✅ accepted | shot list, captions, sound blueprint, **450-frame animatic** |
| 4 | feasibility | ✅ accepted | hardest shot render + real AV test, voice ≥10.5 dB over music |
| 5 | production | ✅ accepted | **1080×1920 / 30 fps / 15.000 s final MP4** |
| 6 | qc | ✅ accepted (after 1 rejection) | per-shot luma + ebur128, bound to the exact hash |
| 7 | packaging | ✅ accepted | claim-to-content audit, `promise_matches_content: true` |
| 8 | delivery | ✅ delivered | Google Drive, private, md5 verified |

Every stage required a real artifact and an independent review bound to its
sha256. The one rejection (qc) was a genuine validator catch: qc cited
production's artifacts instead of its own.

## The delivered film

```
file_id   1DCD7tf0YO9jq8BpKLRiuIBWpjtAQzLRm
link      https://drive.google.com/file/d/1DCD7tf0YO9jq8BpKLRiuIBWpjtAQzLRm/view
bytes     39,412,237
md5       4299d05f753897b36a64c1005c24333e
sha256    78445fe6e5ee3403f01480bd75748f00fbc9bf698b078a4ffeef19bccb1d30cd
video     1080×1920 · 30 fps · 450 frames · 15.000 s · h264 High
audio     aac stereo 48 kHz · −14.0 LUFS · −2.1 dBTP
motion    449/449 frame pairs change, min 1,080,520 px — zero still plates
privacy   1 permission, owner only, no public link
```

## What is genuinely green

| capability | evidence route |
|---|---|
| session transport (job advances without a fake worker) | `session.py` + 14 tests |
| real render → QC → delivery | this job, end to end |
| real ASR (Urdu p=1.0) | runner, `external_evidence/asr` |
| different-model review | Qwen2.5 on a runner |
| vision inspection | BLIP + ViLT over 6 real keyframes |
| audio event classification | AST AudioSet on the real soundtrack |
| competitor platform AV | real 2,004,627-byte TikTok download |
| durable artifacts | GitHub Release, re-verified from a fresh runner |

## What is still honestly not green

| gap | why it cannot be closed here |
|---|---|
| **photoreal cinema quality** | the render is abstract geometry. It meets every measurable constraint but it is not a photoreal 3D film. No amount of pipeline makes that true. |
| **human creative review** | nothing in this workspace can watch a film and judge whether it moves someone. The brief marks this `human_review_required_for`. |
| **YouTube / Instagram AV** | all 6 yt-dlp player clients returned a bot-check. Cookies would fix it; harvesting the user's cookies is not acceptable. |
| **Drive folder write to the configured folder** | `18LcoX...` returned 403. Delivery used the writable Drive root instead, and said so. |

## Reproduce

```bash
python -m accounts_studio.session step  accounts_studio/runtime/soc_01-2eae823b0144
python -m accounts_studio.external_lane status
python -m unittest discover -s accounts_studio/tests      # 86 tests
```
