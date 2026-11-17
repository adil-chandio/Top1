"""Evidence contracts for specialist craft. Attestations are not artistic proof."""
import hashlib
DEPARTMENTS={
 'script':('story_design','edit_sound_blueprint'),
 'feasibility':('art_direction','integrated_motion_test','asset_provenance'),
 'production':('editing','animation','motion_design','typography','compositing','sound_design','music','mix','finishing'),
 'qc':('picture_only_review','audio_only_review','combined_review','reference_comparison','delivery_integrity')
}

def verify(job,stage,result):
    required=DEPARTMENTS.get(stage,())
    if not required:return
    from studio.pipeline import owned
    artifacts={a['path']:a['sha256'] for a in result['artifacts']}
    craft=result.get('craft',{})
    for department in required:
        record=craft.get(department,{})
        if record.get('status') not in ('pass','not_applicable'):raise ValueError('craft missing/failed: '+department)
        if not record.get('observations') or not record.get('rationale'):raise ValueError('craft findings required: '+department)
        if record['status']=='not_applicable':
            if department not in ('typography',):raise ValueError('department cannot be omitted: '+department)
            continue
        paths=record.get('evidence',[])
        if not paths:raise ValueError('craft evidence required: '+department)
        for path in paths:
            if path not in artifacts:raise ValueError('craft evidence not in verified artifacts')
            if hashlib.sha256(owned(job,path).read_bytes()).hexdigest()!=artifacts[path]:raise ValueError('craft evidence changed')
    if stage=='feasibility':
        record=craft['integrated_motion_test']
        if not any(p.lower().endswith('.mp4') for p in record['evidence']):raise ValueError('integrated motion/audio MP4 proof required')
    if stage=='production':
        if not result.get('attribution'):raise ValueError('asset/music attribution manifest required; record original work too')
    if stage=='qc':
        expected=result.get('reviewed_production_sha256')
        if not expected:raise ValueError('QC must bind exact production hash')
