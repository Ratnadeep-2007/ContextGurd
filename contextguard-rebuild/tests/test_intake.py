import json
import time

import pytest
from fastapi.testclient import TestClient

from app.api import create_app
from app.contracts import ConversationRoutes, IntakeRequest
from app.intake import Intake
from app.providers import ProviderFailure
from app.service import Rejected
from app.storage import Store


@pytest.fixture
def env(tmp_path):
    service = Intake(Store(tmp_path / 'intake.sqlite3'))
    owner = service.create_user('Owner', 'fictional-password')
    orchid = service.create_project(owner, 'Orchid', 'Internal analytics pilot v2', 'Can the pilot proceed?')
    cedar = service.create_project(owner, 'Cedar', 'Security review of the mobile application')
    source = service.create_source(owner, 'manual', 'meeting', 'Fictional meeting')
    yield service, owner, orchid, cedar, source
    service.store.db.close()


def request(source, text, **overrides):
    return {'sources': [{'source_id': source['id'], 'passages': [{'item_id': 'm1', 'text': text,
             'location': 'Meeting, 00:01', 'author': 'Fictional speaker'}]}],
            'consent': True, 'test_mode': True, **overrides}


def run(env, text, **overrides):
    service, owner, _, _, source = env
    job, created = service.create_intake(owner, request(source, text, **overrides))
    assert created
    service.process_intake(job['id'])
    return service.store.get('intake', job['id'])


def test_mixed_project_conflicts_disposal_and_citations(env):
    service, owner, orchid, cedar, source = env
    job = run(env, 'Orchid: The pilot release is January 18. The pilot release is January 25.\n'
                   'How was your weekend? UNIQUE_UNRELATED_TEXT\nCedar: The security approval is pending.')
    assert job['status'] == 'complete', job['error']
    assert len(job['review_ids']) == 2 and job['discarded_units'] >= 1 and job['input'] == {}
    reviews = [service.get_review(owner, rid) for rid in job['review_ids']]
    assert {r['project_id'] for r in reviews} == {orchid['id'], cedar['id']}
    assert any(f['kind'] == 'potential_conflict' for r in reviews for f in r['findings'])
    for review in reviews:
        assert all(e['project_id'] == review['project_id'] and e['author'] == 'Fictional speaker' for e in review['evidence'])
        for finding in review['findings']:
            for citation in finding['citations']:
                evidence = service.store.get('evidence', citation['evidence_id'])
                assert citation['quote'] in evidence['text']
    content = json.dumps([service.store.all(k) for k in ('intake', 'source_event', 'evidence', 'review', 'source')])
    assert 'UNIQUE_UNRELATED_TEXT' not in content
    assert not service.visible_evidence(owner, unknown=True)


def test_unrelated_only_does_not_read_memory(env, monkeypatch):
    service, owner, *_ = env
    monkeypatch.setattr(service, 'decisions', lambda *a: pytest.fail('Unrelated input read project memory'))
    job = run(env, 'How was your weekend?')
    assert job['status'] == 'complete' and not job['review_ids'] and job['input'] == {}
    assert not service.store.all('evidence') and job['discarded_units'] == 1


def test_provider_failure_retains_complete_input_and_retry(env):
    service, owner, _, _, source = env
    class Broken:
        def classify(self, *args):
            raise ProviderFailure('Controlled provider unavailable')
    service.providers = Broken()
    job = run(env, 'Orchid must be fast.', test_mode=False, model_consent=True)
    assert job['status'] == 'failed' and job['input']['sources'][0]['passages'][0]['text'] == 'Orchid must be fast.'
    assert not service.store.all('evidence')
    # An explicit retry cannot discard or fabricate data after a provider failure.
    service.retry_intake(owner, job['id'])
    service.process_intake(job['id'])
    assert service.store.get('intake', job['id'])['status'] == 'failed'
    again, queued = service.create_intake(owner, request(source, 'Orchid must be fast.', test_mode=False, model_consent=True))
    assert queued and again['id'] == job['id'] and len(service.store.all('intake')) == 1


