"""Focused coverage: 413 splitting, bounded retries, cross-batch comparisons.

The Synora replay uses the exact documents from the failed live intake
(4af439e4c3fb4495857c1726d1c16d40: Muse timeout, Groq HTTP 413, NVIDIA 500,
stopped at 135/325 units) behind a controlled provider that rejects oversized
requests the same way, so no live keys are needed.
"""
import json
from pathlib import Path

import httpx
import pytest

from app.contracts import Analysis, ConversationRoutes
from app.intake import Intake
from app.providers import PayloadTooLarge, ProviderFailure, Providers
from app.review import Reviews
from app.storage import Store
from test_routing import env  # noqa: F401  (shared fixture, repo convention)


def _ok(payload):
    return httpx.Response(200, json={'choices': [{'message': {'content': json.dumps(payload)}}]})


def _muse_only(monkeypatch):
    monkeypatch.setenv('MODEL_API_KEY', 'test-secret')
    monkeypatch.setenv('MODEL_BASE_URL', 'https://meta.example/v1')
    monkeypatch.setenv('MODEL_NAME', 'configured-model')
    monkeypatch.setenv('GROQ_API_KEY', '')
    monkeypatch.setenv('NVIDIA_API_KEY', '')


def test_413_is_not_retried_with_the_same_payload(monkeypatch):
    _muse_only(monkeypatch)
    calls = []
    def handler(req):
        calls.append(1)
        return httpx.Response(413, json={'error': 'too large'})
    with pytest.raises(PayloadTooLarge) as caught:
        Providers(httpx.MockTransport(handler), sleep=lambda s: None).analyze('goal', [{'id': 'e1', 'text': 'x'}], [])
    assert len(calls) == 1, 'a 413 must trigger splitting, not a same-size retry'
    assert '413' in str(caught.value) and 'too large' in str(caught.value).casefold()


def test_transient_500_retries_are_bounded_then_succeed(monkeypatch):
    _muse_only(monkeypatch)
    calls, sleeps = [], []
    def handler(req):
        calls.append(1)
        if len(calls) < 3:
            return httpx.Response(500, json={'error': 'boom'})
        return _ok({'findings': [], 'limitations': ['Controlled test']})
    result, provider = Providers(httpx.MockTransport(handler), sleep=lambda s: sleeps.append(s)).analyze('goal', [], [])
    assert provider == 'Muse Wonder' and len(calls) == 3
    assert len(sleeps) == 2 and all(0 <= s <= 30 for s in sleeps)


def test_transient_500_gives_up_with_accurate_error(monkeypatch):
    _muse_only(monkeypatch)
    calls = []
    def handler(req):
        calls.append(1)
        return httpx.Response(500, json={'error': 'boom'})
    with pytest.raises(ProviderFailure) as caught:
        Providers(httpx.MockTransport(handler), sleep=lambda s: None).analyze('goal', [], [])
    assert len(calls) == 3, 'retries must be bounded'
    assert '500' in str(caught.value) and 'server error' in str(caught.value).casefold()


def test_read_timeout_is_retried_once_within_bound(monkeypatch):
    _muse_only(monkeypatch)
    calls = []
    def handler(req):
        calls.append(1)
        if len(calls) == 1:
            raise httpx.ReadTimeout('slow', request=req)
        return _ok({'findings': [], 'limitations': ['Controlled test']})
    result, provider = Providers(httpx.MockTransport(handler), sleep=lambda s: None).analyze('goal', [], [])
    assert provider == 'Muse Wonder' and len(calls) == 2


@pytest.fixture
def intake_env(tmp_path):
    service = Intake(Store(tmp_path / 'batching.sqlite3'))
    owner = service.create_user('Owner', 'fictional-password')
    orchid = service.create_project(owner, 'Orchid', 'Internal analytics pilot', 'Can the pilot proceed?')
    source = service.create_source(owner, 'manual', 'meeting', 'Fictional meeting')
    yield service, owner, orchid, source
    service.store.db.close()


def _run_intake(service, owner, source, text, project_id):
    job, created = service.create_intake(owner, {
        'sources': [{'source_id': source['id'], 'passages': [{'item_id': 'm1', 'text': text,
                     'location': 'Meeting, 00:01', 'author': 'Fictional speaker'}]}],
        'project_ids': [project_id], 'consent': True, 'model_consent': True, 'test_mode': False})
    assert created
    service.process_intake(job['id'])
    return service.store.get('intake', job['id'])


