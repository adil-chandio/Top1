"""The full-length V3 editorial schedule on the selected voice's exact clock."""
import json
import os
from pathlib import Path
from pilot import FPS, PLAN, ROOT, V2_WORK, TOOLS

R = ROOT/'feature'
WORK = R/'work'
QA = R/'qa'
DELIVER = Path(os.environ.get('MONARCH_FEATURE_DELIVERY','deliverables/monarch-cam-step-4-v3-full'))
NAME = 'Monarch-Cam-Ant-V3-Full-Cinematic-Cut'
EDL = WORK/'feature.plan'
META = WORK/'feature.json'
WIDTH, HEIGHT = 1280, 720       # 30 distinct native evaluations per second
MASTER = (1920, 1080)
ANCHORS = (0, 708, 2182, 3700, 5188, 6658, 8011, 8994)

# Station changes, exact matched geometry, and narrative restaging (entries not
# listed here get sparser sidelight and new framing on the feature optics).
LENS = {
'funnel_plan_view':50, 'rim_to_basin_staging':51, 'partly_buried_larva':52,
 'the_waiting_pincers':53, 'larva_head_flick':54, 'airborne_quartz_golden_rim':54,
 'moving_sheet_of_grains':1, 'legs_against_the_slide':56, 'foot_searches_for_purchase':0,
 'larva_clears_the_floor':53, 'steep_walls_reverse_view':57, 'trap_persists_high_angle':57,
 'first_look_at_open_jaws':58, 'primed_above_unstable_sand':59,
 'normal_grip_while_feeding':60, 'locked_wide_cross_view':61, 'loading_both_elastic_elements':61,
 'shell_flex_cross_section':63, 'attachment_tensions':62, 'release_and_elastic_recoil':63,
 'capsule_wall_push_close':62, 'apodeme_pull_separate_lever':65, 'both_actions_same_rotation':64,
 'closed_in_under_a_tenth_millisecond':66, 'closed_jaws_no_body_flight':67, 'what_the_jaws_hit':1,
 'back_to_pit_lower_axis':53, 'grounded_tarsi':0, 'open_jaws_tilt_toward_sand':68,
 'snap_in_air_no_external_support':67, 'proof_contact_other_side':69, 'grain_ejecta_extreme_macro':70,
 'lift_and_separation_tracking':71,'clearance_from_across_the_bowl':72,'return_to_supported_feet':78,
 'still_anchored_before_external_push':79,'one_bowl_many_possible_endings':75,
 'back_inside_the_pit':55,'ceiling_angle_stays_inside_rim':75,
 'encounters_same_trap_geometry':75,'run_escape_ordinary_climb':57,'jaw_escape_example_only':72,
 'caught_not_confirmed_dead':52,'survival_not_proven_by_one_jump':78,'searching_for_a_footpath':82,
 'failure_in_a_wider_context':57,'a_question_not_answered_by_replay':51,
 'first_look_at_control_dishes':76,'walking_legs_closed_jaws':67,'closed_condition_jaw_closeup':83,
 'both_handled_different_jaw_motion':77,'three_cohorts_in_parallel':76,'untouched_condition_distinct':76,
 'running_needs_its_own_comparison':82,'handling_is_a_confound':76,'isolate_free_vs_restrained':77,
 'compare_only_the_handled_groups':77,'some_jumps_are_a_way_out':78,
 'revisit_traction_other_side':56,'reprise_head_tilts':58,'reprise_contact_and_empty_spot':70,
 'pincers_cast_a_second_fan':54,'flight_beyond_the_pit_other_side':72,'another_larva_flick':53,
 'slope_never_stops_moving':1,'one_bite_closing_contact':81,'return_to_the_bowl_no_end_card':80,
}

