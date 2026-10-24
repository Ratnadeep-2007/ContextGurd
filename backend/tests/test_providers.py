import httpx
import pytest

from backend.app.providers import ProviderError, complete, strict_schema
from backend.app.schemas import PlanOutput


def test_strict_schema_requires_all_fields():
    schema = strict_schema(PlanOutput.model_json_schema())
    assert schema["additionalProperties"] is False
    assert schema["$defs"]["PlannedCheck"]["required"] == list(schema["$defs"]["PlannedCheck"]["properties"])


def test_missing_keys_are_honest(monkeypatch):
    for key in ["MODEL_API_KEY","GROQ_API_KEY","NVIDIA_API_KEY"]: monkeypatch.delenv(key,raising=False)
    with pytest.raises(ProviderError,match="No enabled AI provider"):
        complete("Planner","Plan",{},PlanOutput)


@pytest.mark.parametrize("bad", [{"choices":[]}, {"choices":[{"message":{"content":"not json"}}]}, {"choices":[{"message":{}}]}])
def test_malformed_response_falls_back(monkeypatch,bad):
    monkeypatch.setenv("MODEL_API_KEY","test-meta"); monkeypatch.setenv("GROQ_API_KEY","test-groq"); monkeypatch.delenv("NVIDIA_API_KEY",raising=False)
    seen=[]
    def handler(request):
        seen.append(str(request.url))
        return httpx.Response(200,json=bad if "meta.ai" in str(request.url) else {"choices":[{"message":{"content":"{\"checks\": []}"}}],"usage":{"prompt_tokens":10,"completion_tokens":5}})
    result,trace,warnings=complete("Planner","Plan",{},PlanOutput,transport=httpx.MockTransport(handler))
    assert result.checks==[] and trace.provider=="groq" and warnings
    assert len(seen)==3


def test_disabled_fallback_does_not_send_to_groq(monkeypatch):
    monkeypatch.delenv("MODEL_API_KEY",raising=False);monkeypatch.setenv("GROQ_API_KEY","test")
    with pytest.raises(ProviderError): complete("Planner","Plan",{},PlanOutput,allow_fallback=False)


def test_auth_error_falls_back_without_leaking_key(monkeypatch):
    monkeypatch.setenv("MODEL_API_KEY","secret-not-for-output");monkeypatch.setenv("GROQ_API_KEY","test");monkeypatch.delenv("NVIDIA_API_KEY",raising=False)
    seen=[]
    def handler(request):
        seen.append(str(request.url))
        return httpx.Response(401) if "meta.ai" in str(request.url) else httpx.Response(200,json={"choices":[{"message":{"content":"{\"checks\":[]}"}}]})
    _,trace,warnings=complete("Planner","Plan",{},PlanOutput,transport=httpx.MockTransport(handler))
    assert trace.provider=="groq" and len(seen)==2
    assert "secret-not-for-output" not in str(warnings)


def test_network_permission_failure_is_actionable_and_does_not_repeat(monkeypatch):
    monkeypatch.setenv('MODEL_API_KEY', 'secret-meta-key')
    monkeypatch.setenv('GROQ_API_KEY', 'secret-groq-key')
    monkeypatch.delenv('NVIDIA_API_KEY', raising=False)
    seen = []
    def handler(request):
        seen.append(str(request.url))
        raise httpx.ConnectError('secret-meta-key must not appear in output', request=request) from PermissionError(13, 'secret-groq-key')
    with pytest.raises(ProviderError) as caught:
        complete('Planner', 'Plan', {}, PlanOutput, transport=httpx.MockTransport(handler))
    message = str(caught.value)
    assert 'meta: outbound connection blocked by local network permissions' in message
    assert 'groq: outbound connection blocked by local network permissions' in message
    assert len(seen) == 2
    assert 'secret-meta-key' not in message and 'secret-groq-key' not in message


def test_all_auth_failures_preserve_safe_diagnostics(monkeypatch):
    monkeypatch.setenv('MODEL_API_KEY', 'secret-key')
    monkeypatch.delenv('GROQ_API_KEY', raising=False)
    monkeypatch.delenv('NVIDIA_API_KEY', raising=False)
    def handler(request):
        return httpx.Response(401, text='secret provider response body')
    with pytest.raises(ProviderError) as caught:
        complete('Planner', 'Plan', {}, PlanOutput, transport=httpx.MockTransport(handler))
    assert 'HTTP 401' in str(caught.value)
    assert 'secret' not in str(caught.value)


def test_timeout_failure_identifies_cause_without_exception_text(monkeypatch):
    monkeypatch.setenv('MODEL_API_KEY', 'secret-key')
    monkeypatch.delenv('GROQ_API_KEY', raising=False)
    monkeypatch.delenv('NVIDIA_API_KEY', raising=False)
    def handler(request):
        raise httpx.ReadTimeout('secret exception details', request=request)
    with pytest.raises(ProviderError, match='request timed out') as caught:
        complete('Planner', 'Plan', {}, PlanOutput, transport=httpx.MockTransport(handler))
    assert 'secret' not in str(caught.value)
