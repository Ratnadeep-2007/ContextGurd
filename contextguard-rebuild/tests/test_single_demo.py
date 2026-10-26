import pytest

from app.review import Reviews
from app.service import Rejected
from app.storage import Store
from scripts.reset_demo import consolidate, FIXTURE
from test_api import client, login, cmd


def test_single_demo_cleanup_preserves_admin_and_reuses_one_review(tmp_path):
    service = Reviews(Store(tmp_path / 'single.sqlite3'))
    owner = service.create_user('ratnadeep', 'fictional-owner-password')
    project = service.create_project(owner, 'synora')
    old = service.create_project(owner, 'Orchid - fictional pilot')
    source = service.create_source(owner, 'manual', 'old-demo', 'Old fictional sample')
    service.ingest(owner, {'source_id': source['id'], 'project_id': old['id'], 'test_mode': True,
        'consent': True, 'passages': [{'item_id': '1', 'text': 'Fictional pilot notes.'}]})
    result = consolidate(service, owner, project['id'])
    assert [p['id'] for p in service.store.all('project')] == [project['id']]
    assert result['project']['demo_fixture'] == FIXTURE
    assert len(result['review']['findings']) == 6
    assert all(f['assignee_id'] and f['state'] == 'open' for f in result['review']['findings'])
    assert len(result['accounts']) == 4
    assert [u['id'] for u in service.store.all('user') if u['role'] == 'owner'] == [owner['id']]
    assert [uid for uid, role in result['project']['members'].items() if role == 'owner'] == [owner['id']]
    again = consolidate(service, owner, project['id'])
    assert again['review']['id'] == result['review']['id']
    assert len(service.store.all('review')) == 1 and len(service.store.all('source')) == 3
    service.store.db.close()


def test_cleanup_refuses_real_content_and_rolls_back(tmp_path):
    service = Reviews(Store(tmp_path / 'protected.sqlite3'))
    owner = service.create_user('ratnadeep', 'fictional-owner-password')
    project = service.create_project(owner, 'synora')
    old = service.create_project(owner, 'Orchid - fictional pilot')
    source = service.create_source(owner, 'manual', 'real-source', 'User document')
    service.ingest(owner, {'source_id': source['id'], 'project_id': old['id'], 'consent': True,
                           'passages': [{'item_id': '1', 'text': 'An actual user note.'}]})
    with pytest.raises(Rejected):
        consolidate(service, owner, project['id'])
    assert len(service.store.all('project')) == 2 and len(service.store.all('evidence')) == 1
    assert len(service.store.all('user')) == 1
    service.store.db.close()


def test_sample_action_is_idempotent(client):
    login(client)
    first = cmd(client, 'demo')
    second = cmd(client, 'demo')
    assert first['project']['id'] == second['project']['id'] and first['source_ids'] == second['source_ids']