def test_each_explicit_or_duplicate_retry_starts_a_new_attempt_clock(env, monkeypatch):
    service, owner, _, _, source = env
    class Broken:
        def classify(self, *args):
            raise ProviderFailure('Controlled provider unavailable')
    service.providers = Broken()
    job = run(env, 'Orchid must be fast.', test_mode=False, model_consent=True)
    assert job['attempt'] == 1 and job['attempt_started'] == job['created']
    original = '2026-10-26T06:46:00+00:00'
    job.update(created=original)
    service.store.put('intake', job)
    monkeypatch.setattr('app.intake.now', lambda: '2026-10-26T10:31:00+00:00')
    retried = service.retry_intake(owner, job['id'])
    assert retried['created'] == original and retried['attempt'] == 2
    assert retried['attempt_started'] == retried['updated'] == '2026-10-26T10:31:00+00:00'
    assert retried['units_processed'] == retried['analysis_done'] == 0
    service.process_intake(job['id'])
    monkeypatch.setattr('app.intake.now', lambda: '2026-10-26T10:35:00+00:00')
    duplicate, queued = service.create_intake(owner, request(source, 'Orchid must be fast.', test_mode=False, model_consent=True))
    assert queued and duplicate['id'] == job['id'] and duplicate['created'] == original
    assert duplicate['attempt'] == 3 and duplicate['attempt_started'] == '2026-10-26T10:35:00+00:00'


@pytest.mark.parametrize('bad', ['missing', 'duplicate', 'inaccessible'])
def test_invalid_model_coverage_or_project_never_discards(env, bad):
    service, owner, orchid, _, source = env
    class Bad:
        def classify(self, units, projects, context):
            routes = [{'unit_id': u['id'], 'disposition': 'matched', 'project_id': orchid['id'],
                       'reason': 'Controlled malformed routing'} for u in units]
            if bad == 'missing':
                routes = routes[:-1]
            elif bad == 'duplicate':
                routes[-1] = routes[0]
            else:
                routes[0]['project_id'] = 'not-authorized'
            return {'routes': routes}, 'Controlled provider'
    service.providers = Bad()
    job = run(env, 'Orchid starts Friday. The pilot release is January 18.', test_mode=False, model_consent=True)
    assert job['status'] == 'failed' and job['input']
    assert not service.store.all('evidence')


def test_complete_unicode_coverage_and_chunk_boundaries(env):
    service, owner, orchid, _, source = env
    text = 'Orchid — café launch!\n\n' + ('The pilot must be fast. ' * 92) + '\nEnd without punctuation'
    job = run(env, text, project_ids=[orchid['id']])
    assert job['status'] == 'complete', job['error']
    assert job['units_total'] == job['units_processed'] and job['units_processed'] > 90
    rows = service.visible_evidence(owner, orchid['id'])
    assert 'End without punctuation' in ' '.join(e['text'] for e in rows)


def test_explicit_candidates_permissions_privacy_and_idempotence(env):
    service, owner, orchid, cedar, source = env
    member = service.create_user('Member', 'fictional-password', owner)
    service.member(owner, orchid['id'], member['id'], 'reviewer')
    service.source_grants(owner, source['id'], [member['id']])
    with pytest.raises(Rejected):
        service.create_intake(member, request(source, 'Cedar security approval is pending.', project_ids=[cedar['id']]))
    payload = request(source, 'Orchid: The security approval is pending.', project_ids=[orchid['id']], share=True)
    job, _ = service.create_intake(member, payload)
    service.process_intake(job['id'])
    second, created = service.create_intake(member, payload)
    assert not created and second['id'] == job['id']
    assert len(service.store.all('review')) == 1
    assert 'input' not in service.intake(member, job['id'])
    stranger = service.create_user('Stranger', 'fictional-password', owner)
    with pytest.raises(Rejected):
        service.intake(stranger, job['id'])


def poll(client, job_id):
    for _ in range(120):
        job = client.get('/api/intakes/' + job_id).json()
        if job['status'] in {'failed', 'complete'}:
            return job
        time.sleep(.01)
    pytest.fail('Fictional intake did not finish')


def test_http_upload_auto_registration_filters_and_exports(tmp_path):
    with TestClient(create_app(tmp_path / 'http.sqlite3', load_settings=False)) as client:
        client.post('/api/setup', json={'username': 'Owner', 'password': 'fictional-password'})
        client.post('/api/login', json={'username': 'Owner', 'password': 'fictional-password'})
        project = client.post('/api/command', json={'action': 'project', 'payload': {'name': 'Orchid',
                              'description': 'Internal pilot'}}).json()
        response = client.post('/api/intakes/upload', data={'consent': 'true', 'test_mode': 'true',
            'project_ids': json.dumps([project['id']])}, files=[
                ('files', ('brief.md', b'Orchid: The pilot release is January 18.')),
                ('files', ('spec.md', b'Orchid: The pilot release is January 25.'))])
        assert response.status_code == 202, response.text
        job = poll(client, response.json()['id'])
        assert job['status'] == 'complete', job
        assert 'input' not in job and len(job['review_ids']) == 1
        rid = job['review_ids'][0]
        filtered = client.get('/api/reviews', params={'project_id': project['id'], 'status': 'open'}).json()
        assert [r['id'] for r in filtered] == [rid]
        assert client.get('/api/reviews?status=recorded').json() == []
        review = client.get('/api/reviews/' + rid).json()
        finding = review['findings'][0]
        payload = {'review_id': rid, 'finding_id': finding['id'], 'answer': 'Use January 25 for this fictional pilot.'}
        assert client.post('/api/command', json={'action': 'respond', 'payload': payload}).status_code == 200
        assert client.post('/api/command', json={'action': 'confirm', 'payload': payload}).status_code == 200
        markdown = client.get('/api/reviews/' + rid + '/document?format=md')
        assert 'Use January 25' in markdown.text and 'Confirmed by Owner' in markdown.text
        word = client.get('/api/reviews/' + rid + '/document')
        assert word.status_code == 200 and word.content[:2] == b'PK'
        assert client.get('/api/reviews?status=recorded').json()[0]['id'] == rid


