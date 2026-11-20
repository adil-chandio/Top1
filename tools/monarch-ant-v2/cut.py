"""V2 editorial decisions. Cut times are measured on the selected VO master.

The source clock is an illustrative animation clock, never a study measurement.
The film clock advances at 30 native evaluations per second. A pin places a
physical event on an exact film frame without introducing a cut or a repeat.
"""
import json
import os
from pathlib import Path

ROOT=Path(os.environ.get('MONARCH_V2_CACHE','.cache/monarch-ant-v2'))
VO=Path(os.environ.get('MONARCH_VO_RECEIPT','.cache/monarch-cam-ant-vo-v1/edit-receipt.json'))
FPS=30
SR=48000
SOURCE='4a3d3c596005cee1f077cc24c0b3a8e55ae9c29614b1f4ed77d119fd5fbf5929'
# Smaller breath windows than V1. All insertions fall between intact takes.
HOLD=[.70,.55,.65,1.75,.95,.70,3.10]
# out on the locked voice clock | set, camera | motion in/out | unique shot | optional pins
CUTS=[[
 (2.08,1,2,.08,.76,'opening_side_climb'),
 (4.20,2,9,1.24,3.45,'sand_shears_downhill'),
 (7.79,1,0,.74,2.07,'tarsi_lose_traction'),
 (10.95,3,5,1.19,2.15,'pincers_rise_in_the_bowl',[(8.95,1.41)]),
 (12.78,1,29,2.14,2.68,'watch_the_head'),
 (16.15,0,3,2.69,3.966,'first_dip_contact_and_recoil',[(14.70,3.42)]),
 (17.47,0,4,3.967,5.583,'opener_crosses_the_far_lip',[(16.88,5.232),(17.31,5.48)]),
 (19.59,6,10,2.87,3.34,'jaws_sweep_inward'),
 (None,9,22,.16,1.88,'after_landing_low_tracking'),
],[
 (25.97,2,6,5.26,8.20,'funnel_plan_view'),
 (28.59,10,7,1.12,3.77,'rim_to_basin_staging'),
 (32.14,8,8,2.28,4.52,'partly_buried_larva'),
 (35.10,8,24,4.55,7.13,'the_waiting_pincers'),
 (37.74,1,23,.48,1.51,'slope_leads_to_center'),
 (39.83,3,24,2.31,2.83,'larva_head_flick',[(38.77,2.56)]),
 (41.81,3,32,2.832,3.37,'airborne_quartz_golden_rim'),
 (43.79,2,9,5.41,7.48,'moving_sheet_of_grains'),
 (47.46,1,28,.83,1.93,'legs_against_the_slide'),
 (51.12,1,0,1.94,2.43,'foot_searches_for_purchase'),
 (55.29,3,8,5.62,6.96,'larva_clears_the_floor',[(52.61,6.05)]),
 (57.65,10,35,7.24,9.55,'steep_walls_reverse_view'),
 (60.52,3,24,7.82,8.60,'second_flick_underside',[(58.97,8.24)]),
 (63.24,10,30,8.59,11.37,'trap_persists_high_angle'),
 (65.58,1,0,2.04,2.67,'floor_releases_the_foot'),
 (68.02,1,36,2.141,2.56,'first_look_at_open_jaws'),
 (None,1,15,2.51,3.13,'primed_above_unstable_sand'),
],[
 (75.98,5,10,.27,2.61,'normal_grip_while_feeding'),
 (79.11,16,11,.42,2.23,'locked_wide_cross_view'),
 (83.18,7,12,.51,2.29,'loading_both_elastic_elements'),
 (85.11,7,13,2.30,2.66,'shell_flex_cross_section'),
 (88.13,7,12,2.67,2.94,'attachment_tensions'),
 (92.84,7,13,2.945,3.91,'release_and_elastic_recoil',[(89.66,3.12)]),
 (98.77,7,27,2.72,3.66,'capsule_wall_push_close'),
 (103.45,7,11,2.75,3.613,'apodeme_pull_separate_lever'),
 (108.23,7,12,2.85,3.68,'both_actions_same_rotation'),
 (114.16,6,11,2.82,3.52,'closed_in_under_a_tenth_millisecond',[(112.18,3.17)]),
 (118.76,12,14,.32,3.92,'closed_jaws_no_body_flight'),
 (None,2,26,4.79,7.44,'what_the_jaws_hit'),
],[
 (124.41,3,32,1.16,1.95,'back_to_pit_lower_axis',[(122.96,1.41)]),
 (126.58,1,0,1.92,2.43,'grounded_tarsi'),
 (129.35,1,15,2.44,2.79,'open_jaws_tilt_toward_sand'),
 (134.03,1,36,2.55,3.20,'one_foreleg_lifts'),
 (140.14,6,14,2.745,3.69,'snap_in_air_no_external_support',[(137.43,3.17)]),
 (145.76,0,37,3.085,3.712,'proof_contact_other_side',[(141.33,3.42),(143.18,3.50)]),
 (148.60,0,26,3.713,3.871,'grain_ejecta_extreme_macro'),
 (152.82,0,16,3.872,4.358,'lift_and_separation_tracking'),
 (156.42,0,17,4.359,5.66,'clearance_from_across_the_bowl',[(155.24,5.232),(156.03,5.48)]),
 (160.99,9,38,.11,1.72,'return_to_supported_feet'),
 (164.54,1,29,2.55,3.236,'still_anchored_before_external_push'),
 (None,10,30,4.13,8.33,'one_bowl_many_possible_endings'),
],[
 (176.91,4,18,2.92,5.41,'failed_launch_wall_hit_and_fall',[(171.91,3.42),(173.84,4.4728)]),
 (179.74,13,28,0.46,1.64,'back_inside_the_pit'),
 (183.72,4,19,3.79,5.71,'ceiling_angle_stays_inside_rim'),
 (187.72,10,6,9.52,13.52,'encounters_same_trap_geometry'),
 (189.88,11,30,2.88,5.31,'run_escape_ordinary_climb'),
 (193.09,0,31,4.31,5.57,'jaw_escape_example_only'),
 (195.04,13,8,1.47,3.33,'caught_not_confirmed_dead'),
 (198.01,9,38,.27,1.65,'survival_not_proven_by_one_jump'),
 (202.57,11,28,.35,3.80,'searching_for_a_footpath'),
 (206.12,4,35,4.07,5.84,'failure_in_a_wider_context'),
 (209.52,10,7,10.38,13.47,'a_question_not_answered_by_replay'),
 (212.27,14,34,.12,2.00,'first_look_at_control_dishes'),
 (None,12,27,.25,4.75,'walking_legs_closed_jaws'),
],[
 (221.56,12,10,1.36,4.53,'closed_condition_jaw_closeup'),
 (226.05,15,21,2.01,5.46,'both_handled_different_jaw_motion'),
 (229.02,14,20,2.22,4.79,'three_cohorts_in_parallel'),
 (231.62,14,34,3.67,6.25,'untouched_condition_distinct'),
 (236.67,11,23,1.91,4.30,'running_needs_its_own_comparison'),
 (240.31,14,20,5.57,7.91,'handling_is_a_confound'),
 (243.88,15,34,3.77,6.84,'isolate_free_vs_restrained'),
 (249.38,15,21,6.86,9.71,'compare_only_the_handled_groups'),
 (252.07,0,33,3.366,4.43,'free_jaws_can_recoil',[(249.95,3.42)]),
 (253.79,11,40,3.85,5.35,'running_still_possible'),
 (256.85,4,19,4.417,5.67,'not_every_jump_clears'),
 (None,9,22,.058,1.95,'some_jumps_are_a_way_out'),
],[
 (265.88,1,28,.83,2.29,'revisit_traction_other_side'),
 (267.32,1,36,2.302,3.236,'reprise_head_tilts'),
 (271.19,0,26,3.238,4.205,'reprise_contact_and_empty_spot',[(267.57,3.42)]),
 (276.33,3,24,5.66,6.87,'pincers_cast_a_second_fan',[(274.27,6.05)]),
 (280.63,0,31,3.411,5.52,'flight_beyond_the_pit_other_side',[(277.75,3.42),(280.12,5.48)]),
 (284.04,3,32,10.23,11.65,'another_larva_flick',[(281.34,10.50)]),
 (287.17,2,9,11.71,15.01,'slope_never_stops_moving'),
 (291.18,0,39,3.172,3.75,'one_bite_closing_contact',[(290.48,3.42)]),
 (None,10,25,13.07,15.77,'return_to_the_bowl_no_end_card'),
]]


