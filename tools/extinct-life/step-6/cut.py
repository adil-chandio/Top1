"""Picture and sound source of truth, conformed to the locked v2 WAV (24/48000).

Scene lengths follow the spoken edit rather than script estimates. Headlines are
selective editorial marks, not the subtitle lane. Graphics and Foley share Beat.f.
"""
from dataclasses import dataclass
from bisect import bisect_right

FPS=24; SR=48000; SPF=SR//FPS
D=(0,63,99,245,470,629,765,869,1040,1154,1267,1353,1457)

def frame(t):return round(t*FPS)

@dataclass(frozen=True)
class Shot:
    f: int
    key: str
    rig: str
    var: int
    air: str
    note: str

opening=(
 ('sousa-intro','v2',0,'grit','Opening recessed track, original CG'),
 ('koum-intro','v2',1,'grit','Matched scale, a separate Cameroon impression'),
 ('modern','v2',2,'globe','Modern regional separation, no travel direction'),
 ('rewind','v2',3,'globe','World-space sweep onto independent 125 Ma model'),
 ('title','v2',4,'brook','Dawn over a hypothetical ancient floodplain'),
 ('koum-locate','v2',5,'globe','Regional pin, not the exact survey site'),
 ('first-horizons','v2',6,'grit','Original oblique look across four strata'),
 ('mayo','v2',7,'brook','Illustrative Mayo Rey riverbed'),
 ('survey','v2',8,'grit','Survey of 283 prints at one site'),
 ('step-weight','v2',9,'mud','Generic articulated contact and release'),
 ('trackways','v2',10,'grit','34 documented trackways; no animal count'),
 ('local-steps','v2',11,'grit','Local direction only, six steps'),
)
S=tuple(Shot(f,*x) for f,x in zip(D[:-1],opening,strict=True))


def s(t,key,rig,var,air,note):return Shot(frame(t),key,rig,var,air,note)

S+=(
 s(D[-1]/FPS,'edge','slabs',0,'grit','Impressions stop at a broken end; no continuation drawn'),
 s(64.558,'four','slabs',1,'grit','Four separate bearing planes fan open; not one event'),
 s(75.198,'erosion','slabs',2,'wind','Fractures, slumping edge and granular loss'),
 s(84.158,'views','scan',0,'studio','Several overlapping views of an original sample slab'),
 s(90.518,'mesh','scan',1,'studio','Projective scan reveals triangulated relief; no team mesh'),
 s(95.898,'tease','floor',0,'grit','Unmeasured preview of diffuse track outline'),
 s(101.763,'ruler','floor',1,'grit','Study transcribed length of one impression (not body size)'),
 s(110.337,'diffuse','floor',2,'mud','Illustrative diffuse margin under raking light'),
 s(120.707,'press','slabs',3,'mud','Same explicit stamp geometry and scale; two substrates'),
 s(131.897,'results','slabs',4,'mud','Firm versus slumped rim; original demonstration'),
 s(136.357,'changing','floor',3,'grit','Clarity fades along one illustrative trackway'),
 s(143.917,'makers','slabs',5,'grit','Different generic track shapes; no animal IDs'),
 s(150.307,'underfoot','slabs',6,'grit','Clean switch from silhouettes to the underlying beds'),
 s(155.883,'ripples','floor',4,'brook','Raking illumination across ripple ridges'),
 s(160.828,'cracks','floor',5,'grit','Desiccation geometry, a separate texture and time'),
 s(163.418,'clues','slabs',7,'grit','Separate levels, not simultaneous rippling and drying'),
 s(168.648,'drain','floor',6,'brook','Water retreats from shallow mud'),
 s(175.698,'wear','floor',7,'mud','Loss of an exposed imprint, possible process'),
 s(182.758,'cement','grain',0,'glass','Original thin-section model with illuminated grain bonds'),
 s(194.468,'mat','grain',1,'mud','Possible thin mat spans sediment; not an actual micrograph'),
 s(202.968,'burial','slabs',8,'mud','New sediment progressively covers a recessed surface'),
 s(208.058,'preserved','floor',8,'grit','Match the buried horizon to exposed rock'),
 s(214.083,'sousa','world',0,'globe','Move the viewer to present-day Brazil, not an animal'),
 s(218.918,'sousa-water','valley',0,'brook','Interpretive freshwater landscape in warm backlight'),
 s(223.008,'sousa-mat','grain',2,'mud','Separate mat interpretation from the Sousa study'),
 s(228.958,'rim','floor',9,'mud','Rim is displaced sediment, not a mystery shape match'),
 s(234.878,'held','slabs',9,'grit','Anonymous cutaway of a cohesive rim'),
 s(240.968,'conditions','slabs',10,'grit','Two distinct wet sediment faces, no matched horizons'),
 s(251.138,'banks','valley',1,'brook','Two views of river settings, not evidence they joined'),
 s(262.068,'unmatched','strata',0,'studio','Two time windows without assumed coincidence'),
 s(270.685,'window','strata',1,'studio','Loose age window, not a timestamp'),
 s(274.193,'pollen','grain',3,'glass','Generic pollen, age clue from nearby deposits'),
 s(280.383,'regional','strata',2,'grit','Sample marks in other rock layers, not the track beds'),
 s(287.463,'broad','strata',3,'studio','Early Cretaceous age, not simultaneous animals'),
 s(294.673,'restore','world',1,'globe','Back to connected land on the licensed 125 Ma snapshot'),
 s(301.243,'bedrock','fault',0,'fault','Anonymous rock unit with inclined faults'),
 s(305.903,'structures','world',2,'globe','Model context for 2024 interpretation; no route traced'),
 s(312.463,'stretch','fault',1,'fault','Extensional faulted block and subsidence'),
 s(320.433,'fill','fault',2,'brook','Sediment wedges accumulate in low block'),
 s(327.976,'land','world',3,'globe','Wider joined region, terrain connection alone'),
 s(332.659,'valleys','valley',2,'brook','Original hypothetical river and valley habitat'),
 s(342.989,'possible','world',4,'globe','Diffuse possible area; neither measured boundaries nor arrows'),
 s(348.789,'generations','habitat',0,'brook','Separate habitat pools over time, no single animal crossing'),
 s(357.009,'fish','fish',0,'water','Original lobefin interpretation with trilobed tail, no species ID'),
 s(366.709,'fish-basins','fish',1,'water','Two other basin groups, not track-site pins'),
 s(376.789,'patterns','habitat',1,'studio','Independent habitat/fossil clues to compare against geography'),
 s(381.969,'tests','habitat',2,'glass','Potential future evidence, not field discoveries'),
 s(395.029,'still-possible','world',5,'globe','Possible area fades; no individual journey'),
 s(402.879,'rift','fault',3,'fault','Schematic staged separation, then the ocean fills'),
 s(412.379,'return','world',6,'globe','Present shoreline snapshot and modern gap at the same scale'),
 s(418.979,'which-journey','world',7,'globe','Same two regions, no animal path'),
 s(423.739,'the-rocks','world',8,'globe','Separated pins settle on rocks carried by plates'),
 s(429.819,'last-print','floor',10,'grit','Quiet return to a single original footprint'),
 s(439.1666667,'sources','credits',0,'studio','Visible research and map credits, after the untouched voice'),
)
F=tuple(x.f for x in S)+(10696,)
N=F[-1]*SPF
assert len(set(F))==len(F) and F==tuple(sorted(F)) and F[-2]*SPF>21_078_604
INDEX={x.key:i for i,x in enumerate(S)}

