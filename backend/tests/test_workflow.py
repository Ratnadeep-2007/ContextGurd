import io

from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from backend.app.ingestion import parse_source
from backend.app.schemas import Case, Candidate, ChallengeOutput, Criterion, Evidence, EvidenceOutput, PlanOutput, PlannedCheck, PriorDecision, Resolution, Trace
from backend.app.workflow import analyze, fingerprint


def test_pdf_text_and_physical_page_preserved():
    writer=PdfWriter();page=writer.add_blank_page(width=300,height=300)
    font=DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')})
    page[NameObject('/Resources')]=DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):writer._add_object(font)})})
    content=DecodedStreamObject();content.set_data(b'BT /F1 12 Tf 30 200 Td (Release November 15, 2026.) Tj ET')
    page[NameObject('/Contents')]=writer._add_object(content)
    buffer=io.BytesIO();writer.write(buffer)
    source=parse_source('proposal.pdf',buffer.getvalue())
    assert source.status=='ready'
    assert 'Release November 15' in source.passages[0].text
    assert source.passages[0].location.startswith('Page 1')


def test_live_three_role_flow_and_user_assertions(monkeypatch):
    from backend.app import workflow
    source=parse_source('notes.txt',b'The final release is November 15.\n\nThe final release is November 20.')
    check=Criterion(id='dates',title='Release dates',description='Check the same release milestone.')
    case=Case(title='Live contract test',goal='Confirm the release milestone',mode='live',sources=[source],criteria=[check])
    case.resolutions.append(Resolution(finding_id='old-issue',action='unknown',answer='Ask the client which milestone is intended.',owner='Maya',source_fingerprint=fingerprint(case)))
    case.prior_decisions=[PriorDecision(id='earlier-choice',project_id='controlled-project',case_id='earlier-review',case_title='Earlier review',finding_id='earlier-date',title='Earlier release choice',question='Which date?',answer='November 20',owner='Lead',source_fingerprint='historical',created_at='2026-10-01T00:00:00Z')]
    calls=[]
    def fake_complete(role,instruction,payload,output,allow_fallback):
        calls.append((role,payload))
        trace=Trace(role=role,provider='controlled-test',model='not-live',duration_ms=1)
        if role=='Planner':
            return PlanOutput(checks=[PlannedCheck(id='dates',title='Release dates',description=check.description,origin='suggested',source_passage_id=None)]),trace,[]
        if role=='Evidence':
            return EvidenceOutput(evidence=[Evidence(id=f'E{i}',check_id='dates',passage_id=p.id,quote=p.text) for i,p in enumerate(source.passages)]),trace,[]
        return ChallengeOutput(findings=[Candidate(check_id='dates',title='Confirm the release date',type='potential_conflict',priority='important',explanation='Two final release dates are supplied.',impact='Release scheduling needs confirmation.',uncertainty='One may be a proposed revision.',question='Which date is authoritative?',recommended_action='Ask the client.',evidence_ids=['E0','E1'])],limitations=[]),trace,[]
    monkeypatch.setattr(workflow,'complete',fake_complete)
    stages=[];report=analyze(case,stages.append)
    assert [x[0] for x in calls]==['Planner','Evidence','Challenge']
    assert calls[0][1]['user_assertions_not_documentary_proof'][0]['owner']=='Maya'
    assert calls[2][1]['user_assertions_not_documentary_proof'][0]['action']=='unknown'
    assert all('coverage' not in check for _, payload in calls for check in payload.get('checks', payload.get('requested_checks', [])))
    assert all(payload['prior_project_decisions_not_documentary_proof'][0]['answer']=='November 20' for _,payload in calls)
    assert report.findings[0].status=='open'
    assert len(report.findings)==1 and report.rejected_count==0
    assert stages[-1]=='Verifying source references'


def test_undo_does_not_change_source_hash(client,sample):
    from .conftest import finish
    hashes=[x['content_hash'] for x in sample['sources']]
    f=sample['report']['findings'][0]
    client.post(f"/api/cases/{sample['id']}/resolutions",json={'version':sample['version'],'finding_id':f['id'],'action':'dismiss','answer':'This task is outside this kickoff.'})
    changed=finish(client,sample['id'])
    assert next(x for x in changed['report']['findings'] if x['id']==f['id'])['status']=='dismissed'
    assert [x['content_hash'] for x in changed['sources']]==hashes


def test_restart_marks_interrupted_job_failed(tmp_path):
    from backend.app.schemas import Run
    from backend.app.store import Store
    path=str(tmp_path/'restart.sqlite3');store=Store(path)
    case=Case(title='Interrupted',goal='Check the kickoff sources',run=Run())
    store.save(case,create=True)
    restored=Store(path).get(case.id)
    assert restored.run.status=='failed' and 'restarted' in restored.run.error


def test_models_receive_only_latest_current_answer():
    from backend.app.sample import sample_case
    from backend.app.workflow import active_assertions
    case=sample_case()
    for answer in ['November 15', 'November 20']:
        case.resolutions.append(Resolution(finding_id='same-issue',action='confirm',answer=answer,source_fingerprint=fingerprint(case)))
    case.resolutions.append(Resolution(finding_id='unrelated',action='unknown',answer='Ask Maya',source_fingerprint=fingerprint(case)))
    assert len(case.resolutions)==3
    current=active_assertions(case)
    assert len(current)==2
    assert next(x for x in current if x.finding_id=='same-issue').answer=='November 20'


def test_cancelled_background_work_cannot_overwrite_result(client,monkeypatch):
    import threading
    import time
    from backend.app import main
    from backend.app.workflow import analyze as actual_analyze
    started=threading.Event();release=threading.Event();done=threading.Event()
    def slow_analyze(case,progress):
        started.set();release.wait(2)
        try:
            return actual_analyze(case,progress)
        finally:
            done.set()
    monkeypatch.setattr(main,'analyze',slow_analyze)
    case=client.post('/api/cases/sample').json()
    client.post(f"/api/cases/{case['id']}/analyze",json={'version':case['version']})
    assert started.wait(1)
    response=client.post(f"/api/cases/{case['id']}/cancel")
    assert response.status_code==200 and response.json()['run']['status']=='cancelled'
    release.set();assert done.wait(2);time.sleep(.03)
    current=client.get(f"/api/cases/{case['id']}").json()
    assert current['run']['status']=='cancelled' and current['report'] is None
