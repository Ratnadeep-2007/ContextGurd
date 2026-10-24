import time
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Importing main creates a module-level app. Keep its startup/recovery logic away
# from the user's live SQLite database, even when pytest runs beside the app.
os.environ['CONTEXTGUARD_DB'] = str(Path(__file__).resolve().parents[2] / 'artifacts' / 'pytest-bootstrap' / 'contextguard.sqlite3')
os.environ['MEM0_BASE_URL'] = ''
os.environ['MEM0_API_KEY'] = ''
os.environ['CONTEXTGUARD_API_ONLY'] = '1'
from backend.app.main import create_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    for key in ["MODEL_API_KEY", "GROQ_API_KEY", "NVIDIA_API_KEY"]:
        monkeypatch.delenv(key, raising=False)
    with TestClient(create_app(str(tmp_path / "test.sqlite3"), serve_frontend=False)) as client:
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
