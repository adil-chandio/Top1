"""Verify source-anchored script intervals, not retention or inferred speech rate."""
import json
from pathlib import Path
B=Path(__file__).parent
# Only caption/mirror anchors, not inferred percentage-based section labels.
ANCHORS=[
 ('Tm8PtCTt2j8','contradiction_to_first_named_candidate',24,97),
 ('Tm8PtCTt2j8','humpback_section_to_sperm_whale_reveal',97,227),
 ('Tm8PtCTt2j8','sperm_section_to_pilot_reveal',227,338),
 ('Tm8PtCTt2j8','sperm_case_start_to_late_counteroutcome',289,538),
 ('49_Ph2q6uIM','skeleton_setup_to_identity_reversal',64,114),
 ('49_Ph2q6uIM','scepticism_to_named_food_hours_number',224,271),
 ('49_Ph2q6uIM','first_daily_routine_to_farming_transition',157,517),
 ('foi5WtXV7E0','contradiction_to_named_identity',19,71),
 ('foi5WtXV7E0','calf_vulnerability_question_to_answer',157,163),
 ('leLeWBxhNa0','opening_seventeen_sharks_to_departure_payoff',18,251),
 ('ZQvfHyfgBtA','published_start_to_first_mechanism_chapter',0,14),
]
def main():
 m=json.loads((B/'SCRIPT_SOURCE_MANIFEST.json').read_text())
 durations={r['id']:r['duration_s'] for r in m['videos']}
 out=[]
 for vid,label,start,end in ANCHORS:
  assert 0 <= start < end <= durations[vid], (vid,label)
  out.append({'video_id':vid,'annotation':label,'start_s':start,'end_s':end,'elapsed_s':end-start,'precision':'caption/chapter anchor; not frame exact; not retention measurement'})
 (B/'data/script_timing_annotations.json').write_text(json.dumps(out,indent=2))
 print(f'{len(out)} source-anchored intervals validated against {len(durations)} video durations')
if __name__=='__main__':main()
