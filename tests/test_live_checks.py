import httpx
import pytest

from app.providers import failure_reason
from scripts.verify_live import FailPrimaryOnce, check_sources, only_provider, whatsapp_readiness
from scripts import launcher


def test_network_permission_diagnostic_does_not_echo_secret():
    secret = 'synthetic-sensitive-value'
    original = PermissionError(13, secret)
    exc = httpx.ConnectError(secret)
    exc.__cause__ = original
    reason = failure_reason(exc)
    assert 'permissions' in reason and secret not in reason


def test_http_status_diagnostic_does_not_echo_response_or_key():
    request = httpx.Request('POST', 'https://example.invalid/private', headers={'Authorization': 'Bearer synthetic-secret'})
    response = httpx.Response(401, request=request, text='sensitive-response')
    exc = httpx.HTTPStatusError('sensitive-error', request=request, response=response)
    assert '401' in failure_reason(exc)
    assert 'sensitive' not in failure_reason(exc) and 'synthetic' not in failure_reason(exc)


def test_individual_provider_mask_restores_original_keys(monkeypatch):
    for key in ('MODEL_API_KEY', 'GROQ_API_KEY', 'NVIDIA_API_KEY'):
        monkeypatch.setenv(key, 'synthetic-' + key)
    import os
    with only_provider('GROQ_API_KEY'):
        assert not os.environ['MODEL_API_KEY'] and os.environ['GROQ_API_KEY']
    assert os.environ['MODEL_API_KEY'] == 'synthetic-MODEL_API_KEY'


def test_sources_without_consent_never_contact_clients():
    class Args:
        sources = True
        source_consent = False
        project = 'Explicit project'
    assert check_sources(None, None, Args())[0]['status'] == 'needs_selection_and_consent'


def test_controlled_failover_does_not_send_the_primary(monkeypatch):
    transport = FailPrimaryOnce()
    with pytest.raises(httpx.ConnectError):
        transport.handle_request(httpx.Request('POST', 'https://example.invalid'))
    assert not transport.first
    transport.close()


def test_live_check_launcher_is_explicit_and_does_not_start_server(monkeypatch):
    monkeypatch.setattr(launcher, 'ensure_env', lambda: None)
    monkeypatch.setattr(launcher, 'probe', lambda: ('occupied', None))
    monkeypatch.setattr(launcher, 'missing_dependencies', lambda: [])
    monkeypatch.setattr(launcher, 'show_status', lambda: None)
    calls = []
    monkeypatch.setattr(launcher.subprocess, 'call', lambda args: calls.append(args) or 2)
    assert launcher.main(['--live-check']) == 2
    assert calls[0][-2:] == ['--live', '--fallback']
    assert 'verify_live.py' in calls[0][1]