@dataclass(frozen=True)
class Beat:
    key: str
    f: int
    sound: str
    text: str=''
    place: str='left'
    tint: str='mint'
    hold: float=4.2
    pan: float=0.
    gain: float=1.
    role: str='text'

    @property
    def sample(self):return self.f*SPF


def b(key,t,kind,text='',place='left',tint='mint',hold=4.2,pan=0.,gain=1.,role='text'):
    return Beat(key,frame(t),kind,text,place,tint,hold,pan,gain,role if text else 'action')

B=(
 b('sousa-open',13/24,'mineral','Sousa Basin','low','gold',1.96,-.30),
 b('koum-open',66/24,'mineral','Koum Basin','low','mint',1.30,.23),
 b('now',149/24,'glass','≈6,000 km','left','gold',4.00),
 b('rewind-scan',245/24,'churn',gain=1.06),
 b('old-lock',275/24,'airchime','125 million years ago','left','cream',7.95),
 b('then',370/24,'glass','≈1,000 km','left-low','mint',3.93),
 b('title-a',473/24,'title','Why These Dinosaur','title-a','cream',6.2,-.18),
 b('title-b',479/24,'title','Footprints Are','title-b','cream',6.0,.04),
 b('title-c',485/24,'title','an Ocean Apart','title-c','gold',5.7,.19),
 b('surfaces',778/24,'dry','4 surfaces','left','gold',3.38),
 b('mayo-type',903/24,'droplet','Mayo Rey River','low','cream',5.15,-.10),
 b('count',1093/24,'mineral','283 footprints','left','mint',2.50),
 b('stamp-down',1183/24,'press',gain=1.3),b('stamp-up',1208/24,'peel',pan=.23),
 b('countways',1273/24,'dry','34 trackways','left','mint',3.40),
 *(b('small-step-'+str(i), (1363+8*i)/24,'step',pan=.35-i*.127,gain=1.05-i*.043) for i in range(6)),
 b('edge-chip',62.04,'break',pan=-.41),
 *(b('strata-'+str(i),65.13+i*.66,'peel',pan=-.24+i*.16,gain=.95) for i in range(4)),
 b('erosion-pop',77.72,'break',pan=.13,gain=1.11),b('erosion-tail',78.62,'granules',pan=.36),
 b('scan-read',85.23,'glass',pan=-.32),b('scan-side',86.58,'glass',pan=.39,gain=.8),
 b('photos',87.838,'glass','2,000+ photos','left','mint',2.60),b('reconstruction',90.58,'churn',gain=.72),
 b('length',102.107,'mineral','≈69 cm','left','gold',6.55),
 b('soft-outline',111.53,'bristle',pan=.22),b('two-muds',122.257,'dry','Same stamp','left','cream',3.32),
 b('test-down',124.22,'press',gain=1.10), b('test-up',128.87,'peel',pan=.22),b('slump',129.86,'granules',pan=.42),
 b('firm-soft',132.35,'dry','Firm mud     /     Soft mud','low','mint',3.97),
 b('less-clear',139.57,'granules',pan=.33,gain=.87),
 b('ripples',157.688,'droplet','Ripple marks','left','mint',2.84),
 b('cracks',161.03,'break','Mud cracks','left','gold',2.32),
 b('drain',169.42,'brook',pan=.31), b('impact-bank',173.91,'press',gain=.87),b('erosion-wash',177.38,'brook',pan=-.16),
 b('cement',188.69,'glass','Mineral cement','left','gold',4.64),
 b('mat',196.58,'bristle','Possible microbial mat','left','mint',5.16),
 b('bury',203.59,'granules',gain=1.27), b('seal',206.97,'dry',pan=.12),
 b('brazil',216.95,'airchime','Sousa Basin, Brazil','left','cream',1.90),
 b('sousa-current',219.58,'brook',pan=-.36),b('sousa-fibres',225.90,'bristle',pan=.22),
 b('rim',230.718,'mineral','Displaced rim','left','gold',3.98),
 b('both',243.81,'peel',gain=.86),b('window-low',271.92,'airchime',gain=.79),
 b('pollen',275.363,'glass','Fossil pollen','left','gold',4.54),
 b('age',288.24,'airchime','Early Cretaceous','left','cream',5.4),
 b('restore-model',294.96,'airchime','125 Ma model','left','mint',5.85),
 b('fault-light',303.84,'mineral',pan=-.31),b('rift-down',313.74,'break',gain=1.01),
 b('rift-fill',321.12,'granules',pan=.25),b('valley-water',335.45,'brook',pan=.28),
 b('range',346.789,'airchime','Possible dispersal area','low','mint',1.96),
 b('habitat-first',350.71,'droplet',pan=-.36),b('habitat-next',353.15,'droplet',pan=.26),b('habitat-last',355.12,'droplet',pan=.40),
 b('mawsonia',362.47,'waterglass','Mawsonia','left','mint',4.20),
 b('other-basins',367.38,'mineral','Fossils in other basins','low','cream',7.48),
 b('more-sites',384.50,'dry','More sites','left','gold',2.8),
 b('better-dates',387.05,'glass','Narrower dates','left','mint',3.28),
 b('better-fossils',390.63,'mineral','Identifiable fossils','left','cream',3.96),
 b('rift-early',404.62,'churn',pan=-.25,gain=.84),b('rift-late',408.78,'brook',pan=.29,gain=1.12),
 b('gap-returns',415.56,'glass','≈6,000 km','left','gold',3.36),
 b('rocks-answer',423.90,'title','The rocks.','left','cream',5.55),
 b('gentle-close',430.28,'mineral',pan=-.13,gain=.57),b('credits-on',439.20,'airchime',gain=.9),
)
B=tuple(sorted(B,key=lambda a:a.f))
BY={q.key:q for q in B}; assert len(BY)==len(B)


def shot_of(f):return bisect_right(F,f)-1


def inside(k):return tuple(q for q in B if F[k]<=q.f<F[k+1])


CHAPTERS=(('The ocean came later',0),('Four pieces of ancient ground',36.192),('The big print has a problem',101.763),
 ('What the mud held onto',155.883),('The other side of the comparison',214.083),('Date the rocks, then move the continents',270.685),
 ('A route, not a trail',327.976),('The journey we can follow',402.879),('Sources and maps',439.1666667))

RIGS=('v2','floor','slabs','scan','grain','world','valley','strata','fault','habitat','fish','credits')


def header():
    lines=['#pragma once','struct Take {int a,b,rig,v;};','constexpr Take TAKES[]={']
    lines.extend(f'    {{{q.f},{F[i+1]},{RIGS.index(q.rig)},{q.var}}},' for i,q in enumerate(S))
    lines+=['};','constexpr int END_FRAME='+str(F[-1])+';']
    for q in B: lines.append(f'constexpr int K_{q.key.upper().replace("-","_")}={q.f};')
    return '\n'.join(lines)+'\n'


if __name__=='__main__':
    for i,x in enumerate(S):print(i+1,x.f,F[i+1],x.key,x.rig,x.var)