def test_model_consent_and_parse_failures_do_not_start_jobs(tmp_path):
    with TestClient(create_app(tmp_path / 'http.sqlite3', load_settings=False)) as client:
        client.post('/api/setup', json={'username': 'Owner', 'password': 'fictional-password'})
        client.post('/api/login', json={'username': 'Owner', 'password': 'fictional-password'})
        client.post('/api/command', json={'action': 'project', 'payload': {'name': 'Orchid'}})
        assert client.post('/api/intakes/text', json={'text': 'Orchid launch.', 'consent': True}).status_code == 403
        response = client.post('/api/intakes/upload', data={'consent': 'true', 'test_mode': 'true'},
                               files={'files': ('bad.exe', b'not supported')})
        assert response.status_code == 400
        assert not client.app.state.service.store.all('intake')


def test_source_revision_retires_removed_passages_and_preserves_decision_history(env):
    service, owner, orchid, _, source = env
    first = run(env, 'Orchid: The pilot release is January 18. The pilot release is January 25.', project_ids=[orchid['id']])
    review = service.get_review(owner, first['review_ids'][0])
    finding = review['findings'][0]
    service.respond(owner, review['id'], finding['id'], 'Use January 25 for the fictional pilot.')
    decision = service.confirm(owner, review['id'], finding['id'])
    second = run(env, 'Orchid: The pilot release is January 25.', project_ids=[orchid['id']])
    assert second['status'] == 'complete'
    assert service.get_review(owner, review['id'])['stale']
    current = service.visible_evidence(owner, orchid['id'])
    assert not any('January 18' in e['text'] for e in current)
    assert service.store.get('decision', decision['id'])['text'] == decision['text']
    with pytest.raises(Rejected):
        service.brief(owner, review['id'])


def test_controlled_model_routes_then_analyzes_without_fixture_fallback(env):
    service, owner, orchid, cedar, source = env
    calls = []
    class Controlled:
        def classify(self, units, projects, context):
            assert {p['id'] for p in projects} == {orchid['id'], cedar['id']}
            assert 'description' in projects[0]
            calls.append('route')
            return ConversationRoutes(routes=[{'unit_id': u['id'], 'disposition': 'matched',
                'project_id': orchid['id'], 'reason': 'Controlled model recognized the pilot context.'} for u in units]), 'Controlled model'
        def analyze(self, goal, evidence, decisions):
            assert calls == ['route'] and all(e['project_id'] == orchid['id'] for e in evidence)
            calls.append('analyze')
            return service.fixture(evidence), 'Controlled model'
    service.providers = Controlled()
    job = run(env, 'The pilot release is January 18. The pilot release is January 25.', test_mode=False, model_consent=True)
    assert job['status'] == 'complete' and calls == ['route', 'analyze']
    assert service.get_review(owner, job['review_ids'][0])['provider'] == 'Controlled model'


@pytest.mark.parametrize('link,expected', [
    ('https://meet.google.com/abc-defg-hij', ('google_meet', 'abc-defg-hij', None)),
    ('https://us05web.zoom.us/j/12345678901?pwd=private-pass', ('zoom', '12345678901', 'private-pass')),
    ('https://teams.microsoft.com/meet/123456789012?p=private-pass', ('teams', '123456789012', 'private-pass')),
])
def test_meeting_link_conversion(link, expected):
    from app.adapters import meeting_link
    assert meeting_link(link) == expected


@pytest.mark.parametrize('link', ['http://meet.google.com/abc-defg-hij', 'https://meet.google.com.evil.test/abc-defg-hij',
                                 'https://meet.google.com@evil.test/abc-defg-hij', 'https://127.0.0.1/abc-defg-hij',
                                 'https://[invalid-host', 'https://zoom.us:invalid/j/12345678901'])
