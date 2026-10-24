"""Project-memory behavior and the real Mem0 REST adapter with controlled HTTP."""
import json

import httpx
import pytest

from backend.app.main import create_app
from backend.app.project_memory import Mem0Index, MemoryIndexError, ProjectMemory, decision_sources
from backend.app.sample import fixture_candidates, sample_case
from backend.app.schemas import Case, Resolution, Run
from backend.app.store import Store
from backend.app.workflow import fingerprint, verify
from .conftest import finish


def earlier_review(store, project_id, answer='January 18, 2027 is the pilot target.'):
    case=sample_case();case.mode='live';case.project_id=project_id;case.title='Controlled earlier project review'
    evidence,candidates=fixture_candidates(case)
    case.report=verify(case,case.criteria,evidence,candidates)
    finding=next(f for f in case.report.findings if f.check_id=='dates')
    case.resolutions.append(Resolution(finding_id=finding.id,action='confirm',answer=answer,owner='Project lead',source_fingerprint=fingerprint(case),finding_title=finding.title,finding_question=finding.question,source_snapshot=decision_sources(case,finding)))
    case.run=Run(status='completed')
    return store.save(case,create=True)


def test_project_names_and_invalid_binding(client):
    assert client.post('/api/projects',json={'name':'  '}).status_code==400
    first=client.post('/api/projects',json={'name':'  Synora   Pilot '})
    assert first.status_code==201 and first.json()['name']=='Synora Pilot'
    assert client.post('/api/projects',json={'name':'synora pilot'}).status_code==409
    assert client.post('/api/cases',json={'project_id':'missing'}).status_code==404
    assert client.get('/api/projects').json()[0]['id']==first.json()['id']


def test_recall_across_reviews_is_project_scoped_and_source_linked(client):
    store=client.app.state.store
    project=store.create_project('Synora')
    other=store.create_project('Another product')
    source=earlier_review(store,project.id)
    earlier_review(store,other.id,'A different product uses December 7.')
    target=client.post('/api/cases',json={'project_id':project.id,'goal':'Confirm the pilot target date'}).json()
    recall=client.get(f"/api/cases/{target['id']}/memory").json()
    assert len(recall['decisions'])==1
    remembered=recall['decisions'][0]
    assert remembered['answer'].startswith('January 18') and remembered['case_id']==source.id
    assert remembered['sources'][0]['name'] and remembered['sources'][0]['quote']
    assert client.get(f'/api/cases/{source.id}/memory').json()['decisions']==[]
    separate=client.post('/api/cases',json={}).json()
    assert client.get(f"/api/cases/{separate['id']}/memory").json()['decisions']==[]


@pytest.mark.parametrize('change',['undo','new_unknown','changed_goal','changed_project','changed_source','delete'])
def test_inactive_decisions_stop_recall_immediately(tmp_path,change):
    store=Store(str(tmp_path/'memory.sqlite3'))
    project=store.create_project('Synora');case=earlier_review(store,project.id)
    assert len(store.decisions(project.id))==1
    if change=='delete':
        store.delete(case.id)
    else:
        if change=='undo': case.resolutions[0].revoked=True
        if change=='new_unknown':
            case.resolutions.append(Resolution(finding_id=case.resolutions[0].finding_id,action='unknown',answer='',source_fingerprint=fingerprint(case)))
        if change=='changed_goal': case.goal+=' with revised scope'
        if change=='changed_project': case.project_id=store.create_project('Other project').id
        if change=='changed_source': case.sources.pop()
        store.save(case)
    assert store.decisions(project.id)==[]
    assert store.search_decisions(project.id,'','January pilot')==[]
    assert any(job['action']=='delete' for job in store.memory_jobs())


def test_sample_decisions_are_not_shared(tmp_path):
    store=Store(str(tmp_path/'sample.sqlite3'));project=store.create_project('Synora')
    case=earlier_review(store,project.id)
    case.mode='sample';store.save(case)
    assert store.decisions(project.id)==[]


def test_mem0_rest_sync_search_and_delete_are_verified_against_sqlite(tmp_path):
    store=Store(str(tmp_path/'mem0.sqlite3'));project=store.create_project('Synora')
    case=earlier_review(store,project.id);decision=store.decisions(project.id)[0]
    calls=[]
    def handler(request):
        payload=json.loads(request.content) if request.content else None
        calls.append((request.method,request.url.path,payload))
        if request.url.path=='/memories':
            assert request.headers['X-API-Key']=='test-service-key'
            assert payload['infer'] is False
            assert payload['metadata']['contextguard_decision_id']==decision.id
            assert payload['user_id']=='contextguard:project:'+project.id
            return httpx.Response(200,json={'results':[{'id':'remote-1','event':'ADD'}]})
        if request.url.path=='/search':
            assert payload['filters']['project_id']==project.id
            return httpx.Response(200,json={'results':[{'memory':'Do not trust this altered remote answer','metadata':{'contextguard_decision_id':decision.id}},{'metadata':{'contextguard_decision_id':'foreign-project-or-deleted-id'}}]})
        return httpx.Response(200,json={'message':'Memory deleted successfully'})
    service=ProjectMemory(store,Mem0Index('http://localhost:8888','test-service-key',httpx.MockTransport(handler)))
    try:
        service.sync()
        assert store.memory_job_status()['synced']==1
        target=Case(project_id=project.id,title='New review',goal='Confirm the pilot date')
        result=service.recall(target)
        assert result['retrieval']=='mem0' and len(result['decisions'])==1
        assert result['decisions'][0]['answer']==decision.answer
        case.resolutions[0].revoked=True;store.save(case)
        assert service.recall(target)['decisions']==[]
        service.sync()
        assert any(method=='DELETE' and path=='/memories/remote-1' for method,path,_ in calls)
    finally:
        service.close()


