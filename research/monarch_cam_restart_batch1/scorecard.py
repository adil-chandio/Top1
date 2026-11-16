"""Evidence-gated editorial ratings. Missing evidence is not a zero or an average."""
WEIGHTS = {'hook':15, 'story':15, 'relative_performance':20,
           'visual_clarity':10, 'fresh_angle':10, 'av_execution':15,
           'preliminary_feasibility':10, 'channel_fit':5}


def evaluate(candidate):
    ratings=candidate.get('ratings',{})
    missing=[]
    total=0.
    for name,weight in WEIGHTS.items():
        item=ratings.get(name)
        if item is None:
            missing.append(name)
            continue
        score=item.get('score')
        if isinstance(score,bool) or not isinstance(score,(int,float)) or not 0<=score<=10:
            raise ValueError('Invalid score: '+name)
        if not item.get('reason') or not item.get('evidence') or item.get('confidence') not in ('low','medium','high'):
            raise ValueError('Score needs reason, evidence and confidence: '+name)
        total+=score*weight/100
    gates=candidate.get('gates',{})
    required=['actual_av_review','comparable_cohort','age_context','primary_claim_screen','rights_feasibility_screen']
    missing_gates=[g for g in required if gates.get(g) is not True]
    eligible=not missing and not missing_gates
    return {'total_out_of_10':round(total,2) if eligible else None,
            'missing_dimensions':missing, 'unresolved_gates':missing_gates,
            'eligible_for_final_recommendation':eligible,
            'score_type':'editorial decision score, not probability of virality'}