def test_meeting_link_rejects_unsupported_hosts(link):
    from app.adapters import AdapterFailure, meeting_link
    with pytest.raises(AdapterFailure):
        meeting_link(link)


def test_connection_controls_consent_and_passcode_privacy(tmp_path, monkeypatch):
    from app import intake_api
    actions = []
    class FakeVexa:
        def __init__(self, *a, **kw):
            pass
        def join(self, platform, meeting_id, consent, passcode):
            actions.append((platform, meeting_id, passcode))
            return {'status': 'requested', 'note': 'Admission not confirmed'}
        def status(self):
            return [{'platform': 'zoom', 'native_meeting_id': '12345678901', 'status': 'awaiting_admission'}]
    monkeypatch.setattr(intake_api, 'Vexa', FakeVexa)
    with TestClient(create_app(tmp_path / 'meeting.sqlite3', load_settings=False)) as client:
        client.post('/api/setup', json={'username': 'Owner', 'password': 'fictional-password'})
        client.post('/api/login', json={'username': 'Owner', 'password': 'fictional-password'})
        payload = {'link': 'https://zoom.us/j/12345678901?pwd=hidden-passcode', 'operation': 'join'}
        assert client.post('/api/meetings', json=payload).status_code == 403
        assert not actions
        response = client.post('/api/meetings', json={**payload, 'consent': True})
        assert response.status_code == 200 and response.json()['status'] == 'requested'
        assert actions == [('zoom', '12345678901', 'hidden-passcode')]
        assert client.post('/api/connections/vexa/check', json={}).status_code == 200
        state = client.get('/api/state').json()
        assert state['sources'][0]['last_bot_status'] == 'awaiting_admission'
        assert 'hidden-passcode' not in json.dumps(state)
        assert not client.app.state.service.store.all('intake')


def test_observed_source_deletion_retires_passages_without_model_or_memory(env, monkeypatch):
    service, owner, orchid, _, source = env
    first = run(env, 'Orchid: The security approval is pending.', project_ids=[orchid['id']])
    payload = request(source, '', project_ids=[orchid['id']])
    payload['sources'][0]['passages'][0]['deleted'] = True
    job, _ = service.create_intake(owner, payload)
    monkeypatch.setattr(service.providers, 'classify', lambda *a: pytest.fail('Deleted text sent to model'))
    monkeypatch.setattr(service, 'decisions', lambda *a: pytest.fail('Deleted text read project memory'))
    service.process_intake(job['id'])
    assert service.store.get('intake', job['id'])['status'] == 'complete'
    assert not service.visible_evidence(owner, orchid['id'])
    assert service.get_review(owner, first['review_ids'][0])['stale']


def test_explicit_scope_does_not_route_other_project_by_similarity(env):
    service, owner, orchid, cedar, _ = env
    job = run(env, 'Cedar: The security approval is pending.', project_ids=[orchid['id']])
    assert job['status'] == 'complete' and not job['review_ids']
    assert not service.visible_evidence(owner, orchid['id'])
    assert not service.visible_evidence(owner, cedar['id'])


def test_approved_mapping_bounds_automatic_routes_but_explicit_choice_overrides(env):
    service, owner, orchid, cedar, source = env
    service.map_source(owner, source['id'], orchid['id'])
    automatic = run(env, 'Cedar: The security approval is pending.')
    assert automatic['status'] == 'complete' and not automatic['review_ids']
    explicit = run(env, 'Cedar: The security approval is pending.', project_ids=[cedar['id']])
    assert explicit['status'] == 'complete'
    assert service.get_review(owner, explicit['review_ids'][0])['project_id'] == cedar['id']


def test_source_revocation_during_model_call_prevents_memory_and_disposal(env):
    service, owner, orchid, cedar, source = env
    member = service.create_user('Member', 'fictional-password', owner)
    service.member(owner, orchid['id'], member['id'], 'reviewer')
    service.source_grants(owner, source['id'], [member['id']])
    class Revoking:
        def classify(self, units, projects, context):
            service.source_grants(owner, source['id'], [])
            return ConversationRoutes(routes=[{'unit_id': u['id'], 'disposition': 'matched',
                'project_id': orchid['id'], 'reason': 'Controlled model route'} for u in units]), 'Controlled'
        def analyze(self, *args):
            pytest.fail('Analysis must not run after source access is revoked')
    service.providers = Revoking()
    job, _ = service.create_intake(member, request(source, 'Orchid is ready.', test_mode=False, model_consent=True))
    service.process_intake(job['id'])
    saved = service.store.get('intake', job['id'])
    assert saved['status'] == 'failed' and saved['input']
    assert not service.store.all('review') and not service.store.all('evidence')