def test_index_failure_preserves_local_recall_and_retry_without_secrets(tmp_path):
    store=Store(str(tmp_path/'retry.sqlite3'));project=store.create_project('Synora');earlier_review(store,project.id)
    def handler(request):
        return httpx.Response(401,text='secret provider body must not be shown')
    service=ProjectMemory(store,Mem0Index('http://localhost:8888','secret-key',httpx.MockTransport(handler)))
    try:
        service.sync()
        job=store.memory_jobs()[0]
        assert job['state']=='error' and 'HTTP 401' in job['error'] and 'secret' not in job['error']
        result=service.recall(Case(project_id=project.id,title='Next',goal='Confirm the next pilot date'))
        assert len(result['decisions'])==1 and result['retrieval']=='local'
        assert 'secret' not in result['notice']
    finally:
        service.close()
    reopened=Store(store.path)
    assert reopened.memory_jobs()[0]['state']=='error'
    assert len(reopened.decisions(project.id))==1


def test_late_index_acknowledgement_cannot_resurrect_undone_decision(tmp_path):
    store=Store(str(tmp_path/'race.sqlite3'));project=store.create_project('Synora');case=earlier_review(store,project.id)
    old_job=store.memory_jobs()[0]
    case.resolutions[0].revoked=True;store.save(case)
    store.finish_memory_job(old_job,'remote-created-after-undo')
    remaining=store.memory_jobs()[0]
    assert remaining['action']=='delete' and remaining['remote_id']=='remote-created-after-undo'
    assert store.decisions(project.id)==[]
    calls=[]
    service=ProjectMemory(store,Mem0Index('http://localhost:8888','',httpx.MockTransport(lambda request:(calls.append(request.url.path) or httpx.Response(200,json={})))))
    try: service.sync()
    finally: service.close()
    assert calls==['/memories/remote-created-after-undo']
    assert store.memory_jobs()==[]


def test_stale_prior_decision_blocks_export_until_recheck(client):
    store=client.app.state.store;project=store.create_project('Synora');source=earlier_review(store,project.id)
    remembered=store.decisions(project.id)[0]
    target=sample_case();target.mode='live';target.project_id=project.id;target.title='New review'
    evidence,candidates=fixture_candidates(target)
    target.report=verify(target,target.criteria,evidence,candidates);target.report.prior_decisions=[remembered]
    target.run=Run(status='completed');store.save(target,create=True)
    assert client.get(f'/api/cases/{target.id}/brief').status_code==200
    source.resolutions[0].revoked=True;store.save(source)
    response=client.get(f'/api/cases/{target.id}/brief')
    assert response.status_code==409 and 'earlier project decision' in response.json()['detail']


@pytest.mark.parametrize('url',['http://remote.example','file:///tmp/memory','https://key:secret@example.com','https://example.com/?key=secret'])
def test_mem0_connection_configuration_avoids_insecure_secret_urls(url):
    with pytest.raises(ValueError): Mem0Index(url)


def test_mem0_invalid_add_response_is_not_marked_synced():
    index=Mem0Index('http://localhost:8888','',httpx.MockTransport(lambda request:httpx.Response(200,json={'results':[]})))
    with pytest.raises(MemoryIndexError,match='did not acknowledge'):
        index.add(type('Record',(),{'question':'Which date?','answer':'January 18','owner':'Lead','project_id':'p','id':'d','case_id':'c','source_fingerprint':'fingerprint'})())


def test_undo_during_remote_search_does_not_return_stale_memory(tmp_path):
    store=Store(str(tmp_path/'inflight.sqlite3'));project=store.create_project('Synora');case=earlier_review(store,project.id)
    decision=store.decisions(project.id)[0]
    def handler(request):
        if request.url.path=='/search':
            case.resolutions[0].revoked=True;store.save(case)
            return httpx.Response(200,json={'results':[{'metadata':{'contextguard_decision_id':decision.id}}]})
        return httpx.Response(200,json={})
    service=ProjectMemory(store,Mem0Index('http://localhost:8888','',httpx.MockTransport(handler)))
    try:
        result=service.recall(Case(project_id=project.id,title='Next review',goal='Confirm the pilot date'))
        assert result['decisions']==[]
    finally:
        service.close()


def test_analysis_receives_prior_context_without_resolving_current_findings(client,monkeypatch):
    from backend.app import main
    monkeypatch.setenv('MODEL_API_KEY','controlled-test-key')
    store=client.app.state.store;project=store.create_project('Synora');earlier_review(store,project.id)
    target=sample_case();target.mode='live';target.project_id=project.id;target.title='Controlled follow-up'
    store.save(target,create=True)
    captured=[]
    def controlled_analyze(case,progress):
        captured.extend(case.prior_decisions)
        evidence,candidates=fixture_candidates(case)
        return verify(case,case.criteria,evidence,candidates)
    monkeypatch.setattr(main,'analyze',controlled_analyze)
    response=client.post(f'/api/cases/{target.id}/analyze',json={'version':target.version})
    assert response.status_code==202
    reviewed=finish(client,target.id)
    assert len(captured)==1 and captured[0].answer.startswith('January 18')
    assert len(reviewed['report']['prior_decisions'])==1
    assert all(f['status']=='open' for f in reviewed['report']['findings'])
    assert 'Earlier project decisions considered' in client.get(f'/api/cases/{target.id}/brief').text
