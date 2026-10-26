import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import launcher


@pytest.fixture(autouse=True)
def normal_launcher_account(monkeypatch):
    # Existing launcher flows describe a normal user, independent of the test host account.
    monkeypatch.setattr(launcher, 'offline_sandbox_account', lambda: False)


def test_offline_account_refuses_server_start_without_installing_or_contacting_sources(monkeypatch, capsys):
    monkeypatch.setattr(launcher, 'offline_sandbox_account', lambda: True)
    monkeypatch.setattr(launcher, 'ensure_env', lambda: pytest.fail('Blocked launch must not mutate setup'))
    monkeypatch.setattr(launcher.subprocess, 'call', lambda *a: pytest.fail('Must not start a server'))
    assert launcher.main([]) == 1
    output = capsys.readouterr().out
    assert 'No server was started' in output and 'File Explorer' in output


@pytest.mark.skipif(sys.platform != 'win32', reason='Windows launcher')
def test_launcher_preserves_broken_environment(tmp_path):
    (tmp_path / 'start.bat').write_bytes((Path(__file__).resolve().parents[1] / 'start.bat').read_bytes())
    binary = tmp_path / '.venv/Scripts/python.exe'
    binary.parent.mkdir(parents=True)
    binary.write_bytes(b'broken environment fixture')
    env = dict(os.environ)
    env.pop('CONTEXTGUARD_PYTHON', None)
    env['CONTEXTGUARD_NO_PAUSE'] = '1'
    result = subprocess.run(['cmd.exe', '/d', '/c', 'start.bat'], cwd=tmp_path, env=env,
                            capture_output=True, text=True, timeout=10)
    assert result.returncode != 0
    assert binary.read_bytes() == b'broken environment fixture'
    assert 'preserved' in result.stdout


def test_settings_creation_preserves_existing_keys(tmp_path):
    (tmp_path / '.env.example').write_text('MODEL_API_KEY=\n')
    launcher.ensure_env(tmp_path)
    assert (tmp_path / '.env').read_text() == 'MODEL_API_KEY=\n'
    (tmp_path / '.env').write_text('MODEL_API_KEY=synthetic-private-setting\n')
    launcher.ensure_env(tmp_path)
    assert 'synthetic-private-setting' in (tmp_path / '.env').read_text()


def test_setup_status_never_displays_secret_values(tmp_path, capsys):
    (tmp_path / '.env').write_text('MODEL_API_KEY=synthetic-private-setting\nMODEL_BASE_URL=https://example.invalid/v1\nMODEL_NAME=example\n')
    launcher.show_status(tmp_path)
    output = capsys.readouterr().out
    assert 'synthetic-private-setting' not in output
    assert 'live access not verified' in output


@pytest.mark.parametrize('matches', [True, False])
def test_probe_distinguishes_this_app_from_other_services(matches):
    import json
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    from threading import Thread
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps({'product': 'ContextGuard' if matches else 'Another product',
                                         'version': 'rebuild', 'instance_id': 'test-instance'}).encode())
        def log_message(self, *args):
            pass
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        status, health = launcher.probe(f'http://127.0.0.1:{server.server_port}', expected='test-instance')
        assert status == ('ours' if matches else 'occupied')
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def test_repeat_launch_reuses_server_without_starting_another(monkeypatch):
    monkeypatch.setattr(launcher, 'ensure_env', lambda: None)
    monkeypatch.setattr(launcher, 'probe', lambda: ('ours', {'setup_required': False}))
    monkeypatch.setattr(launcher, 'missing_dependencies', lambda: [])
    monkeypatch.setattr(launcher, 'show_status', lambda: None)
    monkeypatch.setenv('CONTEXTGUARD_NO_BROWSER', '1')
    monkeypatch.setattr(launcher.subprocess, 'call', lambda *args: pytest.fail('Must not start another server'))
    assert launcher.main([]) == 0


def test_occupied_port_never_installs_or_stops_anything(monkeypatch, capsys):
    monkeypatch.setattr(launcher, 'ensure_env', lambda: None)
    monkeypatch.setattr(launcher, 'probe', lambda: ('occupied', None))
    monkeypatch.setattr(launcher, 'install_dependencies', lambda: pytest.fail('Must not install on a port conflict'))
    assert launcher.main([]) == 1
    assert 'No process was stopped' in capsys.readouterr().out


def test_old_api_reuses_updated_instance_on_alternate_port(monkeypatch, capsys):
    monkeypatch.setattr(launcher, 'ensure_env', lambda: None)
    monkeypatch.setattr(launcher, 'URL', 'http://127.0.0.1:8027')
    def fake_probe(url=None):
        if url == 'http://127.0.0.1:8028':
            return 'ours', {'version': 'rebuild', 'api_revision': 'conversation-v1'}
        return 'ours', {'version': 'rebuild'}
    monkeypatch.setattr(launcher, 'probe', fake_probe)
    monkeypatch.setattr(launcher, 'missing_dependencies', lambda: [])
    monkeypatch.setattr(launcher, 'show_status', lambda: None)
    monkeypatch.setenv('CONTEXTGUARD_NO_BROWSER', '1')
    monkeypatch.setattr(launcher.subprocess, 'call', lambda *args: pytest.fail('Must reuse the updated app'))
    assert launcher.main([]) == 0
    assert launcher.URL.endswith(':8028')
    assert 'older rebuild' in capsys.readouterr().out
