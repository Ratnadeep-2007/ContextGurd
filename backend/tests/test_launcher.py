import io
import json

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