def test_routing_splits_after_413_and_completes(intake_env):
    service, owner, orchid, source = intake_env
    batch_sizes = []
    class Splitter:
        def classify(self, units, projects, context):
            batch_sizes.append(len(units))
            if len(units) > 6:
                raise PayloadTooLarge('Groq: request too large (HTTP 413)')
            return ConversationRoutes(routes=[{'unit_id': u['id'], 'disposition': 'matched',
                'project_id': orchid['id'], 'reason': 'Controlled split routing.'} for u in units]), 'Controlled'
        def analyze(self, goal, evidence, decisions, prior_findings=None):
            return Analysis(findings=[], limitations=['Controlled split analysis.']), 'Controlled'
    service.providers = Splitter()
    text = ' '.join(f'Orchid pilot note {i} proceeds with care.' for i in range(40))
    job = _run_intake(service, owner, source, text, orchid['id'])
    assert job['status'] == 'complete', job['error']
    assert job['units_processed'] == job['units_total'] == 40
    assert max(s for s in batch_sizes) > 6, 'the oversized first batch must have been attempted'
    assert job['analysis_total'] >= 1 and job['analysis_done'] == job['analysis_total']


def test_single_unit_413_fails_with_accurate_retained_error(intake_env):
    service, owner, orchid, source = intake_env
    class AlwaysLarge:
        def classify(self, units, projects, context):
            raise PayloadTooLarge('Groq: request too large (HTTP 413)')
    service.providers = AlwaysLarge()
    job = _run_intake(service, owner, source, 'Orchid pilot note proceeds with care.', orchid['id'])
    assert job['status'] == 'failed' and job['input'], 'complete input must be retained'
    assert '413' in job['error'] and 'split' in job['error'].casefold()


def test_analysis_batches_preserve_cross_document_conflict(env):  # noqa: F811
    service, actor, other, project, second, source = env
    reviews = Reviews(service.store)
    filler = ' Background detail for the pilot readiness discussion.' * 90
    rows = service.ingest(actor, {'source_id': source['id'], 'project_id': project['id'], 'consent': True,
        'test_mode': True, 'passages': [
            {'item_id': 'a', 'text': 'The pilot release is December 7, 2026.' + filler},
            {'item_id': 'b', 'text': 'The pilot release is January 18, 2027.' + filler}]})
    batches = []
    class CrossBatch:
        def analyze(self, goal, evidence, decisions, prior_findings=None):
            batches.append([e['id'] for e in evidence])
            current = {e['id']: e['text'] for e in evidence}
            prior_cites = [c for f in (prior_findings or []) for c in f['citations']]
            jan = next((e for e in evidence if 'January 18, 2027.' in e['text']), None)
            dec_prior = next((c for c in prior_cites if 'December 7, 2026.' in c['quote']), None)
            if jan is not None and dec_prior is not None:
                return Analysis(findings=[{'kind': 'potential_conflict', 'title': 'Pilot date disagreement',
                    'impact': 'The pilot cannot be scheduled on two dates.', 'question': 'Which date is approved?',
                    'next_action': 'Ask the decision owner to confirm one date.', 'priority': 'high',
                    'citations': [dec_prior, {'evidence_id': jan['id'], 'quote': 'The pilot release is January 18, 2027.'}],
                    'uncertainty': 'Controlled cross-batch comparison.', 'same_scope': True,
                    'same_version': True, 'same_period': True}], limitations=['Controlled cross-batch test.']), 'Controlled'
            dec = next((e for e in evidence if 'December 7, 2026.' in e['text']), None)
            findings = [] if dec is None else [{'kind': 'missing_information', 'title': 'Pilot date stated once',
                'impact': 'Only one side of the schedule is visible so far.', 'question': 'Is this date approved?',
                'next_action': 'Confirm the pilot date.', 'priority': 'medium',
                'citations': [{'evidence_id': dec['id'], 'quote': 'The pilot release is December 7, 2026.'}],
                'uncertainty': 'Controlled first-batch finding.', 'same_scope': True,
                'same_version': True, 'same_period': True}]
            return Analysis(findings=findings, limitations=['Controlled cross-batch test.']), 'Controlled'
    reviews.providers = CrossBatch()
    review = reviews.analyze(actor, project['id'], 'Can the pilot proceed?', [source['id']], consent=True)
    assert review['status'] == 'complete', review['failures']
    assert len(batches) == 2, 'the two documents must land in separate analysis batches'
    conflict = next(f for f in review['findings'] if f['kind'] == 'potential_conflict')
    cited = {c['evidence_id'] for c in conflict['citations']}
    assert cited == {rows[0]['id'], rows[1]['id']}, 'the conflict must cite both documents'


