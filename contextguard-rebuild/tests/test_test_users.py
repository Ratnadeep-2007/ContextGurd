import pytest

from app.review import Reviews
from app.service import Rejected
from app.storage import Store
from scripts.seed_test_users import NAMES, seed


@pytest.fixture
def seeded(tmp_path):
    reviews = Reviews(Store(tmp_path / 'assignment.sqlite3'))
    owner = reviews.create_user('Local owner', 'local-test-password')
    untouched = reviews.create_project(owner, 'Existing project')
    result, created = seed(reviews, owner)
    assert created
    assert reviews.store.get('project', untouched['id']) == untouched
    yield reviews, owner, result
    reviews.store.db.close()


def test_accounts_assignment_and_idempotence(seeded):
    reviews, owner, result = seeded
    assert len(result['accounts']) == 4 and len(result['projects']) == 2
    for account in result['accounts']:
        token = reviews.login(account['username'], account['password'])
        assert reviews.actor(token)['id'] == account['id']
        assert account['role'] == 'member'
    for project in result['projects']:
        review = reviews.get_review(owner, project['review_id'])
        assert review['test_mode'] and len(review['findings']) == 6
        assert all(f['assignee_id'] and f['state'] == 'open' for f in review['findings'])
        for citation in (c for f in review['findings'] for c in f['citations']):
            evidence = reviews.store.get('evidence', citation['evidence_id'])
            assert citation['quote'] in evidence['text'] and evidence['project_id'] == project['id']
    counts = {kind: len(reviews.store.all(kind)) for kind in ('user', 'project', 'source', 'review', 'evidence')}
    again, created = seed(reviews, owner)
    assert not created and again['id'] == result['id']
    assert all('password' not in account for account in again['accounts'])
    assert counts == {kind: len(reviews.store.all(kind)) for kind in counts}
    assert not reviews.store.all('decision')


def test_assignee_response_authority_and_project_isolation(seeded):
    reviews, owner, result = seeded
    review_owner, product, engineer, security = result['accounts']
    orchid, cedar = result['projects']
    review = reviews.get_review(engineer, orchid['review_id'])
    finding = next(f for f in review['findings'] if f['assignee_id'] == engineer['id'])
    with pytest.raises(Rejected):
        reviews.assign(engineer, review['id'], finding['id'], engineer['id'])
    with pytest.raises(Rejected):
        reviews.respond(security, review['id'], finding['id'], 'Answer from a different assignee.')
    reviews.respond(engineer, review['id'], finding['id'], 'The fictional service budget is approved.')
    with pytest.raises(Rejected):
        reviews.confirm(engineer, review['id'], finding['id'])
    saved = reviews.get_review(owner, review['id'])
    assert next(f for f in saved['findings'] if f['id'] == finding['id'])['state'] == 'open'
    decision = reviews.confirm(product, review['id'], finding['id'])
    assert decision['confirmed_by'] == product['id']
    with pytest.raises(Rejected):
        reviews.get_review(product, cedar['review_id'])
    with pytest.raises(Rejected):
        reviews.assign(review_owner, cedar['review_id'], cedar['assignments'][0]['finding_id'], product['id'])


def test_username_collision_rolls_back_without_changes(tmp_path):
    reviews = Reviews(Store(tmp_path / 'collision.sqlite3'))
    owner = reviews.create_user('Owner', 'local-test-password')
    reviews.create_user(NAMES[2], 'existing-test-password', owner)
    with pytest.raises(Rejected):
        seed(reviews, owner)
    assert len(reviews.store.all('user')) == 2
    assert not reviews.store.all('project')
    assert not reviews.store.all('test_fixture')
    reviews.store.db.close()


def test_seeded_accounts_over_http(tmp_path):
    from fastapi.testclient import TestClient
    from app.api import create_app

    path = tmp_path / 'http.sqlite3'
    service = Reviews(Store(path))
    owner = service.create_user('Owner', 'local-test-password')
    result, _ = seed(service, owner)
    service.store.db.close()
    with TestClient(create_app(path, load_settings=False)) as client:
        for account in result['accounts']:
            assert client.post('/api/login', json={'username': account['username'],
                                                   'password': account['password']}).status_code == 200
            assert client.get('/api/reviews/' + result['projects'][0]['review_id']).status_code == 200
            cedar = client.get('/api/reviews/' + result['projects'][1]['review_id'])
            assert cedar.status_code == (403 if account['username'] == NAMES[1] else 200)
