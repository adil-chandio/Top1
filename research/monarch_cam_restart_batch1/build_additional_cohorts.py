"""Public original-watch snapshots; descriptive samples, not causal analytics."""
import json,statistics,datetime
from pathlib import Path
P=Path(__file__).parent
REGISTER=P/'THUMBNAIL_INSPECTION_REGISTER.json'
INSPECTED={r['id'] for r in json.loads(REGISTER.read_text())['rows']} if REGISTER.exists() else set()
DAY=datetime.date(2026,11,14)
aff=[('4d1hE5Aenb8','Nightcrawler Facts: The Common Earthworm 🪱 Animal Fact Files','2026-10-11',507,6909),('cv-kZIz58Dk','Stink Bugs Facts: A Stinky Menace 👃 Animal Fact Files','2026-09-06',534,7532),('Ghmo43WEH_k','Buttonquail Facts: SMALL as a BUTTON ⚉ Animal Fact Files','2026-08-14',520,4551),('a7qwlYe7F74','Garden Eel Facts: the Ocean Prairie 🌊 Animal Fact Files','2026-07-12',489,3679),('Sem1b9uzTd0','Padloper Facts: TINIEST Tortoise 🐢 Animal Fact Files','2026-06-15',510,2406),('teHwadQsmK0','Serow: the Ghost Goat 👻 Animal Fact Files','2026-05-10',520,4249)]
dl=[('3tmPS1p-vEQ','Copycats! This Ant Is Surrounded By Imposters | Deep Look','2026-07-28',289,151100),('CJl_relCddQ','These Mudskipper Fins Were Made For Walking | Deep Look','2026-06-30',313,135145),('1VGBy04nIjA','The Slimy Details Behind Banana Slug Mating','2026-06-02',246,48465),('pmLHg_B8uoI','Release The Brood! Roly-poly Birthing Is Intense','2026-05-12',233,306884),('IGtbHRPcSe8','Spotted Lanternflies are the Ultimate Party Crashers','2026-04-21',289,473542)]
cohorts=[]
for channel,raw in [('Animal Fact Files',aff),('Deep Look',dl)]:
 rows=[dict(id=i,url='https://www.youtube.com/watch?v='+i,title=t,upload_date=d,duration_seconds=s,views=v,age_days=(DAY-datetime.date.fromisoformat(d)).days,thumbnail_inspected=i in INSPECTED,video_playback=False,source='original watch-page text metadata; not audiovisual inspection') for i,t,d,s,v in raw]
 eligible=[r for r in rows if r['age_days']>=59]; med=statistics.median(r['views'] for r in eligible)
 for r in rows:r['sample_median_ratio']=round(r['views']/med,3) if r in eligible else None
 cohorts.append(dict(channel=channel,rows=rows,comparison_n=len(eligible),median_views=med,selection='Recovered monthly species profiles May–Oct; October younger held separate' if channel=='Animal Fact Files' else 'Recovered five 3:53–5:13 standalones April–July; hosted Big Ideas and compilations excluded',limitations='Bounded recovered sample; complete catalogue not established; unequal ages and topic/seasonal confounds. No CTR/retention or causal performance attribution.'))
(P/'ADDITIONAL_PRIMARY_COHORTS.json').write_text(json.dumps(dict(age_basis=str(DAY),timestamp_note='Age uses instructed session date; remote runtime may show a different clock. Counts are retrieval snapshots, not archived historical counts.',cohorts=cohorts),indent=2,ensure_ascii=False)+'\n')
b=json.loads((P/'BIZARRE_BEASTS_CURRENT_COHORT.json').read_text())
end={'a0EBpzqWeyI','uWallOyZvn0','xYXRmZJsybs','E4DkTVavyMk'}
strands=[]
for name,flag in [('monthly',False),('Endlings',True)]:
 rows=[r for r in b['rows'] if (r['id'] in end)==flag]
 mature=[r for r in rows if r['in_mature_window']]; med=statistics.median(r['views_snapshot'] for r in mature)
 for r in rows:
  r['strand']=name;r['within_strand_mature_ratio']=round(r['views_snapshot']/med,3) if r in mature else None
 strands.append(dict(strand=name,n_mature=len(mature),median_views=med,ids=[r['id'] for r in rows]))
b['strand_comparisons']=strands
b['pooled_mature_median_use']='historical descriptive pooled statistic only; use strand-specific comparisons, not pooled performance labels'
(P/'BIZARRE_BEASTS_CURRENT_COHORT.json').write_text(json.dumps(b,indent=2,ensure_ascii=False)+'\n')
print([(c['channel'],c['comparison_n'],c['median_views']) for c in cohorts]);print(strands)
