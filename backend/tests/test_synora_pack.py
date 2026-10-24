"""Real six-file/API regression with manually annotated model outputs, not live AI."""
from pathlib import Path

from backend.app.schemas import Candidate, ChallengeOutput, Evidence, EvidenceOutput, PlanOutput, PlannedCheck, Trace
from .conftest import finish


def test_six_file_review_keeps_conflicts_with_qualifying_citations(client, monkeypatch):
    from backend.app import workflow
    monkeypatch.setenv('MODEL_API_KEY', 'controlled-test-key')
    case=client.post('/api/cases',json={'title':'Synora regression','goal':'Clarify Synora scope, approval behavior and pilot timing'}).json()
    prefix=f"/api/cases/{case['id']}"
    pack=Path(__file__).resolve().parents[2]/'synora-review-pack'
    for path in sorted(pack.glob('0[1-6]-*.md')):
        response=client.post(prefix+f"/sources/upload?version={case['version']}",files={'file':(path.name,path.read_bytes(),'text/markdown')})
        assert response.status_code==200
        case=response.json()
    assert len(case['sources'])==6 and all(s['status']=='ready' for s in case['sources'])
    hashes=[s['content_hash'] for s in case['sources']]
    annotations=[
        ('dates','01-product-brief.md','December 7, 2026'),
        ('dates','04-release-checklist.md','January 18, 2027'),
        ('approval','01-product-brief.md','Canvas edits are not ingested as evidence.'),
        ('approval','06-project-lead-email.md','Saved canvas edits will be imported'),
        ('approval','02-architecture-notes.md','must remain pending until'),
        ('approval','06-project-lead-email.md','will be written into project memory automatically.'),
        ('assumptions','06-project-lead-email.md','This email is only a proposal'),
    ]
    evidence=[]
    for i,(check_id,name,needle) in enumerate(annotations):
        source=next(s for s in case['sources'] if s['name']==name)
        passage=next(p for p in source['passages'] if needle in p['text'])
        evidence.append(Evidence(id=f'e{i}',check_id=check_id,passage_id=passage['id'],quote=passage['text']))
    candidates=[]
    for check_id,title,refs in [('dates','Pilot date differs',['e0','e1','e6']),('approval','Canvas direction differs',['e2','e3','e6']),('approval','Approval policy differs',['e4','e5','e6'])]:
        candidates.append(Candidate(check_id=check_id,title=title,type='potential_conflict',priority='important',explanation='Drafts propose different behavior or timing.',impact='Clarify affected planning.',uncertainty='No draft is established as authoritative.',question='Which proposal applies?',recommended_action='Record the decision.',evidence_ids=refs))
    seen_assertions=[]
    def controlled_complete(role,instruction,payload,output,allow_fallback):
        trace=Trace(role=role,provider='controlled-test',model='manual-annotations-not-live',duration_ms=0)
        if role=='Planner':
            seen_assertions.append(payload['user_assertions_not_documentary_proof'])
            return PlanOutput(checks=[PlannedCheck(id=c['id'],title=c['title'],description=c['description'],origin='suggested',source_passage_id=None) for c in case['criteria']]),trace,[]
        if role=='Evidence':
            return EvidenceOutput(evidence=evidence),trace,[]
        return ChallengeOutput(findings=candidates,limitations=['Controlled regression: model outputs are manually annotated.']),trace,[]
    monkeypatch.setattr(workflow,'complete',controlled_complete)
    assert client.post(prefix+'/analyze',json={'version':case['version']}).status_code==202
    reviewed=finish(client,case['id'])
    assert len(reviewed['report']['findings'])==3
    assert reviewed['report']['rejected_count']==0
    date=next(f for f in reviewed['report']['findings'] if f['check_id']=='dates')
    assert client.post(prefix+'/resolutions',json={'version':reviewed['version'],'finding_id':date['id'],'action':'confirm','answer':'Synthetic test decision: January 18 is the selected pilot target.','owner':'Test project lead'}).status_code==202
    updated=finish(client,case['id'])
    saved=next(f for f in updated['report']['findings'] if f['id']==date['id'])
    assert saved['status']=='user_confirmed' and saved['owner']=='Test project lead'
    assert seen_assertions[-1][0]['answer'].startswith('Synthetic test decision')
    assert [s['content_hash'] for s in updated['sources']]==hashes
    brief=client.get(prefix+'/brief')
    assert brief.status_code==200 and 'User statement (not documentary proof)' in brief.text
    assert '06-project-lead-email.md' in brief.text
    resolution=updated['resolutions'][0]
    assert client.post(prefix+f"/resolutions/{resolution['id']}/undo",json={'version':updated['version']}).status_code==202
    undone=finish(client,case['id'])
    assert all(f['status']=='open' for f in undone['report']['findings'])
