"""Bounded R&D response validation. No downloading or executing candidate repos here."""
def validate_repair(result):
    if result.get('status')!='complete':raise ValueError('R&D did not resolve issue')
    if result.get('paid_spend') is not False:raise ValueError('R&D cannot authorize purchases')
    if not result.get('problem') or not result.get('acceptance_test'):raise ValueError('R&D needs specific problem/test')
    candidates=result.get('candidates',[])
    if not 1<=len(candidates)<=3:raise ValueError('R&D shortlist must contain 1–3 candidates')
    chosen=[c for c in candidates if c.get('selected') is True]
    if len(chosen)!=1:raise ValueError('select exactly one tested solution')
    for c in candidates:
        if not c.get('source_url','').startswith('https://') or not c.get('decision_reason'):raise ValueError('candidate provenance/decision missing')
    c=chosen[0]
    for key in ('license_review','security_review','compatibility','version','test_evidence','comparison','rollback'):
        if not c.get(key):raise ValueError('selected solution missing '+key)
    if c.get('test_passed') is not True:raise ValueError('untested solution cannot be integrated')
    return result
