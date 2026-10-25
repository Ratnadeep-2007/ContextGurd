import json

import httpx
import pytest

from app.contracts import Analysis
from app.providers import ProviderFailure, Providers
from app.review import Reviews
from app.service import Rejected
from test_routing import env, ingest


def setup(env):
    s, a, b, p, q, source = env
    r = Reviews(s.store)
    s.member(a, p['id'], b['id'], 'reviewer')
    source['allowed_users'].append(b['id'])
    s.store.put('source', source)
    rows = s.ingest(a, {'source_id': source['id'], 'project_id': p['id'], 'consent': True, 'test_mode': True,
                       'passages': [{'item_id': 'a', 'text': 'The pilot release is January 18.'},
                                    {'item_id': 'b', 'text': 'The pilot release is January 25.'}]})
    review = r.analyze(a, p['id'], 'Can the pilot proceed?', [source['id']], test_mode=True)
    return r, a, b, p, q, source, rows, review


def test_full_decision_and_immutable_memory(env):
    r, a, b, p, q, source, rows, review = setup(env)
    f = review['findings'][0]
    assert review['readiness'] == 'Needs clarification'
    r.assign(a, review['id'], f['id'], b['id'])
    r.respond(b, review['id'], f['id'], 'Use January 18 for the pilot.')
    assert r.get_review(a, review['id'])['findings'][0]['state'] == 'open'
    with pytest.raises(Rejected):
        r.confirm(b, review['id'], f['id'])
    decision = r.confirm(a, review['id'], f['id'])
    assert decision['confirmed_by'] == a['id']
    assert r.get_review(a, review['id'])['readiness'] == 'Ready'
    assert not r.decisions(a, q['id'])
    assert 'Use January 18' in r.brief(a, review['id'])


def test_review_owner_only_assignment_and_responsibility(env):
    r, a, b, p, q, source, rows, review = setup(env)
    with pytest.raises(Rejected):
        r.assign(b, review['id'], review['findings'][0]['id'], b['id'])
    r.responsibility(a, p['id'], 'pilot', b['id'])
    new = r.analyze(a, p['id'], 'Check pilot readiness', [source['id']], test_mode=True)
    assert new['findings'][0]['suggested_assignee_id'] == b['id']
    assert new['findings'][0]['assignee_id'] is None


def test_changed_sources_block_confirmation_and_export(env):
    r, a, b, p, q, source, rows, review = setup(env)
    f = review['findings'][0]
    r.respond(a, review['id'], f['id'], 'Need to ask finance; currently unknown.')
    r.ingest(a, {'source_id': source['id'], 'consent': True, 'test_mode': True,
                 'passages': [{'item_id': 'a', 'text': 'Changed schedule.'}]})
    assert r.get_review(a, review['id'])['stale']
    with pytest.raises(Rejected):
        r.confirm(a, review['id'], f['id'])
    with pytest.raises(Rejected):
        r.brief(a, review['id'])


def test_false_conflict_downgrade_and_invalid_quotes(env):
    r, a, b, p, q, source, rows, review = setup(env)
    proposed = {k: v for k, v in review['findings'][0].items() if k in Analysis.model_fields['findings'].annotation.__args__[0].model_fields}
    proposed['same_version'] = False
    assert r.verified(proposed, rows, [])['kind'] == 'clarification_needed'
    proposed['citations'][0]['quote'] = 'A fabricated quote.'
    with pytest.raises(Rejected):
        r.verified(proposed, rows, [])


def test_failed_provider_does_not_fabricate(env):
    r, a, b, p, q, source, rows, review = setup(env)
    class Broken:
        def analyze(self, *args):
            raise ProviderFailure('Provider unavailable')
    r.providers = Broken()
    result = r.analyze(a, p['id'], 'Check pilot readiness', [source['id']], consent=True)
    assert result['status'] == 'failed' and result['findings'] == []


def test_unassigned_content_is_left_without_model_or_memory_lookup(env, monkeypatch):
    s, actor, other, project, second, source = env
    rows = ingest(env)
    reviews = Reviews(s.store)

    def forbidden(*args, **kwargs):
        raise AssertionError('Unassigned content must not trigger model or memory lookup')

    monkeypatch.setattr(reviews, 'decisions', forbidden)
    monkeypatch.setattr(reviews.providers, 'analyze', forbidden)
    result = reviews.analyze(actor, project['id'], 'Check our pilot readiness', [source['id']], consent=True)
    assert result['status'] == 'failed'
    assert result['evidence'] == result['memory'] == result['findings'] == []
    saved = s.store.get('evidence', rows['id'])
    assert saved['routing'] == 'unknown' and saved['project_id'] is None