# Keyframe pins are elapsed model time, not real times reported by a study.
TUNE = {
 'closed_jaws_no_body_flight':dict(mode=16,src=[3.202,4.02]),
 'moving_sheet_of_grains':dict(mode=21,src=[.32,1.91]),
 'slope_never_stops_moving':dict(mode=21,src=[1.34,3.31]),
 'funnel_plan_view': dict(mode=10,src=[4.861,7.5]),
 'rim_to_basin_staging': dict(src=[7.502,8.56]),
 'legs_against_the_slide': dict(src=[.631,1.888]),
 'locked_wide_cross_view': dict(mode=6,src=[.28,.809]),
 'loading_both_elastic_elements': dict(src=[.81,2.29]),
 'proof_contact_other_side':dict(src=[3.012,3.706],pins=[[4297,3.42],[4310,3.495],[4370,3.615]]),
 'grain_ejecta_extreme_macro': dict(src=[3.707,3.887],pins=[[4474,3.809]]),
 'lift_and_separation_tracking': dict(src=[3.889,4.358]),
 'revisit_traction_other_side': dict(src=[.638,1.888]),
 'reprise_contact_and_empty_spot':dict(src=[3.35,4.205]),
 'return_to_the_bowl_no_end_card':dict(mode=23,src=[4.86,5.86]),
}


def shot(first,end,mode,camera,a,b,subject,beat,pins=()):
    return dict(first=first,end=end,mode=mode,camera=camera,src=[a,b],subject=subject,beat=beat,pins=[list(z) for z in pins])


def opening():
    a=[]
    for r in PLAN.read_text().splitlines():
        if not r or r.startswith('#'): continue
        lo,hi,m,c,x,y,s,*k=r.split();a.append(shot(int(lo),int(hi),int(m),int(c),float(x),float(y),s,1,[(int(f),float(t)) for f,t in zip(k[::2],k[1::2])]))
    return a


def design():
    WORK.mkdir(parents=True,exist_ok=True);QA.mkdir(parents=True,exist_ok=True)
    v=json.loads((V2_WORK/'film-v2.json').read_text())
    assert v['fps']==FPS and tuple(f for f,_ in v['chapters'])+(v['frames'],)==ANCHORS
    shots=opening()
    for a in v['shots']:
        if a['beat']==1:continue
        s=a.copy();k=s['subject']
        if k=='failed_launch_wall_hit_and_fall':
            shots.extend([shot(5188,5299,4,73,2.82,3.954,'return_of_the_same_stance',5,[(5267,3.42)]),
                          shot(5299,5417,4,74,3.956,5.41,'wall_collision_and_return',5,[(5325,4.4728)])]);continue
        if k=='the_waiting_pincers':
            shots.extend([shot(985,1033,8,53,4.55,5.91,'pincer_in_the_dark',2),
                          shot(1033,1074,8,124,5.92,7.13,'the_waiting_pincers',2)]);continue
        if k=='one_bowl_many_possible_endings':
            shots.extend([shot(4993,5053,10,51,4.13,5.18,'gravity_returns_us_to_the_pit',4),
                          shot(5053,5188,10,75,5.20,8.33,k,4)]);continue
        if k=='walking_legs_closed_jaws':
            shots.extend([shot(6478,6559,12,67,.25,2.48,'one_condition_jaw_held_shut',5),
                          shot(6559,6658,15,77,2.49,4.75,'same_feet_different_jaws',5)]);continue
        s.update(TUNE.get(k,{}));s['camera']=LENS.get(k,100+a['camera'])
        shots.append(s)
    assert shots[-1]['end']==ANCHORS[-1] and shots[0]['first']==0
    assert all(a['end']==b['first'] for a,b in zip(shots,shots[1:]))
    assert len({s['subject'] for s in shots})==len(shots)
    for r in shots:
        x=[(r['first'],r['src'][0]),*r['pins'],(r['end']-1,r['src'][1])]
        assert all(a<c and b<d for (a,b),(c,d) in zip(x,x[1:])),r
    m={k:v[k] for k in ('fps','frames','duration_s','vo_ranges','vo_sha256','chapters','picture_holds')}
    m['shots']=shots;m['resolution']=[WIDTH,HEIGHT];m['delivery_resolution']=MASTER
    EDL.write_text(''.join(f"{r['first']} {r['end']} {r['mode']} {r['camera']} {r['src'][0]:.6f} {r['src'][1]:.6f} {r['subject']}"
                           + ''.join(f" {f} {t:.6f}" for f,t in r['pins'])+'\n' for r in shots))
    META.write_text(json.dumps(m,indent=2)+'\n');print(f'{len(shots)} takes; 7 chapters; {m["frames"]} frames / {m["duration_s"]:.2f} s')
    return m


if __name__=='__main__':design()
