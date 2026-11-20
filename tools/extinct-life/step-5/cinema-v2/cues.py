"""Single frame clock for picture beats, typography, and its sound design.

Do not time individual mix cues by listening to a second edit. FX cues are
triggered at frame start (sample = frame * 2,000). Anticipations are separate.
"""
from dataclasses import dataclass

FPS=24
SR=48_000
SPF=SR//FPS
FRAMES=(0,63,99,245,470,629,765,869,1040,1154,1267,1353,1457)
END=FRAMES[-1]/FPS
NSAMPLES=FRAMES[-1]*SPF


@dataclass(frozen=True)
class Cue:
    id: str
    frame: int
    move: int
    voice: str              # matching sound family, not a speaker or TTS voice
    pan: float=0.
    strength: float=1.
    show: bool=True         # False for environmental/physical or prelap sounds

    @property
    def sample(self):return self.frame*SPF

    @property
    def seconds(self):return self.frame/FPS


CUTS=(
    Cue('open',0,15,'grain-bed',-.22,.95,False),
    Cue('brazil',13,13,'rock-type',-.36,1.04),
    Cue('match',63,11,'cut-gravel',.14,1.,False),
    Cue('cameroon',66,12,'rock-type',.32,.96),
    Cue('orbit-air',93,21,'air-approach',-.12,.83,False),
    Cue('orbit',102,14,'orbit-mark',-.26,1.12),
    Cue('sousa-pin',115,14,'point',-.51,.84),
    Cue('koum-pin',125,14,'point',.56,.94),
    Cue('distance-now',149,15,'measure',.06,1.),
    Cue('rewind-prelap',235,14,'suction',-.1,1.,False),
    Cue('rewind',245,13,'rewind',-.04,1.03),
    Cue('model-lock',275,15,'arrival',.12,1.07),
    Cue('sousa-past',281,12,'old-point',-.35,.85),
    Cue('koum-past',289,12,'old-point',.37,.94),
    Cue('distance-then',370,15,'old-measure',.02,.95),
    Cue('title-bed',470,19,'title-bed',0.,1.,False),
    Cue('title-one',473,16,'lift',-.14,1.1),
    Cue('title-two',479,16,'lift',.02,.82),
    Cue('title-three',485,17,'resolve',.14,1.),
    Cue('dive-air',624,26,'air-approach',-.25,1.04,False),
    Cue('approach',641,13,'orbit-mark',-.16,.78),
    Cue('local-fix',684,15,'point',.16,.92),
    Cue('strata-entry',765,12,'cut-gravel',-.06,.77,False),
    Cue('four-surfaces',778,13,'rock-type',-.28,.96),
    Cue('layer-1',783,10,'layer',.18,.91),
    Cue('layer-2',790,10,'layer',.30,.88),
    Cue('layer-3',797,10,'layer',.40,.89),
    Cue('layer-4',804,10,'layer',.48,.92),
    Cue('river-open',869,20,'water-open',.23,1.,False),
    Cue('mayo-rey',903,15,'water-type',-.29,1.12),
    Cue('survey-cut',1040,13,'cut-gravel',.12,.79,False),
    Cue('footprint-count',1093,15,'count',-.28,1.08),
    Cue('footfall-type',1159,14,'rock-type',-.30,.90),
    Cue('contact',1183,13,'impact',.04,1.,False),
    Cue('release',1208,23,'peel',.22,.94,False),
    Cue('trackway-count',1273,14,'old-count',-.30,1.02),
    Cue('sequence',1357,15,'lift',-.26,.93),
    Cue('step-1',1363,9,'step',.35,1.0),
    Cue('step-2',1371,9,'step',.21,.9),
    Cue('step-3',1379,9,'step',.13,.94),
    Cue('step-4',1387,9,'step',-.04,.89),
    Cue('step-5',1395,9,'step',-.10,.84),
    Cue('step-6',1403,9,'step',-.18,.80),
)
CUES={q.id:q for q in CUTS}
assert len(CUES)==len(CUTS) and all(0<=q.frame<FRAMES[-1]-8 and q.move>4 for q in CUTS)
assert tuple(sorted(CUES.values(),key=lambda q:q.frame))==CUTS


def bound(x):return max(0.,min(1.,x))


def smooth(x):
    u=bound(x)
    return u*u*(3-2*u)


def progress(name,f):
    cue=CUES[name]
    return bound((f-cue.frame)/cue.move)


def ease_out(x):return 1-(1-bound(x))**3


def end_envelope(f,end,taper=9):return smooth((end-f)/taper)


def native_marks():
    return {'EARTH_REWIND':CUES['rewind'].frame,'EARTH_LOCK':CUES['model-lock'].frame,
            'MUD_CONTACT':CUES['contact'].frame,'MUD_RELEASE':CUES['release'].frame,
            'FIRST_FRAMES':FRAMES}
