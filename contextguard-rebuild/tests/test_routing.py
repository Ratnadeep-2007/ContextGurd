import pytest

from app.service import Rejected, Service
from app.storage import Store


@pytest.fixture
def env(tmp_path):
    service = Service(Store(tmp_path / 'test.sqlite3'))
    owner = service.create_user('Alex', 'test-password-123')
    other = service.create_user('Jamie', 'another-test-pass', owner)
    p = service.create_project(owner, 'Orchid')
    q = service.create_project(owner, 'Cedar')
    source = service.create_source(owner, 'manual', 'brief', 'Brief')
    return service, owner, other, p, q, source


def ingest(env, **kw):
    s, a, b, p, q, source = env
    return s.ingest(a, {'source_id': source['id'], 'consent': True,
                        'passages': [{'item_id': 'one', 'text': 'Orchid pilot starts on January 18.'}], **kw})[0]


def test_unknown_before_memory_and_suggestions(env):
    s, a, b, p, q, source = env
    e = ingest(env)
    assert e['routing'] == 'unknown' and not s.visible_evidence(a, p['id'])
    assert s.suggestions(a, e['id'])[0]['confirmed'] is False
    s.route(a, e['id'], p['id'])
    assert len(s.visible_evidence(a, p['id'])) == 1


def test_explicit_overrides_mapping(env):
    s, a, b, p, q, source = env
    s.map_source(a, source['id'], p['id'])
    e = ingest(env, project_id=q['id'])
    assert e['project_id'] == q['id']


def test_approved_mapping(env):
    s, a, b, p, q, source = env
    s.map_source(a, source['id'], p['id'])
    assert ingest(env)['project_id'] == p['id']


def test_unauthorized_source_and_project(env):
    s, a, b, p, q, source = env
    with pytest.raises(Rejected):
        s.ingest(b, {'source_id': source['id'], 'consent': True, 'project_id': p['id'], 'passages': [{'item_id': 'x', 'text': 'Private'}]})
    assert not s.store.all('evidence')
    shared = s.create_source(a, 'slack', 'C1', 'Shared', [b['id']])
    with pytest.raises(Rejected):
        s.ingest(b, {'source_id': shared['id'], 'consent': True, 'project_id': p['id'], 'passages': [{'item_id': 'x', 'text': 'Private'}]})


def test_dedup_revision_and_no_cross_project_duplicate(env):
    s, a, b, p, q, source = env
    e = ingest(env, project_id=p['id'])
    assert ingest(env, project_id=p['id'])['id'] == e['id']
    with pytest.raises(Rejected):
        ingest(env, project_id=q['id'])
    revised = ingest(env, project_id=p['id'], passages=[{'item_id': 'one', 'text': 'Orchid pilot starts on January 20.'}])
    assert revised['previous_id'] == e['id']
    assert not s.store.get('evidence', e['id'])['active']


def test_segment_keeps_original_and_dismiss(env):
    s, a, b, p, q, source = env
    e = ingest(env)
    segment = s.segment(a, e['id'], q['id'], 'pilot starts on January 18.')
    assert segment['parent_id'] == e['id'] and s.store.get('evidence', e['id'])['text'] == e['text']
    s.route(a, e['id'], action='dismiss')
    assert not s.visible_evidence(a, unknown=True)


def test_consent_and_unknown_project(env):
    s, a, b, p, q, source = env
    with pytest.raises(Rejected):
        ingest(env, project_id='nonexistent')
    with pytest.raises(Rejected):
        s.ingest(a, {'source_id': source['id'], 'passages': [{'item_id': 'x', 'text': 'hello'}]})


def test_cross_workspace_boundary(env):
    s, a, b, p, q, source = env
    fake = {**a, 'workspace': 'another-workspace'}
    with pytest.raises(Rejected):
        s.project(fake, p['id'])
    with pytest.raises(Rejected):
        s.source(fake, source['id'])
