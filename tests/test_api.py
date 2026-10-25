import pytest
from fastapi.testclient import TestClient

from app.api import create_app


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(tmp_path / 'api.sqlite3', load_settings=False)) as c:
        yield c


def login(client):
    assert client.post('/api/setup', json={'username': 'Alex', 'password': 'fictional-password'}).status_code == 200
    assert client.post('/api/login', json={'username': 'Alex', 'password': 'fictional-password'}).status_code == 200


def cmd(client, action, payload=None):
    response = client.post('/api/command', json={'action': action, 'payload': payload or {}})
    assert response.status_code == 200, response.text
    return response.json()


def test_complete_api_flow_and_reload(client):
    login(client)
    demo = cmd(client, 'demo')
    review = cmd(client, 'analyze', {'project_id': demo['project']['id'], 'goal': 'Can this fictional pilot proceed?', 'source_ids': demo['source_ids'], 'test_mode': True})
    assert len(review['findings']) == 6
    for finding in review['findings']:
        for citation in finding['citations']:
            e = next(e for e in review['evidence'] if e['id'] == citation['evidence_id'])
            assert citation['quote'] in e['text']
    f = review['findings'][0]
    cmd(client, 'respond', {'review_id': review['id'], 'finding_id': f['id'], 'answer': 'Use January 18 for this pilot.'})
    cmd(client, 'confirm', {'review_id': review['id'], 'finding_id': f['id']})
    again = client.get('/api/reviews/' + review['id']).json()
    assert again['findings'][0]['state'] == 'resolved'
    brief = client.get('/api/reviews/' + review['id'] + '/brief')
    assert brief.status_code == 200 and 'Use January 18' in brief.text and 'Fictional' in brief.text


def test_auth_csrf_and_no_secret_echo(client):
    assert client.get('/api/state').status_code == 401
    assert client.post('/api/setup', json={'username': 'A', 'password': 'secret-sensitive'}).status_code == 422
    response = client.post('/api/setup', json={'username': 'A', 'password': 'secret-sensitive'})
    assert 'secret-sensitive' not in response.text
    login(client)
    assert client.post('/api/command', headers={'Origin': 'https://evil.example'}, json={'action': 'demo'}).status_code == 403
    assert client.get('/api/state', headers={'Host': 'evil.example'}).status_code == 403
    assert 'HttpOnly' in client.post('/api/login', json={'username': 'Alex', 'password': 'fictional-password'}).headers['set-cookie']


def test_unknown_upload_and_parsing_failure(client):
    login(client)
    source = cmd(client, 'source', {'type': 'manual', 'container': 'doc1', 'label': 'Test document'})
    parsed = client.post('/api/upload', data={'source_id': source['id'], 'consent': 'true'}, files={'file': ('notes.md', b'Selected project notes.')})
    assert parsed.json()['evidence'][0]['routing'] == 'unknown'
    failed = client.post('/api/upload', data={'source_id': source['id'], 'consent': 'true'}, files={'file': ('bad.pdf', b'bad pdf')})
    assert failed.json()['evidence'][0]['extraction'] == 'failed'
    assert len(client.get('/api/state').json()['unknown']) == 2


def test_oauth_scopes_state_and_replay_guard(client, monkeypatch):
    login(client)
    monkeypatch.setenv('SLACK_CLIENT_ID', 'fictional-client')
    monkeypatch.setenv('SLACK_CLIENT_SECRET', 'fictional-secret')
    result = client.post('/api/slack/connect').json()
    assert 'channels%3Aread%2Cchannels%3Ahistory' in result['url'] and 'chat%3Awrite' not in result['url']
    assert client.get('/api/slack/callback?state=wrong&code=test').status_code == 403


def test_no_vexa_join_without_consent_or_key(client, monkeypatch):
    login(client)
    for name in ('VEXA_API_KEY', 'VEXA_BOT_KEY', 'VEXA_TX_KEY'):
        monkeypatch.delenv(name, raising=False)
    source = cmd(client, 'source', {'type': 'vexa', 'container': 'google_meet:abc-defg-hij', 'label': 'Selected meeting'})
    assert client.post('/api/command', json={'action': 'vexa_join', 'payload': {'source_id': source['id']}}).status_code == 403
    assert client.post('/api/command', json={'action': 'vexa_join', 'payload': {'source_id': source['id'], 'consent': True}}).status_code == 409


