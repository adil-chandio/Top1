"""Build deterministic-content V6 review handoff; never modify candidate/signoff."""
import hashlib,json,zipfile
from pathlib import Path
BASE=Path('research/monarch_cam_gecko_batch5')
OUT=Path('studio/runtime/gecko/v6-private-handoff')
VIDEO=Path('studio/runtime/gecko/caption-readability/gecko-english-review-cut-v6.mp4')
EXPECTED='cebe198ec2cb2b7ae95145aad00c65879cd30c95a13a7f264d6b952dba1e9994'
README='''# Monarch Cam — How Does a Gecko Let Go? — V6 review handoff

REVIEW ONLY — NOT FINAL — NOT FOR PUBLICATION

English,66seconds,540×960,24fps. V6 corrects caption grouping/readability only; V5 mechanism/framing is retained and the AAC audio stream is identical. No new narration or listening approval.

Open gecko-english-review-cut-v6.mp4. Burned-in English captions are already visible. Optional SRT duplicates them; leave external subtitles disabled unless needed separately. All scientific references and asset provenance are in CREDITS_AND_SOURCES_ENGLISH.md. No scientific-figure/photo pixels, commercial music, purchased models or borrowed footage are bundled.

Critical listening (original film times):10.7–16.0s Tokay/setae;20.0–26.3s “They aren't suction cups” and van der Waals;around33.2s narration join;44.0–47.7s digital hyperextension. The18.10second diagnostic WAV contains separated narration-only excerpts, not a revised mix. The clip map provides original and diagnostic timestamps.

Unconstrained ASR returned scientific-term and negation discrepancies. These could be recognizer errors, NOT proof the narration says the wrong words. Listen to the actual recording. The agent has NOT listened or performed native-speed whole-film AV review.

Technical evidence:V6 full decode/no errors; exact English caption word sequence preserved;29groups, minimum0.7s and maximum20characters/second by heuristic; original AAC bitstream unchanged. V5 had66one-second decoded picture samples inspected across4sheets. V6 has targeted decoded correction samples inspected. None equals a whole-film native-speed listening/craft pass.

OPEN HOLDS:actual pronunciation/negation/prosody/seam/effects balance listening;whole-native-AV pacing/craft review;exact Tokay anatomy/biological rig validation. Geometry is qualitative schematic, not a measured skeletal/tendon/contact-force model. Curved tapered schematic claws II–V and clawless shortest I do not certify exact anatomy.

Review at normal speed with audio. Record observations/timecodes or return the review desk JSON. Favorable observations do not automatically clear specialist anatomy or authorize publication. No third-party reviewer approval, final QC pass or publication permission is implied by this private transfer.

This is a compact review handoff, NOT a complete source/Blender production archive. No credentials or raw external reference media are included. MANIFEST.json lists every payload file's SHA-256 and size. The earlier V5 ZIP remains historical; this bundle is V6.
'''

def main():
 assert hashlib.sha256(VIDEO.read_bytes()).hexdigest()==EXPECTED
 OUT.mkdir(parents=True,exist_ok=True)
 payload={
  'README_ENGLISH.md':README.encode(),
  VIDEO.name:VIDEO.read_bytes(),
  'english-captions-review-v6.srt':Path('studio/runtime/gecko/caption-readability/english-captions-review-v6.srt').read_bytes(),
  'CREDITS_AND_SOURCES_ENGLISH.md':Path('research/monarch_cam_gecko_batch4/CREDITS_AND_SOURCES_ENGLISH.md').read_bytes(),
  'critical-audio-review.wav':Path('studio/runtime/gecko/review-package/critical-audio-review.wav').read_bytes(),
  'CRITICAL_AUDIO_CLIP_MAP.json':(BASE/'CRITICAL_AUDIO_CLIP_MAP.json').read_bytes(),
  'V6_READABILITY_REVIEW_ROMAN_URDU.md':(BASE/'V6_READABILITY_REVIEW_ROMAN_URDU.md').read_bytes(),
  'CAPTION_READABILITY_RECEIPT.json':(BASE/'CAPTION_READABILITY_RECEIPT.json').read_bytes(),
 }
 manifest={'candidate':'v6','status':'REVIEW ONLY — NOT FINAL','video_sha256':EXPECTED,'agent_listening_performed':False,'native_whole_AV_pass':False,'exact_biology_pass':False,'final_signoff':False,'publication_authorized':False,'files':[{'name':n,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()} for n,b in sorted(payload.items())]}
 payload['MANIFEST.json']=(json.dumps(manifest,indent=2)+'\n').encode()
 z=OUT/'monarch-cam-gecko-v6-review-bundle.zip'
 with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED) as arc:
  for name,b in sorted(payload.items()):arc.writestr(zipfile.ZipInfo(name,date_time=(2026,11,14,0,0,0)),b,compress_type=zipfile.ZIP_DEFLATED)
 with zipfile.ZipFile(z) as arc:
  assert arc.testzip() is None
  for item in manifest['files']:
   raw=arc.read(item['name']);assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256']
 assert z.stat().st_size<100*1024*1024 and VIDEO.stat().st_size<100*1024*1024
 (OUT/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
 receipt={'bundle':str(z),'bundle_bytes':z.stat().st_size,'bundle_sha256':hashlib.sha256(z.read_bytes()).hexdigest(),'bundle_md5':hashlib.md5(z.read_bytes()).hexdigest(),'video':str(VIDEO),'video_bytes':VIDEO.stat().st_size,'video_sha256':EXPECTED,'video_md5':hashlib.md5(VIDEO.read_bytes()).hexdigest(),'payload_files':len(payload),'zip_integrity':'PASS','manifest_hash_checks':'PASS','final_signoff':False}
 (BASE/'V6_HANDOFF_BUILD_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
