import io
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import serve


def test_identifies_existing_contextguard(monkeypatch):
    responses = iter([{"status": "ok"}, {"info": {"title": "ContextGuard"}}])
    monkeypatch.setattr(serve, "urlopen", lambda *args, **kwargs: io.BytesIO(json.dumps(next(responses)).encode()))
    assert serve.already_running()


def test_does_not_mistake_other_service_for_contextguard(monkeypatch):
    responses = iter([{"status": "ok"}, {"info": {"title": "Another service"}}])
    monkeypatch.setattr(serve, "urlopen", lambda *args, **kwargs: io.BytesIO(json.dumps(next(responses)).encode()))
    assert not serve.already_running()


def test_second_launch_returns_success(monkeypatch, capsys):
    monkeypatch.setattr(serve, "already_running", lambda: True)
    assert serve.main() == 0
    assert "already running" in capsys.readouterr().out


def test_missing_frontend_has_actionable_error(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(serve, "already_running", lambda: False)
    monkeypatch.setattr(serve, "ROOT", tmp_path)
    assert serve.main() == 1
    assert "npm.cmd run build" in capsys.readouterr().err


@pytest.mark.skipif(sys.platform != 'win32', reason='Windows batch launcher regression')
def test_broken_virtual_environment_is_preserved(tmp_path):
    launcher = Path(__file__).resolve().parents[2] / 'start.bat'
    (tmp_path / 'start.bat').write_bytes(launcher.read_bytes())
    binary = tmp_path / '.venv' / 'Scripts' / 'python.exe'
    binary.parent.mkdir(parents=True)
    binary.write_bytes(b'broken environment fixture')
    result = subprocess.run(['cmd.exe', '/d', '/c', 'start.bat'], cwd=tmp_path, env={**os.environ, 'CONTEXTGUARD_NO_PAUSE': '1', 'CONTEXTGUARD_NO_BROWSER': '1'}, capture_output=True, text=True, timeout=10)
    assert result.returncode != 0
    assert binary.read_bytes() == b'broken environment fixture'
    assert 'preserved' in result.stdout and '.venv-backup' in result.stdout


def test_partial_frontend_build_has_actionable_error(monkeypatch,tmp_path,capsys):
    monkeypatch.setattr(serve,'already_running',lambda:False)
    monkeypatch.setattr(serve,'ROOT',tmp_path)
    dist=tmp_path/'frontend'/'dist';dist.mkdir(parents=True)
    (dist/'index.html').write_text('<html></html>')
    assert serve.main()==1
    assert 'Frontend build missing' in capsys.readouterr().err