def test_slack_oauth_pull_pipeline_and_replay(client, monkeypatch):
    import httpx
    from urllib.parse import parse_qs, urlsplit
    from app import api
    login(client)
    monkeypatch.setenv('SLACK_CLIENT_ID', 'fictional-client')
    monkeypatch.setenv('SLACK_CLIENT_SECRET', 'fictional-secret')
    # Controlled protector lets us test OAuth state/pull wiring when Windows DPAPI is denied.
    monkeypatch.setattr(api, 'transform', lambda value, decrypt=False: 'synthetic-oauth-token' if decrypt else 'controlled-protected-token')
    start = client.post('/api/slack/connect').json()
    state = parse_qs(urlsplit(start['url']).query)['state'][0]
    real_client = httpx.Client
    calls = []
    def handler(req):
        method = req.url.path.rsplit('/', 1)[-1]
        calls.append(method)
        responses = {'oauth.v2.access': {'ok': True, 'access_token': 'synthetic-oauth-token', 'team': {'id': 'T11'}},
                     'auth.test': {'ok': True, 'team_id': 'T11'}, 'conversations.info': {'ok': True},
                     'chat.getPermalink': {'ok': True, 'permalink': 'https://example.slack.com/archives/C11/p1700000000000001'},
                     'conversations.history': {'ok': True, 'messages': [{'ts': '1700000000.000001', 'text': 'Selected Slack statement.', 'user': 'U1'}]}}
        return httpx.Response(200, json=responses[method])
    monkeypatch.setattr(api.httpx, 'Client', lambda *args, **kwargs: real_client(*args, **{**kwargs, 'transport': httpx.MockTransport(handler)}))
    callback = client.get('/api/slack/callback', params={'state': state, 'code': 'synthetic-code'}, follow_redirects=False)
    assert callback.status_code == 303
    assert client.get('/api/slack/callback', params={'state': state, 'code': 'synthetic-code'}).status_code == 403
    project = cmd(client, 'project', {'name': 'Slack sample'})
    source = cmd(client, 'source', {'type': 'slack', 'container': 'T11:C11', 'label': 'Selected Slack channel'})
    rows = cmd(client, 'slack_fetch', {'source_id': source['id'], 'project_id': project['id'], 'consent': True})
    assert rows[0]['project_id'] == project['id'] and rows[0]['external_identity'] == 'U1'
    credential = client.app.state.service.store.all('credential')[0]
    assert 'synthetic-oauth-token' not in json_dump(credential)
    cmd(client, 'slack_disconnect')
    assert client.post('/api/command', json={'action': 'slack_fetch', 'payload': {'source_id': source['id'], 'consent': True}}).status_code == 409
    assert not any('postMessage' in call for call in calls)


def json_dump(value):
    import json
    return json.dumps(value)


def test_vexa_fetch_pipeline_and_source_revision(client, monkeypatch):
    import httpx
    from app import api
    login(client)
    monkeypatch.setenv('VEXA_API_KEY', 'synthetic-key')
    real_client = httpx.Client
    counter = [0]
    def handler(req):
        counter[0] += 1
        return httpx.Response(200, json={'status': 'completed', 'segments': [{'segment_id': 'stable-segment', 'text': 'Pilot date.' if counter[0] == 1 else 'Revised pilot date.', 'speaker': 'Alex', 'completed': True, 'start': 1, 'end': 2}]})
    monkeypatch.setattr(api.httpx, 'Client', lambda *args, **kwargs: real_client(*args, **{**kwargs, 'transport': httpx.MockTransport(handler)}))
    p = cmd(client, 'project', {'name': 'Meeting project'})
    s = cmd(client, 'source', {'type': 'vexa', 'container': 'google_meet:abc-defg-hij', 'label': 'Selected meeting'})
    payload = {'source_id': s['id'], 'project_id': p['id'], 'consent': True}
    first = cmd(client, 'vexa_fetch', payload)[0]
    second = cmd(client, 'vexa_fetch', payload)[0]
    assert second['previous_id'] == first['id'] and second['author'] == 'Alex'
    assert client.get('/api/evidence/' + first['id'] + '/original').json()['original']['segments'][0]['text'] == 'Pilot date.'


def test_shorter_document_retires_removed_passages(client):
    login(client)
    project = cmd(client, 'project', {'name': 'Document changes'})
    source = cmd(client, 'source', {'type': 'manual', 'container': 'versioned-file', 'label': 'Versioned document'})
    data = {'source_id': source['id'], 'project_id': project['id'], 'consent': 'true'}
    first = client.post('/api/upload', data=data, files={'file': ('same.md', b'First passage.\n\nRemoved passage.')}).json()['evidence']
    client.post('/api/upload', data=data, files={'file': ('same.md', b'First passage.')})
    current = client.get('/api/projects/' + project['id'] + '/evidence').json()['evidence']
    assert [e['text'] for e in current] == ['First passage.']
    assert not client.app.state.service.current(first[1])


def test_slack_channel_refresh_does_not_retire_thread_replies(client, monkeypatch):
    import httpx
    from app import api
    login(client)
    monkeypatch.setenv('SLACK_BOT_TOKEN', 'synthetic-token')
    monkeypatch.setenv('SLACK_TEAM_ID', 'T11')
    real_client = httpx.Client
    def handle(req):
        method = req.url.path.rsplit('/', 1)[-1]
        responses = {'auth.test': {'ok': True, 'team_id': 'T11'}, 'conversations.info': {'ok': True},
                     'chat.getPermalink': {'ok': True, 'permalink': ''},
                     'conversations.history': {'ok': True, 'messages': [{'ts': '1700000000.000001', 'text': 'Parent statement.'}]}}
        return httpx.Response(200, json=responses[method])
    monkeypatch.setattr(api.httpx, 'Client', lambda *args, **kwargs: real_client(*args, **{**kwargs, 'transport': httpx.MockTransport(handle)}))
    p = cmd(client, 'project', {'name': 'Slack threads'})
    s = cmd(client, 'source', {'type': 'slack', 'container': 'T11:C11', 'label': 'Channel'})
    service = client.app.state.service
    actor = service.actor(client.cookies.get('cg_session'))
    reply = service.ingest(actor, {'source_id': s['id'], 'project_id': p['id'], 'consent': True,
        'passages': [{'item_id': '1700000001.000001', 'text': 'Thread reply.', 'details': {'thread_ts': '1700000000.000001'}}]})[0]
    cmd(client, 'slack_fetch', {'source_id': s['id'], 'project_id': p['id'], 'consent': True})
    assert service.current(reply)