def test_synora_pack_replay_completes_despite_413s(intake_env):
    pack = Path(__file__).resolve().parents[2] / 'synora-review-pack'
    files = sorted(p for p in pack.glob('*.md')) + sorted(pack.glob('07-*.txt'))
    if len(files) < 7:
        pytest.skip('Synora sample pack is not present in this checkout.')
    service, owner, orchid, _ = intake_env
    project = service.create_project(owner, 'Synora', 'Project-intelligence workspace pilot', 'Can the pilot proceed?')
    sources = []
    for path in files:
        # Sources dedupe on (type, container): one container per file, like an upload.
        src = service.create_source(owner, 'manual', 'sample-' + path.stem, path.name)
        sources.append({'source_id': src['id'], 'passages': [{'item_id': path.stem,
                        'text': path.read_text(encoding='utf-8'), 'location': path.name, 'author': 'Sample pack'}]})
    splits = {'classify': 0, 'analyze': 0}
    class SynoraModels:
        def classify(self, units, projects, context):
            if len(units) > 8:
                splits['classify'] += 1
                raise PayloadTooLarge('Groq: request too large (HTTP 413)')
            return ConversationRoutes(routes=[{'unit_id': u['id'], 'disposition': 'matched',
                'project_id': project['id'], 'reason': 'Controlled Synora replay routing.'} for u in units]), 'Controlled'
        def analyze(self, goal, evidence, decisions, prior_findings=None):
            if sum(len(e['text']) for e in evidence) > 6000:
                splits['analyze'] += 1
                raise PayloadTooLarge('Groq: request too large (HTTP 413)')
            prior_cites = [c for f in (prior_findings or []) for c in f['citations']]
            dec = next((e for e in evidence if 'December 7, 2026' in e['text']), None)
            jan = next((e for e in evidence if 'January 18, 2027' in e['text']), None)
            prior_dec = next((c for c in prior_cites if 'December 7, 2026' in c['quote']), None)
            prior_jan = next((c for c in prior_cites if 'January 18, 2027' in c['quote']), None)
            def cite(e, needle):
                return {'evidence_id': e['id'], 'quote': needle}
            if jan is not None and prior_dec is not None:
                return Analysis(findings=[{'kind': 'potential_conflict', 'title': 'Pilot date disagreement',
                    'impact': 'The Synora pilot is scheduled on two different dates.',
                    'question': 'Which pilot date is approved?', 'next_action': 'Confirm one date with the project lead.',
                    'priority': 'high', 'citations': [prior_dec, cite(jan, 'January 18, 2027')],
                    'uncertainty': 'Controlled Synora replay.', 'same_scope': True, 'same_version': True,
                    'same_period': True}], limitations=['Controlled Synora replay.']), 'Controlled'
            if dec is not None and prior_jan is not None:
                return Analysis(findings=[{'kind': 'potential_conflict', 'title': 'Pilot date disagreement',
                    'impact': 'The Synora pilot is scheduled on two different dates.',
                    'question': 'Which pilot date is approved?', 'next_action': 'Confirm one date with the project lead.',
                    'priority': 'high', 'citations': [prior_jan, cite(dec, 'December 7, 2026')],
                    'uncertainty': 'Controlled Synora replay.', 'same_scope': True, 'same_version': True,
                    'same_period': True}], limitations=['Controlled Synora replay.']), 'Controlled'
            if dec is not None and jan is not None:
                return Analysis(findings=[{'kind': 'potential_conflict', 'title': 'Pilot date disagreement',
                    'impact': 'The Synora pilot is scheduled on two different dates.',
                    'question': 'Which pilot date is approved?', 'next_action': 'Confirm one date with the project lead.',
                    'priority': 'high', 'citations': [cite(dec, 'December 7, 2026'), cite(jan, 'January 18, 2027')],
                    'uncertainty': 'Controlled Synora replay.', 'same_scope': True, 'same_version': True,
                    'same_period': True}], limitations=['Controlled Synora replay.']), 'Controlled'
            single = dec or jan
            findings = [] if single is None else [{'kind': 'missing_information', 'title': 'Pilot date stated',
                'impact': 'One pilot date is visible; approval is not shown.', 'question': 'Is this date approved?',
                'next_action': 'Confirm the pilot date.', 'priority': 'medium',
                'citations': [cite(single, 'December 7, 2026' if single is dec else 'January 18, 2027')],
                'uncertainty': 'Controlled Synora replay.', 'same_scope': True, 'same_version': True,
                'same_period': True}]
            return Analysis(findings=findings, limitations=['Controlled Synora replay.']), 'Controlled'
    service.providers = SynoraModels()
    job, created = service.create_intake(owner, {'sources': sources, 'project_ids': [project['id']],
        'consent': True, 'model_consent': True, 'test_mode': False})
    assert created
    service.process_intake(job['id'])
    job = service.store.get('intake', job['id'])
    assert job['status'] == 'complete', job['error']
    assert job['units_processed'] == job['units_total'] > 100
    assert splits['classify'] > 0 and splits['analyze'] > 0, 'both stages must have split after 413s'
    review = service.get_review(owner, job['review_ids'][0])
    conflict = next(f for f in review['findings'] if f['kind'] == 'potential_conflict')
    cited_sources = {service.store.get('evidence', c['evidence_id'])['source_id'] for c in conflict['citations']}
    assert len(cited_sources) >= 2, 'the consolidated Synora date conflict must cite both source sides'
