from fastapi.testclient import TestClient

from app.api import create_app
from app.contracts import ConversationRoutes, Passage
from app.review import Reviews
from app.adapters import AdapterFailure
from test_api import login, cmd
from test_intake import poll


class ControlledModels:
    def classify(self, units, projects, context):
        return ConversationRoutes(routes=[{'unit_id': u['id'], 'disposition': 'matched',
            'project_id': projects[0]['id'], 'reason': 'Controlled fictional source test.'} for u in units]), 'Controlled model'

    def analyze(self, goal, evidence, decisions):
        return Reviews.fixture(evidence), 'Controlled model'


def test_vexa_join_stop_fetch_controls_and_processing(tmp_path, monkeypatch):
    from app import intake_api
    calls = []
    class Vexa:
        def __init__(self, *args, **kwargs):
            pass
        def status(self):
            return []
        def join(self, platform, native, consent, passcode):
            calls.append(('join', platform, native))
            assert consent is True
            return {'status': 'requested', 'note': 'Host admission required.'}
        def stop(self, platform, native):
            calls.append(('stop', platform, native))
            return {'status': 'stop_requested', 'note': 'Stop requested.'}
        def fetch(self, platform, native):
            calls.append(('fetch', platform, native))
            return [Passage(item_id='s1', text='Orchid: The security approval is pending.',
                            author='Fictional speaker', location='Meeting, 10s')], {}
    monkeypatch.setattr(intake_api, 'Vexa', Vexa)
    monkeypatch.setenv('VEXA_API_KEY', 'fictional-vexa-key')
    with TestClient(create_app(tmp_path / 'vexa.sqlite3', providers=ControlledModels(), load_settings=False)) as client:
        login(client)
        cmd(client, 'project', {'name': 'Orchid'})
        check = client.post('/api/connections/vexa/check', json={})
        assert check.status_code == 200 and check.json()['ok'] is True
        assert client.get('/api/state').json()['connection_details']['vexa']['status'] == 'Connected'
        payload = {'link': 'https://meet.google.com/abc-defg-hij', 'consent': True}
        assert client.post('/api/meetings', json={**payload, 'operation': 'join'}).json()['status'] == 'requested'
        assert client.post('/api/meetings', json={**payload, 'operation': 'stop'}).json()['status'] == 'stop_requested'
        response = client.post('/api/meetings', json={**payload, 'operation': 'fetch', 'model_consent': True})
        assert response.status_code == 200
        job = poll(client, response.json()['job']['id'])
        assert job['status'] == 'complete' and len(job['review_ids']) == 1
        review = client.get('/api/reviews/' + job['review_ids'][0]).json()
        assert review['evidence'][0]['author'] == 'Fictional speaker'
        assert [c[0] for c in calls] == ['join', 'stop', 'fetch']


def test_connection_failure_updates_status_without_fabricating_connection(tmp_path, monkeypatch):
    from app import intake_api
    class Offline:
        def __init__(self, *args, **kwargs):
            pass
        def status(self):
            raise AdapterFailure('Controlled Vexa service unavailable.')
    monkeypatch.setattr(intake_api, 'Vexa', Offline)
    monkeypatch.setenv('VEXA_API_KEY', 'fictional-vexa-key')
    with TestClient(create_app(tmp_path / 'offline.sqlite3', load_settings=False)) as client:
        login(client)
        assert client.post('/api/connections/vexa/check', json={}).status_code == 409
        details = client.get('/api/state').json()['connection_details']['vexa']
        assert details['status'] == 'Connection failed' and 'unavailable' in details['last_check']
        assert not client.app.state.service.store.all('intake')


def test_slack_selected_channel_processing_disconnect_and_missing_oauth(tmp_path, monkeypatch):
    from app import intake_api
    class Slack:
        def __init__(self, token, team):
            assert team == 'T11'
        def call(self, method, **kwargs):
            if method == 'auth.test':
                return {'ok': True, 'team_id': 'T11'}
            assert kwargs['types'] == 'public_channel'
            return {'channels': [{'id': 'C11', 'name': 'orchid', 'is_member': True},
                                 {'id': 'C22', 'name': 'other', 'is_member': False}]}
        def fetch(self, channel, thread, start, end):
            assert channel == 'C11'
            return [Passage(item_id='1700000000.000001', text='Orchid: The security approval is pending.')], {'complete': True}
    monkeypatch.setattr(intake_api, 'Slack', Slack)
    monkeypatch.setenv('SLACK_BOT_TOKEN', 'fictional-slack-token')
    monkeypatch.setenv('SLACK_TEAM_ID', 'T11')
    monkeypatch.delenv('SLACK_CLIENT_ID', raising=False)
    monkeypatch.delenv('SLACK_CLIENT_SECRET', raising=False)
    with TestClient(create_app(tmp_path / 'slack.sqlite3', providers=ControlledModels(), load_settings=False)) as client:
        login(client)
        cmd(client, 'project', {'name': 'Orchid'})
        assert client.post('/api/slack/connect', json={}).status_code == 409
        assert client.post('/api/connections/slack/check', json={}).status_code == 200
        assert client.get('/api/slack/channels').json()['channels'] == [{'id': 'C11', 'name': 'orchid'}]
        response = client.post('/api/slack/capture', json={'channel': 'C11', 'consent': True, 'model_consent': True})
        assert response.status_code == 202 and poll(client, response.json()['id'])['status'] == 'complete'
        cmd(client, 'slack_disconnect')
        assert client.post('/api/connections/slack/check', json={}).status_code == 409
        assert client.get('/api/state').json()['connection_details']['slack']['status'] == 'Not connected'
        assert client.post('/api/slack/local-connect', json={}).status_code == 200
        assert client.get('/api/state').json()['connection_details']['slack']['status'] == 'Connected'
        assert client.post('/api/connections/slack/check', json={}).status_code == 200
        assert client.get('/api/slack/channels').status_code == 200
