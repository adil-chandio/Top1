"""The one portrait film's editorial clock, voice copy, and dependency paths."""
from pathlib import Path
from hashlib import sha256
import json
import os

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
CACHE=Path(os.environ.get('ATL_SHORT_CACHE',ROOT/'.cache/atlantic-short'))
FILM=ROOT/'.cache/monarch-extinct/atlantic-tracks/film'
FIELDS=FILM/'fields'
BANK=FILM/'sound-v2/sources'
MATS=CACHE/'materials'
OUT=ROOT/'deliverables/extinct-life-short-01'
QA=CACHE/'qa'
W,H,FPS,FRAMES,SR=1080,1920,30,1020,48000
N=SR*FRAMES//FPS
TITLE='Why Dinosaur Footprints Can Fool You'
NAME='Atlantic-Tracks-Short-01'
CUTS=(0,82,169,282,365,442,501,574,810,947,FRAMES)
SHOTS=('The contact','Firm mud / matched camera','Soft mud / matched camera','The failing lip',
       'Sousa Basin','Koum Basin','Modern Atlantic','Map rewind','Rock faces','Return to impact')
TAKES=(
 ('01-hook',2,('Same foot.','Two different prints.')),
 ('02-firm',85,('Firm mud holds the shape.',)),
 ('03-soft',173,('In softer mud,','the walls slump as the foot lifts.','The toes can fool you.')),
 ('04-sites',369,('Three-toed dinosaur tracks in Brazil.','More in Cameroon,','roughly six thousand kilometres away today.')),
 ('05-rewind',575,('Rewind the map.','Before the Atlantic opened here,','both places were on the same landmass.')),
 ('06-question',825,("But connected land isn't a trail.",'So what in the rocks hints at a route?')),
)
EVENTS={
    'hook_impact':5,'hook_lift':28,'hook_slump':38,'firm_impact':92,'firm_lift':117,
    'soft_impact':179,'soft_lift':204,'soft_slump':214,'lip_drip':306,'map_rewind':618,'rock_chip':824,
}

def digest(p):
    with Path(p).open('rb') as f:
        h=sha256()
        for block in iter(lambda:f.read(1<<20),b''):h.update(block)
    return h.hexdigest()

def dump(p,obj):
    Path(p).parent.mkdir(parents=True,exist_ok=True)
    Path(p).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
