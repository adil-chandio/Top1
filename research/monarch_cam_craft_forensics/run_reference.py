"""Reuse established bounded archive-decoding pipeline, one configured reference.
Research-only temporary media; output frames do not imply actual inspection.
No credentials/source footage are committed. No audio-listening claim.
"""
import os
from pathlib import Path
label=os.environ['REFERENCE_LABEL']
assert label in {'short','long','zack'}
config=f'research/monarch_cam_craft_forensics/{label}_config.json'
source=Path('research/monarch_cam_restart_batch1/archive_batch.py').read_text()
source=source.replace("'research/monarch_cam_restart_batch1/archive_batch_config.json'",repr(config))
# Distinct transport names and receipts for a collection used more than once.
source=source.replace('ab-image-',f'cf-{label}-image-').replace('ab-receipt-',f'cf-{label}-receipt-')
# A multi-video collection's first arbitrary info.json is NOT this selected file's provenance.
source=source.replace("for f in info[:2]:","for f in [x for x in info if x['name'].removesuffix('.info.json') == cfg.get('files',{}).get(ident,'').removesuffix('.ia.mp4').removesuffix('.mp4')][:1]:")
exec(compile(source,'bounded_reference_pipeline','exec'))

if not globals().get('r',{}).get('sheets'):
 raise SystemExit('Source acquisition/decoding did not produce sheets; inspect cf receipt')
