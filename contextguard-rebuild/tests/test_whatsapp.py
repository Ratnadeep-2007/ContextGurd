import base64
import json
import os
import shutil
import time
from pathlib import Path

import pytest

from fastapi.testclient import TestClient

from app.api import create_app
from app.whatsapp import WhatsApp
from app.service import Rejected
from test_api import login, cmd
from test_intake import poll
from test_source_controls import ControlledModels


class ControlledWhatsApp:
    def __init__(self):
        self.calls = []
        self.selected = []
        self.messages = []
        self.connected = False

    def close(self):
        pass

    def summary(self, workspace):
        return {'runtime_available': True, 'configured': True, 'status': 'connected' if self.connected else 'awaiting_scan',
                'selected': self.selected, 'message_count': len(self.messages), 'qr_available': not self.connected, 'chats': []}

    def call(self, workspace, method, payload=None):
        self.calls.append((workspace, method, payload))
        if method == 'connect':
            return {'status': 'awaiting_scan'}
        if method == 'select':
            self.selected = payload['ids']
            return {'selected': self.selected}
        if method == 'messages':
            return {'messages': self.messages}
        if method == 'ack':
            self.messages = []
            return {'ok': True}
        if method == 'qr':
            return {'png': base64.b64encode(b'fictional-qr-image').decode()}
        if method == 'chats':
            return {'chats': [{'id': '123@g.us', 'name': 'Fictional group'}]}

    def disconnect(self, workspace):
        self.connected = False
        self.selected = []
        self.messages = []
        return {'status': 'disconnected'}


def test_whatsapp_pair_selection_capture_and_citations(tmp_path):
    app = create_app(tmp_path / 'wa.sqlite3', providers=ControlledModels(), load_settings=False)
    reader = ControlledWhatsApp()
    app.state.whatsapp = reader
    with TestClient(app) as client:
        login(client)
        project = cmd(client, 'project', {'name': 'Orchid'})
        assert client.post('/api/whatsapp/connect', json={'consent': False}).status_code == 403
        assert not reader.calls
        assert client.post('/api/whatsapp/connect', json={'consent': True}).json()['status'] == 'awaiting_scan'
        assert client.get('/api/whatsapp/qr').content == b'fictional-qr-image'
        reader.connected = True
        assert client.post('/api/whatsapp/chats', json={}).json()['chats'][0]['id'] == '123@g.us'
        assert client.post('/api/whatsapp/select', json={'consent': True, 'ids': ['status@broadcast']}).status_code == 400
        assert client.post('/api/whatsapp/select', json={'consent': True, 'ids': ['123@g.us']}).status_code == 200
        reader.messages = [{'id': '123@g.us:m1', 'chat': '123@g.us', 'message_id': 'm1', 'revision': 1,
            'text': 'Orchid security approval is pending.', 'author': 'Fictional speaker',
            'external_identity': '7@s.whatsapp.net', 'timestamp': '2026-10-25T10:00:00Z'}]
        payload = {'consent': True, 'model_consent': False, 'project_ids': [project['id']]}
        assert client.post('/api/whatsapp/capture', json=payload).status_code == 403
        assert reader.messages
        payload['model_consent'] = True
        response = client.post('/api/whatsapp/capture', json=payload)
        assert response.status_code == 202, response.text
        job = poll(client, response.json()['id'])
        assert job['status'] == 'complete' and not reader.messages
        review = client.get('/api/reviews/' + job['review_ids'][0]).json()
        evidence = review['evidence'][0]
        assert evidence['author'] == 'Fictional speaker' and evidence['external_identity'] == '7@s.whatsapp.net'
        assert '123@g.us' in evidence['location'] and 'm1' in evidence['location']
        for finding in review['findings']:
            for citation in finding['citations']:
                assert citation['quote'] in next(e['text'] for e in review['evidence'] if e['id'] == citation['evidence_id'])
        assert client.post('/api/whatsapp/disconnect', json={}).json()['status'] == 'disconnected'


def test_whatsapp_admin_boundary_and_unselected_source_rejection(tmp_path):
    app = create_app(tmp_path / 'wa-permissions.sqlite3', load_settings=False)
    reader = ControlledWhatsApp()
    app.state.whatsapp = reader
    with TestClient(app) as client:
        login(client)
        project = cmd(client, 'project', {'name': 'Orchid'})
        member = cmd(client, 'user', {'username': 'Reader', 'password': 'fictional-reader-password'})
        reader.connected = True
        reader.selected = ['123@g.us']
        reader.messages = [{'chat': '999@g.us', 'text': 'Unselected secret.'}]
        payload = {'consent': True, 'model_consent': True, 'project_ids': [project['id']]}
        assert client.post('/api/whatsapp/capture', json=payload).status_code == 409
        assert not app.state.service.store.all('intake')
        client.post('/api/login', json={'username': member['username'], 'password': 'fictional-reader-password'})
        before = len(reader.calls)
        for path in ['connect', 'disconnect', 'chats', 'capture', 'select']:
            body = payload if path == 'capture' else {'consent': True, 'ids': []} if path == 'select' else {'consent': True} if path == 'connect' else {}
            assert client.post('/api/whatsapp/' + path, json=body).status_code == 403
        for path in ['status', 'qr']:
            assert client.get('/api/whatsapp/' + path).status_code == 403
        assert len(reader.calls) == before
        assert client.get('/api/state').json()['connection_details']['whatsapp']['selected'] == []