def at(shot, t):
    # Inverse of the renderer's piecewise linear time map; for sample-accurate spotting.
    points=[(shot['first'],shot['src'][0]),*shot['pins'],(shot['end']-1,shot['src'][1])]
    for (a,u),(b,v) in zip(points,points[1:]):
        if u<=t<=v:
            return (a+(b-a)*(t-u)/(v-u))/FPS
    return None


def spot(shot):
    a=shot['first']/FPS;b=shot['end']/FPS;m=shot['mode'];cam=shot['camera'];key=shot['subject']
    cue=[]
    def add(name, clock, level, control):
        s=at(shot,clock)
        if s is not None and a<=s<b:
            cue.append(dict(name=name,scene=key,time_s=round(s,6),level=level,pan=control))
    if m in (0,1,4):
        pan=.26 if cam in (16,17,37,39) else -.2
        for t in (.19,.48,.82,1.12,1.51,1.87,2.15,2.53,2.82):add('tarsus',t,.65 if cam in (0,36) else .36,pan)
        for t in (.53,1.44,2.07):add('loose_sand',t,.67 if cam==0 else .42,pan*.4)
        if m!=1:add('ground_strike',3.42,.80 if 'contact' in key or 'failed' in key else .51,pan)
        if m==0:
            add('grain_release',3.49,.41 if cam!=26 else .61,pan*.4)
            add('landing',5.48,.64,-pan)
        if m==4:
            add('wall_clip',4.4728,.74,pan)
            add('sand_return',4.66,.70,pan*.45)
    if m==3:
        for t in (.38,1.41,2.56,6.05,8.24,10.5,12.3):add('flick',t,.72,.18 if cam in (8,32) else -.19)
    if m in (2,8,10):
        # Nonperiodic, occasional quiet bed texture; never a looping noise floor.
        s=a+min(1.18,(b-a)*.44)
        cue.append(dict(name='sand_return',scene=key,time_s=round(s,6),level=.30,pan=.12 if cam%2 else -.2))
    if m in (6,7):add('air_click' if m==6 else 'cambered_click',3.17,.56 if m==6 else .36,0.)
    if m in (9,11,13):
        for t in (.22,.67,1.03,1.41,1.84,2.20,2.86,3.41,4.02,4.33,4.86,5.20):
            add('tarsus' if m!=13 else 'loose_sand',t,.42 if m==11 else .37,-.13)
    if m==15:
        for t in (2.38,4.43,7.54,9.00):add('air_click',t,.36,-.43)
    return cue


