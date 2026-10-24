"""Serve the production frontend and API on loopback; run npm run build first."""
import os
import json
import socket
import sys
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

def already_running() -> bool:
    """Identify our app before treating an occupied port as a successful launch."""
    try:
        with urlopen("http://127.0.0.1:8017/api/health", timeout=2) as response:
            health = json.load(response)
        with urlopen("http://127.0.0.1:8017/openapi.json", timeout=2) as response:
            schema = json.load(response)
        return isinstance(health, dict) and isinstance(schema, dict) and health.get("status") == "ok" and schema.get("info", {}).get("title") == "ContextGuard"
    except (URLError, TimeoutError, OSError, ValueError):
        return False


def main() -> int:
    if already_running():
        print("ContextGuard is already running: http://localhost:8017", flush=True)
        return 0
    if not (ROOT / "frontend/dist/index.html").is_file() or not (ROOT / 'frontend/dist/assets').is_dir():
        print("Frontend build missing. Run npm.cmd install and npm.cmd run build inside the frontend folder, then launch start.bat again.", file=sys.stderr)
        return 1
    try:
        import uvicorn
        import fastapi  # noqa: F401 -- fail with useful setup guidance before booting
    except ImportError:
        print("Python dependencies are missing. Run: python -m pip install -r backend/requirements-tested.txt", file=sys.stderr)
        return 1
    try:
        with socket.socket() as check:
            check.bind(("127.0.0.1", 8017))
    except OSError:
        print("Port 8017 is occupied by another service or an unhealthy ContextGuard instance. Close that service, then run start.bat again. No process was stopped.", file=sys.stderr)
        return 1
    print("Starting ContextGuard: http://localhost:8017\nKeep this window open. Press Ctrl+C to stop.", flush=True)
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8017, log_level="info")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