def test_whatsapp_missing_runtime_has_no_socket_or_plaintext_key(tmp_path):
    reader = WhatsApp(tmp_path)
    assert not reader.summary('workspace')['runtime_available']
    try:
        reader.call('workspace', 'connect')
        assert False
    except Rejected as exc:
        assert exc.status == 409
    assert not reader.sessions and not (tmp_path / 'data').exists()


@pytest.mark.skipif(os.name != 'nt' or not shutil.which('node'), reason='Windows encrypted bridge process')
def test_private_stdio_process_and_session_vault_with_fake_socket(tmp_path, monkeypatch):
    """Real stdio/AES process; explicitly fake socket and key protector, no network or DPAPI claim."""
    def fixture_protection(value, decrypt=False):
        return base64.b64decode(value).decode() if decrypt else base64.b64encode(value.encode()).decode()
    monkeypatch.setattr('app.whatsapp.transform', fixture_protection)
    source = Path(__file__).resolve().parents[1] / 'connectors/whatsapp'
    target = tmp_path / 'connectors/whatsapp'
    target.mkdir(parents=True)
    for name in ('bridge.mjs', 'reader.mjs', 'vault.mjs', 'package.json'):
        shutil.copyfile(source / name, target / name)
    modules = target / 'node_modules'
    fake = modules / 'baileys'
    fake.mkdir(parents=True)
    (fake / 'package.json').write_text(json.dumps({'type': 'module', 'main': 'index.mjs'}))
    (fake / 'index.mjs').write_text('''
import {EventEmitter} from 'node:events';
export const BufferJSON={};
export const proto={Message:{AppStateSyncKeyData:{fromObject:x=>x}}};
export const initAuthCreds=()=>({testCredential:'fictional-private-session'});
export default function socket(config){
 if(config.syncFullHistory!==false||config.markOnlineOnConnect!==false||config.shouldSyncHistoryMessage()!==false)throw Error('unsafe configuration');
 const ev=new EventEmitter();
 const qr=setTimeout(()=>{ev.emit('connection.update',{qr:'fictional-pairing-qr'});ev.emit('creds.update',{registered:true});},10);
 const open=setTimeout(()=>ev.emit('connection.update',{connection:'open'}),600);
 const incoming=setInterval(()=>ev.emit('messages.upsert',{messages:[
 {key:{id:'m1',remoteJid:'123@g.us'},message:{conversation:'Authorized fixture text'},messageTimestamp:1800000000},
 {key:{id:'m2',remoteJid:'999@g.us'},message:{conversation:'Unselected secret fixture'},messageTimestamp:1800000000}]}),200);
 const end=()=>{clearTimeout(qr);clearTimeout(open);clearInterval(incoming);};
 return {ev,user:{id:'1@s.whatsapp.net'},end,logout:async()=>end(),groupFetchAllParticipating:async()=>({'123@g.us':{id:'123@g.us',subject:'Fictional group'}})};
}
''')
    qr = modules / 'qrcode'
    qr.mkdir()
    (qr / 'package.json').write_text(json.dumps({'type': 'module', 'main': 'index.mjs'}))
    (qr / 'index.mjs').write_text("export default {toBuffer:async()=>Buffer.from('fictional-image')};")
    reader = WhatsApp(tmp_path)
    def await_status(expected):
        for _ in range(60):
            value = reader.summary('fixture-workspace')
            if value['status'] == expected:
                return value
            time.sleep(.03)
        pytest.fail('Controlled bridge did not reach expected state.')
    try:
        reader.call('fixture-workspace', 'connect')
        await_status('awaiting_scan')
        assert base64.b64decode(reader.call('fixture-workspace', 'qr')['png']) == b'fictional-image'
        await_status('connected')
        reader.call('fixture-workspace', 'select', {'ids': ['123@g.us']})
        for _ in range(60):
            rows = reader.call('fixture-workspace', 'messages')['messages']
            if rows:
                break
            time.sleep(.03)
        assert len(rows) == 1 and rows[0]['text'] == 'Authorized fixture text'
        directory = tmp_path / 'data/whatsapp/fixture-workspace'
        assert b'fictional-private-session' not in (directory / 'session.enc').read_bytes()
        assert len(base64.b64decode(fixture_protection((directory / 'vault.dpapi').read_text(), decrypt=True))) == 32
        reader.disconnect('fixture-workspace')
        assert not list(directory.iterdir()) and not reader.sessions
    finally:
        reader.close()


@pytest.mark.skipif(os.name != 'nt', reason='Windows protection failure boundary')
def test_whatsapp_refuses_pairing_when_windows_key_protection_fails(tmp_path, monkeypatch):
    reader = WhatsApp(tmp_path)
    monkeypatch.setattr(reader, 'available', lambda: True)
    def denied(*args, **kwargs):
        raise RuntimeError('Controlled protection failure')
    monkeypatch.setattr('app.whatsapp.transform', denied)
    with pytest.raises(Rejected, match='Windows session protection failed'):
        reader.call('fixture-workspace', 'connect')
    assert not reader.sessions
    assert not list((tmp_path / 'data/whatsapp/fixture-workspace').iterdir())
