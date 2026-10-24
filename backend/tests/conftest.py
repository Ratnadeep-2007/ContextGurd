import time

import pytest
from fastapi.testclient import TestClient

from backend.app.main import create_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    for key in ["MODEL_API_KEY", "GROQ_API_KEY", "NVIDIA_API_KEY"]:
        monkeypatch.delenv(key, raising=False)
    with TestClient(create_app(str(tmp_path / "test.sqlite3"))) as client:
        yield client


def finish(client, case_id):
    for _ in range(200):
        case = client.get(f"/api/cases/{case_id}").json()
        if case.get("run") and case["run"]["status"] != "running":
            assert case["run"]["status"] == "completed", case["run"]
            return case
        time.sleep(.02)
    raise AssertionError("Run did not finish")


@pytest.fixture
def sample(client):
    case = client.post("/api/cases/sample").json()
    response = client.post(f"/api/cases/{case['id']}/analyze", json={"version": case["version"]})
    assert response.status_code == 202
    return finish(client, case["id"])