def test_supersede_and_conflicting_new_review_links_prior_decision(env):
    r, a, b, p, q, source, rows, review = setup(env)
    f = review['findings'][0]
    r.respond(a, review['id'], f['id'], 'Use January 18.')
    first = r.confirm(a, review['id'], f['id'])
    class Linked:
        def analyze(self, goal, evidence, decisions):
            assert decisions[0]['id'] == first['id']
            proposal = {k: v for k, v in f.items() if k in Analysis.model_fields['findings'].annotation.__args__[0].model_fields}
            proposal['decision_ids'] = [first['id']]
            return Analysis(findings=[proposal], limitations=['Controlled provider test.']), 'Controlled'
    r.providers = Linked()
    second_review = r.analyze(a, p['id'], 'Review the new date', [source['id']], consent=True)
    f2 = second_review['findings'][0]
    assert f2['state'] == 'open' and f2['decision_ids'] == [first['id']]
    r.respond(a, second_review['id'], f2['id'], 'Use January 25 instead.')
    second = r.confirm(a, second_review['id'], f2['id'], supersedes=first['id'])
    assert second['supersedes'] == first['id']
    assert r.store.get('decision', first['id'])['text'] == 'Use January 18.'


def test_provider_fallback_and_schema_validation(monkeypatch):
    monkeypatch.setenv('MODEL_API_KEY', 'test-secret')
    monkeypatch.setenv('MODEL_BASE_URL', 'https://meta.example/v1')
    monkeypatch.setenv('MODEL_NAME', 'configured-model')
    monkeypatch.setenv('GROQ_API_KEY', 'test-groq')
    urls = []
    def handler(req):
        urls.append(req.url.host)
        if req.url.host == 'meta.example':
            return httpx.Response(200, json={'choices': [{'message': {'content': 'invalid json'}}]})
        return httpx.Response(200, json={'choices': [{'message': {'content': json.dumps({'findings': [], 'limitations': ['Controlled test']})}}]})
    result, provider = Providers(httpx.MockTransport(handler)).analyze('goal', [], [])
    assert provider == 'Groq' and len(urls) == 2


def test_provider_retries_transient_quota_response_once(monkeypatch):
    monkeypatch.setenv('MODEL_API_KEY', 'test-secret')
    monkeypatch.setenv('MODEL_BASE_URL', 'https://meta.example/v1')
    monkeypatch.setenv('MODEL_NAME', 'configured-model')
    monkeypatch.setenv('GROQ_API_KEY', '')
    calls = []
    def handler(req):
        calls.append(req.url.host)
        if len(calls) == 1:
            return httpx.Response(429, headers={'Retry-After': '0'}, json={'error': 'quota'})
        return httpx.Response(200, json={'choices': [{'message': {'content': json.dumps({'findings': [], 'limitations': ['Controlled test']})}}]})
    result, provider = Providers(httpx.MockTransport(handler)).analyze('goal', [], [])
    assert provider == 'Muse Wonder' and len(calls) == 2


def test_no_unknown_memory_leak(env):
    r, a, b, p, q, source, rows, review = setup(env)
    unknown_source = r.create_source(a, 'manual', 'unknown', 'Unknown')
    r.ingest(a, {'source_id': unknown_source['id'], 'consent': True, 'test_mode': True,
                 'passages': [{'item_id': 'x', 'text': 'The pilot release is January 18.'}]})
    empty = r.analyze(a, q['id'], 'Check project readiness', [unknown_source['id']], test_mode=True)
    assert empty['status'] == 'failed' and not empty['memory'] and not empty['evidence']


def test_unknown_answer_cannot_be_confirmed(env):
    r, a, b, p, q, source, rows, review = setup(env)
    f = review['findings'][0]
    r.respond(a, review['id'], f['id'], 'We do not know; ask the sponsor.', answer_known=False)
    with pytest.raises(Rejected):
        r.confirm(a, review['id'], f['id'])
    assert r.get_review(a, review['id'])['findings'][0]['state'] == 'open'


def test_explicit_different_milestones_overrides_model_claim(env):
    r, a, b, p, q, source, rows, review = setup(env)
    proposed = {k: v for k, v in review['findings'][0].items() if k in Analysis.model_fields['findings'].annotation.__args__[0].model_fields}
    rows[0]['details']['milestone'] = 'pilot'
    rows[1]['details']['milestone'] = 'public launch'
    assert r.verified(proposed, rows, [])['kind'] == 'clarification_needed'