def main():
    rec=json.loads(VO.read_text());beats=rec['beats'];n=rec['samples']
    assert rec['sample_rate']==SR and rec['wav_sha256']==SOURCE and n==13987270
    pivots=[0]+[(a['end_sample_exclusive']+b['start_sample'])//2 for a,b in zip(beats,beats[1:])]+[n]
    shots=[];events=[];chapter=[];ranges=[];offset=0;f=0
    for i,takes in enumerate(CUTS):
        a,b=pivots[i:i+2];ranges.append([a,b,a+round(SR*offset)]);chapter.append([f,beats[i]['title']]);
        for out,mode,cam,t0,t1,name,*breaks in takes:
            edge=round((b/SR+offset+HOLD[i] if out is None else out+offset)*FPS)
            pins=[(round((sec+offset)*FPS),ts) for sec,ts in (breaks[0] if breaks else [])]
            s=dict(first=f,end=edge,mode=mode,camera=cam,src=[t0,t1],subject=name,pins=pins,beat=i+1)
            k=[(f,t0)]+pins+[(edge-1,t1)]
            if not all(a<c and b<d for (a,b),(c,d) in zip(k,k[1:])):raise ValueError(s)
            shots.append(s);events.extend(spot(s));f=edge
        offset+=HOLD[i]
    assert len({r['subject'] for r in shots})==len(shots)
    assert len({(r['mode'],r['camera'],*r['src']) for r in shots})==len(shots)
    assert f*SR//FPS >= ranges[-1][-1]+ranges[-1][1]-ranges[-1][0]
    w=ROOT/'work';w.mkdir(parents=True,exist_ok=True)
    (w/'film-v2.plan').write_text(''.join(
        f"{s['first']} {s['end']} {s['mode']} {s['camera']} {' '.join(map(str,s['src']))} {s['subject']}"
        +''.join(f" {p} {t:.6f}" for p,t in s['pins'])+'\n' for s in shots))
    j=dict(duration_s=f/FPS,frames=f,fps=FPS,vo_sha256=SOURCE,vo_ranges=ranges,
           picture_holds=HOLD,chapters=chapter,shots=shots,events=sorted(events,key=lambda x:x['time_s']))
    (w/'film-v2.json').write_text(json.dumps(j,indent=2)+'\n')
    print(f'{len(shots)} camera cuts · {f} native frames · {f/FPS:.3f}s · {len(events)} localized Foley events')
    for s in shots:
        if s['pins']:print(s['subject']+': '+', '.join(f'{p/FPS:.3f}s → {t:g}' for p,t in s['pins']))

if __name__=='__main__':main()
